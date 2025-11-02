#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

cd "${REPO_ROOT}"

APP_PATH="dist/FireKEY.app"
PKG_NAME="FireKEY.pkg"
IDENTIFIER="com.firekey.app"
VERSION="1.0"

if [ ! -d "${APP_PATH}" ]; then
  echo "${APP_PATH} not found. Run scripts/build_mac_app.sh first." >&2
  exit 1
fi

if ! command -v pkgbuild >/dev/null 2>&1; then
  echo "pkgbuild is required. It ships with Xcode command line tools." >&2
  exit 1
fi

rm -f "${PKG_NAME}"

PKG_ROOT=$(mktemp -d)
trap 'rm -rf "${PKG_ROOT}"' EXIT
mkdir -p "${PKG_ROOT}/Applications"
cp -R "${APP_PATH}" "${PKG_ROOT}/Applications/"

pkgbuild \
  --root "${PKG_ROOT}" \
  --identifier "${IDENTIFIER}" \
  --version "${VERSION}" \
  --install-location / \
  "${PKG_NAME}"

echo "Installer package created at ${PKG_NAME}"
