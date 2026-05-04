"""Polls Windows for the number of connected monitors."""

from __future__ import annotations

import subprocess

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# PowerShell one-liner that returns just an integer - the count of connected
# monitors - and nothing else. Much nicer than parsing the full object dump
# with a regex like the old code did.
_COUNT_QUERY = (
    "(Get-CimInstance -Namespace root\\wmi "
    "-ClassName WmiMonitorBasicDisplayParams "
    "| Measure-Object).Count"
)


class MonitorDetector:
    """Counts connected monitors via WMI.

    We poll because WM_DISPLAYCHANGE doesn't fire reliably when switching
    to clone mode (resolution doesn't necessarily change). Yes, polling is
    crude. Yes, it works.
    """

    def __init__(self) -> None:
        self._last_known_count: int = 0

    def count(self) -> int:
        """Return the number of connected monitors.

        If the query fails, returns the last successful count instead
        of raising. First-ever failure returns 0.
        """
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", _COUNT_QUERY],
                capture_output=True,
                text=True,
                check=True,
                creationflags=_CREATE_NO_WINDOW,
            )
            count = int(result.stdout.strip())
            self._last_known_count = count
            return count
        except (subprocess.CalledProcessError, ValueError, OSError):
            # If PowerShell itself errors, or returns something that isn't a
            # number, keep calm and carry on. The next poll will likely work.
            return self._last_known_count