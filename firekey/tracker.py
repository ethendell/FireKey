"""Utilities for tracking token usage and estimated cost of API calls."""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ModelPricing:
    """Pricing information for a model.

    Attributes:
        input_cost_per_1k: Cost in USD per 1,000 input tokens.
        output_cost_per_1k: Cost in USD per 1,000 output tokens.
    """

    input_cost_per_1k: float
    output_cost_per_1k: float

    def cost_for(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for the provided prompt and completion tokens."""
        input_cost = (prompt_tokens / 1000.0) * self.input_cost_per_1k
        output_cost = (completion_tokens / 1000.0) * self.output_cost_per_1k
        return input_cost + output_cost


@dataclass
class CallRecord:
    """Represents a single API call accounting entry."""

    file_name: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float


@dataclass
class _PendingCall:
    """Internal representation of a call that has started but not finished."""

    file_name: str
    model: str
    estimated_prompt_tokens: int


class TokenUsageTracker:
    """Track token usage and estimated cost for API calls."""

    def __init__(
        self,
        model_pricing: Optional[Dict[str, ModelPricing]] = None,
        default_model: str = "gpt-4o-mini",
        default_pricing: Optional[ModelPricing] = None,
    ) -> None:
        self._model_pricing = model_pricing or {}
        self._default_model = default_model
        self._default_pricing = default_pricing or ModelPricing(0.00015, 0.0006)
        self._pending: Dict[str, _PendingCall] = {}
        self._records: List[CallRecord] = []
        self._total_tokens = 0
        self._total_cost = 0.0

    @property
    def records(self) -> Tuple[CallRecord, ...]:
        """Return immutable view of recorded calls."""

        return tuple(self._records)

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed across all tracked calls."""

        return self._total_tokens

    @property
    def total_cost(self) -> float:
        """Total estimated cost across all tracked calls."""

        return self._total_cost

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using a simple heuristic.

        The heuristic assumes an average of four characters per token which is a
        reasonable approximation for English text.
        """

        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4))

    def start_call(self, file_name: str, prompt_text: str, model: Optional[str] = None) -> str:
        """Record the beginning of an API call and return a correlation id."""

        call_id = uuid.uuid4().hex
        resolved_model = model or self._default_model
        estimated_prompt_tokens = self.estimate_tokens(prompt_text)
        self._pending[call_id] = _PendingCall(
            file_name=file_name,
            model=resolved_model,
            estimated_prompt_tokens=estimated_prompt_tokens,
        )
        return call_id

    def finish_call(
        self,
        call_id: str,
        completion_text: str = "",
        *,
        model: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
    ) -> CallRecord:
        """Finalize a call using available usage information.

        Args:
            call_id: Identifier returned by :meth:`start_call`.
            completion_text: Text returned by the API for estimating completion tokens
                when usage metadata is absent.
            model: Optional override for the model used by the call.
            usage: Optional dictionary containing usage metrics from the API response.
                Recognised keys include ``prompt_tokens``, ``completion_tokens`` and
                ``total_tokens``.
        """

        pending = self._pending.pop(call_id)
        resolved_model = model or pending.model
        prompt_tokens = pending.estimated_prompt_tokens
        completion_tokens = 0
        total_tokens = 0

        if usage:
            prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
            if completion_tokens == 0 and total_tokens and prompt_tokens:
                completion_tokens = max(total_tokens - prompt_tokens, 0)
        else:
            completion_tokens = self.estimate_tokens(completion_text)
            total_tokens = prompt_tokens + completion_tokens

        pricing = self._model_pricing.get(resolved_model, self._default_pricing)
        cost = pricing.cost_for(prompt_tokens, completion_tokens)

        self._total_tokens += total_tokens
        self._total_cost += cost

        record = CallRecord(
            file_name=pending.file_name,
            model=resolved_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )
        self._records.append(record)

        message = (
            f"[{record.file_name}] Tokens used: {record.total_tokens} | "
            f"Approx Cost: ${record.cost:.6f} | Model: {record.model}"
        )
        print(message)

        return record

    def format_summary(self) -> str:
        """Generate a readable summary string."""

        return (
            f"Total tokens: {self._total_tokens} | "
            f"Estimated cost: ${self._total_cost:.6f}"
        )

    def print_summary(self) -> None:
        """Print a summary line for the entire run."""

        print(self.format_summary())

    def csv_footer_comment(self) -> str:
        """Return a comment line that can be appended to a CSV file."""

        return f"# {self.format_summary()}"
