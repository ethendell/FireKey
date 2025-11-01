"""CSV logging helpers for FireKey token tracking."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

from .tracker import CallRecord, TokenUsageTracker


@dataclass
class CSVLogger:
    """Persist call records into a CSV file with an optional summary comment."""

    csv_path: Path
    headers: Sequence[str] = (
        "file_name",
        "model",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cost",
    )
    rows: List[List[str]] = field(default_factory=list)

    def add_record(self, record: CallRecord) -> None:
        """Queue a :class:`CallRecord` for persistence."""

        self.rows.append(
            [
                record.file_name,
                record.model,
                str(record.prompt_tokens),
                str(record.completion_tokens),
                str(record.total_tokens),
                f"{record.cost:.6f}",
            ]
        )

    def extend(self, records: Iterable[CallRecord]) -> None:
        """Queue multiple records for persistence."""

        for record in records:
            self.add_record(record)

    def write(self, tracker: TokenUsageTracker, include_summary: bool = True) -> None:
        """Write queued rows to disk and optionally append a summary comment."""

        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(self.headers)
            writer.writerows(self.rows)
            if include_summary:
                fh.write("\n")
                fh.write(tracker.csv_footer_comment())
                fh.write("\n")
