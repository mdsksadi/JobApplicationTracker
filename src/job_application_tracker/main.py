"""Command-line entry point for JobApplicationTracker."""

from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="job-application-tracker",
        description="Track job applications with weekly goals and on-demand export.",
    )
    parser.add_argument("--version", action="version", version=f"job-application-tracker {__version__}")
    return parser


def main() -> None:
    build_parser().parse_args()
    import customtkinter as ctk

    from .ui.main_window import App

    ctk.set_default_color_theme("blue")
    application = App()
    application.mainloop()


if __name__ == "__main__":
    main()
