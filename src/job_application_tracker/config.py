"""Small, persistent configuration.

Application *records* are deliberately never written automatically. The only
file this module writes is ``config.json`` in the platform's user config dir,
holding preferences and license activation state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "JobApplicationTracker"
CONFIG_DIR = Path(user_config_dir(APP_NAME, appauthor="Sadi App"))
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_STATUSES: list[str] = [
    "Pending",
    "Submitted",
    "Rejected",
    "1st Interview",
    "2nd Interview",
    "Offer",
    "Accepted",
    "Withdrawn",
]

CUSTOM_STATUS_OPTION = "+ Add custom status..."


@dataclass
class Config:
    weekly_target: int = 5
    custom_statuses: list[str] = field(default_factory=list)
    theme: str = "system"  # system | light | dark
    page_size: int = 20
    last_export_dir: str = ""
    activated: bool = False
    licensee: str = ""

    @property
    def statuses(self) -> list[str]:
        """Built-in statuses plus user-added ones, de-duplicated."""
        result = list(DEFAULT_STATUSES)
        for status in self.custom_statuses:
            cleaned = status.strip()
            if cleaned and cleaned not in result:
                result.append(cleaned)
        return result

    def add_custom_status(self, status: str) -> str:
        cleaned = status.strip()
        if not cleaned:
            return ""
        if cleaned not in self.custom_statuses and cleaned not in DEFAULT_STATUSES:
            self.custom_statuses.append(cleaned)
        self.save()
        return cleaned

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(CONFIG_PATH)

    @classmethod
    def load(cls) -> "Config":
        if not CONFIG_PATH.exists():
            return cls()
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        known = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in known}
        try:
            return cls(**clean)
        except TypeError:
            return cls()
