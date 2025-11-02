"""Demonstration utilities for the FireKey tracking helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Tuple

from .csv_logger import CSVLogger
from .session import TrackingSession
from .tracked_client import (
    TrackedAPIClient,
    default_completion_extractor,
    default_usage_extractor,
)
from .tracker import ModelPricing, TokenUsageTracker


def mock_api_sender(*, prompt: str, model: str, **_: Dict) -> Dict[str, Dict[str, int]]:
    """A fake API sender that returns a deterministic payload for demos/tests."""

    completion = prompt[::-1]
    usage = {
        "prompt_tokens": len(prompt) // 4 or 1,
        "completion_tokens": len(completion) // 4 or 1,
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    return {
        "model": model,
        "choices": [{"message": {"content": completion}}],
        "usage": usage,
    }


def run_demo(prompts: Iterable[Tuple[str, str]], csv_path: Path) -> None:
    """Process a series of prompts using the tracking helpers."""

    tracker = TokenUsageTracker(
        model_pricing={"demo-model": ModelPricing(0.0001, 0.0002)},
        default_model="demo-model",
    )
    csv_logger = CSVLogger(csv_path=csv_path)
    client = TrackedAPIClient(
        sender=mock_api_sender,
        tracker=tracker,
        default_model="demo-model",
    )

    with TrackingSession(tracker, csv_logger) as session:
        for file_name, prompt in prompts:
            _, record = client(
                file_name=file_name,
                prompt=prompt,
                completion_text_extractor=default_completion_extractor,
                usage_extractor=default_usage_extractor,
                return_record=True,
            )
            session.record(record)
