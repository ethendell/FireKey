"""Logic for loading prompt templates from disk."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, List, Optional
import string

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True)
class PromptTemplate:
    """Represents a prompt template loaded from disk."""

    file_name: str
    name: str
    system_prompt: str
    user_prompt: str

    def render(self, *, type_value: str, context: str) -> Dict[str, str]:
        formatter = string.Formatter()
        values = _SafeDict({"type": type_value, "context": context})
        system = formatter.vformat(self.system_prompt, (), values)
        user = formatter.vformat(self.user_prompt, (), values)
        return {"system_prompt": system, "user_prompt": user}


class PromptRepository:
    """Loads prompt templates from the prompts directory."""

    def __init__(self, prompt_dir: Path = PROMPT_DIR) -> None:
        self._prompt_dir = prompt_dir
        self._cache: Dict[str, PromptTemplate] = {}
        self.reload()

    def reload(self) -> None:
        self._cache.clear()
        if not self._prompt_dir.exists():
            return
        for path in sorted(self._prompt_dir.glob("*.txt")):
            template = self._load_template(path)
            if template is not None:
                self._cache[template.file_name] = template

    def list_templates(self) -> List[PromptTemplate]:
        return list(self._cache.values())

    def get(self, file_name: str) -> Optional[PromptTemplate]:
        return self._cache.get(file_name)

    def _load_template(self, path: Path) -> Optional[PromptTemplate]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        name = data.get("name")
        system_prompt = data.get("system_prompt")
        user_prompt = data.get("user_prompt")
        if not all(isinstance(value, str) for value in (name, system_prompt, user_prompt)):
            return None
        return PromptTemplate(
            file_name=path.name,
            name=name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )


__all__ = ["PromptRepository", "PromptTemplate", "PROMPT_DIR"]
