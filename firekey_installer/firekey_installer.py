import platform
import shutil
import subprocess
import threading
import urllib.request
import zipfile
from pathlib import Path
from time import sleep

import tkinter as tk
from tkinter import messagebox, ttk


APP_NAME = "FireKEY"
REPO_ZIP_URL = "https://github.com/YourRepo/FireKEY/archive/refs/heads/main.zip"
APPLICATIONS_DIR = Path("/Applications")
APP_BUNDLE_NAME = f"{APP_NAME}.app"
APP_BUNDLE_PATH = APPLICATIONS_DIR / APP_BUNDLE_NAME
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "firekey_temp"
ICON_PATH = BASE_DIR / "assets" / "firekey_icon.png"
POST_INSTALL_SCRIPT = BASE_DIR / "install_scripts" / "post_install.sh"


class FireKeyInstaller:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FireKEY Installer")
        self.root.geometry("480x320")
        self.root.resizable(False, False)

        if ICON_PATH.exists():
            try:
                icon = tk.PhotoImage(file=str(ICON_PATH))
                self.root.iconphoto(False, icon)
            except tk.TclError:
                # Ignore icon load failures so the installer can run without the asset
                pass

        title_label = tk.Label(root, text="🔥 FireKEY Setup", font=("Helvetica", 18, "bold"))
        title_label.pack(pady=15)

        info_label = tk.Label(
            root,
            text=(
                "This installer will set up FireKEY, install dependencies, "
                "and place it in Applications."
            ),
            wraplength=420,
            justify="center",
        )
        info_label.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=360, mode="determinate")
        self.progress.pack(pady=15)

        self.status = tk.Label(root, text="Ready to install.", fg="gray")
        self.status.pack(pady=5)

        self.install_btn = tk.Button(root, text="Install FireKEY", command=self.start_install)
        self.install_btn.pack(pady=10)

        self.quit_btn = tk.Button(root, text="Quit", command=root.quit)
        self.quit_btn.pack(side="bottom", pady=10)

    def start_install(self) -> None:
        self.install_btn.config(state="disabled")
        threading.Thread(target=self.run_installation, daemon=True).start()

    def run_installation(self) -> None:
        steps = [
            ("Checking system...", self.check_system),
            ("Installing Homebrew...", self.install_homebrew),
            ("Installing dependencies...", self.install_dependencies),
            ("Downloading FireKEY...", self.download_firekey),
            ("Installing FireKEY app...", self.install_firekey),
            ("Finalizing setup...", self.finalize_install),
        ]

        total_steps = len(steps)

        for index, (label, action) in enumerate(steps, start=1):
            self.update_status(label)
            try:
                action()
            except Exception as exc:
                self.update_status(f"Error: {exc}")
                messagebox.showerror("FireKEY Installer", f"Installation failed: {exc}")
                self.install_btn.config(state="normal")
                return

            self.progress["value"] = (index / total_steps) * 100
            sleep(0.5)

        self.update_status("Installation complete!")
        messagebox.showinfo("FireKEY Installer", "FireKEY installed successfully!")
        self.launch_firekey()

    def update_status(self, message: str) -> None:
        self.status.config(text=message)
        self.root.update_idletasks()

    # Installation steps -------------------------------------------------
    def check_system(self) -> None:
        if platform.system() != "Darwin":
            raise RuntimeError("This installer is for macOS only.")

    def install_homebrew(self) -> None:
        if shutil.which("brew") is not None:
            return

        install_cmd = (
            '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )
        subprocess.run(install_cmd, shell=True, check=True)

    def install_dependencies(self) -> None:
        subprocess.run("brew install create-dmg", shell=True, check=False)
        subprocess.run(
            "pip3 install --upgrade pyinstaller pillow opencv-python pandas openai",
            shell=True,
            check=False,
        )

    def download_firekey(self) -> None:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        zip_path = TEMP_DIR / "firekey.zip"
        urllib.request.urlretrieve(REPO_ZIP_URL, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(TEMP_DIR)

        zip_path.unlink(missing_ok=True)

    def _find_extracted_root(self) -> Path:
        for child in TEMP_DIR.iterdir():
            if child.is_dir():
                return child
        raise RuntimeError("Unable to locate extracted FireKEY files.")

    def install_firekey(self) -> None:
        extracted_root = self._find_extracted_root()

        if APP_BUNDLE_PATH.exists():
            shutil.rmtree(APP_BUNDLE_PATH)

        macos_dir = APP_BUNDLE_PATH / "Contents" / "MacOS"
        resources_dir = APP_BUNDLE_PATH / "Contents" / "Resources"
        macos_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(extracted_root, macos_dir, dirs_exist_ok=True)

        if ICON_PATH.exists():
            shutil.copy(ICON_PATH, resources_dir / "firekey_icon.png")

        plist_content = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
    <key>CFBundleName</key>
    <string>FireKEY</string>
    <key>CFBundleExecutable</key>
    <string>main.py</string>
    <key>CFBundleIdentifier</key>
    <string>com.firekey.app</string>
    <key>CFBundleIconFile</key>
    <string>firekey_icon</string>
</dict>
</plist>
"""
        info_plist = APP_BUNDLE_PATH / "Contents" / "Info.plist"
        info_plist.write_text(plist_content, encoding="utf-8")

        if POST_INSTALL_SCRIPT.exists():
            subprocess.run(["/bin/bash", str(POST_INSTALL_SCRIPT), str(APP_BUNDLE_PATH)], check=False)

    def finalize_install(self) -> None:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)

    def launch_firekey(self) -> None:
        app_exec = APP_BUNDLE_PATH / "Contents" / "MacOS" / "main.py"
        if not app_exec.exists():
            messagebox.showwarning(
                "FireKEY Installer",
                "FireKEY was installed, but the launcher could not be found.",
            )
            return

        subprocess.Popen(["open", str(app_exec)])


def main() -> None:
    root = tk.Tk()
    app = FireKeyInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()
