"""Utilities for post-processing metadata keywords."""

from __future__ import annotations

from collections.abc import Iterable, MutableMapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple, Tuple

try:  # Optional dependency used only when available.
    import pandas as _pd  # type: ignore
except Exception:  # pragma: no cover - pandas is optional for this project.
    _pd = None  # type: ignore

__all__ = [
    "KeywordProcessingResult",
    "append_keyword_columns",
    "clean_keywords",
]

DEFAULT_VOCAB_PATH = Path(__file__).resolve().parent.parent / "resources" / "controlled_vocabulary.txt"


class KeywordProcessingResult(NamedTuple):
    """Container for cleaned keyword results."""

    valid_keywords: Tuple[str, ...]
    review_keywords: Tuple[str, ...]

    def as_strings(self, delimiter: str = "; ") -> Tuple[str, str]:
        """Return joined string representations for CSV serialization."""

        valid = delimiter.join(self.valid_keywords)
        review = delimiter.join(self.review_keywords)
        return valid, review


@lru_cache(maxsize=1)
def _load_vocabulary(path: Path | None = None) -> set[str]:
    """Load the controlled vocabulary from ``path``.

    The vocabulary file is expected to contain one keyword per line. Lines that are
    empty or start with ``#`` are ignored. Values are normalised to lower-case.
    """

    vocab_path = Path(path) if path else DEFAULT_VOCAB_PATH
    if not vocab_path.exists():  # pragma: no cover - defensive branch
        raise FileNotFoundError(f"Controlled vocabulary not found at {vocab_path!s}")

    vocabulary: set[str] = set()
    with vocab_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            keyword = line.strip().lower()
            if not keyword or keyword.startswith("#"):
                continue
            vocabulary.add(keyword)
    return vocabulary


def _normalise_keywords(raw_keywords: object) -> list[str]:
    """Convert a raw keyword container into a cleaned list of strings.

    ``raw_keywords`` may be an iterable of strings, a comma or semicolon separated
    string, or ``None``/empty. Whitespace is stripped but other canonicalisation is
    handled by :func:`clean_keywords`.
    """

    if raw_keywords is None:
        return []

    if isinstance(raw_keywords, str):
        return [item.strip() for item in _split_string_keywords(raw_keywords) if item.strip()]

    if isinstance(raw_keywords, Sequence) and not isinstance(raw_keywords, (str, bytes, bytearray)):
        normalised: list[str] = []
        for item in raw_keywords:
            if item is None:
                continue
            item_str = str(item).strip()
            if item_str:
                normalised.append(item_str)
        return normalised

    if isinstance(raw_keywords, Iterable):
        normalised = []
        for item in raw_keywords:
            if item is None:
                continue
            item_str = str(item).strip()
            if item_str:
                normalised.append(item_str)
        return normalised

    item_str = str(raw_keywords).strip()
    return [item_str] if item_str else []


def _split_string_keywords(keywords: str) -> list[str]:
    """Split a keyword string on common delimiters."""

    separators = [";", ",", "|"]
    current = [keywords]
    for separator in separators:
        tokens: list[str] = []
        for item in current:
            if separator in item:
                tokens.extend(part.strip() for part in item.split(separator))
            else:
                tokens.append(item)
        current = tokens
    return [item for item in current if item]


def clean_keywords(
    keywords: object,
    vocabulary_path: Path | None = None,
    *,
    limit: int = 50,
) -> KeywordProcessingResult:
    """Clean a keyword collection according to project rules.

    Parameters
    ----------
    keywords:
        Collection of keyword candidates. Strings may be delimited by commas,
        semicolons, or pipes. ``None`` yields empty results.
    vocabulary_path:
        Optional path to the controlled vocabulary file. Defaults to the
        repository-level resource.
    limit:
        Maximum number of unique keywords to consider. Defaults to ``50`` as per
        project requirements.
    """

    cleaned: list[str] = []
    seen: set[str] = set()
    for keyword in _normalise_keywords(keywords):
        lowered = keyword.lower()
        if not lowered or lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(lowered)
        if len(cleaned) >= limit:
            break

    vocabulary = _load_vocabulary(vocabulary_path)
    valid: list[str] = []
    review: list[str] = []
    for keyword in cleaned:
        if keyword in vocabulary:
            valid.append(keyword)
        else:
            review.append(keyword)

    return KeywordProcessingResult(tuple(valid), tuple(review))


def append_keyword_columns(
    data: object,
    keywords_field: str = "Keywords",
    *,
    valid_field: str = "Valid Keywords",
    review_field: str = "Review Keywords",
    vocabulary_path: Path | None = None,
    delimiter: str = "; ",
    as_strings: bool = True,
):
    """Append keyword validation columns to tabular metadata.

    ``data`` may be either a :class:`pandas.DataFrame` (if pandas is installed) or
    a mutable sequence of mapping objects representing rows. The function returns a
    new object of the same type and leaves the input unmodified.
    """

    def _store(result: KeywordProcessingResult):
        if as_strings:
            return result.as_strings(delimiter)
        return result.valid_keywords, result.review_keywords

    vocabulary = vocabulary_path  # ensure consistent default caching

    if _pd is not None and isinstance(data, _pd.DataFrame):  # pragma: no cover - depends on pandas
        df = data.copy()
        if keywords_field in df:
            source = list(df[keywords_field])
        else:
            source = [None] * len(df)

        valid_column: list[str | Tuple[str, ...]] = []
        review_column: list[str | Tuple[str, ...]] = []
        for value in source:
            result = clean_keywords(value, vocabulary)
            valid_value, review_value = _store(result)
            valid_column.append(valid_value)
            review_column.append(review_value)
        df[valid_field] = valid_column
        df[review_field] = review_column
        return df

    if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        processed_rows = []
        for row in data:
            if not isinstance(row, MutableMapping):
                raise TypeError(
                    "append_keyword_columns expects a sequence of mapping rows when pandas is unavailable."
                )
            row_copy = dict(row)
            result = clean_keywords(row_copy.get(keywords_field), vocabulary)
            valid_value, review_value = _store(result)
            row_copy[valid_field] = valid_value
            row_copy[review_field] = review_value
            processed_rows.append(row_copy)
        return processed_rows

    raise TypeError(
        "Unsupported data container. Provide a pandas.DataFrame or a sequence of mapping rows."
    )
