#!/usr/bin/env python3
"""
FireKEY GUI Installer for macOS
--------------------------------
Installs dependencies, downloads FireKEY, and creates a launchable app bundle.
"""

import os
import sys
import platform
import threading
import subprocess
import urllib.request
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from time import sleep

FIREKEY_URL = "https://github.com/YourRepo/FireKEY/archive/refs/heads/main.zip"
APP_PATH = "/Applications/FireKEY.app"
ICON_PATH = "assets/firekey_icon.png"


class FireKeyInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥 FireKEY Installer")
        self.root.geometry("480x320")
        self.root.resizable(False, False)

        try:
            self.root.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
        except Exception:
            pass

        tk.Label(root, text="🔥 FireKEY Setup", font=("Helvetica", 18, "bold")).pack(pady=15)
        tk.Label(
            root,
            text="This installer will set up FireKEY, install dependencies, "
                 "and place it in Applications.",
            wraplength=420, justify="center"
        ).pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=360, mode="determinate")
        self.progress.pack(pady=15)

        self.status = tk.Label(root, text="Ready to install.", fg="gray")
        self.status.pack(pady=5)

        self.install_btn = tk.Button(root, text="Install FireKEY", command=self.start_install)
        self.install_btn.pack(pady=10)

        tk.Button(root, text="Quit", command=root.quit).pack(side="bottom", pady=10)

    # -------------------------------------------------
    def start_install(self):
        self.install_btn.config(state="disabled")
        threading.Thread(target=self.run_installation, daemon=True).start()

    def update_status(self, msg):
        self.status.config(text=msg)
        self.root.update_idletasks()

    # -------------------------------------------------
    def run_installation(self):
        steps = [
            ("Checking system...", self.check_system),
            ("Installing Homebrew...", self.install_homebrew),
            ("Installing dependencies...", self.install_dependencies),
            ("Downloading FireKEY...", self.download_firekey),
            ("Installing FireKEY app...", self.install_firekey),
            ("Finalizing setup...", self.finalize_install),
        ]
        total = len(steps)
        for i, (text, func) in enumerate(steps, 1):
            self.update_status(text)
            try:
                func()
            except Exception as e:
                self.update_status(f"Error: {e}")
                messagebox.showerror("FireKEY Installer", f"Installation failed:\n{e}")
                self.install_btn.config(state="normal")
                return
            self.progress["value"] = (i / total) * 100
            sleep(0.5)
        self.update_status("Installation complete!")
        messagebox.showinfo("FireKEY Installer", "FireKEY installed successfully!")
        self.launch_firekey()

    # -------------------------------------------------
    def check_system(self):
        if platform.system() != "Darwin":
            raise RuntimeError("This installer is for macOS only.")

    def install_homebrew(self):
        if shutil.which("brew"):
            return  # Already installed

        self.update_status("Preparing to install Homebrew...")
        messagebox.showinfo(
            "Homebrew Required",
            "Homebrew will be installed using Terminal.\n\n"
            "When the Terminal window opens:\n"
            "1. Press RETURN to confirm installation.\n"
            "2. Enter your macOS password if prompted.\n"
            "3. Wait until installation completes.\n\n"
            "After that, return to FireKEY Installer and click OK."
        )

        script_path = os.path.expanduser("~/firekey_install_homebrew.sh")
        with open(script_path, "w") as f:
            f.write("""#!/bin/bash
echo "Installing Homebrew..."
arch -arm64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo "✅ Homebrew installation finished or already installed."
read -p "Press RETURN to close this window..."
""")
        os.chmod(script_path, 0o755)

        subprocess.run(f"open -a Terminal {script_path}", shell=True)

        messagebox.showinfo(
            "FireKEY Installer",
            "Once Homebrew finishes installing in Terminal, click OK to continue."
        )

        if not shutil.which("brew"):
            raise RuntimeError("Homebrew installation incomplete. Please rerun after finishing Homebrew setup.")

    def install_dependencies(self):
        self.update_status("Installing dependencies...")
        subprocess.run("brew install create-dmg", shell=True, check=False)
        subprocess.run(
            "pip3 install --upgrade pyinstaller pillow opencv-python pandas openai",
            shell=True, check=False
        )

    def download_firekey(self):
        self.update_status("Downloading FireKEY source...")
        local_zip = "firekey.zip"
        urllib.request.urlretrieve(FIREKEY_URL, local_zip)
        with zipfile.ZipFile(local_zip, "r") as zip_ref:
            zip_ref.extractall("firekey_temp")
        os.remove(local_zip)

    def install_firekey(self):
        self.update_status("Building FireKEY app bundle...")
        if os.path.exists(APP_PATH):
            shutil.rmtree(APP_PATH)
        os.makedirs(f"{APP_PATH}/Contents/MacOS", exist_ok=True)
        shutil.copytree("firekey_temp/FireKEY-main", f"{APP_PATH}/Contents/MacOS", dirs_exist_ok=True)
        # copy icon
        icon_dst = f"{APP_PATH}/Contents/Resources/firekey_icon.png"
        os.makedirs(os.path.dirname(icon_dst), exist_ok=True)
        shutil.copy(ICON_PATH, icon_dst)
        # write Info.plist
        plist = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
         "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
          <key>CFBundleName</key><string>FireKEY</string>
          <key>CFBundleExecutable</key><string>main.py</string>
          <key>CFBundleIdentifier</key><string>com.firekey.app</string>
          <key>CFBundleIconFile</key><string>firekey_icon</string>
          <key>LSApplicationCategoryType</key><string>public.app-category.productivity</string>
        </dict>
        </plist>"""
        with open(f"{APP_PATH}/Contents/Info.plist", "w") as f:
            f.write(plist)

    def finalize_install(self):
        self.update_status("Cleaning up temporary files...")
        shutil.rmtree("firekey_temp", ignore_errors=True)
        try:
            os.remove(os.path.expanduser("~/firekey_install_homebrew.sh"))
        except FileNotFoundError:
            pass

    def launch_firekey(self):
        app_exec = f"{APP_PATH}/Contents/MacOS/main.py"
        try:
            subprocess.Popen(["open", "-a", app_exec])
        except Exception:
            messagebox.showinfo(
                "Manual Launch Required",
                "Installation complete.\nYou can open FireKEY from your Applications folder."
            )


# -------------------------------------------------
if __name__ == "__main__":
    if platform.system() != "Darwin":
        print("FireKEY Installer is for macOS only.")
        sys.exit(1)
    root = tk.Tk()
    app = FireKeyInstaller(root)
    root.mainloop()
