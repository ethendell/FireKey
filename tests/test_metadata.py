from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import pytest

from firekey.metadata import FIELDNAMES, append_metadata


def read_metadata(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_append_creates_file_and_header(tmp_path: Path) -> None:
    metadata_file = tmp_path / "metadata.csv"

    append_metadata(
        metadata_file,
        filename="example.txt",
        title="Example",
        description="Simple description",
        keywords=["demo", "test"],
        model_used="gpt-5-codex",
    )

    assert metadata_file.exists()
    rows = read_metadata(metadata_file)
    assert len(rows) == 1
    row = rows[0]
    assert list(row.keys()) == FIELDNAMES
    assert row["Filename"] == "example.txt"
    assert row["Keywords"] == "demo; test"
    # Should be ISO formatted timestamp.
    datetime.fromisoformat(row["Date processed"])


def test_append_preserves_existing_rows(tmp_path: Path) -> None:
    metadata_file = tmp_path / "metadata.csv"

    append_metadata(
        metadata_file,
        filename="first.bin",
        title="First",
        description="Initial asset",
        keywords="alpha",
        model_used="model-a",
    )

    append_metadata(
        metadata_file,
        filename="second.bin",
        title="Second",
        description="Follow-up asset",
        keywords=["beta", "release"],
        model_used="model-b",
    )

    rows = read_metadata(metadata_file)
    assert [row["Filename"] for row in rows] == ["first.bin", "second.bin"]
    assert rows[0]["Keywords"] == "alpha"
    assert rows[1]["Keywords"] == "beta; release"


def test_invalid_keywords_type(tmp_path: Path) -> None:
    metadata_file = tmp_path / "metadata.csv"

    with pytest.raises(TypeError):
        append_metadata(
            metadata_file,
            filename="bad.bin",
            title="Bad",
            description="",
            keywords=42,  # type: ignore[arg-type]
            model_used="model",
        )
