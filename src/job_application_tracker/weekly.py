"""Calendar-week counting and the motivation background colour."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from .models import Application

RED_DARK = (224, 86, 86)
WHITE = (255, 255, 255)
GREEN = (140, 220, 160)

DARK_RED = (92, 32, 32)
DARK_NEUTRAL = (38, 38, 38)
DARK_GREEN = (34, 84, 52)


def week_bounds(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    start = today - timedelta(days=today.weekday())  # Monday
    return start, start + timedelta(days=6)  # Sunday


def count_for_week(applications: Iterable[Application], today: date | None = None) -> int:
    start, end = week_bounds(today)
    count = 0
    for app in applications:
        try:
            applied = date.fromisoformat((app.application_date or "").strip())
        except ValueError:
            continue
        if start <= applied <= end:
            count += 1
    return count


def _blend(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> str:
    t = max(0.0, min(1.0, t))
    channels = [round(a + (b - a) * t) for a, b in zip(c1, c2)]
    return "#{:02X}{:02X}{:02X}".format(*channels)


def background_color(count: int, target: int, dark: bool = False) -> str:
    """Map this week's progress to a background colour.

    0 applications -> strong red, approaching target -> white, exactly target
    -> white, above target -> increasingly green (capped at 2x the target).
    """
    target = max(1, int(target))
    ratio = count / target

    if dark:
        if ratio <= 1:
            return _blend(DARK_RED, DARK_NEUTRAL, ratio)
        return _blend(DARK_NEUTRAL, DARK_GREEN, min(1.0, (ratio - 1.0)))

    if ratio <= 1:
        return _blend(RED_DARK, WHITE, ratio)
    return _blend(WHITE, GREEN, min(1.0, (ratio - 1.0)))


def progress_label(count: int, target: int) -> str:
    target = max(0, int(target))
    if count == target:
        return f"This week: {count} / {target} - target reached"
    if count > target:
        return f"This week: {count} / {target} - {count - target} over target"
    return f"This week: {count} / {target} - {target - count} to go"
