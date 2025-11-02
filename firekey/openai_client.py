"""Wrapper around the OpenAI client used by FireKey."""

from __future__ import annotations

import importlib.util
import os
from typing import Optional


def _load_openai_module():
    """Dynamically load the OpenAI module if available."""

    spec = importlib.util.find_spec("openai")
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        return None
    loader.exec_module(module)  # type: ignore[attr-defined]
    return module


_OPENAI_MODULE = _load_openai_module()


class OpenAIClient:
    """Thin wrapper that hides library version differences."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._module = _OPENAI_MODULE
        self._client = None

        if self._module is not None and hasattr(self._module, "OpenAI") and self.api_key:
            self._client = self._module.OpenAI(api_key=self.api_key)

    def generate_response(self, prompt: str) -> str:
        """Send the merged context prompt to OpenAI."""

        prompt = prompt.strip()
        if not prompt:
            return "No prompt provided."

        if self._module is None:
            return "OpenAI client library is not installed."

        if self._client is not None:
            try:
                if hasattr(self._client, "responses"):
                    response = self._client.responses.create(
                        model=self.model,
                        input=[{"role": "user", "content": prompt}],
                    )
                    first_output = response.output[0]
                    if getattr(first_output, "content", None):
                        first_segment = first_output.content[0]
                        text = getattr(first_segment, "text", None)
                        if text:
                            return text.strip()
                    # Fallback to entire representation
                    return str(response)
            except Exception as exc:  # pragma: no cover - defensive
                return f"OpenAI request failed: {exc}"

        # Support for legacy openai>=0.28 style APIs
        if hasattr(self._module, "ChatCompletion"):
            try:
                response = self._module.ChatCompletion.create(  # type: ignore[attr-defined]
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    api_key=self.api_key,
                )
                choice = response["choices"][0]
                message = choice.get("message", {})
                content = message.get("content")
                if isinstance(content, str):
                    return content.strip()
                return str(response)
            except Exception as exc:  # pragma: no cover - defensive
                return f"OpenAI request failed: {exc}"

        return "OpenAI client is not configured."
