"""Smoke test for detector and display switcher.

Run from repo root with:
    python scripts/test_core.py

This is a developer sanity check, not a real test suite.
"""

from __future__ import annotations

import sys
import time

from monitor_monitor.constants import DisplayMode
from monitor_monitor.detector import MonitorDetector
from monitor_monitor.display import DisplaySwitcher


def main() -> int:
    print("=== Monitor Monitor core smoke test ===\n")

    detector = MonitorDetector()
    switcher = DisplaySwitcher()

    # Step 1: count monitors
    print("Counting connected monitors...")
    count = detector.count()
    print(f"  -> {count} monitor(s) detected\n")

    if count == 0:
        print("WARNING: Detector returned 0. Either PowerShell failed or")
        print("something is genuinely weird about this machine.\n")

    # Step 2: parse a CLI value
    print("Parsing CLI value 'extend'...")
    mode = DisplayMode.from_cli("extend")
    print(f"  -> {mode} (flag={mode.flag}, label={mode.label!r})\n")

    # Step 3: ask before actually switching, because this changes the user's display
    answer = input("Switch display to EXTEND mode now? [y/N]: ").strip().lower()
    if answer == "y":
        print("Switching...")
        switcher.switch(DisplayMode.EXTEND)
        print("  -> switch command sent. Check your screens.")
    else:
        print("Skipped the actual switch.")

    # Step 4: poll a couple times to make sure the detector is stable
    print("\nPolling detector 3 times (1s apart)...")
    for i in range(3):
        time.sleep(1)
        print(f"  tick {i + 1}: {detector.count()} monitor(s)")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())