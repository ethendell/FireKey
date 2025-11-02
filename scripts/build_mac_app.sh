#!/usr/bin/env bash
set -euo pipefail

# Resolve the repository root relative to this script regardless of where it is called from
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

cd "${REPO_ROOT}"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "PyInstaller is required. Install it with 'pip install pyinstaller'." >&2
  exit 1
fi

ICON_PATH="assets/firekey.icns"
ICON_ARGS=()

if [[ -f "${ICON_PATH}" ]]; then
  ICON_ARGS=(--icon "${ICON_PATH}")
else
  echo "Warning: ${ICON_PATH} not found. The app will use the default PyInstaller icon." >&2
fi

PYINSTALLER_ARGS=(
  --noconfirm
  --windowed
  --onefile
  --name "FireKEY"
  "${ICON_ARGS[@]}"
  main.py
)

# Clean previous build artifacts to avoid stale bundles
rm -rf build dist FireKEY.spec

pyinstaller "${PYINSTALLER_ARGS[@]}"

APP_BUNDLE="dist/FireKEY.app"
INFO_PLIST="${APP_BUNDLE}/Contents/Info.plist"
RESOURCES_DIR="${APP_BUNDLE}/Contents/Resources"
RESOURCE_ICON="${RESOURCES_DIR}/firekey.icns"

if [[ ! -f "${INFO_PLIST}" ]]; then
  echo "Error: ${INFO_PLIST} not found. PyInstaller may have failed." >&2
  exit 1
fi

python3 "${SCRIPT_DIR}/update_plist.py" "${INFO_PLIST}"

if [[ -f "${ICON_PATH}" ]]; then
  mkdir -p "${RESOURCES_DIR}"
  cp "${ICON_PATH}" "${RESOURCE_ICON}"
fi

echo "macOS application bundle created at ${APP_BUNDLE}"
