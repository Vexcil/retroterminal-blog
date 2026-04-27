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
from urllib.parse import unquote

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
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._()' +,-]+")


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
        if self.path in {"", "/"}:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", self.viewer_url)
            self.end_headers()
            return

        if self.path == "/data/tabs.json":
            return self.serve_file(self.data_dir / "tabs.json", cache_control="no-store")

        if self.path == "/healthz":
            return self.send_json(HTTPStatus.OK, {"ok": True})

        if self.path.startswith("/files/"):
            try:
                relative_path = unquote(self.path[len("/files/"):]).lstrip("/")
                return self.serve_file(
                    self.safe_join(self.files_dir, relative_path),
                    cache_control="public, max-age=300",
                )
            except PermissionError:
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self):
        if self.path != "/upload":
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
        if self.path in {"", "/"}:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", self.viewer_url)
            self.end_headers()
            return

        if self.path == "/data/tabs.json":
            return self.serve_file(self.data_dir / "tabs.json", head_only=True, cache_control="no-store")

        if self.path.startswith("/files/"):
            try:
                relative_path = unquote(self.path[len("/files/"):]).lstrip("/")
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
        header = file_data[:128]
        if len(header) < 16:
            raise ValueError("Binary tab file is too small.")
        if b"<html" in header.lower() or header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
            raise ValueError("Upload does not look like a supported tab file.")
        if not any(signature in header for signature in GP_SIGNATURES):
            raise ValueError(f"{filename} does not match an expected Guitar Pro file signature.")

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
