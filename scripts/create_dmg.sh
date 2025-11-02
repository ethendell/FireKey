#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

cd "${REPO_ROOT}"

APP_PATH="dist/FireKEY.app"
DMG_NAME="FireKEY-Installer.dmg"

if [ ! -d "${APP_PATH}" ]; then
  echo "${APP_PATH} not found. Run scripts/build_mac_app.sh first." >&2
  exit 1
fi

if ! command -v create-dmg >/dev/null 2>&1; then
  echo "create-dmg is required. Install it with 'brew install create-dmg'." >&2
  exit 1
fi

rm -f "${DMG_NAME}"

create-dmg \
  --volname "FireKEY Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --app-drop-link 425 200 \
  --icon "FireKEY.app" 175 200 \
  "${DMG_NAME}" "dist/"

echo "Disk image created at ${DMG_NAME}"
