"""Modal dialogs used by the main window."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk
from tkinter import filedialog, messagebox

from .. import exporter, license as license_module
from ..config import Config, DEFAULT_STATUSES

PAD = 12


class Dialog(ctk.CTkToplevel):
    """Base class giving every dialog modal behaviour and centering."""

    def __init__(self, master, title: str, width: int = 440, height: int = 320):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color=("#F9F9F9", "#1E1E1E"))
        self._center(width, height)
        self.grab_set()
        self.after(120, self.focus_force)
        self.bind("<Escape>", lambda _event: self.destroy())

    def _center(self, width: int, height: int) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def buttons(self, save_text: str = "Save", on_save: Callable | None = None,
                on_cancel: Callable | None = None) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=PAD, pady=(4, PAD))
        ctk.CTkButton(
            frame, text="Cancel",
            command=on_cancel if on_cancel is not None else self.destroy,
            width=90,
        ).pack(side="right")
        if on_save is not None:
            ctk.CTkButton(frame, text=save_text, command=on_save, width=110).pack(
                side="right", padx=(0, 8)
            )
        return frame


class RequirementsDialog(Dialog):
    """Space-saving editor for a row's requirement list."""

    def __init__(self, master, title: str, requirements: list[str],
                 on_save: Callable[[list[str]], None]):
        super().__init__(master, title, width=480, height=440)
        self._items = [str(item) for item in requirements if str(item).strip()]
        self._on_save = on_save

        ctk.CTkLabel(
            self, text="Requirements for this application", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=PAD, pady=(PAD, 6))

        self._list = ctk.CTkScrollableFrame(self, label_text="Current requirements", height=210)
        self._list.pack(fill="both", expand=True, padx=PAD)

        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=PAD, pady=8)
        self._entry = ctk.CTkEntry(add_frame, placeholder_text="e.g. Python, 3+ years Django")
        self._entry.pack(side="left", fill="x", expand=True)
        self._entry.bind("<Return>", lambda _e: self._add())
        ctk.CTkButton(add_frame, text="Add", width=70, command=self._add).pack(side="left", padx=(8, 0))
        self.buttons("Save requirements", self._save)
        self._render()

    def _render(self) -> None:
        for widget in self._list.winfo_children():
            widget.destroy()
        if not self._items:
            ctk.CTkLabel(
                self._list, text="No requirements added yet.", text_color="gray60"
            ).pack(pady=18)
            return
        for index, item in enumerate(self._items):
            row = ctk.CTkFrame(self._list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{index + 1}.", width=28, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=item, anchor="w", justify="left").pack(
                side="left", fill="x", expand=True
            )
            ctk.CTkButton(
                row, text="x", width=28, height=24, fg_color="#B44444",
                hover_color="#8E3333", command=lambda i=index: self._remove(i),
            ).pack(side="right")

    def _add(self) -> None:
        value = self._entry.get().strip()
        if not value:
            return
        self._items.append(value)
        self._entry.delete(0, "end")
        self._render()

    def _remove(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self._items.pop(index)
            self._render()

    def _save(self) -> None:
        self._on_save([item for item in self._items if item.strip()])
        self.destroy()


class CustomStatusDialog(Dialog):
    def __init__(self, master, on_save: Callable[[str], None]):
        super().__init__(master, "Add custom status", width=400, height=210)
        self._on_save = on_save
        ctk.CTkLabel(self, text="Status name (e.g. 3rd Interview)", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=PAD, pady=(PAD, 8)
        )
        self._entry = ctk.CTkEntry(self, width=340)
        self._entry.pack(padx=PAD)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda _e: self._save())
        self.buttons("Add status", self._save)

    def _save(self) -> None:
        value = self._entry.get().strip()
        if not value:
            messagebox.showwarning("empty", "Status cannot be empty.", parent=self)
            return
        if value in DEFAULT_STATUSES:
            self._on_save(value)
            self.destroy()
            return
        self._on_save(value)
        self.destroy()


class NotesDialog(Dialog):
    def __init__(self, master, title: str, text: str, on_save: Callable[[str], None]):
        super().__init__(master, title, width=520, height=360)
        self._on_save = on_save
        ctk.CTkLabel(self, text="Important notes", font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=PAD, pady=(PAD, 8)
        )
        self._text = ctk.CTkTextbox(self, wrap="word", height=230)
        self._text.pack(fill="both", expand=True, padx=PAD)
        self._text.insert("1.0", text or "")
        self.buttons("Save notes", self._save)

    def _save(self) -> None:
        self._on_save(self._text.get("1.0", "end-1c"))
        self.destroy()


class SettingsDialog(Dialog):
    def __init__(self, master, config: Config, on_save: Callable[[int, int, str], None]):
        super().__init__(master, "Settings", width=420, height=350)
        self._config = config
        self._on_save = on_save
        self.bind("<Escape>", lambda _event: self._cancel())

        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=17, weight="bold")).pack(
            anchor="w", padx=PAD, pady=(PAD, 14)
        )

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=PAD, pady=6)
        ctk.CTkLabel(row1, text="Applications per week", width=170, anchor="w").pack(side="left")
        self._target = ctk.CTkEntry(row1, width=90)
        self._target.insert(0, str(config.weekly_target))
        self._target.pack(side="left")

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=PAD, pady=6)
        ctk.CTkLabel(row2, text="Rows per page", width=170, anchor="w").pack(side="left")
        self._page = ctk.CTkEntry(row2, width=90)
        self._page.insert(0, str(config.page_size))
        self._page.pack(side="left")

        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=PAD, pady=6)
        ctk.CTkLabel(row3, text="Appearance", width=170, anchor="w").pack(side="left")
        self._theme = ctk.CTkOptionMenu(
            row3, values=["system", "light", "dark"], width=120, command=self._preview_theme
        )
        self._theme.set(config.theme)
        self._theme.pack(side="left")

        ctk.CTkLabel(
            self,
            text="The weekly target sets the background colour:\n"
                 "red below target, white at target, green above.",
            justify="left", text_color="gray60", font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=PAD, pady=14)
        self.buttons("Save settings", self._save, on_cancel=self._cancel)

    def _preview_theme(self, choice: str) -> None:
        ctk.set_appearance_mode(choice)

    def _cancel(self) -> None:
        ctk.set_appearance_mode(self._config.theme)
        self.destroy()

    def _save(self) -> None:
        try:
            target = int(self._target.get().strip())
            page = int(self._page.get().strip())
        except ValueError:
            messagebox.showerror("Invalid number", "Target and page size must be whole numbers.", parent=self)
            return
        if target < 1 or page < 1 or page > 100:
            messagebox.showerror("Out of range", "Target must be >= 1 and rows per page 1-100.", parent=self)
            return
        self._on_save(target, page, self._theme.get())
        self.destroy()


class ActivationDialog(Dialog):
    def __init__(self, master, config: Config, on_success: Callable[[str], None]):
        super().__init__(master, "Remove watermark - Sadi App", width=480, height=270)
        self._config = config
        self._on_success = on_success
        ctk.CTkLabel(
            self, text="Enter your license code", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=PAD, pady=(PAD, 6))
        ctk.CTkLabel(
            self, text="The code starts with JAT1. and was issued to you by the developer.",
            text_color="gray60", font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=PAD)
        self._entry = ctk.CTkEntry(self, width=430, placeholder_text="JAT1.eyJhcHAi...")
        self._entry.pack(padx=PAD, pady=12)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda _e: self._verify())
        self._status = ctk.CTkLabel(self, text="", text_color="#C44B4B", wraplength=430)
        self._status.pack(anchor="w", padx=PAD)
        self.buttons("Activate", self._verify)

    def _verify(self) -> None:
        valid, message = license_module.verify_code(self._entry.get())
        if not valid:
            self._status.configure(text=message)
            return
        self._on_success(message)
        self.destroy()


class ExportDialog(Dialog):
    def __init__(self, master, config: Config, store, on_done: Callable[[Path], None]):
        super().__init__(master, "Export applications", width=500, height=290)
        self._config = config
        self._store = store
        self._on_done = on_done
        self._format = ctk.StringVar(value="csv")

        ctk.CTkLabel(self, text="Choose export format", font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=PAD, pady=(PAD, 8)
        )
        formats = ctk.CTkFrame(self, fg_color="transparent")
        formats.pack(fill="x", padx=PAD)
        for key, label in exporter.FORMAT_LABELS.items():
            ctk.CTkRadioButton(
                formats, text=label, variable=self._format, value=key
            ).pack(anchor="w", pady=2)

        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.pack(fill="x", padx=PAD, pady=10)
        self._path = ctk.CTkEntry(path_frame, placeholder_text="Choose a file path")
        self._path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_frame, text="Browse", width=80, command=self._browse).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            self, text="No file is written until you press Export.", text_color="gray60",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=PAD)
        self.buttons("Export", self._export)

    def _browse(self) -> None:
        fmt = self._format.get()
        initial = self._config.last_export_dir or None
        path = filedialog.asksaveasfilename(
            parent=self, title="Save export as", initialdir=initial,
            filetypes=[exporter.filetypes()[list(exporter.FORMAT_LABELS).index(fmt)]],
            defaultextension=exporter.EXTENSIONS[fmt],
        )
        if path:
            self._path.delete(0, "end")
            self._path.insert(0, path)

    def _export(self) -> None:
        raw = self._path.get().strip()
        if not raw:
            messagebox.showwarning("No path", "Choose where to save the export.", parent=self)
            return
        fmt = self._format.get()
        try:
            target = exporter.export(self._store, fmt, raw)
        except RuntimeError as exc:
            messagebox.showerror("Missing dependency", str(exc), parent=self)
            return
        except (OSError, ValueError) as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)
            return
        self._config.last_export_dir = str(target.parent)
        self._config.save()
        self._on_done(target)
        self.destroy()


def show_info(title: str, message: str, master=None) -> None:
    messagebox.showinfo(title, message, parent=master)


def show_error(title: str, message: str, master=None) -> None:
    messagebox.showerror(title, message, parent=master)


def show_warning(title: str, message: str, master=None) -> None:
    messagebox.showwarning(title, message, parent=master)


def ask_yes_no(title: str, message: str, master=None) -> bool:
    return messagebox.askyesno(title, message, parent=master)


def ask_export_on_close(master=None) -> bool | None:
    """True = export first, False = discard, None = cancel closing."""
    return messagebox.askyesnocancel(
        "Unsaved session",
        "You have applications in memory that have not been exported.\n\n"
        "Export before quitting? (Choosing 'No' discards them permanently.)",
        parent=master,
    )
