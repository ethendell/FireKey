from pathlib import Path
import json
import xml.etree.ElementTree as ET

import pytest

from firekey.exporter import ExportSummary, Exporter


@pytest.fixture
def sample_records(tmp_path: Path) -> list[dict]:
    poster_dir = tmp_path / "posters"
    poster_dir.mkdir()
    poster = poster_dir / "thumb.jpg"
    poster.write_text("poster", encoding="utf-8")
    return [
        {"filename": "one.mp4", "poster_frame": poster, "title": "One"},
        {"filename": "two.mp4", "title": "Two"},
    ]


def test_csv_export_creates_expected_files(tmp_path: Path, sample_records: list[dict]) -> None:
    exporter = Exporter(base_export_dir=tmp_path)
    summary = ExportSummary(model="gpt-test", tokens=100, cost=1.23)

    result = exporter.export(sample_records, "CSV", summary)

    assert result.folder is not None
    assert result.metadata_path and result.metadata_path.exists()
    assert result.summary_path and result.summary_path.exists()
    assert result.poster_frame_paths

    summary_payload = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary_payload["total_files"] == 2
    assert summary_payload["model"] == "gpt-test"


def test_json_export_uses_destination(tmp_path: Path, sample_records: list[dict]) -> None:
    exporter = Exporter(base_export_dir=tmp_path / "default")
    destination = tmp_path / "custom.json"
    summary = ExportSummary(model="gpt", tokens=50, cost=0.5)

    result = exporter.export(sample_records, "JSON", summary, output_path=destination)

    assert result.metadata_path == destination
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["summary"]["total_files"] == len(sample_records)


def test_xml_export(tmp_path: Path, sample_records: list[dict]) -> None:
    exporter = Exporter(base_export_dir=tmp_path / "default")
    destination = tmp_path / "metadata.xml"
    summary = ExportSummary(model="gpt", tokens=50, cost=0.5)

    result = exporter.export(sample_records, "XML", summary, output_path=destination)

    assert result.metadata_path == destination
    tree = ET.parse(destination)
    root = tree.getroot()
    total = root.find("summary/total_files")
    assert total is not None and total.text == str(len(sample_records))
