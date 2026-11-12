#!/usr/bin/env python3
import argparse
from urllib.error import HTTPError, URLError
from songsterr_bridge import songsterr_response
from gametabs_bridge import search as gametabs_search, import_tab as gametabs_import, GameTabsLoginRequired
from tabs_access import authorized, login, serve_private_viewer, config as access_config
from youtube_sync_store import get_sync, save_sync
from songsterr_import_store import find_import, remember_import
from tab_catalog import identity as catalog_identity, matches as catalog_matches
import cgi
import json
import mimetypes
import os
import re
import sys
import threading
import zipfile
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from xml.etree import ElementTree
from urllib.parse import parse_qs, unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build_tab_index import VALID_EXT, build_entries, normalize_url_prefix

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
UPLOAD_SUBDIR = "uploads"
SAFE_XML_EXTS = {".xml", ".musicxml"}
ZIP_EXTS = {".gpx", ".capx", ".mxl"}
GP_BINARY_EXTS = {".gp", ".gp3", ".gp4", ".gp5"}
GP_SIGNATURES = (
    b"FICHIER GUITAR PRO",
    b"FICHIER GUITARE PRO",
    b"FILE GUITAR PRO",
)
BLOCKED_FILE_SIGNATURES = (
    (b"MZ", "Windows executable"),
    (b"\x7fELF", "Linux executable"),
    (b"PK\x03\x04", "ZIP archive"),
    (b"%PDF-", "PDF document"),
    (b"\x89PNG\r\n\x1a\n", "PNG image"),
    (b"GIF87a", "GIF image"),
    (b"GIF89a", "GIF image"),
    (b"\xff\xd8\xff", "JPEG image"),
)
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._()' +,-]+")
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
DEFAULT_SORT = "title-asc"
VALID_SORTS = {"title-asc", "title-desc", "recent", "played"}


def parse_args():
    parser = argparse.ArgumentParser(description="Serve RetroTerminal tab data and files.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=4080, type=int)
    parser.add_argument("--data-dir", default="/home/vex/tabs-host/data")
    parser.add_argument("--files-dir", default="/home/vex/tabs-archive")
    parser.add_argument("--allow-origin", default="https://retroterminal.net")
    parser.add_argument("--viewer-url", default="https://retroterminal.net/tabs/")
    parser.add_argument("--url-prefix", default="/files")
    parser.add_argument("--play-counts-file", default="/home/vex/tabs-host/data/play-counts.json")
    return parser.parse_args()


class TabsHostHandler(SimpleHTTPRequestHandler):
    server_version = "RetroTerminalTabs/1.0"
    upload_lock = threading.Lock()
    index_lock = threading.Lock()
    index_cache = None
    index_cache_mtime = None
    index_cache_path = None
    play_counts_lock = threading.Lock()
    play_counts_cache = None
    play_counts_mtime = None

    def __init__(
        self,
        *args,
        data_dir,
        files_dir,
        allow_origin,
        viewer_url,
        url_prefix,
        play_counts_file,
        **kwargs,
    ):
        self.data_dir = Path(data_dir).resolve()
        self.files_dir = Path(files_dir).resolve()
        self.allow_origin = allow_origin
        self.viewer_url = viewer_url
        self.url_prefix = normalize_url_prefix(url_prefix)
        self.play_counts_file = Path(play_counts_file).resolve()
        super().__init__(*args, **kwargs)

    def end_headers(self):
        requested_origin = self.headers.get('Origin', '')
        known_origins = (access_config() or {}).get('origins', [])
        self.send_header("Access-Control-Allow-Origin", requested_origin if requested_origin in known_origins else self.allow_origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Expose-Headers", "Accept-Ranges, Content-Length, Content-Range")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/session':
            return self.send_json(HTTPStatus.OK, {'authenticated': authorized(self)})
        if parsed.path != '/healthz' and not authorized(self):
            return self.send_json(HTTPStatus.UNAUTHORIZED, {'error': 'Please sign in.'})
        if parsed.path == '/api/youtube-sync':
            return get_sync(self, parse_qs(parsed.query))
        if parsed.path == '/api/gametabs/search':
            try:
                return self.send_json(HTTPStatus.OK, gametabs_search(parse_qs(parsed.query)))
            except ValueError as error:
                return self.send_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
            except (HTTPError, URLError, TimeoutError, OSError, KeyError, TypeError):
                return self.send_json(HTTPStatus.BAD_GATEWAY, {'error': 'GameTabs search is unavailable. Try again later.'})
        if parsed.path in ('/api/songsterr/search', '/api/songsterr/sync'):
            try:
                return self.send_json(HTTPStatus.OK, songsterr_response(parsed.path, parse_qs(parsed.query)))
            except ValueError as error:
                return self.send_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
            except (HTTPError, URLError, TimeoutError, OSError, KeyError, TypeError):
                return self.send_json(HTTPStatus.BAD_GATEWAY, {'error': 'Songsterr is unavailable. You can still paste a YouTube URL and mark timing manually.'})
        if parsed.path in ('/viewer', '/viewer/'):
            return serve_private_viewer(self)

        if parsed.path in {"", "/"}:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", self.viewer_url)
            self.end_headers()
            return

        if parsed.path == "/data/tabs.json":
            return self.serve_file(self.data_dir / "tabs.json", cache_control="no-store")

        if parsed.path == "/api/tabs":
            return self.serve_tabs_page(parsed.query)

        if parsed.path == "/healthz":
            return self.send_json(HTTPStatus.OK, {"ok": True})

        if parsed.path.startswith("/files/"):
            try:
                relative_path = unquote(parsed.path[len("/files/"):]).lstrip("/")
                return self.serve_file(
                    self.safe_join(self.files_dir, relative_path),
                    cache_control="private, no-store",
                )
            except PermissionError:
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self):
        if urlparse(self.path).path == '/api/login':
            return login(self)
        origin = self.headers.get('Origin')
        if origin and origin not in (access_config() or {}).get('origins', []):
            return self.send_json(HTTPStatus.FORBIDDEN, {'error': 'Origin is not allowed.'})
        if not authorized(self):
            return self.send_json(HTTPStatus.UNAUTHORIZED, {'error': 'Please sign in.'})
        if urlparse(self.path).path == '/api/youtube-sync':
            return save_sync(self)
        if urlparse(self.path).path == '/api/gametabs/import':
            return self.import_gametabs()
        if urlparse(self.path).path == '/api/songsterr/import':
            return self.import_songsterr()
        if urlparse(self.path).path != "/upload":
            if urlparse(self.path).path == "/api/play":
                return self.record_play()
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0:
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing upload body."})
        if content_length > MAX_UPLOAD_BYTES:
            return self.send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": f"Upload exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."},
            )

        try:
            uploaded_name, file_data = self.parse_upload()
            safe_name = self.sanitize_filename(uploaded_name)
            suffix = Path(safe_name).suffix.lower()
            self.validate_upload(safe_name, suffix, file_data)

            upload_dir = self.files_dir / UPLOAD_SUBDIR
            upload_dir.mkdir(parents=True, exist_ok=True)
            destination = self.make_unique_destination(upload_dir, safe_name)

            with self.upload_lock:
                destination.write_bytes(file_data)
                self.rebuild_index()

            return self.send_json(
                HTTPStatus.CREATED,
                {
                    "message": "Upload complete.",
                    "title": destination.stem,
                    "file": self.make_public_file_url(destination),
                },
            )
        except ValueError as err:
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(err)})
        except Exception as err:
            return self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Upload failed: {err}"})

    def do_HEAD(self):
        if not authorized(self):
            return self.send_json_body(HTTPStatus.UNAUTHORIZED, {'error': 'Please sign in.'}, head_only=True)
        parsed = urlparse(self.path)

        if parsed.path in {"", "/"}:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", self.viewer_url)
            self.end_headers()
            return

        if parsed.path == "/data/tabs.json":
            return self.serve_file(self.data_dir / "tabs.json", head_only=True, cache_control="no-store")

        if parsed.path == "/api/tabs":
            return self.serve_tabs_page(parsed.query, head_only=True)

        if parsed.path.startswith("/files/"):
            try:
                relative_path = unquote(parsed.path[len("/files/"):]).lstrip("/")
                return self.serve_file(
                    self.safe_join(self.files_dir, relative_path),
                    head_only=True,
                    cache_control="private, no-store",
                )
            except PermissionError:
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def safe_join(self, base_dir: Path, relative_path: str) -> Path:
        candidate = (base_dir / relative_path).resolve()
        if os.path.commonpath([str(base_dir), str(candidate)]) != str(base_dir):
            raise PermissionError("Path escapes base directory")
        return candidate

    def serve_file(self, file_path: Path, head_only: bool = False, cache_control: str = "no-store"):
        try:
            file_path = file_path.resolve()
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.send_header("Cache-Control", cache_control)
        self.end_headers()

        if head_only:
            return

        with file_path.open("rb") as handle:
            self.wfile.write(handle.read())

    def send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json_body(self, status: int, payload: dict, head_only: bool = False):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def serve_tabs_page(self, query: str, head_only: bool = False):
        params = parse_qs(query, keep_blank_values=True)
        page = self.parse_positive_int(params.get("page", ["1"])[0], default=1)
        page_size = self.parse_positive_int(
            params.get("page_size", [str(DEFAULT_PAGE_SIZE)])[0],
            default=DEFAULT_PAGE_SIZE,
            maximum=MAX_PAGE_SIZE,
        )
        search = (params.get("search", [""])[0] or "").strip().lower()
        search_field = 'artist' if params.get('search_field', [''])[0] == 'artist' else 'all'
        artist_exact = params.get('artist_exact', [''])[0] == '1'
        sort = (params.get("sort", [DEFAULT_SORT])[0] or DEFAULT_SORT).strip()
        if sort not in VALID_SORTS:
            sort = DEFAULT_SORT
        folder = (params.get("folder", [""])[0] or "").strip()

        entries = self.get_enriched_entries()
        if search:
            entries = [item for item in entries if catalog_matches(item, search, search_field, artist_exact)]
        if folder:
            entries = [item for item in entries if item.get("folder") == folder]

        entries = self.sort_entries(entries, sort)
        folders = self.get_folder_options()

        total = len(entries)
        max_page = max(1, (total + page_size - 1) // page_size)
        page = min(page, max_page)
        start = (page - 1) * page_size
        end = start + page_size
        items = entries[start:end]

        return self.send_json_body(
            HTTPStatus.OK,
            {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": page < max_page,
                "sort": sort,
                "search": search,
                "search_field": search_field,
                "folder": folder,
                "folders": folders,
            },
            head_only=head_only,
        )

    def parse_positive_int(self, value: str, default: int, maximum: int | None = None):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        if parsed < 1:
            parsed = default
        if maximum is not None:
            parsed = min(parsed, maximum)
        return parsed

    def get_index_entries(self):
        output_path = self.data_dir / "tabs.json"
        if not output_path.exists():
            return []

        current_mtime = output_path.stat().st_mtime_ns
        cache = type(self)
        with self.index_lock:
            if cache.index_cache is not None and cache.index_cache_mtime == current_mtime and cache.index_cache_path == output_path:
                return cache.index_cache

            with output_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)

            loaded = [dict(item, **catalog_identity(item)) for item in loaded]
            cache.index_cache = loaded
            cache.index_cache_mtime = current_mtime
            cache.index_cache_path = output_path
            return loaded

    def get_play_counts(self):
        with self.play_counts_lock:
            return self._get_play_counts_locked()

    def _get_play_counts_locked(self):
        if not self.play_counts_file.exists():
            return {}

        current_mtime = self.play_counts_file.stat().st_mtime_ns
        if self.play_counts_cache is not None and self.play_counts_mtime == current_mtime:
            return self.play_counts_cache

        with self.play_counts_file.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)

        normalized = {}
        for raw_key, raw_value in loaded.items():
            key = self.normalize_file_key(raw_key)
            if not key:
                continue
            normalized[key] = int(normalized.get(key, 0)) + int(raw_value)

        self.play_counts_cache = normalized
        self.play_counts_mtime = current_mtime
        return normalized

    def save_play_counts(self, counts: dict):
        self.play_counts_file.parent.mkdir(parents=True, exist_ok=True)
        with self.play_counts_file.open("w", encoding="utf-8") as handle:
            json.dump(counts, handle, ensure_ascii=False, indent=2)
        self.play_counts_cache = counts
        self.play_counts_mtime = self.play_counts_file.stat().st_mtime_ns

    def get_enriched_entries(self):
        counts = self.get_play_counts()
        entries = []
        for item in self.get_index_entries():
            enriched = dict(item)
            enriched["play_count"] = int(counts.get(self.normalize_file_key(item["file"]), 0))
            entries.append(enriched)
        return entries

    def get_folder_options(self):
        folders = sorted({item.get("folder", "Root") for item in self.get_index_entries()})
        return folders

    def sort_entries(self, entries, sort: str):
        if sort == "title-desc":
            return sorted(entries, key=lambda item: item["title"].lower(), reverse=True)
        if sort == "recent":
            return sorted(
                entries,
                key=lambda item: (-int(item.get("modified_at", 0)), item["title"].lower()),
            )
        if sort == "played":
            return sorted(
                entries,
                key=lambda item: (-int(item.get("play_count", 0)), item["title"].lower()),
            )
        return sorted(entries, key=lambda item: item["title"].lower())

    def parse_upload(self):
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError("Upload must use multipart/form-data.")

        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
        }
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=environ,
        )
        file_item = form["file"] if "file" in form else None
        if file_item is None or not getattr(file_item, "filename", ""):
            raise ValueError("Choose a file to upload.")

        file_data = file_item.file.read(MAX_UPLOAD_BYTES + 1)
        if not file_data:
            raise ValueError("Uploaded file is empty.")
        if len(file_data) > MAX_UPLOAD_BYTES:
            raise ValueError(f"Upload exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")

        return file_item.filename, file_data

    def import_gametabs(self):
        # Authenticated GameTabs downloading must use its supported login flow.
        # Until that is configured, the bridge fails closed without writing files.
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024:
                raise ValueError('Invalid import request.')
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise ValueError('Invalid import request.')
            gametabs_import(request.get('id', ''))
            return self.send_json(HTTPStatus.NOT_IMPLEMENTED, {'error': 'GameTabs import is not configured yet.'})
        except GameTabsLoginRequired as error:
            return self.send_json(HTTPStatus.CONFLICT, {'error': str(error), 'code': 'gametabs_login_required'})
        except (ValueError, TypeError) as error:
            return self.send_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
        except (HTTPError, URLError, TimeoutError, OSError):
            return self.send_json(HTTPStatus.BAD_GATEWAY, {'error': 'GameTabs is unavailable. No tabs were changed.'})

    def import_songsterr(self):
        import tempfile
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024:
                raise ValueError('Invalid import request.')
            song_id = str(json.loads(self.rfile.read(length)).get('id', ''))
            if not re.fullmatch(r'[1-9][0-9]{0,9}', song_id):
                raise ValueError('Invalid Songsterr song ID.')
            with self.upload_lock:
                # Check before fetching/converting, under the same lock as file creation.
                existing = find_import(self, int(song_id))
                if existing:
                    return self.send_json(HTTPStatus.OK, {'title': existing.stem, 'file': self.make_public_file_url(existing), 'songsterr_id': int(song_id), 'alreadyExists': True})
                from songsterr_vendor.gen_gp import fetch_all_tracks, generate_gp
                meta, tracks = fetch_all_tracks(int(song_id))
                name = self.sanitize_filename(str(meta.get('artist', '')) + ' - ' + str(meta.get('title', song_id)) + '.gp')
                with tempfile.TemporaryDirectory() as folder:
                    generated = Path(folder) / 'import.gp'
                    generate_gp(tracks, generated, meta)
                    data = generated.read_bytes()
                if len(data) > MAX_UPLOAD_BYTES:
                    raise ValueError('Generated tab is too large.')
                destination_dir = self.files_dir / UPLOAD_SUBDIR
                destination_dir.mkdir(parents=True, exist_ok=True)
                destination = self.make_unique_destination(destination_dir, name)
                destination.write_bytes(data)
                remember_import(self, int(song_id), destination)
                self.rebuild_index()
            return self.send_json(HTTPStatus.CREATED, {'title': destination.stem, 'file': self.make_public_file_url(destination), 'songsterr_id': int(song_id)})
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            return self.send_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
        except Exception:
            return self.send_json(HTTPStatus.BAD_GATEWAY, {'error': 'Songsterr import failed. Your existing tabs were not modified.'})

    def sanitize_filename(self, filename: str) -> str:
        base_name = Path(filename).name.strip()
        if not base_name:
            raise ValueError("Invalid filename.")

        cleaned = SAFE_NAME_RE.sub("_", base_name).strip("._ ")
        if not cleaned:
            raise ValueError("Filename contains no usable characters.")

        suffix = Path(cleaned).suffix.lower()
        if suffix not in VALID_EXT:
            raise ValueError("Unsupported file type.")

        stem = Path(cleaned).stem[:120].strip() or "tab"
        return f"{stem}{suffix}"

    def record_play(self):
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0 or content_length > 4096:
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid play payload."})

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON payload."})

        file_url = (payload.get("file") or "").strip()
        file_key = self.normalize_file_key(file_url)
        if not file_key:
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing file value."})

        valid_files = {self.normalize_file_key(item["file"]) for item in self.get_index_entries()}
        if file_key not in valid_files:
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Unknown tab file."})

        with self.play_counts_lock:
            counts = dict(self._get_play_counts_locked())
            counts[file_key] = int(counts.get(file_key, 0)) + 1
            self.save_play_counts(counts)

        return self.send_json(HTTPStatus.OK, {"ok": True, "file": file_url, "play_count": counts[file_key]})

    def normalize_file_key(self, file_url: str):
        if not file_url:
            return ""
        parsed = urlparse(file_url)
        if parsed.scheme or parsed.netloc:
            return parsed.path or ""
        return file_url

    def validate_upload(self, filename: str, suffix: str, file_data: bytes):
        if suffix in SAFE_XML_EXTS:
            self.validate_xml(file_data)
            return
        if suffix in ZIP_EXTS:
            self.validate_zip(file_data)
            return
        if suffix in GP_BINARY_EXTS:
            self.validate_gp_binary(filename, file_data)
            return
        raise ValueError("Unsupported file type.")

    def validate_xml(self, file_data: bytes):
        sample = file_data[:2048].decode("utf-8", errors="ignore").lower()
        if "<!doctype" in sample or "<!entity" in sample:
            raise ValueError("XML uploads may not contain DOCTYPE or ENTITY declarations.")
        try:
            ElementTree.fromstring(file_data)
        except ElementTree.ParseError as err:
            raise ValueError(f"Invalid XML file: {err}") from err

    def validate_zip(self, file_data: bytes):
        if not zipfile.is_zipfile(self.bytes_as_file(file_data)):
            raise ValueError("Zip-based tab file is invalid.")

    def validate_gp_binary(self, filename: str, file_data: bytes):
        header = file_data[:2048]
        if len(header) < 16:
            raise ValueError("Binary tab file is too small.")
        header_lower = header.lower()
        if b"<html" in header_lower or b"<!doctype html" in header_lower or b"<script" in header_lower:
            raise ValueError("Upload looks like HTML, not a Guitar Pro file.")
        if header.startswith(b"#!"):
            raise ValueError("Upload looks like a script, not a Guitar Pro file.")
        if header.startswith(b"PK\x03\x04"):
            if self.is_valid_zip_upload(file_data):
                return
            raise ValueError(f"{filename} is a zip container, but it is not a valid tab archive.")
        for signature, description in BLOCKED_FILE_SIGNATURES:
            if header.startswith(signature):
                raise ValueError(f"Upload looks like a {description}, not a Guitar Pro file.")
        if not any(signature in header for signature in GP_SIGNATURES):
            if self.looks_like_plain_text(file_data):
                raise ValueError(f"{filename} looks like plain text, not a Guitar Pro binary file.")

    def looks_like_plain_text(self, file_data: bytes):
        sample = file_data[:4096]
        if not sample:
            return False
        if b"\x00" in sample:
            return False
        text_bytes = sum(
            1 for byte in sample
            if byte in (9, 10, 13) or 32 <= byte <= 126
        )
        return text_bytes / len(sample) > 0.95

    def is_valid_zip_upload(self, file_data: bytes):
        try:
            with zipfile.ZipFile(self.bytes_as_file(file_data)) as archive:
                names = archive.namelist()
                if not names:
                    return False
                for name in names:
                    normalized = name.replace("\\", "/")
                    if normalized.startswith("/") or ".." in normalized.split("/"):
                        return False
                return True
        except zipfile.BadZipFile:
            return False

    def bytes_as_file(self, file_data: bytes):
        import io

        return io.BytesIO(file_data)

    def make_unique_destination(self, upload_dir: Path, filename: str) -> Path:
        candidate = upload_dir / filename
        if not candidate.exists():
            return candidate

        stem = candidate.stem
        suffix = candidate.suffix
        for index in range(2, 1000):
            alt = upload_dir / f"{stem}-{index}{suffix}"
            if not alt.exists():
                return alt
        raise ValueError("Too many files with the same name already exist.")

    def rebuild_index(self):
        entries = build_entries(str(self.files_dir), self.url_prefix, "")
        output_path = self.data_dir / "tabs.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = output_path.with_suffix('.json.tmp')
        with temporary_path.open("w", encoding="utf-8") as handle:
            json.dump(entries, handle, ensure_ascii=False, indent=2)
        temporary_path.replace(output_path)
        with self.index_lock:
            cache = type(self)
            cache.index_cache = [dict(item, **catalog_identity(item)) for item in entries]
            cache.index_cache_mtime = output_path.stat().st_mtime_ns
            cache.index_cache_path = output_path

    def make_public_file_url(self, destination: Path) -> str:
        rel_path = destination.relative_to(self.files_dir).as_posix()
        return f"{self.url_prefix}/{rel_path}"


def main():
    args = parse_args()
    handler = partial(
        TabsHostHandler,
        data_dir=args.data_dir,
        files_dir=args.files_dir,
        allow_origin=args.allow_origin,
        viewer_url=args.viewer_url,
        url_prefix=args.url_prefix,
        play_counts_file=args.play_counts_file,
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving tabs host on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
