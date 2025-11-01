"""Wrapper utilities to integrate :class:`TokenUsageTracker` with API clients."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from .tracker import CallRecord, TokenUsageTracker


class TrackedAPIClient:
    """Wrap a callable-based API client to add token tracking automatically."""

    def __init__(
        self,
        sender: Callable[..., Any],
        tracker: TokenUsageTracker,
        *,
        default_model: Optional[str] = None,
    ) -> None:
        self._sender = sender
        self._tracker = tracker
        self._default_model = default_model

    def __call__(
        self,
        *,
        file_name: str,
        prompt: str,
        model: Optional[str] = None,
        completion_text_extractor: Optional[Callable[[Any], str]] = None,
        usage_extractor: Optional[Callable[[Any], Optional[Mapping[str, int]]]] = None,
        record_callback: Optional[Callable[[CallRecord], None]] = None,
        return_record: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Send a tracked API call.

        Args:
            file_name: Name of the file associated with the call.
            prompt: Text prompt sent to the API.
            model: Optional override for the model name.
            completion_text_extractor: Optional function to extract the completion text
                from the raw API response when usage metadata is missing.
            usage_extractor: Optional function returning a usage mapping compatible with
                :meth:`TokenUsageTracker.finish_call`.
            **kwargs: Additional keyword arguments forwarded to the sender.
        """

        resolved_model = model or self._default_model
        call_id = self._tracker.start_call(file_name=file_name, prompt_text=prompt, model=resolved_model)
        response = self._sender(prompt=prompt, model=resolved_model, **kwargs)

        usage: Optional[Mapping[str, int]] = None
        if usage_extractor is not None:
            usage = usage_extractor(response)
            if usage is not None:
                usage = dict(usage)

        completion_text = ""
        if completion_text_extractor is not None:
            completion_text = completion_text_extractor(response)

        record = self._tracker.finish_call(
            call_id,
            completion_text=completion_text,
            model=resolved_model,
            usage=usage,
        )
        if record_callback is not None:
            record_callback(record)

        if return_record:
            return response, record
        return response


def default_completion_extractor(response: Any) -> str:
    """Attempt to extract completion text from a variety of response shapes."""

    if response is None:
        return ""

    if isinstance(response, str):
        return response

    message = getattr(response, "message", None)
    if message and hasattr(message, "content"):
        return str(message.content)

    choices: Optional[Iterable[Any]] = getattr(response, "choices", None)
    if choices:
        first = next(iter(choices), None)
        if first is not None:
            content = getattr(first, "message", None)
            if content and hasattr(content, "content"):
                return str(content.content)
            if hasattr(first, "text"):
                return str(first.text)

    return ""


def default_usage_extractor(response: Any) -> Optional[Mapping[str, int]]:
    """Extract usage metadata from OpenAI-like responses when available."""

    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, Mapping):
        usage = response.get("usage")
    if usage is None:
        return None

    mapping: Dict[str, int] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = getattr(usage, key, None)
        if value is None and isinstance(usage, Mapping):
            value = usage.get(key)
        if value is not None:
            mapping[key] = int(value)
    return mapping or None
