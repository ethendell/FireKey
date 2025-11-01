from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from typing import Dict

from firekey.exceptions import APIError, NetworkError
from firekey.processor import FireKeyProcessor


def test_caches_processed_files(tmp_path: Path) -> None:
    file_a = tmp_path / "file_a.txt"
    file_a.write_text("Hello", encoding="utf-8")

    processor = FireKeyProcessor(
        cache_dir=tmp_path / "cache",
        log_path=tmp_path / "logs/firekey-errors.txt",
        retry_delay=0.0,
    )

    results = processor.process_files([file_a])
    cache_file = tmp_path / "cache" / "file_a.txt.json"

    assert cache_file.exists()
    assert results["file_a.txt"].cache_path == cache_file

    stored = json.loads(cache_file.read_text(encoding="utf-8"))
    assert stored["file_name"] == "file_a.txt"

    # Second run should use cache by default
    calls = 0

    def client(_: Path) -> Dict:
        nonlocal calls
        calls += 1
        return {"value": 1}

    processor = FireKeyProcessor(
        cache_dir=tmp_path / "cache",
        log_path=tmp_path / "logs/firekey-errors.txt",
        client=client,
        retry_delay=0.0,
    )

    processor.process_files([file_a])
    assert calls == 0


def test_force_reprocess_overrides_cache(tmp_path: Path) -> None:
    file_a = tmp_path / "file_a.txt"
    file_a.write_text("Hello", encoding="utf-8")

    calls = 0

    def client(_: Path) -> Dict:
        nonlocal calls
        calls += 1
        return {"value": calls}

    processor = FireKeyProcessor(
        cache_dir=tmp_path / "cache",
        log_path=tmp_path / "logs/firekey-errors.txt",
        client=client,
        retry_delay=0.0,
    )

    processor.process_files([file_a], force_reprocess=True)
    processor.process_files([file_a], force_reprocess=True)
    assert calls == 2


def test_retries_then_succeeds(tmp_path: Path) -> None:
    file_a = tmp_path / "file_a.txt"
    file_a.write_text("Hello", encoding="utf-8")

    attempts = 0

    def client(_: Path) -> Dict:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise NetworkError("temporary")
        return {"value": "ok"}

    processor = FireKeyProcessor(
        cache_dir=tmp_path / "cache",
        log_path=tmp_path / "logs/firekey-errors.txt",
        client=client,
        retry_delay=0.0,
    )

    processor.process_files([file_a])
    cache_file = tmp_path / "cache" / "file_a.txt.json"
    assert json.loads(cache_file.read_text(encoding="utf-8")) == {"value": "ok"}
    assert attempts == 3


def test_retries_then_fails(tmp_path: Path) -> None:
    file_a = tmp_path / "file_a.txt"
    file_a.write_text("Hello", encoding="utf-8")

    def client(_: Path) -> Dict:
        raise APIError("boom")

    log_path = tmp_path / "logs/firekey-errors.txt"

    processor = FireKeyProcessor(
        cache_dir=tmp_path / "cache",
        log_path=log_path,
        client=client,
        max_retries=2,
        retry_delay=0.0,
    )

    processor.process_files([file_a])
    cache_file = tmp_path / "cache" / "file_a.txt.json"
    assert not cache_file.exists()

    log_content = log_path.read_text(encoding="utf-8")
    assert "Attempt 1" in log_content
    assert "Attempt 2" in log_content
