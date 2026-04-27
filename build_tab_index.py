import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote, urljoin

DEFAULT_TABS_DIR = "assets/tabs"
DEFAULT_OUTPUT = "assets/data/tabs.json"
DEFAULT_URL_PREFIX = "/assets/tabs"

# File types alphaTab can use
VALID_EXT = {".gp", ".gp3", ".gp4", ".gp5", ".gpx", ".musicxml", ".xml", ".capx"}
SKIP_DIRS = {"__MACOSX", ".git"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a JSON index for the RetroTerminal tab viewer."
    )
    parser.add_argument(
        "--tabs-dir",
        default=DEFAULT_TABS_DIR,
        help="Filesystem directory containing tab files.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Path to the JSON file to write.",
    )
    parser.add_argument(
        "--url-prefix",
        default=DEFAULT_URL_PREFIX,
        help="URL prefix where the tab files are served, for example /assets/tabs or /files.",
    )
    parser.add_argument(
        "--file-base-url",
        default="",
        help="Optional absolute origin for hosted files, for example https://tabs.retroterminal.net.",
    )
    return parser.parse_args()


def make_title_from_filename(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename))[0]
    base = base.replace("_", " ")
    return " ".join(base.split())


def normalize_url_prefix(url_prefix: str) -> str:
    cleaned = (url_prefix or "").strip()
    if not cleaned:
        return ""
    if not cleaned.startswith("/"):
        cleaned = "/" + cleaned
    return cleaned.rstrip("/")


def make_file_url(relative_path: str, url_prefix: str, file_base_url: str) -> str:
    rel_url = quote(relative_path.replace(os.sep, "/"), safe="/()!,-._~'")
    joined_path = "/".join(part for part in [url_prefix.strip("/"), rel_url] if part)
    web_path = "/" + joined_path if joined_path else "/"

    if file_base_url:
        return urljoin(file_base_url.rstrip("/") + "/", web_path.lstrip("/"))

    return web_path


def should_skip_file(filename: str) -> bool:
    return filename.startswith(".") or filename.startswith("._")


def get_folder_info(relative_path: str):
    path_parts = Path(relative_path).parts
    folder = path_parts[0] if len(path_parts) > 1 else "Root"
    parent = Path(relative_path).parent
    folder_path = "" if str(parent) == "." else str(parent).replace(os.sep, "/")
    return folder, folder_path


def build_entries(tabs_dir: str, url_prefix: str, file_base_url: str):
    entries = []
    tabs_root = Path(tabs_dir).resolve()

    for root, dirs, files in os.walk(tabs_root):
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in SKIP_DIRS and not directory.startswith(".")
        ]

        for filename in files:
            if should_skip_file(filename):
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext not in VALID_EXT:
                continue

            full_path = Path(root) / filename
            rel_path = os.path.relpath(full_path, tabs_root)
            folder, folder_path = get_folder_info(rel_path)
            stat = full_path.stat()

            entries.append(
                {
                    "title": make_title_from_filename(filename),
                    "file": make_file_url(rel_path, url_prefix, file_base_url),
                    "filename": filename,
                    "path": rel_path.replace(os.sep, "/"),
                    "folder": folder,
                    "folder_path": folder_path,
                    "modified_at": int(stat.st_mtime),
                }
            )

    entries.sort(key=lambda item: item["title"].lower())
    return entries


def main():
    args = parse_args()
    url_prefix = normalize_url_prefix(args.url_prefix)
    entries = build_entries(args.tabs_dir, url_prefix, args.file_base_url)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)

    print(f"Wrote {len(entries)} entries to {output_path}")


if __name__ == "__main__":
    main()
