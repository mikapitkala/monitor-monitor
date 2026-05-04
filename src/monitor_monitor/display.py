"""Wraps DisplaySwitch.exe so we don't flash a console window every time."""

from __future__ import annotations

import subprocess
from typing import Protocol

from monitor_monitor.constants import DisplayMode


# CREATE_NO_WINDOW is a Windows-only subprocess flag that suppresses the console
# window that would otherwise flash up. Falls back to 0 (no-op) on other platforms
# so the code is at least importable, though the app only runs on Windows.
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class DisplaySwitcher:
    """Invokes DisplaySwitch.exe with a chosen mode."""

    def switch(self, mode: DisplayMode) -> None:
        """Switch Windows to the given display mode.

        Silently no-ops if DisplaySwitch.exe fails - the detector will
        try again on the next tick.
        """
        try:
            subprocess.run(
                ["DisplaySwitch.exe", mode.flag],
                check=True,
                creationflags=_CREATE_NO_WINDOW,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # DisplaySwitch.exe is part of Windows; if it's missing or fails,
            # there's not much we can do at runtime. Swallow and move on.
            pass


class SupportsSwitch(Protocol):
    """Structural type for anything that can switch display modes.

    Lets us swap in a fake during tests or a no-op during dry runs.
    """

    def switch(self, mode: DisplayMode) -> None: ...