"""Generate app.ico from the tray icon rendering logic.

Run this manually when the icon design changes. The output is committed to
the repo so builds don't depend on running this script every time.

Windows .ico files can contain multiple resolutions. We include the sizes
Windows actually uses: 16 (tray/titlebar), 32 (taskbar), 48 (alt-tab),
256 (Explorer large icons). Modern Windows picks the best fit automatically.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ACCENT_BLUE = "#0A84FF"
DEEP_PURPLE = "#2B0A3D"


def _draw_extend_icon(size: int) -> Image.Image:
    """Render the 'Extend' tray icon at an arbitrary size.

    Extend is the most recognizable mode (two filled rectangles) so we use it
    as the app icon. The tray icon switches dynamically at runtime; this is
    just the installer/exe/shortcut icon.
    """
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # Transparent bg
    dc = ImageDraw.Draw(image)

    # Scale the original 64x64 coordinates up to the requested size
    scale = size / 64
    top_rect = tuple(int(v * scale) for v in (4, 4, 60, 32))
    bottom_rect = tuple(int(v * scale) for v in (10, 36, 54, 60))

    dc.rectangle(top_rect, fill=ACCENT_BLUE)
    dc.rectangle(bottom_rect, fill=ACCENT_BLUE)
    return image


def main() -> None:
    sizes = [16, 32, 48, 256]
    images = [_draw_extend_icon(s) for s in sizes]

    output_dir = Path(__file__).parent.parent / "src" / "monitor_monitor" / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "app.ico"

    images[-1].save(output_path, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Wrote {output_path} with sizes {sizes}")


if __name__ == "__main__":
    main()