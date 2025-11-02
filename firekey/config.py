"""Configuration management for FireKey."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Callable, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "api_key": "",
    "default_model": "gpt-4o-mini",
    "default_creativity": 0.4,
}


def default_config_path() -> Path:
    """Return the default location of the configuration file.

    The path can be overridden by setting the ``FIREKEY_CONFIG_PATH``
    environment variable. Otherwise, ``config.json`` in the current
    working directory is used.
    """

    env_path = os.getenv("FIREKEY_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return Path.cwd() / "config.json"


class ConfigManager:
    """Handle loading and persisting configuration for FireKey."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config: Dict[str, Any] | None = None

    @property
    def config(self) -> Dict[str, Any]:
        """Return the in-memory configuration, loading it if necessary."""

        if self._config is None:
            self.load()
        assert self._config is not None  # for type checkers
        return self._config

    def load(self) -> Dict[str, Any]:
        """Load the configuration from disk, creating defaults if needed."""

        if not self.config_path.exists():
            self._config = DEFAULT_CONFIG.copy()
            self._ensure_parent_directory()
            self.save()
            return self._config

        try:
            with self.config_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:  # pragma: no cover - log path
            print(
                f"Failed to parse {self.config_path}: {exc}. Resetting to defaults.",
                file=sys.stderr,
            )
            data = {}
        except OSError as exc:  # pragma: no cover - log path
            print(
                f"Could not read {self.config_path}: {exc}. Resetting to defaults.",
                file=sys.stderr,
            )
            data = {}

        if not isinstance(data, MutableMapping):
            data = {}

        merged_config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        merged_config.update(data)

        if data != merged_config:
            self._config = merged_config
            self.save()
        else:
            self._config = merged_config

        return self._config

    def save(self) -> None:
        """Persist the in-memory configuration to disk."""

        if self._config is None:
            return
        self._ensure_parent_directory()
        with self.config_path.open("w", encoding="utf-8") as fh:
            json.dump(self._config, fh, indent=2)
            fh.write("\n")

    def ensure_api_key(self, prompt: Callable[[str], str] | None = None) -> str:
        """Prompt for and persist the API key if it is missing."""

        if prompt is None:
            prompt = input

        config = self.config
        api_key = str(config.get("api_key", "")).strip()
        if api_key:
            return api_key

        while True:
            user_input = prompt("Enter your FireKey API key: ").strip()
            if user_input:
                config["api_key"] = user_input
                self.save()
                return user_input
            print("API key cannot be blank. Please enter a valid key.")

    def _ensure_parent_directory(self) -> None:
        """Ensure that the directory for the config file exists."""

        parent = self.config_path.parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
