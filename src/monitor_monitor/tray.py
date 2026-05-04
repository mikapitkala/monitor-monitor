"""System tray icon and menu.

Runs pystray on its own thread. Callbacks marshal back to the main thread
via the owning app.
"""

from __future__ import annotations

from threading import Thread
from typing import Callable

import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw

from monitor_monitor.constants import ACCENT_BLUE, COOL_GREY, DEEP_PURPLE, DisplayMode


def _build_icon_image(mode: DisplayMode) -> Image.Image:
    """Draw a 64x64 tray icon depicting the current mode.

    Two stacked rectangles represent the two display targets. Filled = active,
    outlined = inactive. Matches the original app's visual language.
    """
    bg = DEEP_PURPLE if ctk.get_appearance_mode() == "Dark" else COOL_GREY
    image = Image.new("RGB", (64, 64), bg)
    dc = ImageDraw.Draw(image)

    top_rect = (4, 4, 60, 32)
    bottom_rect = (10, 36, 54, 60)

    if mode == DisplayMode.INTERNAL:
        # Top outlined (external off), bottom filled (internal on)
        dc.rectangle(top_rect, outline=ACCENT_BLUE)
        dc.rectangle(bottom_rect, fill=ACCENT_BLUE)
    elif mode == DisplayMode.CLONE:
        # Both filled, overlapping - same content
        dc.rectangle((4, 4, 60, 60), outline=ACCENT_BLUE)
        dc.rectangle((8, 8, 52, 52), fill=ACCENT_BLUE)
    elif mode == DisplayMode.EXTEND:
        # Both filled - independent displays
        dc.rectangle(top_rect, fill=ACCENT_BLUE)
        dc.rectangle(bottom_rect, fill=ACCENT_BLUE)
    elif mode == DisplayMode.EXTERNAL:
        # Top filled (external on), bottom outlined (internal off)
        dc.rectangle(top_rect, fill=ACCENT_BLUE)
        dc.rectangle(bottom_rect, outline=ACCENT_BLUE)

    return image


class TrayManager:
    """Owns the pystray icon and menu. Talks to the app via callbacks."""

    def __init__(
        self,
        on_mode_selected: Callable[[DisplayMode], None],
        on_restore: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._on_mode_selected = on_mode_selected
        self._on_restore = on_restore
        self._on_quit = on_quit

        self._current_mode: DisplayMode = DisplayMode.EXTEND
        self._icon = pystray.Icon("Monitor Monitor")
        self._icon.icon = _build_icon_image(self._current_mode)
        self._icon.menu = self._build_menu()

    def start(self) -> None:
        Thread(target=self._icon.run, daemon=True).start()

    def stop(self) -> None:
        self._icon.stop()

    def set_mode(self, mode: DisplayMode) -> None:
        """Called by the app when the mode changes. Updates both icon and menu."""
        self._current_mode = mode
        self._icon.icon = _build_icon_image(mode)
        self._icon.menu = self._build_menu()
        self._icon.update_menu()

    def _build_menu(self) -> pystray.Menu:
        def make_mode_handler(mode: DisplayMode):
            # Closure captures `mode` at definition time. pystray calls
            # this with no arguments, matching the original's signature.
            return lambda: self._on_mode_selected(mode)

        def mode_item(mode: DisplayMode) -> pystray.MenuItem:
            prefix = " ✔ " if mode == self._current_mode else "     "
            return pystray.MenuItem(prefix + mode.label, make_mode_handler(mode))

        return pystray.Menu(
            mode_item(DisplayMode.INTERNAL),
            mode_item(DisplayMode.CLONE),
            mode_item(DisplayMode.EXTEND),
            mode_item(DisplayMode.EXTERNAL),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Restore", self._on_restore, default=True),
            pystray.MenuItem("Close", self._on_quit),
        )

        return pystray.Menu(
            mode_item(DisplayMode.INTERNAL),
            mode_item(DisplayMode.CLONE),
            mode_item(DisplayMode.EXTEND),
            mode_item(DisplayMode.EXTERNAL),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Restore",
                lambda _icon, _item: self._on_restore(),
                default=True,
            ),
            pystray.MenuItem("Close", lambda _icon, _item: self._on_quit()),
        )