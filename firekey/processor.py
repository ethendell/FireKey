"""Core processing logic for FireKey.

This module exposes :class:`FireKeyProcessor` which adds caching, retry
behaviour, and logging for file based processing workflows.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence

from .exceptions import APIError, FireKeyError, NetworkError


DEFAULT_CACHE_DIR = Path("cache")
DEFAULT_LOG_PATH = Path("logs/firekey-errors.txt")
DEFAULT_RETRY_DELAY = 3.0
DEFAULT_MAX_RETRIES = 3


@dataclass
class ProcessingResult:
    """A simple wrapper describing the processing outcome for a file."""

    file_name: str
    cache_path: Path
    was_reprocessed: bool


class FireKeyProcessor:
    """Process files with caching, retries, and error logging.

    Parameters
    ----------
    cache_dir:
        Directory used for cached responses. If it does not exist it will be
        created automatically.
    log_path:
        Path to the error log file. Parent directories will be created if they
        do not already exist.
    client:
        Callable used to perform the heavy lifting of producing JSON serialisable
        data for a file. The callable receives the path to the file as its only
        argument and must return a dictionary. A default client is provided that
        simply mirrors basic file metadata.
    max_retries:
        Maximum number of attempts that will be made for retryable errors.
    retry_delay:
        Delay in seconds between retry attempts. The default value honours the
        product requirement of a three second pause.
    """

    def __init__(
        self,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
        log_path: Path | str = DEFAULT_LOG_PATH,
        *,
        client: Optional[Callable[[Path], Dict]] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.log_path = Path(log_path)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.client = client or self._default_client
        self.max_retries = max(1, max_retries)
        self.retry_delay = max(0.0, retry_delay)

    def process_files(
        self, file_paths: Sequence[Path | str], *, force_reprocess: bool = False
    ) -> Dict[str, ProcessingResult]:
        """Process ``file_paths`` respecting cache state and retry rules.

        Parameters
        ----------
        file_paths:
            Iterable of filesystem paths to process.
        force_reprocess:
            When ``True`` cached responses are ignored, mimicking a checked
            "Force Reprocess" box in the user interface.

        Returns
        -------
        Dict[str, ProcessingResult]
            Mapping from file name to :class:`ProcessingResult` instances for
            successfully processed files.
        """

        results: Dict[str, ProcessingResult] = {}

        for raw_path in file_paths:
            file_path = Path(raw_path)
            if not file_path.exists():
                self._log_error(
                    f"File '{file_path}' does not exist; skipping processing."
                )
                continue

            cache_file = self.cache_dir / f"{file_path.name}.json"

            use_cache = cache_file.exists() and not force_reprocess
            if use_cache:
                results[file_path.name] = ProcessingResult(
                    file_name=file_path.name,
                    cache_path=cache_file,
                    was_reprocessed=False,
                )
                continue

            try:
                payload = self._process_with_retries(file_path)
            except FireKeyError:
                # Errors are already logged inside ``_process_with_retries``.
                continue

            with cache_file.open("w", encoding="utf-8") as file_obj:
                json.dump(payload, file_obj, ensure_ascii=False, indent=2)

            results[file_path.name] = ProcessingResult(
                file_name=file_path.name,
                cache_path=cache_file,
                was_reprocessed=force_reprocess,
            )

        return results

    def _process_with_retries(self, file_path: Path) -> Dict:
        """Invoke the client with retry support for network/API errors."""

        attempt = 0
        while True:
            attempt += 1
            try:
                return self.client(file_path)
            except (NetworkError, APIError) as exc:  # retryable errors
                self._log_error(
                    f"Attempt {attempt} for '{file_path.name}' failed: {exc}"
                )
                if attempt >= self.max_retries:
                    raise
                time.sleep(self.retry_delay)
            except Exception as exc:  # pragma: no cover - defensive catch
                self._log_error(
                    f"Unrecoverable error for '{file_path.name}': {exc}"
                )
                raise FireKeyError(str(exc)) from exc

    @staticmethod
    def _default_client(file_path: Path) -> Dict:
        """Produce a deterministic JSON payload for ``file_path``.

        The default behaviour extracts a few pieces of metadata so the
        application works out-of-the-box, even without an external API.
        """

        stat = file_path.stat()
        content = file_path.read_text(encoding="utf-8") if file_path.suffix in {
            ".txt",
            ".md",
            ".json",
        } else None
        return {
            "file_name": file_path.name,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "content_preview": content[:200] if content else None,
        }

    def _log_error(self, message: str) -> None:
        """Append ``message`` to the error log with a timestamp."""

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
