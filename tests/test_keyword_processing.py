from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from firekey.keyword_processing import KeywordProcessingResult, append_keyword_columns, clean_keywords


def write_vocab(tmp_path: Path, contents: str = "firekey\nmetadata\narchives\n") -> Path:
    vocab_path = tmp_path / "vocab.txt"
    vocab_path.write_text(contents, encoding="utf-8")
    return vocab_path


def test_clean_keywords_filters_and_splits(tmp_path: Path):
    vocab = write_vocab(tmp_path)
    raw_keywords = ["FireKey", "  firekey  ", "Archives", "NewTerm", "", None]

    result = clean_keywords(raw_keywords, vocabulary_path=vocab)

    assert isinstance(result, KeywordProcessingResult)
    assert result.valid_keywords == ("firekey", "archives")
    assert result.review_keywords == ("newterm",)


def test_clean_keywords_handles_strings_and_limits(tmp_path: Path):
    vocab = write_vocab(tmp_path, contents="keyword\nother\n")
    raw_keywords = ";".join(f"Keyword {i}" for i in range(1, 70))

    result = clean_keywords(raw_keywords, vocabulary_path=vocab)

    assert len(result.valid_keywords) <= 50
    assert len(result.review_keywords) <= 50
    combined = set(result.valid_keywords) | set(result.review_keywords)
    assert len(combined) == 50
    assert all(keyword == keyword.lower() for keyword in combined)


def test_append_keyword_columns_on_sequence(tmp_path: Path):
    vocab = write_vocab(tmp_path, contents="firekey\nmetadata\n")
    rows = [
        {"Title": "Record 1", "Keywords": ["FireKey", "Unknown"]},
        {"Title": "Record 2", "Keywords": "metadata, Another"},
    ]

    processed = append_keyword_columns(rows, vocabulary_path=vocab)

    # Ensure original input is not mutated
    assert rows[0].get("Valid Keywords") is None

    assert processed[0]["Valid Keywords"] == "firekey"
    assert processed[0]["Review Keywords"] == "unknown"
    assert processed[1]["Valid Keywords"] == "metadata"
    assert processed[1]["Review Keywords"] == "another"


def test_append_keyword_columns_can_return_sequences(tmp_path: Path):
    vocab = write_vocab(tmp_path, contents="firekey\nmetadata\n")
    rows = [{"Keywords": ["FireKey", "Unknown"]}]

    processed = append_keyword_columns(rows, vocabulary_path=vocab, as_strings=False)

    assert processed[0]["Valid Keywords"] == ("firekey",)
    assert processed[0]["Review Keywords"] == ("unknown",)


def test_append_keyword_columns_rejects_invalid_rows():
    with pytest.raises(TypeError):
        append_keyword_columns(["not-a-mapping"])  # type: ignore[arg-type]
