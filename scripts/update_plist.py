#!/usr/bin/env python3
"""Ensure required metadata keys are present in a macOS Info.plist file."""

from __future__ import annotations

import plistlib
import sys
from pathlib import Path

REQUIRED_KEYS = {
    "CFBundleName": "FireKEY",
    "CFBundleDisplayName": "FireKEY",
    "CFBundleExecutable": "FireKEY",
    "CFBundleIdentifier": "com.firekey.app",
    "CFBundleVersion": "1.0",
    "CFBundleIconFile": "firekey.icns",
    "LSApplicationCategoryType": "public.app-category.productivity",
    "NSHighResolutionCapable": True,
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: update_plist.py /path/to/Info.plist", file=sys.stderr)
        return 2

    plist_path = Path(sys.argv[1])
    if not plist_path.is_file():
        print(f"Error: {plist_path} does not exist or is not a file.", file=sys.stderr)
        return 1

    with plist_path.open("rb") as fp:
        plist_data = plistlib.load(fp)

    updated = False
    for key, value in REQUIRED_KEYS.items():
        if plist_data.get(key) != value:
            plist_data[key] = value
            updated = True

    if updated:
        with plist_path.open("wb") as fp:
            plistlib.dump(plist_data, fp)
        print(f"Updated {plist_path} with required FireKEY metadata.")
    else:
        print(f"{plist_path} already contains the required FireKEY metadata.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
