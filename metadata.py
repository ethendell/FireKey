"""Utilities for generating metadata for stock images using OpenAI models."""

from __future__ import annotations

import base64
import io
import json
from typing import Any, Dict, List, Optional

from PIL import Image
from openai import OpenAI


_SYSTEM_MESSAGE = (
    "You are a professional stock content metadata creator. For each image, "
    "write a concise title (≤225 characters), detailed description (≤800 characters), "
    "and up to 50 relevant keywords. Return valid JSON with keys: title, description, keywords."
)

_USER_MESSAGE = "Analyze this image and create metadata suitable for iStock/Getty."

_ALLOWED_MODELS = {"gpt-4o", "gpt-4o-mini"}


def _encode_image_to_base64(image_path: str) -> str:
    """Open an image with Pillow, encode it to base64, and return the string."""
    with Image.open(image_path) as img:
        buffer = io.BytesIO()
        format_ = img.format or "PNG"
        img.save(buffer, format=format_)
        image_bytes = buffer.getvalue()
    return base64.b64encode(image_bytes).decode("utf-8")


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Attempt to parse JSON from text, handling extra prose or fencing."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    raise ValueError("Unable to parse JSON from model response")


def _normalise_keywords(value: Any) -> List[str]:
    """Ensure keywords are returned as a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [keyword.strip() for keyword in value.split(",") if keyword.strip()]
    return [str(value).strip()]


def generate_metadata(
    image_path: str,
    context: Optional[str] = None,
    model: str = "gpt-4o-mini",
    creativity: float = 0.7,
) -> Dict[str, Any]:
    """Generate stock-image metadata using an OpenAI vision-capable model."""
    if model not in _ALLOWED_MODELS:
        raise ValueError(f"Model must be one of {_ALLOWED_MODELS}, got {model!r}")

    encoded_image = _encode_image_to_base64(image_path)

    client = OpenAI()

    user_content = _USER_MESSAGE
    if context:
        user_content = f"{user_content}\n\nAdditional context: {context.strip()}"

    response = client.responses.create(
        model=model,
        temperature=creativity,
        system=[{"role": "system", "content": [{"type": "text", "text": _SYSTEM_MESSAGE}]}],
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_content},
                    {"type": "input_image", "image": {"b64_json": encoded_image}},
                ],
            }
        ],
    )

    raw_output = getattr(response, "output_text", None)
    if not raw_output:
        # Fallback for SDKs that return structured content
        try:
            parts: List[str] = []
            for item in getattr(response, "output", []):
                for part in getattr(item, "content", []):
                    if getattr(part, "type", "") == "output_text":
                        text_piece = getattr(part, "text", "")
                        if text_piece:
                            parts.append(text_piece)
            raw_output = "".join(parts)
        except AttributeError as exc:
            raise ValueError("Unexpected response structure from OpenAI API") from exc
    if not raw_output:
        raise ValueError("OpenAI API returned an empty response")

    payload = _extract_json_object(raw_output)

    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    keywords = _normalise_keywords(payload.get("keywords"))

    return {
        "title": title,
        "description": description,
        "keywords": keywords,
    }
