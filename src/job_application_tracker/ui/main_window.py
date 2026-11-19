"""Main application window."""

from __future__ import annotations

import math
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog

from .. import exporter
from ..config import CUSTOM_STATUS_OPTION, Config
from ..models import Application
from ..store import ApplicationStore
from ..weekly import background_color, count_for_week, progress_label
from . import dialogs
from .grid import ApplicationGrid


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.config_obj = Config.load()
        self.store = ApplicationStore()
        ctk.set_appearance_mode(self.config_obj.theme)

        self.title("Job Application Tracker")
        self.geometry("1500x880")
        self.minsize(1350, 640)
        self._center_window()
        self.page = 1
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._refresh()
        self.after(150, self.grid_widget.focus_input)

    # ---------------------------------------------------------------- layout
    def _center_window(self) -> None:
        self.update_idletasks()
        width, height = 1500, 880
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(
            top, text="Job Application Tracker", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")
        self.weekly_label = ctk.CTkLabel(
            top, text="", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.weekly_label.pack(side="left", padx=18)

        buttons = [
            ("Add", self._add_from_toolbar, "#2E7D4F"),
            ("Export", self._export, None),
            ("Import", self._import, None),
            ("Log", self._view_log, None),
            ("Settings", self._settings, None),
        ]
        for text, command, color in buttons:
            ctk.CTkButton(
                top, text=text, width=74, command=command,
                fg_color=color, hover_color="#25663F" if color else None,
            ).pack(side="right", padx=3)

        self.activate_button = ctk.CTkButton(
            top, text="Activate", width=84, command=self._activate
        )
        self.activate_button.pack(side="right", padx=3)

        callbacks = {
            "add": self._add,
            "update": self._update,
            "delete": self._delete,
            "custom_status": self._custom_status,
        }
        self.grid_widget = ApplicationGrid(self, self.config_obj, callbacks)
        self.grid_widget.pack(fill="both", expand=True, padx=14, pady=4)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(4, 12))
        ctk.CTkButton(bottom, text="< Previous", width=100, command=self._previous).pack(side="left")
        self.page_label = ctk.CTkLabel(bottom, text="Page 1 of 1", font=ctk.CTkFont(size=12))
        self.page_label.pack(side="left", padx=12)
        ctk.CTkButton(bottom, text="Next >", width=100, command=self._next).pack(side="left")
        self.total_label = ctk.CTkLabel(bottom, text="", text_color="gray60")
        self.total_label.pack(side="left", padx=14)
        self.unsaved_label = ctk.CTkLabel(
            bottom, text="", text_color="#9A5B00", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.unsaved_label.pack(side="right")

        self.watermark = ctk.CTkLabel(
            self, text="Sadi App", font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("gray72", "gray40"),
        )
        self.watermark.place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-8)
        self.watermark.lift()

    # --------------------------------------------------------------- refresh
    def _refresh(self) -> None:
        applications = self.store.all()
        page_size = max(1, self.config_obj.page_size)
        pages = max(1, math.ceil(len(applications) / page_size))
        self.page = min(max(1, self.page), pages)
        start = (self.page - 1) * page_size
        self.grid_widget.render(applications[start:start + page_size])

        self.page_label.configure(text=f"Page {self.page} of {pages}")
        self.total_label.configure(text=f"Total: {len(applications)} application(s)")
        self.unsaved_label.configure(
            text="Unsaved session - use Export to keep your data" if applications else ""
        )
        self.activate_button.configure(
            text=f"Licensed: {self.config_obj.licensee}" if self.config_obj.activated else "Activate"
        )
        if self.config_obj.activated:
            self.watermark.place_forget()
        else:
            self.watermark.place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-8)
            self.watermark.lift()
        self._update_status_bars()

    def _update_status_bars(self) -> None:
        count = count_for_week(self.store.all())
        target = self.config_obj.weekly_target
        self.weekly_label.configure(text=progress_label(count, target))
        dark = ctk.get_appearance_mode().lower() == "dark"
        self.configure(fg_color=background_color(count, target, dark))

    # --------------------------------------------------------------- actions
    def _add(self, fields: dict) -> None:
        self.store.add(Application(**fields))
        self.page = 1
        self._refresh()

    def _add_from_toolbar(self) -> None:
        self.grid_widget.submit()

    def _update(self, app_id: int, changes: dict) -> None:
        self.store.update(app_id, changes)
        self._update_status_bars()

    def _delete(self, app_id: int) -> None:
        app = self.store.get(app_id)
        if app is None:
            return
        if not dialogs.ask_yes_no(
            "Delete application",
            f"Delete {app.company or 'this application'} - {app.position or '(no position)'}?",
            self,
        ):
            return
        self.store.delete(app_id)
        self._refresh()

    def _custom_status(self, combo, app_id: int | None) -> None:
        def save(value: str) -> None:
            name = self.config_obj.add_custom_status(value)
            if not name:
                return
            combo.configure(values=self.config_obj.statuses + [CUSTOM_STATUS_OPTION])
            combo.set(name)
            if app_id is not None:
                self.store.update(app_id, {"status": name})

        dialogs.CustomStatusDialog(self, save)

    def _previous(self) -> None:
        if self.page > 1:
            self.page -= 1
            self._refresh()

    def _next(self) -> None:
        pages = max(1, math.ceil(len(self.store) / max(1, self.config_obj.page_size)))
        if self.page < pages:
            self.page += 1
            self._refresh()

    def _settings(self) -> None:
        def save(target: int, page_size: int, theme: str) -> None:
            self.config_obj.weekly_target = target
            self.config_obj.page_size = page_size
            self.config_obj.theme = theme
            ctk.set_appearance_mode(theme)
            self.config_obj.save()
            self.page = 1
            self._refresh()

        dialogs.SettingsDialog(self, self.config_obj, save)

    def _activate(self) -> None:
        def success(name: str) -> None:
            self.config_obj.activated = True
            self.config_obj.licensee = name
            self.config_obj.save()
            self._refresh()
            dialogs.show_info("Activated", f"Thank you, {name}! The watermark has been removed.", self)

        dialogs.ActivationDialog(self, self.config_obj, success)

    def _export(self) -> None:
        def done(path: Path) -> None:
            dialogs.show_info("Export complete", f"Saved {len(self.store)} application(s) to:\n{path}", self)

        dialogs.ExportDialog(self, self.config_obj, self.store, done)

    def _import(self) -> None:
        path = filedialog.askopenfilename(
            parent=self, title="Import applications",
            filetypes=[("JSON or CSV", "*.json *.csv"), ("JSON", "*.json"), ("CSV", "*.csv")],
            initialdir=self.config_obj.last_export_dir or None,
        )
        if not path:
            return
        try:
            suffix = Path(path).suffix.lower()
            if suffix == ".json":
                apps = exporter.applications_from_json(path)
            elif suffix == ".csv":
                apps = exporter.applications_from_csv(path)
            else:
                raise ValueError("Only .json and .csv files can be imported.")
            if not apps:
                raise ValueError("No applications found in that file.")
            self.store.load_many(apps)
            self.config_obj.last_export_dir = str(Path(path).parent)
            self.config_obj.save()
        except (OSError, ValueError) as exc:
            dialogs.show_error("Import failed", str(exc), self)
            return
        self.page = 1
        self._refresh()
        dialogs.show_info("Import complete", f"Loaded {len(apps)} application(s) into memory.", self)

    def _view_log(self) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Activity log (in memory)")
        window.geometry("760x520")
        window.transient(self)
        window.grab_set()
        ctk.CTkLabel(
            window, text="Activity log - this session only",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=14, pady=12)
        text = ctk.CTkTextbox(window, wrap="none")
        text.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        lines = self.store.activity_lines() or ["(no activity yet)"]
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

    def _on_close(self) -> None:
        if not len(self.store):
            self.destroy()
            return
        answer = dialogs.ask_export_on_close(self)
        if answer is None:
            return
        if answer is False:
            self.destroy()
            return

        def done(path: Path) -> None:
            dialogs.show_info("Export complete", f"Saved to:\n{path}", self)
            self.destroy()

        dialogs.ExportDialog(self, self.config_obj, self.store, done)
