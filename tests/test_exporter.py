import json

import pytest

from job_application_tracker.exporter import (
    applications_from_csv,
    applications_from_json,
    export,
)
from job_application_tracker.models import Application
from job_application_tracker.store import ApplicationStore


@pytest.fixture
def store():
    result = ApplicationStore()
    result.add(Application(
        company="Acme", position="Engineer", requirements=["Python", "SQL"],
        link="https://example.com/job/1", status="Submitted", credential=" referrals ",
        application_date="2026-11-19", notes="Follow up next week",
    ))
    return result


@pytest.mark.parametrize("fmt", ["json", "csv", "txt", "md", "xlsx"])
def test_export_writes_only_when_called(tmp_path, store, fmt):
    target = export(store, fmt, tmp_path / f"out_{fmt}")
    assert target.exists()
    assert target.stat().st_size > 0
    assert store.activity[-1].action == "EXPORT"


def test_json_round_trip(tmp_path, store):
    path = export(store, "json", tmp_path / "data.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["count"] == 1
    assert payload["applications"][0]["company"] == "Acme"
    apps = applications_from_json(path)
    assert apps[0].requirements == ["Python", "SQL"]


def test_csv_round_trip(tmp_path, store):
    path = export(store, "csv", tmp_path / "data.csv")
    apps = applications_from_csv(path)
    assert apps[0].company == "Acme"
    assert apps[0].requirements == ["Python", "SQL"]


def test_txt_includes_activity_and_application(tmp_path, store):
    path = export(store, "txt", tmp_path / "data.txt")
    content = path.read_text(encoding="utf-8")
    assert "Acme" in content
    assert "ACTIVITY LOG" in content
