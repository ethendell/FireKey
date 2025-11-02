"""Command line interface for the FireKey processor."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .processor import FireKeyProcessor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process files using the FireKey pipeline with caching and retries.",
    )
    parser.add_argument(
        "paths",
        metavar="PATH",
        nargs="+",
        help="One or more files or directories to process.",
    )
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        help="Process files even if cached responses are available.",
    )
    return parser


def _expand_paths(raw_paths: List[str]) -> List[Path]:
    expanded: List[Path] = []
    for raw in raw_paths:
        path = Path(raw)
        if path.is_dir():
            expanded.extend(sorted(p for p in path.iterdir() if p.is_file()))
        else:
            expanded.append(path)
    return expanded


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    processor = FireKeyProcessor()
    file_paths = _expand_paths(args.paths)
    results = processor.process_files(
        file_paths, force_reprocess=args.force_reprocess
    )

    if not results:
        print("No files were processed.")
        return

    print("Processed files:")
    for result in results.values():
        status = "reprocessed" if result.was_reprocessed else "cached"
        print(f"- {result.file_name}: {result.cache_path} ({status})")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
