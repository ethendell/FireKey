#!/bin/bash
set -euo pipefail

APP_BUNDLE_PATH="${1:-}"

if [[ -z "${APP_BUNDLE_PATH}" ]]; then
  echo "Usage: $0 <app_bundle_path>" >&2
  exit 1
fi

echo "Post-install hook executed for ${APP_BUNDLE_PATH}" >&2
