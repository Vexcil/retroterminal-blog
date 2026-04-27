#!/usr/bin/env python3
import argparse
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


def parse_args():
    parser = argparse.ArgumentParser(description="Serve RetroTerminal tab data and files.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=4080, type=int)
    parser.add_argument("--data-dir", default="/home/vex/tabs-host/data")
    parser.add_argument("--files-dir", default="/home/vex/tabs-archive")
    parser.add_argument("--allow-origin", default="https://retroterminal.net")
    parser.add_argument("--viewer-url", default="https://retroterminal.net/tabs/")
    parser.add_argument("--url-prefix", default="/files")
    return parser.parse_args()


class TabsHostHandler(SimpleHTTPRequestHandler):
    server_version = "RetroTerminalTabs/1.0"
    upload_lock = threading.Lock()
    index_lock = threading.Lock()
    index_cache = None
    index_cache_mtime = None

    def __init__(self, *args, data_dir, files_dir, allow_origin, viewer_url, url_prefix, **kwargs):
        self.data_dir = Path(data_dir).resolve()
        self.files_dir = Path(files_dir).resolve()
        self.allow_origin = allow_origin
        self.viewer_url = viewer_url
        self.url_prefix = normalize_url_prefix(url_prefix)
        super().__init__(*args, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", self.allow_origin)
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
                    cache_control="public, max-age=300",
                )
            except PermissionError:
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self):
        if urlparse(self.path).path != "/upload":
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
                    cache_control="public, max-age=300",
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
        sort = (params.get("sort", ["title-asc"])[0] or "title-asc").strip()

        entries = self.get_index_entries()
        if search:
            entries = [item for item in entries if search in item["title"].lower()]

        reverse = sort == "title-desc"
        entries = sorted(entries, key=lambda item: item["title"].lower(), reverse=reverse)

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
        with self.index_lock:
            if self.index_cache is not None and self.index_cache_mtime == current_mtime:
                return self.index_cache

            with output_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)

            self.index_cache = loaded
            self.index_cache_mtime = current_mtime
            return loaded

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
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(entries, handle, ensure_ascii=False, indent=2)
        with self.index_lock:
            self.index_cache = entries
            self.index_cache_mtime = output_path.stat().st_mtime_ns

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
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving tabs host on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
