"""Profile management utilities for FireKey."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Profile:
    """Represents a context profile stored on disk."""

    name: str
    context: str
    path: Optional[Path] = None

    def to_dict(self) -> dict:
        """Return the JSON-serialisable representation of the profile."""

        return {"name": self.name, "context": self.context}


class ProfileManager:
    """Loads and persists context profiles from the profiles directory."""

    def __init__(self, profiles_dir: Path):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_profiles(self) -> List[Profile]:
        """Return all valid profiles found in the profiles directory."""

        profiles: List[Profile] = []
        for path in sorted(self.profiles_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                # Skip malformed profile files but continue processing others.
                continue

            name = data.get("name")
            context = data.get("context", "")
            if not isinstance(name, str) or not isinstance(context, str):
                continue

            profiles.append(Profile(name=name.strip(), context=context, path=path))

        return profiles

    # ------------------------------------------------------------------
    # Saving / deleting
    # ------------------------------------------------------------------
    def save_profile(self, profile: Profile, *, original_path: Optional[Path] = None) -> Profile:
        """Persist the given profile and return the saved instance."""

        target_path = self._path_for_name(profile.name, existing_path=original_path or profile.path)
        target_path.write_text(
            json.dumps(profile.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if original_path and original_path != target_path and original_path.exists():
            original_path.unlink()
        return Profile(name=profile.name, context=profile.context, path=target_path)

    def delete_profile(self, profile: Profile) -> None:
        """Remove the profile's file from disk."""

        if profile.path and profile.path.exists():
            profile.path.unlink()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _path_for_name(self, name: str, *, existing_path: Optional[Path] = None) -> Path:
        """Create a unique JSON path for the provided profile name."""

        slug = self._slugify(name)
        base = slug or "profile"
        candidate = base
        counter = 1
        while True:
            path = self.profiles_dir / f"{candidate}.json"
            if existing_path is not None and path == existing_path:
                return path
            if not path.exists():
                return path
            counter += 1
            candidate = f"{base}-{counter}"

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug
