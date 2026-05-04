"""Main application class and GUI."""

from __future__ import annotations

import datetime
from importlib.resources import files
from threading import Thread
from time import sleep

import customtkinter as ctk
from win32api import GetMonitorInfo, MonitorFromPoint

from monitor_monitor.constants import (
    ACCENT_BLUE,
    ACCENT_BLUE_HOVER,
    BORDER_WIDTH,
    BUTTON_SPACING,
    CORNER_RADIUS,
    DANGER_RED,
    DEFAULT_POLL_INTERVAL_SECONDS,
    UI_FONT_FALLBACK,
    UI_FONT_FAMILY,
    UI_FONT_SIZE,
    WHITE,
    DisplayMode,
)
from monitor_monitor.detector import MonitorDetector
from monitor_monitor.display import DisplaySwitcher
from monitor_monitor.tray import TrayManager

# Max lines shown in the in-app log before we start dropping old ones
_MAX_LOG_LINES = 4

def _load_theme() -> None:
    """Point customtkinter at our bundled theme.json.

    Uses importlib.resources so it works both in dev and when frozen
    by PyInstaller. Falls back to a built-in theme if ours is missing.
    """
    try:
        theme_path = files("monitor_monitor.assets").joinpath("theme.json")
        ctk.set_default_color_theme(str(theme_path))
    except (FileNotFoundError, ModuleNotFoundError):
        ctk.set_default_color_theme("blue")

def _timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")

def _resolve_font() -> tuple[str, int]:
    """Pick Segoe UI Variable on Windows 11, fall back to Segoe UI elsewhere.

    Tk will silently use a default font if the requested family is missing,
    which looks inconsistent. We check what's actually available.
    """
    from tkinter import font as tkfont

    available = set(tkfont.families())
    family = UI_FONT_FAMILY if UI_FONT_FAMILY in available else UI_FONT_FALLBACK
    return (family, UI_FONT_SIZE)

class MonitorWatcherApp:
    """The main app - GUI, detector thread, and tray all wired together."""

    def __init__(
        self,
        root: ctk.CTk,
        initial_mode: DisplayMode,
        poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> None:
        self.root = root
        self._poll_interval = poll_interval
        self._selected_mode: DisplayMode = initial_mode
        self._log_lines: list[str] = []

        self._detector = MonitorDetector()
        self._switcher = DisplaySwitcher()

        self._configure_window()
        self._ui_font = _resolve_font()
        self._build_ui()

        self._tray = TrayManager(
            on_mode_selected=self._on_tray_mode_selected,
            on_restore=self._on_tray_restore,
            on_quit=self._on_tray_quit,
        )
        self._tray.start()

        self.root.protocol("WM_DELETE_WINDOW", self._hide_window)
        self.root.bind("<FocusOut>", self._on_focus_out)

        # Apply the initial mode selection (updates UI + tray, no switch yet)
        self._set_mode(initial_mode, announce=True)

        self._start_detector_thread()

        self.root.after(50, self._grab_focus)

    # Window sizing & placement ------------------------------------------------

    def _configure_window(self) -> None:
        """Size the window and park it above the system tray on the primary screen."""
        ctk.set_appearance_mode("System")
        _load_theme()

        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        work_area = monitor_info.get("Work")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        taskbar_height = screen_height - work_area[3]

        # Target ~340px at standard DPI, scaling with display density.
        # Tk reports pixels, but winfo_fpixels('1i') gives us pixels-per-inch
        # so we can reason in inches (roughly DPI-independent).
        dpi = self.root.winfo_fpixels("1i")
        scale = dpi / 96.0  # 96 DPI is the Windows baseline

        app_width = int(340 * scale)
        app_height = int(340 * scale)

        # Clamp so it doesn't go absurdly small on low-DPI or huge on high-DPI
        app_width = max(300, min(app_width, 500))
        app_height = max(280, min(app_height, 440))
        work_right = work_area[2]
        work_bottom = work_area[3]
        x = work_right - app_width
        y = work_bottom - app_height

        self.root.title("Monitor Monitor")  # It monitors monitors
        self.root.geometry(f"{app_width}x{app_height}+{x}+{y}")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

    # UI construction ----------------------------------------------------------

    def _build_ui(self) -> None:
        # Log area at the top - read-only, 4 lines of recent activity
        self._text_widget = ctk.CTkTextbox(
            self.root,
            height=90,
            activate_scrollbars=False,
            corner_radius=CORNER_RADIUS,
            border_width=BORDER_WIDTH,
            font=self._ui_font,
        )
        self._text_widget.pack(pady=10, padx=10, fill=ctk.X)
        self._set_log_editable(False)

        self._button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self._button_frame.pack(pady=5, fill=ctk.X)

        # One button per mode
        self._mode_buttons: dict[DisplayMode, ctk.CTkButton] = {
            mode: self._create_mode_button(mode) for mode in DisplayMode
        }

        # Minimize to tray
        bottom_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        bottom_frame.pack(fill=ctk.X, padx=10, pady=5)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        # Minimize to tray
        self._minimize_button = ctk.CTkButton(
            bottom_frame,
            text="Minimize to Tray",
            corner_radius=CORNER_RADIUS,
            border_width=BORDER_WIDTH,
            font=self._ui_font,
            command=self._hide_window,
        )
        self._minimize_button.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self._minimize_button.bind(
            "<Enter>",
            lambda _e: self._minimize_button.configure(
                text_color=WHITE, fg_color=ACCENT_BLUE_HOVER, border_color=ACCENT_BLUE_HOVER
            ),
        )
        self._minimize_button.bind("<Leave>", lambda _e: self._restore_minimize_colors())

        # Close is visually distinct - red on hover
        self._close_button = ctk.CTkButton(
            bottom_frame,
            text="Close",
            corner_radius=CORNER_RADIUS,
            border_width=BORDER_WIDTH,
            font=self._ui_font,
            fg_color="transparent",
            text_color=[DANGER_RED, WHITE],
            border_color=DANGER_RED,
            hover_color=DANGER_RED,
            command=self._on_close,
        )
        self._close_button.grid(row=0, column=1, sticky="ew", padx=(2, 0))
        self._close_button.bind(
            "<Enter>",
            lambda _e: self._close_button.configure(
                text_color=WHITE, fg_color=DANGER_RED, border_color=DANGER_RED
            ),
        )
        self._close_button.bind("<Leave>", lambda _e: self._restore_close_colors())

    def _create_mode_button(self, mode: DisplayMode) -> ctk.CTkButton:
        # Single-click selects the mode, double-click forces a switch right now
        button = ctk.CTkButton(
            self._button_frame,
            text=mode.label,
            corner_radius=CORNER_RADIUS,
            border_width=BORDER_WIDTH,
            font=self._ui_font,
            command=lambda m=mode: self._set_mode(m, announce=True),
        )
        button.pack(side=ctk.TOP, pady=BUTTON_SPACING, padx=10, fill=ctk.X)
        button.bind("<Enter>", lambda _e, b=button: self._on_hover(b))
        button.bind("<Leave>", lambda _e, b=button, m=mode: self._on_leave(b, m))
        button.bind(
            "<Double-Button-1>",
            lambda _e, m=mode: self._force_switch(m),
        )
        return button

    # Hover behavior -----------------------------------------------------------

    def _on_hover(self, button: ctk.CTkButton) -> None:
        button.configure(text_color=WHITE, fg_color=ACCENT_BLUE_HOVER, border_color=ACCENT_BLUE_HOVER)

    def _on_leave(self, button: ctk.CTkButton, mode: DisplayMode) -> None:
        # Selected mode stays filled; everything else goes back to outlined
        if mode == self._selected_mode:
            button.configure(fg_color=ACCENT_BLUE, text_color=WHITE, border_color=ACCENT_BLUE)
        else:
            idle_color = WHITE if ctk.get_appearance_mode() == "Dark" else ACCENT_BLUE
            button.configure(fg_color="transparent", text_color=idle_color, border_color=idle_color)

    def _restore_minimize_colors(self) -> None:
        idle_color = WHITE if ctk.get_appearance_mode() == "Dark" else ACCENT_BLUE
        self._minimize_button.configure(
            text_color=idle_color, fg_color="transparent", border_color=idle_color
        )

    def _restore_close_colors(self) -> None:
        idle_color = WHITE if ctk.get_appearance_mode() == "Dark" else DANGER_RED
        self._close_button.configure(
            text_color=idle_color, fg_color="transparent", border_color=DANGER_RED
        )

    def _refresh_button_colors(self) -> None:
        """Repaint all mode buttons to match the current selection and theme.

        Called on a timer because the OS can change light/dark mode underneath us.
        """
        for mode, button in self._mode_buttons.items():
            if mode == self._selected_mode:
                button.configure(fg_color=ACCENT_BLUE, text_color=WHITE, border_color=ACCENT_BLUE)
            else:
                idle_color = WHITE if ctk.get_appearance_mode() == "Dark" else ACCENT_BLUE
                button.configure(
                    fg_color="transparent", text_color=idle_color, border_color=idle_color
                )

    # Mode selection -----------------------------------------------------------

    def _set_mode(self, mode: DisplayMode, announce: bool = False) -> None:
        """Record the user's mode preference and update UI + tray to match.

        Does NOT invoke DisplaySwitch.exe. That only happens on monitor-count
        changes or explicit double-clicks.
        """
        self._selected_mode = mode
        if announce:
            self._log(f"[{_timestamp()}]: Behavior set to: {mode.label}")
        self._refresh_button_colors()
        self._tray.set_mode(mode)

    def _force_switch(self, mode: DisplayMode) -> None:
        """Double-click handler: select the mode AND apply it right now."""
        self._set_mode(mode, announce=False)
        self._log(f"[{_timestamp()}]: Switching to {mode.label}")
        self._switcher.switch(mode)

    # Detector thread ----------------------------------------------------------

    def _start_detector_thread(self) -> None:
        Thread(target=self._detector_loop, daemon=True).start()

    def _detector_loop(self) -> None:
        """Background loop. Posts all UI updates back via root.after()."""
        last_count = self._detector.count()
        self._post(lambda: self._log(f"[{_timestamp()}]: Initial monitor count: {last_count}"))

        while True:
            sleep(self._poll_interval)
            # Cheap way to keep the UI matching the OS light/dark mode
            self._post(self._refresh_button_colors)

            new_count = self._detector.count()
            if new_count == last_count:
                continue

            if new_count > last_count:
                mode = self._selected_mode
                self._post(
                    lambda c=new_count, m=mode: self._log(
                        f"[{_timestamp()}]: Monitor added, switching to: {m.label}. New count: {c}"
                    )
                )
                self._switcher.switch(mode)
            else:
                self._post(
                    lambda c=new_count: self._log(
                        f"[{_timestamp()}]: Monitor removed, new count: {c}"
                    )
                )
            last_count = new_count

    def _post(self, fn) -> None:
        """Schedule a callable to run on the Tk main thread.

        Any UI touch from the detector thread MUST go through this. tkinter
        is not thread-safe and weird things happen otherwise (hangs, segfaults).
        """
        self.root.after(0, fn)

    # Logging ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        self._set_log_editable(True)
        self._log_lines.append(message)
        if len(self._log_lines) > _MAX_LOG_LINES:
            self._log_lines.pop(0)
        self._text_widget.delete(1.0, ctk.END)
        self._text_widget.insert(ctk.END, "\n".join(self._log_lines))
        self._set_log_editable(False)

    def _set_log_editable(self, enable: bool) -> None:
        # Disabled by default so users can't type into the log
        self._text_widget.configure(state="normal" if enable else "disabled")

    # Window management --------------------------------------------------------

    def _hide_window(self) -> None:
        self.root.withdraw()

    def _show_window(self) -> None:
        self.root.deiconify()
        self.root.after(50, self._grab_focus)

    def _grab_focus(self) -> None:
        """Force focus to the window.

        focus_force() is the blunt instrument here - it grabs focus even if
        the user is interacting with something else. For a tray app being
        deliberately opened, that's what we want. For a normal app it would
        be rude.
        """
        self.root.lift()
        self.root.focus_force()

    def _on_close(self) -> None:
        self._tray.stop()
        self.root.after(0, self.root.quit)
    
    def _on_focus_out(self, _event: object) -> None:
        """Minimize to tray when the window loses focus to another app.

        Note: FocusOut also fires when focus moves between child widgets,
        so we verify the window truly doesn't own focus anymore before hiding.
        The after(100, ...) gives Tk time to settle focus to its new target
        before we check - without it we'd see transient "no focus" states
        during normal widget interaction.
        """
        self.root.after(100, self._hide_if_unfocused)

    def _hide_if_unfocused(self) -> None:
        # focus_displayof() returns the widget with focus, or None if focus
        # is on another application entirely
        if self.root.focus_displayof() is None:
            self._hide_window()

    # Tray callbacks -----------------------------------------------------------

    def _on_tray_mode_selected(self, mode: DisplayMode) -> None:
        self._post(lambda: self._set_mode(mode, announce=True))

    def _on_tray_restore(self) -> None:
        self._post(self._show_window)

    def _on_tray_quit(self) -> None:
        self._post(self._on_close)