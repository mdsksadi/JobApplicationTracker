"""Explicit, on-demand export writers.

A file is created only when one of these functions is called from the Export
dialog. There is no automatic background saving anywhere in the application.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .models import Application
from .store import ApplicationStore

CSV_FIELDS = [
    "number", "company", "position", "requirements", "link", "status",
    "credential", "application_date", "notes", "created_at", "updated_at",
]

FORMAT_LABELS = {
    "json": "JSON file (*.json)",
    "csv": "CSV file (*.csv)",
    "txt": "Text log (*.txt)",
    "md": "Markdown table (*.md)",
    "xlsx": "Excel workbook (*.xlsx)",
}

EXTENSIONS = {
    "json": ".json",
    "csv": ".csv",
    "txt": ".txt",
    "md": ".md",
    "xlsx": ".xlsx",
}


def filetypes() -> list[tuple[str, str]]:
    return [(label, f"*{EXTENSIONS[key]}") for key, label in FORMAT_LABELS.items()]


def _ensure_extension(path: Path, fmt: str) -> Path:
    ext = EXTENSIONS.get(fmt, "")
    if ext and path.suffix.lower() != ext:
        return path.with_suffix(ext)
    return path


def export(store: ApplicationStore, fmt: str, path: str | Path) -> Path:
    fmt = fmt.lower()
    target = _ensure_extension(Path(path).expanduser(), fmt)
    target.parent.mkdir(parents=True, exist_ok=True)
    writers = {
        "json": _write_json,
        "csv": _write_csv,
        "txt": _write_txt,
        "md": _write_markdown,
        "xlsx": _write_xlsx,
    }
    if fmt not in writers:
        raise ValueError(f"Unsupported export format: {fmt}")
    writers[fmt](store, target)
    store.log("EXPORT", f"{fmt.upper()} -> {target}")
    return target


def _write_json(store: ApplicationStore, path: Path) -> None:
    payload = {
        "app": "JobApplicationTracker",
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(store),
        "applications": [app.to_dict() for app in store.all()],
        "activity_log": store.activity_lines(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_csv(store: ApplicationStore, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for index, app in enumerate(store.all(), start=1):
            writer.writerow({
                "number": index,
                "company": app.company,
                "position": app.position,
                "requirements": "; ".join(app.requirements),
                "link": app.link,
                "status": app.status,
                "credential": app.credential,
                "application_date": app.application_date,
                "notes": app.notes,
                "created_at": app.created_at,
                "updated_at": app.updated_at,
            })


def _write_txt(store: ApplicationStore, path: Path) -> None:
    lines = [
        "JOB APPLICATION TRACKER - EXPORT LOG",
        "=" * 48,
        f"Exported: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"Applications: {len(store)}",
        "",
    ]
    for index, app in enumerate(store.all(), start=1):
        lines.extend([
            f"[{index:03d}] {app.company or '(no company)'} - {app.position or '(no position)'}",
            f"      Status: {app.status}",
            f"      Date: {app.application_date or '(not set)'}",
            f"      Link: {app.link or '-'}",
            f"      Credential: {app.credential or '-'}",
            f"      Requirements: {'; '.join(app.requirements) if app.requirements else '-'}",
            f"      Notes: {app.notes or '-'}",
            "",
        ])
    lines.extend(["ACTIVITY LOG", "-" * 48])
    lines.extend(store.activity_lines() or ["(no activity recorded)"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(store: ApplicationStore, path: Path) -> None:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ") or "-"

    lines = [
        "# Job Application Tracker - Export",
        "",
        f"Exported: {datetime.now():%Y-%m-%d %H:%M:%S}  ",
        f"Applications: {len(store)}",
        "",
        "| # | Company | Position | Requirements | Link | Status | Credential | Date | Notes |",
        "|---|---------|----------|--------------|------|--------|------------|------|-------|",
    ]
    for index, app in enumerate(store.all(), start=1):
        lines.append(
            "| {n} | {c} | {p} | {r} | {l} | {s} | {cr} | {d} | {no} |".format(
                n=index,
                c=cell(app.company),
                p=cell(app.position),
                r=cell("; ".join(app.requirements)),
                l=cell(app.link),
                s=cell(app.status),
                cr=cell(app.credential),
                d=cell(app.application_date),
                no=cell(app.notes),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_xlsx(store: ApplicationStore, path: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Excel export needs the optional dependency. Install it with:\n"
            "  pip install 'job-application-tracker[excel]'"
        ) from exc

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Applications"
    sheet.append(CSV_FIELDS)
    for index, app in enumerate(store.all(), start=1):
        sheet.append([
            index,
            app.company,
            app.position,
            "; ".join(app.requirements),
            app.link,
            app.status,
            app.credential,
            app.application_date,
            app.notes,
            app.created_at,
            app.updated_at,
        ])
    activity = workbook.create_sheet("Activity Log")
    activity.append(["Timestamp", "Action", "Detail"])
    for entry in store.activity:
        activity.append([entry.timestamp, entry.action, entry.detail])
    workbook.save(path)


def applications_from_json(path: str | Path) -> list[Application]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        records = data.get("applications", [])
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError("JSON file does not contain a list of applications.")
    return [Application.from_dict(record) for record in records if isinstance(record, dict)]


def applications_from_csv(path: str | Path) -> list[Application]:
    result: list[Application] = []
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            record = dict(row)
            record.pop("number", None)
            result.append(Application.from_dict(record))
    return result
