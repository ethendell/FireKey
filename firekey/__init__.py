"""Utilities for working with FireKey metadata."""

from .metadata import FIELDNAMES, MetadataEntry, append_metadata

__all__ = ["FIELDNAMES", "MetadataEntry", "append_metadata"]
"""FireKey package."""

from .config import ConfigManager, DEFAULT_CONFIG, default_config_path

__all__ = ["ConfigManager", "DEFAULT_CONFIG", "default_config_path"]
