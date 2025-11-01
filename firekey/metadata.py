"""Helpers for creating and updating the project metadata CSV.

The helper exposed here keeps the metadata CSV in append mode so that
existing rows are never lost.  When the CSV does not exist a header with the
expected columns is written automatically before the new row is appended.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import csv
from pathlib import Path
from typing import Iterable, Sequence

FIELDNAMES = [
    "Filename",
    "Title",
    "Description",
    "Keywords",
    "Date processed",
    "Model used",
]


@dataclass(slots=True)
class MetadataEntry:
    """Container describing a single metadata row.

    Parameters mirror the CSV header.  ``keywords`` may be provided either as
    a pre-formatted string or as an iterable of keyword values which will be
    joined with ``"; "``.
    """

    filename: str
    title: str
    description: str
    keywords: Sequence[str] | str
    model_used: str
    processed_at: datetime | None = None

    def as_row(self) -> dict[str, str]:
        """Return the entry as a dictionary ready for :mod:`csv` writing."""

        processed_at = self.processed_at or datetime.now(timezone.utc)
        keywords_value = _normalise_keywords(self.keywords)
        return {
            "Filename": self.filename,
            "Title": self.title,
            "Description": self.description,
            "Keywords": keywords_value,
            "Date processed": processed_at.isoformat(timespec="seconds"),
            "Model used": self.model_used,
        }


def append_metadata(
    metadata_path: str | Path,
    filename: str,
    title: str,
    description: str,
    keywords: Sequence[str] | str,
    model_used: str,
    *,
    processed_at: datetime | None = None,
) -> Path:
    """Append a row of metadata to ``metadata_path``.

    The CSV file is created automatically when necessary.  A header is written
    only when the file did not exist (or was empty), ensuring the previous
    contents remain untouched.

    Parameters
    ----------
    metadata_path:
        Path to the metadata CSV file.
    filename, title, description:
        Values describing the processed asset.
    keywords:
        Either a pre-formatted keyword string or an iterable which will be
        joined using ``"; "``.
    model_used:
        Identifier of the model responsible for the asset.
    processed_at:
        Optional :class:`~datetime.datetime` override for the processing time.

    Returns
    -------
    :class:`pathlib.Path`
        The resolved path to the metadata file.
    """

    destination = Path(metadata_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    entry = MetadataEntry(
        filename=filename,
        title=title,
        description=description,
        keywords=keywords,
        model_used=model_used,
        processed_at=processed_at,
    )

    needs_header = True
    if destination.exists():
        needs_header = destination.stat().st_size == 0

    with destination.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if needs_header:
            writer.writeheader()
        writer.writerow(entry.as_row())

    return destination


def _normalise_keywords(value: Sequence[str] | str) -> str:
    """Normalise *value* into a keyword string."""

    if isinstance(value, str):
        return value

    if not isinstance(value, Iterable):
        raise TypeError("keywords must be a string or an iterable of strings")

    return "; ".join(str(keyword) for keyword in value)


__all__ = ["FIELDNAMES", "MetadataEntry", "append_metadata"]
