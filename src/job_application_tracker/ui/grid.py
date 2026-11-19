"""The 9-column editable grid: one input row plus the current page of records."""

from __future__ import annotations

import webbrowser
from typing import Callable

import customtkinter as ctk

from ..config import CUSTOM_STATUS_OPTION, Config
from ..models import Application, normalize_date
from . import dialogs

HEADERS = [
    "Number", "Company Name", "Position", "Requirements", "Link",
    "Status", "Credential", "Application date", "Important notes",
]
WIDTHS = [62, 145, 145, 128, 150, 140, 125, 145, 185]


class ApplicationGrid(ctk.CTkFrame):
    def __init__(self, master, config: Config, callbacks: dict[str, Callable]):
        super().__init__(master, fg_color="transparent")
        self.config_obj = config
        self.cb = callbacks
        self._input_requirements: list[str] = []
        self._data_rows: list[dict] = []
        self._populating = False

        for column, weight in enumerate(WIDTHS):
            self.grid_columnconfigure(column, minsize=weight)

        self._build_header()
        self._input_row = self._create_row(row=1, display="NEW", app=None, is_input=True)
        self._input_row["number_btn"].configure(
            text="+", fg_color="#2E7D4F", hover_color="#25663F",
            command=self._submit_input,
        )

    # --------------------------------------------------------------- helpers
    def _build_header(self) -> None:
        for column, title in enumerate(HEADERS):
            ctk.CTkLabel(
                self, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).grid(row=0, column=column, padx=3, pady=(4, 8), sticky="w")

    def _entry(self, row: int, column: int, width: int, placeholder: str = "") -> ctk.CTkEntry:
        widget = ctk.CTkEntry(self, width=width, placeholder_text=placeholder)
        widget.grid(row=row, column=column, padx=2, pady=2, sticky="w")
        return widget

    def _cell(self, row: int, column: int) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=column, padx=2, pady=2, sticky="w")
        return frame

    def _status_values(self) -> list[str]:
        return self.config_obj.statuses + [CUSTOM_STATUS_OPTION]

    def _create_row(self, row: int, display: str, app: Application | None,
                    is_input: bool) -> dict:
        widgets: dict = {"app": app, "all": [], "is_input": is_input}
        app_id = None if app is None else app.id

        def track(widget):
            widgets["all"].append(widget)
            return widget

        # Number
        number_cell = self._cell(row, 0)
        widgets["all"].append(number_cell)
        widgets["number_label"] = track(ctk.CTkLabel(
            number_cell, text=display, width=28, anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
        ))
        widgets["number_label"].pack(side="left")
        widgets["number_btn"] = track(ctk.CTkButton(
            number_cell, text="x", width=26, height=24,
            fg_color="#B44444", hover_color="#8E3333" if not is_input else "#2E7D4F",
            font=ctk.CTkFont(size=12),
        ))
        widgets["number_btn"].pack(side="left", padx=(2, 0))

        # Text fields
        widgets["company"] = track(self._entry(row, 1, WIDTHS[1] - 8, "Company"))
        widgets["position"] = track(self._entry(row, 2, WIDTHS[2] - 8, "Position"))

        # Requirements button
        widgets["requirements"] = (
            list(self._input_requirements) if is_input else list(app.requirements)
        )
        widgets["requirements_btn"] = track(ctk.CTkButton(
            self, width=WIDTHS[3] - 8, height=28, anchor="w",
            text=self._requirements_text(widgets["requirements"]),
            command=lambda: self._open_requirements(widgets),
        ))
        widgets["requirements_btn"].grid(row=row, column=3, padx=2, pady=2, sticky="w")

        # Link + open button
        link_cell = self._cell(row, 4)
        widgets["all"].append(link_cell)
        widgets["link"] = track(ctk.CTkEntry(
            link_cell, width=WIDTHS[4] - 42, placeholder_text="https://..."
        ))
        widgets["link"].pack(side="left")
        widgets["open_btn"] = track(ctk.CTkButton(
            link_cell, text="open", width=38, height=24,
            command=lambda: self._open_link(widgets["link"].get()),
        ))
        widgets["open_btn"].pack(side="left", padx=(3, 0))

        # Status combobox
        widgets["status"] = track(ctk.CTkComboBox(
            self, width=WIDTHS[5] - 8, values=self._status_values(),
            command=lambda value: self._on_status(widgets, value),
        ))
        widgets["status"].grid(row=row, column=5, padx=2, pady=2, sticky="w")

        # Credential
        widgets["credential"] = track(self._entry(row, 6, WIDTHS[6] - 8, "Credential"))

        # Date + Today button
        date_cell = self._cell(row, 7)
        widgets["all"].append(date_cell)
        widgets["date"] = track(ctk.CTkEntry(
            date_cell, width=WIDTHS[7] - 46, placeholder_text="YYYY-MM-DD"
        ))
        widgets["date"].pack(side="left")
        widgets["today_btn"] = track(ctk.CTkButton(
            date_cell, text="today", width=40, height=24,
            command=lambda: self._set_today(widgets),
        ))
        widgets["today_btn"].pack(side="left", padx=(3, 0))

        # Notes + expand button
        notes_cell = self._cell(row, 8)
        widgets["all"].append(notes_cell)
        widgets["notes"] = track(ctk.CTkEntry(
            notes_cell, width=WIDTHS[8] - 40, placeholder_text="Notes"
        ))
        widgets["notes"].pack(side="left")
        widgets["notes_btn"] = track(ctk.CTkButton(
            notes_cell, text="...", width=30, height=24,
            command=lambda: self._open_notes(widgets),
        ))
        widgets["notes_btn"].pack(side="left", padx=(3, 0))

        # Bind text-field commits
        bindings = [
            ("company", "company"), ("position", "position"), ("link", "link"),
            ("credential", "credential"), ("date", "application_date"),
            ("notes", "notes"),
        ]
        for key, field in bindings:
            widget = widgets[key]
            handler = lambda _event, w=widget, f=field, item=widgets: self._commit_field(w, f, item)
            widget.bind("<FocusOut>", handler)
            widget.bind("<Return>", handler)

        if not is_input and app is not None:
            self._populate_row(widgets, app)
        elif is_input:
            widgets["status"].set("Pending")
            widgets["status_value"] = "Pending"

        return widgets

    @staticmethod
    def _requirements_text(items: list[str]) -> str:
        return f"Requirements ({len(items)})" if items else "Requirements"

    def _populate_row(self, widgets: dict, app: Application) -> None:
        self._populating = True
        try:
            for key, value in (
                ("company", app.company), ("position", app.position), ("link", app.link),
                ("credential", app.credential), ("date", app.application_date),
                ("notes", app.notes.replace("\n", " ")),
            ):
                widgets[key].delete(0, "end")
                if value:
                    widgets[key].insert(0, value)
            widgets["status"].configure(values=self._status_values())
            widgets["status"].set(app.status or "Pending")
            widgets["status_value"] = app.status or "Pending"
            widgets["requirements"] = list(app.requirements)
            widgets["requirements_btn"].configure(text=self._requirements_text(app.requirements))
        finally:
            self._populating = False

    # -------------------------------------------------------------- actions
    def _commit_field(self, widget, field: str, widgets: dict) -> None:
        if self._populating:
            return
        value = widget.get().strip()
        if field == "application_date" and value:
            normalized = normalize_date(value)
            if not normalized:
                dialogs.show_error(
                    "Invalid date", "Use YYYY-MM-DD (e.g. 2026-11-19).", self
                )
                widget.delete(0, "end")
                return
            if normalized != value:
                widget.delete(0, "end")
                widget.insert(0, normalized)
                value = normalized
        if widgets["is_input"]:
            return
        app = widgets.get("app")
        if app is None:
            return
        if field == "notes" and value == app.notes.replace("\n", " "):
            return  # multi-line note already saved through the notes dialog
        if field == "status":
            widgets["status_value"] = value
        self.cb["update"](app.id, {field: value})

    def _on_status(self, widgets: dict, value: str) -> None:
        if self._populating:
            return
        if value == CUSTOM_STATUS_OPTION:
            widgets["status"].set(widgets.get("status_value", "Pending"))
            app_id = widgets["app"].id if widgets.get("app") is not None else None
            self.cb["custom_status"](widgets["status"], app_id)
            return
        widgets["status_value"] = value
        if not widgets["is_input"] and widgets.get("app") is not None:
            self.cb["update"](widgets["app"].id, {"status": value})

    def _set_today(self, widgets: dict) -> None:
        from ..models import today_str
        widgets["date"].delete(0, "end")
        widgets["date"].insert(0, today_str())
        self._commit_field(widgets["date"], "application_date", widgets)

    def _open_link(self, url: str) -> None:
        url = url.strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
        except Exception as exc:  # noqa: BLE001
            dialogs.show_error("Could not open link", str(exc), self)

    def _open_requirements(self, widgets: dict) -> None:
        label = widgets["app"].company if widgets.get("app") else "new application"

        def save(items: list[str]) -> None:
            widgets["requirements"] = list(items)
            if widgets["is_input"]:
                self._input_requirements[:] = items
            widgets["requirements_btn"].configure(text=self._requirements_text(items))
            if not widgets["is_input"] and widgets.get("app") is not None:
                self.cb["update"](widgets["app"].id, {"requirements": items})

        dialogs.RequirementsDialog(
            self, f"Requirements - {label}", widgets["requirements"], save
        )

    def _open_notes(self, widgets: dict) -> None:
        current = widgets["notes"].get().strip()
        if not widgets["is_input"] and widgets.get("app") is not None:
            current = widgets["app"].notes

        def save(text: str) -> None:
            widgets["notes"].delete(0, "end")
            widgets["notes"].insert(0, text.replace("\n", " "))
            if not widgets["is_input"] and widgets.get("app") is not None:
                self.cb["update"](widgets["app"].id, {"notes": text})

        dialogs.NotesDialog(self, "Important notes", current, save)

    # ---------------------------------------------------------------- public
    def get_input_fields(self) -> dict:
        return {
            "company": self._input_row["company"].get().strip(),
            "position": self._input_row["position"].get().strip(),
            "requirements": list(self._input_requirements),
            "link": self._input_row["link"].get().strip(),
            "status": self._input_row["status"].get().strip() or "Pending",
            "credential": self._input_row["credential"].get().strip(),
            "application_date": self._input_row["date"].get().strip(),
            "notes": self._input_row["notes"].get().strip(),
        }

    def _submit_input(self) -> None:
        fields = self.get_input_fields()
        if not fields["company"] and not fields["position"]:
            dialogs.show_warning("Empty row", "Enter at least a company or position.", self)
            return
        self.cb["add"](fields)
        self.clear_input()

    def clear_input(self) -> None:
        self._input_requirements.clear()
        for key in ("company", "position", "link", "credential", "date", "notes"):
            self._input_row[key].delete(0, "end")
        self._input_row["status"].set("Pending")
        self._input_row["status_value"] = "Pending"
        self._input_row["requirements_btn"].configure(text="Requirements")

    def focus_input(self) -> None:
        self._input_row["company"].focus_set()

    def submit(self) -> None:
        self._submit_input()

    def render(self, applications: list[Application]) -> None:
        for widgets in self._data_rows:
            for widget in widgets["all"]:
                widget.destroy()
        self._data_rows.clear()

        for index, app in enumerate(applications):
            row = self._create_row(row=2 + index, display=str(index + 1), app=app, is_input=False)
            row["number_btn"].configure(command=lambda app_id=app.id: self.cb["delete"](app_id))
            self._data_rows.append(row)

        if not applications:
            ctk.CTkLabel(
                self, text="No applications yet. Fill row 1 and press + to add one.",
                text_color="gray60", anchor="w",
            ).grid(row=2, column=1, columnspan=6, sticky="w", pady=6)
