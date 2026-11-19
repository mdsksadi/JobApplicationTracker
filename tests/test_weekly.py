from datetime import date

from job_application_tracker.models import Application
from job_application_tracker.weekly import (
    background_color,
    count_for_week,
    progress_label,
    week_bounds,
)


def test_week_bounds_monday_to_sunday():
    assert week_bounds(date(2026, 11, 19)) == (date(2026, 11, 16), date(2026, 11, 22))
    assert week_bounds(date(2026, 11, 16)) == (date(2026, 11, 16), date(2026, 11, 22))
    assert week_bounds(date(2026, 11, 22)) == (date(2026, 11, 16), date(2026, 11, 22))


def test_count_for_week_ignores_other_weeks_and_bad_dates():
    apps = [
        Application(application_date="2026-11-16"),
        Application(application_date="2026-11-19"),
        Application(application_date="2026-11-22"),
        Application(application_date="2026-11-23"),
        Application(application_date="not-a-date"),
        Application(application_date=""),
    ]
    assert count_for_week(apps, date(2026, 11, 19)) == 3


def test_background_color_boundaries():
    assert background_color(0, 5) == "#E05656"
    assert background_color(5, 5) == "#FFFFFF"
    assert background_color(3, 5) != background_color(0, 5)
    green = background_color(10, 5)
    red = background_color(0, 5)
    assert green != "#FFFFFF" and green != red
    assert background_color(5, 5, dark=True) == "#262626"


def test_progress_label():
    assert "2 to go" in progress_label(3, 5)
    assert "target reached" in progress_label(5, 5)
    assert "1 over target" in progress_label(6, 5)
