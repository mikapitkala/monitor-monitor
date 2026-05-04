"""Entry point for `python -m monitor_monitor`."""

from __future__ import annotations

import argparse

import customtkinter as ctk

from monitor_monitor.app import MonitorWatcherApp
from monitor_monitor.constants import CLI_MODE_CHOICES, DisplayMode


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="monitor-monitor",
        description="Auto-apply your preferred Windows display mode when monitors change",
    )
    parser.add_argument(
        "mode",
        choices=CLI_MODE_CHOICES,
        default="extend",
        nargs="?",
        help=(
            "'1' or 'internal' for Internal only, "
            "'2' or 'clone' for Clone, "
            "'3' or 'extend' for Extend (default), "
            "'4' or 'external' for External only"
        ),
    )
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Start minimized to the system tray",
    )
    return parser.parse_args()


def main() -> None:
    """Run the Monitor Monitor application."""
    args = _parse_args()
    initial_mode = DisplayMode.from_cli(args.mode)

    root = ctk.CTk()
    app = MonitorWatcherApp(root, initial_mode=initial_mode)

    if args.minimized:
        app.root.withdraw()

    root.mainloop()


if __name__ == "__main__":
    main()