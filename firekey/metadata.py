"""Metadata extraction utilities for FireKey."""

from __future__ import annotations

import base64
import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, MutableMapping, Optional, Sequence

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
DEFAULT_CACHE_DIR = Path(".cache") / "firekey"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_VIDEO_FRAME_COUNT = 5


class MetadataGenerationError(RuntimeError):
    """Raised when metadata generation fails."""


@dataclass
class PosterFrame:
    """Container describing the poster frame information."""

    source_path: Path
    output_path: Optional[Path]


def extract_key_frames(
    video_path: Path | str,
    frame_count: int = DEFAULT_VIDEO_FRAME_COUNT,
    *,
    cache_dir: Path | str | None = None,
) -> List[Path]:
    """Extract evenly spaced key frames from a video file.

    Args:
        video_path: Path to the video file to sample.
        frame_count: Number of frames to capture.
        cache_dir: Optional directory where temporary JPEGs are stored.

    Returns:
        A list of paths to the saved frame images.

    Raises:
        MetadataGenerationError: If the video cannot be processed.
    """

    try:
        import cv2  # type: ignore
    except ImportError as exc:  # pragma: no cover - OpenCV may not be installed in tests
        raise MetadataGenerationError("OpenCV (cv2) is required to extract key frames.") from exc

    video_path = Path(video_path)
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR / "frames"
    cache_dir = Path(cache_dir)

    if not video_path.exists():
        raise MetadataGenerationError(f"Video file not found: {video_path}")

    cache_dir.mkdir(parents=True, exist_ok=True)
    # Create an isolated directory for this video's frames to prevent stale files.
    video_cache_dir = cache_dir / f"{video_path.stem}_{uuid.uuid4().hex[:8]}"
    video_cache_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise MetadataGenerationError(f"Unable to open video file: {video_path}")

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 0

    frame_count = max(1, frame_count)
    frame_indices: List[int]
    if total_frames > 0 and frame_count > 1:
        frame_indices = [
            min(total_frames - 1, round(i * (total_frames - 1) / (frame_count - 1)))
            for i in range(frame_count)
        ]
    elif total_frames > 0:
        frame_indices = [total_frames // 2]
    else:
        frame_indices = list(range(frame_count))

    # Remove potential duplicates caused by rounding when frame_count exceeds available frames.
    frame_indices = sorted(dict.fromkeys(frame_indices))
    if not frame_indices:
        frame_indices = [0]

    frame_paths: List[Path] = []
    grabbed_frames = 0
    for target_index in frame_indices:
        if total_frames > 0:
            capture.set(cv2.CAP_PROP_POS_FRAMES, target_index)
        else:
            # Without a frame count, advance sequentially to approximate sampling.
            while grabbed_frames < target_index:
                grabbed_frames += 1
                if not capture.read()[0]:
                    break

        success, frame = capture.read()
        if not success or frame is None:
            continue

        filename = f"{video_path.stem}_frame_{target_index:06d}.jpg"
        frame_path = video_cache_dir / filename
        if not cv2.imwrite(str(frame_path), frame):
            continue

        frame_paths.append(frame_path)

    capture.release()

    if not frame_paths:
        raise MetadataGenerationError(f"Failed to extract frames from video: {video_path}")

    return frame_paths


def generate_metadata(
    image_path: Path | str,
    *,
    client,
    csv_path: Path | str | None = None,
    model: str = DEFAULT_MODEL,
    cache_dir: Path | str | None = None,
    frame_count: int = DEFAULT_VIDEO_FRAME_COUNT,
) -> MutableMapping[str, object]:
    """Generate metadata for an image or video file.

    Args:
        image_path: Path to the media to analyze.
        client: Pre-configured OpenAI client instance.
        csv_path: Optional path to the CSV file used for output placement.
        model: The OpenAI model to call.
        cache_dir: Directory to use for cached assets such as extracted frames.
        frame_count: Number of frames to sample for videos.

    Returns:
        A mapping containing metadata fields such as title, description, keywords, and
        poster frame information.
    """

    image_path = Path(image_path)
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    poster_frame: Optional[PosterFrame] = None
    media_paths: Sequence[Path]
    is_video = image_path.suffix.lower() in VIDEO_EXTENSIONS

    if is_video:
        frame_paths = extract_key_frames(image_path, frame_count=frame_count, cache_dir=cache_dir / "frames")
        media_paths = frame_paths
        poster_frame = PosterFrame(source_path=frame_paths[0], output_path=None)
        prompt_text = (
            "Analyze these frames as a single video. Summarize the visible action, camera movement, and context. "
            "Generate a concise title (≤225 chars), detailed description (≤800 chars), and 50 keywords relevant to the video."
        )
    else:
        media_paths = [image_path]
        prompt_text = (
            "Analyze this image. Summarize the visible action, camera movement or composition, and context. "
            "Generate a concise title (≤225 chars), detailed description (≤800 chars), and 50 keywords relevant to the image."
        )

    response = _request_metadata_from_openai(
        client=client,
        model=model,
        prompt_text=prompt_text,
        media_paths=media_paths,
    )
    if response is None:
        raise MetadataGenerationError("No metadata returned by OpenAI API.")

    merged = _merge_metadata_responses([response])

    if poster_frame:
        poster_output = _save_poster_frame(poster_frame, csv_path)
        poster_frame.output_path = poster_output
        merged["poster_frame_path"] = str(poster_output or poster_frame.source_path)
    else:
        merged.setdefault("poster_frame_path", None)

    return merged


def _request_metadata_from_openai(
    *,
    client,
    model: str,
    prompt_text: str,
    media_paths: Sequence[Path],
) -> Optional[MutableMapping[str, object]]:
    content = [
        {"type": "text", "text": prompt_text},
    ]
    for media in media_paths:
        content.append({"type": "input_image", "image_base64": _encode_image_to_base64(media)})

    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": content}],
    )
    return _parse_response_to_json(response)


def _encode_image_to_base64(image_path: Path) -> str:
    data = image_path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def _parse_response_to_json(response) -> Optional[MutableMapping[str, object]]:
    """Extract a JSON object from an OpenAI response object."""

    text_chunks: List[str] = []

    if hasattr(response, "output"):
        for item in getattr(response, "output", []):
            contents = getattr(item, "content", [])
            for content in contents:
                if getattr(content, "type", None) == "output_text":
                    text_chunks.append(getattr(content, "text", ""))
    elif hasattr(response, "choices"):
        choices = getattr(response, "choices", [])
        if choices:
            message = choices[0]
            if isinstance(message, dict):
                text = message.get("message", {}).get("content") or message.get("text")
            else:
                text = getattr(message, "message", None)
                if text is not None and hasattr(text, "content"):
                    text = text.content
            if isinstance(text, str):
                text_chunks.append(text)

    full_text = "\n".join(chunk.strip() for chunk in text_chunks if chunk.strip())
    if not full_text:
        return None

    json_text = _extract_json_text(full_text)
    if not json_text:
        return None

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise MetadataGenerationError("Failed to parse JSON metadata from OpenAI response.") from exc

    if not isinstance(data, MutableMapping):
        raise MetadataGenerationError("OpenAI response JSON must be an object.")

    return data


def _extract_json_text(text: str) -> Optional[str]:
    """Extract a JSON object from free-form text containing code fences."""

    text = text.strip()
    if not text:
        return None

    if "```" in text:
        segments = text.split("```")
        for segment in segments:
            segment = segment.strip()
            if segment.startswith("{") and segment.endswith("}"):
                return segment

    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        return text[start : end + 1]

    return None


def _merge_metadata_responses(responses: Sequence[MutableMapping[str, object]]) -> MutableMapping[str, object]:
    if not responses:
        raise MetadataGenerationError("At least one response is required to merge metadata.")

    if len(responses) == 1:
        return dict(responses[0])

    merged: MutableMapping[str, object] = {}

    titles = [resp.get("title") for resp in responses if isinstance(resp.get("title"), str)]
    descriptions = [resp.get("description") for resp in responses if isinstance(resp.get("description"), str)]

    merged["title"] = _select_longest_text(titles, max_length=225)
    merged["description"] = _select_longest_text(descriptions, max_length=800)

    all_keywords: List[str] = []
    for resp in responses:
        keywords = resp.get("keywords")
        if isinstance(keywords, str):
            keywords_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        elif isinstance(keywords, Iterable):
            keywords_list = [str(kw).strip() for kw in keywords if str(kw).strip()]
        else:
            keywords_list = []
        all_keywords.extend(keywords_list)

    seen = set()
    deduped_keywords = []
    for keyword in all_keywords:
        normalized = keyword.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped_keywords.append(keyword)
        if len(deduped_keywords) >= 50:
            break

    merged["keywords"] = deduped_keywords

    # Preserve additional keys from the first response when not already present.
    base_response = responses[0]
    for key, value in base_response.items():
        if key in {"title", "description", "keywords"}:
            continue
        merged.setdefault(key, value)

    return merged


def _select_longest_text(options: Sequence[str], *, max_length: int) -> Optional[str]:
    if not options:
        return None

    sorted_options = sorted(
        (option for option in options if option),
        key=lambda text: (len(text.split()), len(text)),
        reverse=True,
    )
    for option in sorted_options:
        if len(option) <= max_length:
            return option
        truncated = option[:max_length].rstrip()
        if truncated:
            return truncated
    return sorted_options[0][:max_length]


def _save_poster_frame(poster_frame: PosterFrame, csv_path: Path | str | None) -> Optional[Path]:
    if csv_path is None:
        return None

    csv_path = Path(csv_path)
    destination = csv_path.with_name(f"{csv_path.stem}_poster.jpg")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(poster_frame.source_path, destination)
    return destination
