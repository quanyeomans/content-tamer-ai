"""
CLI Display Utilities with ANSI color support and terminal detection.

Provides cross-platform terminal capabilities with graceful fallbacks
for unsupported terminals and environments.
"""

import os
import sys
from enum import Enum
from typing import Optional, Tuple, Union


class MessageLevel(Enum):
    """Message severity levels for hierarchical display."""

    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Colors:
    """ANSI color codes and terminal styling."""

    # Reset
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # Cursor control
    CURSOR_UP = "\033[A"
    CURSOR_DOWN = "\033[B"
    CLEAR_LINE = "\033[K"
    CLEAR_SCREEN = "\033[2J"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"


class TerminalCapabilities:
    """Detects and manages terminal display capabilities."""

    def __init__(self, force_no_unicode: bool = False):
        self._supports_color = None
        self._supports_unicode = None
        self._terminal_width = None
        self._force_no_unicode = force_no_unicode

    @property
    def supports_color(self) -> bool:
        """Check if terminal supports ANSI colors."""
        if self._supports_color is None:
            self._supports_color = self._detect_color_support()
        return self._supports_color

    @property
    def supports_unicode(self) -> bool:
        """Check if terminal supports Unicode characters."""
        if self._supports_unicode is None:
            self._supports_unicode = self._detect_unicode_support()
        return self._supports_unicode

    @property
    def terminal_width(self) -> int:
        """Get terminal width, with fallback to 80."""
        if self._terminal_width is None:
            self._terminal_width = self._detect_terminal_width()
        return self._terminal_width

    def _detect_color_support(self) -> bool:
        """Detect ANSI color support across platforms."""
        # Check if output is redirected
        if not sys.stdout.isatty():
            return False

        # Check environment variables
        if os.environ.get("NO_COLOR"):
            return False

        if os.environ.get("FORCE_COLOR"):
            return True

        # Windows-specific checks
        if sys.platform == "win32":
            # Windows 10 version 1511 and later support ANSI
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                )
                build = winreg.QueryValueEx(key, "CurrentBuild")[0]
                winreg.CloseKey(key)
                return int(build) >= 10586  # Windows 10 build 1511
            except (ImportError, OSError, ValueError):
                # Fallback: assume modern Windows supports it
                return True

        # Unix-like systems
        term = os.environ.get("TERM", "").lower()
        if any(x in term for x in ["color", "ansi", "xterm", "screen", "tmux"]):
            return True

        # Conservative fallback
        return False

    def _detect_unicode_support(self) -> bool:
        """Detect Unicode support."""
        # If forced to disable Unicode, return False
        if self._force_no_unicode:
            return False
            
        try:
            # Try encoding Unicode box-drawing characters
            "█▓▒░→".encode(sys.stdout.encoding or "utf-8")
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def _detect_terminal_width(self) -> int:
        """Detect terminal width with fallbacks."""
        try:
            # Try os.get_terminal_size (Python 3.3+)
            return os.get_terminal_size().columns
        except (OSError, AttributeError):
            pass

        try:
            # Try environment variable
            columns = os.environ.get("COLUMNS")
            if columns:
                return int(columns)
        except (ValueError, TypeError):
            pass

        # Fallback to common default
        return 80


class ColorFormatter:
    """Format text with colors and styling."""

    def __init__(self, no_color: bool = False):
        self.capabilities = TerminalCapabilities(force_no_unicode=no_color)
        self.no_color = no_color or not self.capabilities.supports_color

    def colorize(self, text: str, color: str, bold: bool = False) -> str:
        """Apply color and styling to text."""
        if self.no_color:
            return text

        style = ""
        if bold:
            style += Colors.BOLD

        # Map color names to ANSI codes
        color_map = {
            "red": Colors.RED,
            "green": Colors.GREEN,
            "yellow": Colors.YELLOW,
            "blue": Colors.BLUE,
            "cyan": Colors.CYAN,
            "magenta": Colors.MAGENTA,
            "white": Colors.WHITE,
            "bright_red": Colors.BRIGHT_RED,
            "bright_green": Colors.BRIGHT_GREEN,
            "bright_yellow": Colors.BRIGHT_YELLOW,
            "bright_blue": Colors.BRIGHT_BLUE,
            "bright_cyan": Colors.BRIGHT_CYAN,
            "bright_white": Colors.BRIGHT_WHITE,
            "dim": Colors.DIM,
        }

        color_code = color_map.get(color.lower(), "")
        return f"{style}{color_code}{text}{Colors.RESET}"

    def progress_bar(
        self,
        current: int,
        total: int,
        width: int = 40,
        fill_char: str = "█",
        empty_char: str = "░",
    ) -> str:
        """Create a colorized progress bar."""
        # Use Unicode if supported, ASCII fallback
        if not self.capabilities.supports_unicode:
            fill_char = "#"
            empty_char = "-"

        if total == 0:
            empty_bar = self.colorize(empty_char * width, "dim")
            return f"[{empty_bar}]"

        filled_width = int((current / total) * width)
        filled = fill_char * filled_width
        empty = empty_char * (width - filled_width)

        progress = self.colorize(filled, "bright_cyan", bold=True)
        remaining = self.colorize(empty, "dim")

        return f"[{progress}{remaining}]"

    def format_message(self, message: str, level: MessageLevel) -> str:
        """Format message according to its severity level."""
        level_config = {
            MessageLevel.DEBUG: ("dim", "🔍", False),
            MessageLevel.INFO: ("blue", "ℹ️", False),
            MessageLevel.SUCCESS: ("bright_green", "✅", True),
            MessageLevel.WARNING: ("bright_yellow", "⚠️", True),
            MessageLevel.ERROR: ("bright_red", "❌", True),
            MessageLevel.CRITICAL: ("bright_red", "🚨", True),
        }

        color, icon, bold = level_config[level]

        # Use ASCII fallback if Unicode not supported
        if not self.capabilities.supports_unicode:
            icon_map = {
                "🔍": "[DEBUG]",
                "ℹ️": "[INFO]",
                "✅": "[OK]",
                "⚠️": "[WARN]",
                "❌": "[ERROR]",
                "🚨": "[CRIT]",
            }
            icon = icon_map.get(icon, icon)

        colored_icon = self.colorize(icon, color, bold=bold)
        return f"{colored_icon} {message}"

    def highlight_filename(self, filename: str) -> str:
        """Highlight target filename prominently."""
        return self.colorize(filename, "bright_yellow", bold=True)

    def format_time(self, seconds: float) -> str:
        """Format elapsed time in a readable way."""
        if seconds < 60:
            time_str = f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            time_str = f"{minutes}m{secs:02d}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            time_str = f"{hours}h{minutes:02d}m"

        return self.colorize(time_str, "dim")


def get_terminal_capabilities() -> TerminalCapabilities:
    """Get terminal capabilities (convenience function)."""
    return TerminalCapabilities()


def create_formatter(no_color: bool = False) -> ColorFormatter:
    """Create color formatter with current terminal capabilities."""
    return ColorFormatter(no_color=no_color)
