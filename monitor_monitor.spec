# PyInstaller spec file for Monitor Monitor.
#
# Run via: pyinstaller monitor_monitor.spec
# Or use: python scripts/build.py

from pathlib import Path

project_root = Path(SPECPATH)
src_root = project_root / "src" / "monitor_monitor"

block_cipher = None

a = Analysis(
    [str(src_root / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        # (source, destination_inside_bundle)
        # Keep the package layout intact so importlib.resources works
        (str(src_root / "assets" / "theme.json"), "monitor_monitor/assets"),
        (str(src_root / "assets" / "app.ico"), "monitor_monitor/assets"),
    ],
    hiddenimports=[
        # customtkinter sometimes needs help - belt and suspenders
        "customtkinter",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Things we definitely don't need - keeps the binary smaller
        "matplotlib",
        "numpy",
        "pytest",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="monitor-monitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX compression triggers AV false positives - not worth it
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # --windowed equivalent
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_root / "assets" / "app.ico"),
    version=str(project_root / "version_info.txt"),
)