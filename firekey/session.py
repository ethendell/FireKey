"""High level helpers for running tracked API sessions."""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Optional

from .csv_logger import CSVLogger
from .tracker import CallRecord, TokenUsageTracker


class TrackingSession(AbstractContextManager["TrackingSession"]):
    """Context manager that prints a summary and optionally writes CSV output."""

    def __init__(self, tracker: TokenUsageTracker, csv_logger: Optional[CSVLogger] = None) -> None:
        self.tracker = tracker
        self.csv_logger = csv_logger

    def __enter__(self) -> "TrackingSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.csv_logger is not None:
            self.csv_logger.write(self.tracker)
        self.tracker.print_summary()
        return False

    def record(self, record: CallRecord) -> None:
        """Store a record in the backing CSV logger if configured."""

        if self.csv_logger is not None:
            self.csv_logger.add_record(record)
