"""FireKey desktop application for generating stock photo metadata."""
from __future__ import annotations

import base64
import glob
import io
import json
import os
import threading
from dataclasses import dataclass
from typing import Iterable, List, Optional

import pandas as pd
from openai import OpenAI
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")


@dataclass
class Metadata:
    filename: str
    title: str
    description: str
    keywords: List[str]


class FireKeyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FireKEY - Stock Metadata Generator")
        self.client: Optional[OpenAI] = None

        self.folder_path = tk.StringVar(value="No folder selected")

        self._build_ui()

    def _build_ui(self) -> None:
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(main_frame, text="FireKEY", font=("Segoe UI", 18, "bold"))
        title_label.pack(anchor=tk.W)

        description_label = tk.Label(
            main_frame,
            text="Generate stock photo metadata using OpenAI",
            font=("Segoe UI", 11),
        )
        description_label.pack(anchor=tk.W, pady=(0, 10))

        folder_frame = tk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        folder_label = tk.Label(folder_frame, text="Selected folder:")
        folder_label.pack(side=tk.LEFT)

        folder_entry = tk.Entry(folder_frame, textvariable=self.folder_path, state="readonly")
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_button = tk.Button(folder_frame, text="Browse", command=self.select_folder)
        browse_button.pack(side=tk.RIGHT)

        self.process_button = tk.Button(
            main_frame,
            text="Process Folder",
            command=self.start_processing,
            state=tk.NORMAL,
            width=20,
        )
        self.process_button.pack(pady=(0, 10))

        log_label = tk.Label(main_frame, text="Progress")
        log_label.pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def select_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log_message(f"Selected folder: {folder}")

    def start_processing(self) -> None:
        folder = self.folder_path.get()
        if not folder or folder == "No folder selected":
            messagebox.showwarning("FireKEY", "Please select a folder before processing.")
            return

        if not os.path.isdir(folder):
            messagebox.showerror("FireKEY", "The selected folder does not exist.")
            return

        self.process_button.config(state=tk.DISABLED)
        self.log_message("Starting processing...\n")

        thread = threading.Thread(target=self.process_folder, args=(folder,), daemon=True)
        thread.start()

    def process_folder(self, folder: str) -> None:
        try:
            image_files = self._collect_image_files(folder)
            if not image_files:
                self.log_message("No supported image files found in the selected folder.\n")
                return

            client = self._get_client()
            if client is None:
                return

            metadata_rows: List[Metadata] = []
            for index, image_path in enumerate(image_files, start=1):
                filename = os.path.basename(image_path)
                self.log_message(f"({index}/{len(image_files)}) Processing {filename}...")
                try:
                    metadata = self._generate_metadata(client, image_path)
                    metadata_rows.append(metadata)
                    self.log_message(f"Metadata generated for {filename}.\n")
                except Exception as exc:  # noqa: BLE001
                    self.log_message(f"Failed to process {filename}: {exc}\n")

            if metadata_rows:
                self._save_metadata(folder, metadata_rows)
                self.log_message("Metadata saved to metadata.csv\n")
                messagebox.showinfo("FireKEY", "Processing complete! Metadata saved as metadata.csv.")
        finally:
            self.process_button.config(state=tk.NORMAL)

    def _collect_image_files(self, folder: str) -> List[str]:
        image_paths: List[str] = []
        for extension in SUPPORTED_EXTENSIONS:
            pattern = os.path.join(folder, f"*{extension}")
            image_paths.extend(glob.glob(pattern))
        image_paths.sort()
        return image_paths

    def _get_client(self) -> Optional[OpenAI]:
        try:
            if self.client is None:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    self.log_message("OPENAI_API_KEY environment variable is not set.\n")
                    messagebox.showerror(
                        "FireKEY", "OpenAI API key is missing. Set the OPENAI_API_KEY environment variable."
                    )
                    return None
                self.client = OpenAI(api_key=api_key)
            return self.client
        except Exception as exc:  # noqa: BLE001
            self.log_message(f"Failed to initialize OpenAI client: {exc}\n")
            messagebox.showerror("FireKEY", "Unable to initialize OpenAI client. See log for details.")
            return None

    def _generate_metadata(self, client: OpenAI, image_path: str) -> Metadata:
        encoded_image = self._encode_image(image_path)
        prompt = (
            "You are an expert stock photography curator. Review the provided image and craft metadata suitable "
            "for stock photo platforms. Respond with JSON containing the keys 'Title', 'Description', and "
            "'Keywords'. The description should be 1-2 sentences. Provide 12-20 concise, comma-separated "
            "keywords as an array of strings."
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": "You analyze images and create descriptive metadata for stock photography.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_base64": encoded_image},
                    ],
                },
            ],
            max_output_tokens=400,
        )

        output_text = response.output_text
        try:
            data = json.loads(output_text)
        except json.JSONDecodeError as exc:  # noqa: PERF203
            raise ValueError("OpenAI response was not valid JSON.") from exc

        keywords = data.get("Keywords")
        if isinstance(keywords, str):
            keywords_list = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]
        elif isinstance(keywords, Iterable):
            keywords_list = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]
        else:
            keywords_list = []

        return Metadata(
            filename=os.path.basename(image_path),
            title=str(data.get("Title", "")),
            description=str(data.get("Description", "")),
            keywords=keywords_list,
        )

    def _encode_image(self, image_path: str) -> str:
        with Image.open(image_path) as image:
            rgb_image = image.convert("RGB")
            buffer = io.BytesIO()
            rgb_image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _save_metadata(self, folder: str, rows: List[Metadata]) -> None:
        df = pd.DataFrame(
            [
                {
                    "Filename": metadata.filename,
                    "Title": metadata.title,
                    "Description": metadata.description,
                    "Keywords": ", ".join(metadata.keywords),
                }
                for metadata in rows
            ]
        )
        output_path = os.path.join(folder, "metadata.csv")
        df.to_csv(output_path, index=False)

    def log_message(self, message: str) -> None:
        def append() -> None:
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n" if not message.endswith("\n") else message)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)

        self.log_text.after(0, append)


def main() -> None:
    root = tk.Tk()
    app = FireKeyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
