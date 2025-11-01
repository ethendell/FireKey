"""Sample metadata used by the FireKey GUI."""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import json

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_metadata.json"


def load_sample_metadata() -> List[Dict[str, object]]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    records = payload.get("records", [])
    normalized: List[Dict[str, object]] = []
    for record in records:
        normalized_record = dict(record)
        poster_frame = normalized_record.get("poster_frame")
        if poster_frame:
            normalized_record["poster_frame"] = Path(poster_frame)
        normalized.append(normalized_record)
    return normalized
