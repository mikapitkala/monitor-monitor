"""Enums, colors, and mappings used across the app."""

from enum import Enum


class DisplayMode(Enum):
    """The four modes DisplaySwitch.exe knows about.

    The value is the numeric flag DisplaySwitch.exe expects on the command line.
    The label is what we show to humans.
    """

    INTERNAL = ("1", "Internal only")
    CLONE = ("2", "Clone")
    EXTEND = ("3", "Extend")
    EXTERNAL = ("4", "External only")

    def __init__(self, flag: str, label: str) -> None:
        self.flag = flag
        self.label = label

    @classmethod
    def from_cli(cls, value: str) -> "DisplayMode":
        """Parse a CLI argument (number or name) into a DisplayMode."""
        normalized = value.strip().lower()
        for mode in cls:
            if normalized == mode.flag or normalized == mode.name.lower():
                return mode
        raise ValueError(f"Unknown display mode: {value!r}")

    @classmethod
    def from_label(cls, label: str) -> "DisplayMode":
        """Look up a mode by its human-readable label."""
        for mode in cls:
            if mode.label == label:
                return mode
        raise ValueError(f"Unknown display label: {label!r}")


# Accepted values for the CLI mode argument
CLI_MODE_CHOICES: tuple[str, ...] = (
    "1", "2", "3", "4",
    "internal", "clone", "extend", "external",
)

# Color palette - modern blue, leaves room for theming later
ACCENT_BLUE = "#0A84FF"         # Primary, selected states
ACCENT_BLUE_HOVER = "#38BDF8"   # Hover states
DEEP_PURPLE = "#1E1B3A"         # Dark mode background accent
SOFT_GREY = "#F4F4F5"           # Light mode background accent
DANGER_RED = "#EF4444"          # Close button
COOL_GREY = "F5F5F7"
WHITE = "#FFFFFF"

# How often the detector polls for monitor changes
DEFAULT_POLL_INTERVAL_SECONDS = 5

# Should probably look like Windows
CORNER_RADIUS = 6
BORDER_WIDTH = 1
BUTTON_SPACING = 4
UI_FONT_FAMILY = "Segoe UI Variable"
UI_FONT_FALLBACK = "Segoe UI"  # Pre-Windows 11 machines don't have Variable
UI_FONT_SIZE = 13