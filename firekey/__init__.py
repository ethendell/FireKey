"""FireKey package providing API token usage tracking utilities."""

from .tracker import TokenUsageTracker, ModelPricing
from .csv_logger import CSVLogger
from .tracked_client import TrackedAPIClient, default_completion_extractor, default_usage_extractor
from .session import TrackingSession
from .demo import run_demo

__all__ = [
    "ModelPricing",
    "TokenUsageTracker",
    "CSVLogger",
    "TrackedAPIClient",
    "default_completion_extractor",
    "default_usage_extractor",
    "TrackingSession",
    "run_demo",
]
"""FireKey package."""

from .app import FireKeyApp, main

__all__ = ["FireKeyApp", "main"]
"""FireKey package initialization."""

from .metadata import extract_key_frames, generate_metadata

__all__ = ["extract_key_frames", "generate_metadata"]
"""Utilities for working with FireKey metadata."""

from .metadata import FIELDNAMES, MetadataEntry, append_metadata

__all__ = ["FIELDNAMES", "MetadataEntry", "append_metadata"]
"""FireKey package."""

from .config import ConfigManager, DEFAULT_CONFIG, default_config_path

__all__ = ["ConfigManager", "DEFAULT_CONFIG", "default_config_path"]
