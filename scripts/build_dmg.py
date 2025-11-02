#!/usr/bin/env python3
"""
FireKEY macOS DMG Builder
---------------------------------
Builds a standalone FireKEY Installer.app and packages it into a DMG file.
"""

import subprocess
import shutil
import sys
from pathlib import Path

# --- CONFIGURATION ---
APP_NAME = "FireKEY Installer"
ICON_PATH = "assets/firekey_icon.icns"
ENTRY_SCRIPT = "firekey_installer.py"
DIST_DIR = Path("dist")
DMG_NAME = "FireKEY-Installer.dmg"
VOLUME_NAME = "FireKEY Setup"
SIGN_IDENTITY = None  # e.g. "Developer ID Application: Your Name (TEAMID)"
# ---------------------

def run(cmd, **kwargs):
    """Run a shell command with visible output."""
    print(f"➡️  Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True, **kwargs)

def ensure_dependencies():
    print("🔧 Checking dependencies...")
    run("pip install pyinstaller")
    if shutil.which("brew") is None:
        raise SystemExit("Homebrew not found. Please install it first.")
    run("brew install create-dmg")

def clean_previous_builds():
    print("🧹 Cleaning previous builds...")
    for entry in ['build', 'dist', f'{APP_NAME}.spec']:
        entry_path = Path(entry)
        if entry_path.is_dir():
            shutil.rmtree(entry_path, ignore_errors=True)
        elif entry_path.exists():
            entry_path.unlink()
    DIST_DIR.mkdir(exist_ok=True)

def build_app():
    print("🏗️  Building .app bundle...")
    cmd = (
        f'pyinstaller --noconfirm --windowed '
        f'--name "{APP_NAME}" '
        f'--icon "{ICON_PATH}" '
        f'{ENTRY_SCRIPT}'
    )
    run(cmd)
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        raise SystemExit("❌ PyInstaller failed to build the app.")
    print(f"✅ Created app at: {app_path}")
    return app_path

def code_sign(app_path):
    if SIGN_IDENTITY:
        print("🔏 Signing app...")
        run(f'codesign --deep --force --verify --verbose '
            f'--sign "{SIGN_IDENTITY}" "{app_path}")
    else:
        print("⚠️  No signing identity configured. Skipping code signing.")

def build_dmg(app_path):
    print("💽 Creating DMG...")
    dmg_path = DIST_DIR / DMG_NAME
    if dmg_path.exists():
        dmg_path.unlink()

    cmd = (
        f'create-dmg '
        f'--volname "{VOLUME_NAME}" '
        f'--window-pos 200 120 '
        f'--window-size 600 400 '
        f'--icon-size 100 '
        f'--app-drop-link 425 200 '
        f'--icon "{app_path.name}" 175 200 '
        f'"{DMG_NAME}" "{DIST_DIR}"'
    )
    run(cmd, cwd=DIST_DIR)
    print(f"✅ DMG created at: {dmg_path.resolve()}")
    return dmg_path

def main():
    print("🔥 FireKEY macOS Builder 🔥\n")
    ensure_dependencies()
    clean_previous_builds()
    app_path = build_app()
    code_sign(app_path)
    dmg_path = build_dmg(app_path)

    print("\n✅ Build complete!")
    print(f"App: {app_path}")
    print(f"DMG: {dmg_path}")
    print("\nYou can now upload the DMG for easy download.")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
