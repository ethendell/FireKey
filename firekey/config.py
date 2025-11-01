"""Utilities for reading and writing FireKEY configuration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Optional, Any, Dict


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


@dataclass
class AppConfig:
    """Represents persisted configuration for the application."""

    last_template: Optional[str] = None

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "AppConfig":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        last_template = data.get("last_template")
        if last_template is not None and not isinstance(last_template, str):
            last_template = None
        return cls(last_template=last_template)

    def save(self, path: Path = CONFIG_PATH) -> None:
        payload: Dict[str, Any] = {"last_template": self.last_template}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = ["AppConfig", "CONFIG_PATH"]
