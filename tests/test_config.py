from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from firekey.config import ConfigManager, DEFAULT_CONFIG


def read_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_load_creates_default_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(config_path)

    config = manager.load()

    assert config == DEFAULT_CONFIG
    assert config_path.exists()
    assert read_config(config_path) == DEFAULT_CONFIG


def test_load_merges_missing_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text('{"api_key": "abc123"}', encoding="utf-8")

    manager = ConfigManager(config_path)
    config = manager.load()

    expected = DEFAULT_CONFIG.copy()
    expected["api_key"] = "abc123"
    assert config == expected
    assert read_config(config_path) == expected


def test_ensure_api_key_prompts_until_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(config_path)
    manager.load()

    responses: Iterator[str] = iter(["", "  ", "secret-key"])

    api_key = manager.ensure_api_key(prompt=lambda _: next(responses))

    assert api_key == "secret-key"
    saved = read_config(config_path)
    assert saved["api_key"] == "secret-key"
