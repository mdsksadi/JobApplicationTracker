"""Data model and validation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

DATE_FORMAT = "%Y-%m-%d"


@dataclass
class Application:
    id: int = 0
    company: str = ""
    position: str = ""
    requirements: list[str] = field(default_factory=list)
    link: str = ""
    status: str = "Pending"
    credential: str = ""
    application_date: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Application":
        allowed = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in allowed}
        reqs = clean.get("requirements") or []
        if isinstance(reqs, str):
            reqs = [r.strip() for r in reqs.split(";") if r.strip()]
        clean["requirements"] = [str(r) for r in reqs]
        for key in ("company", "position", "link", "status", "credential",
                    "application_date", "notes", "created_at", "updated_at"):
            if key in clean and clean[key] is None:
                clean[key] = ""
        try:
            clean["id"] = int(clean.get("id", 0) or 0)
        except (TypeError, ValueError):
            clean["id"] = 0
        return cls(**clean)

    def summary(self) -> str:
        return f"#{self.id:03d} | {self.company or '(no company)'} | {self.position or '(no position)'}"


@dataclass
class ActivityEntry:
    timestamp: str
    action: str
    detail: str

    def to_line(self) -> str:
        return f"{self.timestamp} | {self.action:<8} | {self.detail}"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today_str() -> str:
    return date.today().strftime(DATE_FORMAT)


def normalize_date(value: str) -> str:
    """Return YYYY-MM-DD if valid, otherwise an empty string."""
    value = (value or "").strip()
    if not value:
        return ""
    for fmt in (DATE_FORMAT, "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).strftime(DATE_FORMAT)
        except ValueError:
            continue
    return ""


def is_valid_date(value: str) -> bool:
    return bool(normalize_date(value))
