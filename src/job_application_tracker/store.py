"""In-memory application store and activity timeline.

Nothing in this module touches the filesystem. Persistence happens only when
the user explicitly exports.
"""

from __future__ import annotations

from typing import Iterable

from .models import ActivityEntry, Application, now_iso


class ApplicationStore:
    def __init__(self) -> None:
        self.applications: list[Application] = []
        self.activity: list[ActivityEntry] = []
        self._next_id = 1

    # ------------------------------------------------------------------ read
    def get(self, app_id: int) -> Application | None:
        for app in self.applications:
            if app.id == app_id:
                return app
        return None

    def all(self) -> list[Application]:
        """Newest-entered first (insertion order)."""
        return list(self.applications)

    def __len__(self) -> int:
        return len(self.applications)

    # ----------------------------------------------------------------- write
    def add(self, app: Application) -> Application:
        app.id = self._next_id
        self._next_id += 1
        app.created_at = now_iso()
        app.updated_at = app.created_at
        self.applications.insert(0, app)
        self.log("ADD", app.summary())
        return app

    def update(self, app_id: int, changes: dict) -> Application | None:
        app = self.get(app_id)
        if app is None:
            return None
        for key, value in changes.items():
            if not hasattr(app, key):
                continue
            old = getattr(app, key)
            if old == value:
                continue
            setattr(app, key, value)
            self.log("EDIT", f"#{app.id:03d} | {key}: {old!r} -> {value!r}")
        app.updated_at = now_iso()
        return app

    def delete(self, app_id: int) -> bool:
        app = self.get(app_id)
        if app is None:
            return False
        self.applications.remove(app)
        self.log("DELETE", app.summary())
        return True

    def load_many(self, apps: Iterable[Application], *, log: bool = True) -> int:
        count = 0
        for app in apps:
            app.id = self._next_id
            self._next_id += 1
            if not app.created_at:
                app.created_at = now_iso()
            if not app.updated_at:
                app.updated_at = app.created_at
            self.applications.append(app)
            count += 1
        if log:
            self.log("IMPORT", f"{count} application(s) loaded into memory")
        return count

    def log(self, action: str, detail: str) -> None:
        self.activity.append(ActivityEntry(now_iso(), action, detail))

    def activity_lines(self) -> list[str]:
        return [entry.to_line() for entry in self.activity]

    def clear(self) -> None:
        self.applications.clear()
        self.activity.clear()
        self._next_id = 1
