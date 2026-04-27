#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-/home/vex/retroterminal-blog/deploy/tabs-sync.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${REPO_DIR:=/home/vex/retroterminal-blog}"
: "${MAINFRAME_HOST:=the-mainframe.tail4c4915.ts.net}"
: "${MAINFRAME_USER:=vex}"
: "${MAINFRAME_TABS_PATH:?Set MAINFRAME_TABS_PATH in $ENV_FILE}"
: "${TABS_SOURCE_DIR:=/home/vex/tabs-archive}"
: "${RSYNC_SSH_IDENTITY:=/home/vex/.ssh/id_ed25519_status}"
: "${RSYNC_SSH_PORT:=22}"

mkdir -p "$TABS_SOURCE_DIR"

rsync \
  -av \
  --delete \
  --mkpath \
  -e "ssh -i $RSYNC_SSH_IDENTITY -p $RSYNC_SSH_PORT" \
  "$MAINFRAME_USER@$MAINFRAME_HOST:$MAINFRAME_TABS_PATH/" \
  "$TABS_SOURCE_DIR/"

REPO_DIR="$REPO_DIR" \
TABS_SOURCE_DIR="$TABS_SOURCE_DIR" \
"$REPO_DIR/scripts/build_tabs_host.sh"
