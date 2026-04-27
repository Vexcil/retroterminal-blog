#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/vex/retroterminal-blog}"
TABS_SOURCE_DIR="${TABS_SOURCE_DIR:-/home/vex/tabs-archive}"
TABS_HOST_ROOT="${TABS_HOST_ROOT:-/home/vex/tabs-host}"
TABS_DATA_DIR="${TABS_DATA_DIR:-$TABS_HOST_ROOT/data}"
TABS_PUBLIC_ORIGIN="${TABS_PUBLIC_ORIGIN:-https://tabs.retroterminal.net}"
TABS_URL_PREFIX="${TABS_URL_PREFIX:-/files}"

mkdir -p "$TABS_DATA_DIR"

python3 "$REPO_DIR/build_tab_index.py" \
  --tabs-dir "$TABS_SOURCE_DIR" \
  --output "$TABS_DATA_DIR/tabs.json" \
  --url-prefix "$TABS_URL_PREFIX" \
  --file-base-url "$TABS_PUBLIC_ORIGIN"

echo "Tabs index written to $TABS_DATA_DIR/tabs.json"
