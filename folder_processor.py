"""Utilities for processing folders of images and generating metadata."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import pandas as pd
from tkinter import Tk, filedialog


MetadataGenerator = Callable[[Path, str, str, float], dict]


@dataclass
class FolderProcessor:
    """Process folders of images and persist generated metadata.

    Parameters
    ----------
    metadata_generator:
        Callable that produces metadata for a single image. The callable is
        invoked with the image path, context string, model identifier and
        creativity value. It must return a mapping that can be converted to a
        :class:`pandas.Series` or dictionary.
    log_callback:
        Function that receives log messages to be displayed in the GUI.
    """

    metadata_generator: Optional[MetadataGenerator] = None
    log_callback: Optional[Callable[[str], None]] = None

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})

    def __post_init__(self) -> None:
        if self.log_callback is None:
            self.log_callback = lambda message: None

    def _log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)

    def select_folder(self) -> Optional[str]:
        """Open a folder picker dialog and return the selected path."""
        root = Tk()
        root.withdraw()
        root.update()
        try:
            folder = filedialog.askdirectory()
        finally:
            root.destroy()

        if folder:
            self._log(f"Selected folder: {folder}")
            return folder

        self._log("Folder selection cancelled by the user.")
        return None

    def process_folder(
        self,
        folder_path: str,
        context: str,
        model: str,
        creativity: float,
    ) -> Optional[pd.DataFrame]:
        """Generate metadata for each supported image within ``folder_path``."""
        path = Path(folder_path).expanduser().resolve()
        if not path.exists():
            self._log(f"Error: Folder does not exist - {path}")
            return None

        image_files = sorted(
            file_path
            for file_path in path.iterdir()
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
        )

        if not image_files:
            self._log("No supported images found in the selected folder.")
            return pd.DataFrame()

        records: List[dict] = []

        for image_path in image_files:
            self._log(f"Processing image: {image_path.name}")
            try:
                metadata = self.generate_metadata(image_path, context, model, creativity)
            except Exception as exc:  # pragma: no cover - GUI logging focus
                self._log(f"Error processing {image_path.name}: {exc}")
                continue

            if metadata is None:
                self._log(f"Warning: No metadata returned for {image_path.name}.")
                continue

            if not isinstance(metadata, dict):
                metadata = dict(metadata)

            metadata.setdefault("filename", image_path.name)
            records.append(metadata)

        if not records:
            self._log("No metadata generated for the selected folder.")
            return pd.DataFrame()

        dataframe = pd.DataFrame.from_records(records)
        output_path = path / "metadata.csv"
        dataframe.to_csv(output_path, index=False)
        self._log(f"Metadata saved to {output_path}")
        return dataframe

    def generate_metadata(self, image_path: Path, context: str, model: str, creativity: float) -> dict:
        """Proxy to the configured ``metadata_generator`` callable."""
        if self.metadata_generator is None:
            raise RuntimeError("metadata_generator must be provided to generate metadata.")
        return self.metadata_generator(image_path, context, model, creativity)
