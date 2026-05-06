"""Build the Windows executable via PyInstaller.

Cleans previous build artifacts first so you don't get stale bundles.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).parent.parent

    # PyInstaller leaves these behind - nuke them for a clean build
    for directory in ("build", "dist"):
        path = project_root / directory
        if path.exists():
            print(f"Removing {path}")
            shutil.rmtree(path)

    spec = project_root / "monitor_monitor.spec"
    if not spec.exists():
        print(f"Missing spec file: {spec}", file=sys.stderr)
        sys.exit(1)

    print("Running PyInstaller...")
    result = subprocess.run(
        ["pyinstaller", "--clean", str(spec)],
        cwd=project_root,
        check=False,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)

    exe_path = project_root / "dist" / "MonitorMonitor.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\nSuccess: {exe_path} ({size_mb:.1f} MB)")
    else:
        print("Build finished but executable not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()