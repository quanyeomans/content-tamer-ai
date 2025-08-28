"""
Tests for CLI display utilities - ANSI colors and terminal detection.
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from utils.cli_display import (
    ColorFormatter,
    Colors,
    MessageLevel,
    TerminalCapabilities,
    create_formatter,
    get_terminal_capabilities,
)


class TestColors(unittest.TestCase):
    """Test ANSI color constants."""

    def test_color_constants_are_strings(self):
        """Verify all color constants are valid strings."""
        self.assertIsInstance(Colors.RED, str)
        self.assertIsInstance(Colors.GREEN, str)
        self.assertIsInstance(Colors.BLUE, str)
        self.assertIsInstance(Colors.RESET, str)

    def test_ansi_escape_sequences(self):
        """Verify ANSI escape sequences are correct."""
        self.assertTrue(Colors.RED.startswith("\033["))
        self.assertTrue(Colors.GREEN.startswith("\033["))
        self.assertEqual(Colors.RESET, "\033[0m")
        self.assertEqual(Colors.BOLD, "\033[1m")


class TestTerminalCapabilities(unittest.TestCase):
    """Test terminal capability detection."""

    def setUp(self):
        self.capabilities = TerminalCapabilities()

    def test_color_support_detection(self):
        """Test color support detection logic."""
        # Should return boolean
        result = self.capabilities.supports_color
        self.assertIsInstance(result, bool)

    def test_unicode_support_detection(self):
        """Test Unicode support detection."""
        result = self.capabilities.supports_unicode
        self.assertIsInstance(result, bool)

    def test_terminal_width_detection(self):
        """Test terminal width detection with fallback."""
        width = self.capabilities.terminal_width
        self.assertIsInstance(width, int)
        self.assertGreaterEqual(width, 40)  # Minimum reasonable width

    @patch.dict(os.environ, {"NO_COLOR": "1"})
    def test_no_color_environment_variable(self):
        """Test NO_COLOR environment variable is respected."""
        capabilities = TerminalCapabilities()
        # Force re-detection
        capabilities._supports_color = None
        self.assertFalse(capabilities.supports_color)

    @patch.dict(os.environ, {"FORCE_COLOR": "1"})
    def test_force_color_environment_variable(self):
        """Test FORCE_COLOR environment variable is respected."""
        capabilities = TerminalCapabilities()
        # Force re-detection
        capabilities._supports_color = None
        # Note: This might still be False if isatty() returns False
        result = capabilities.supports_color
        self.assertIsInstance(result, bool)

    @patch("sys.stdout.isatty", return_value=False)
    def test_non_tty_disables_color(self, mock_isatty):
        """Test that non-TTY output disables color."""
        capabilities = TerminalCapabilities()
        capabilities._supports_color = None  # Force re-detection
        self.assertFalse(capabilities.supports_color)

    @patch("os.get_terminal_size")
    def test_terminal_width_fallback(self, mock_get_size):
        """Test terminal width fallback when os.get_terminal_size fails."""
        mock_get_size.side_effect = OSError("Terminal size unavailable")
        capabilities = TerminalCapabilities()
        capabilities._terminal_width = None  # Force re-detection
        width = capabilities.terminal_width
        self.assertEqual(width, 80)  # Should fallback to 80


class TestColorFormatter(unittest.TestCase):
    """Test color formatting functionality."""

    def setUp(self):
        self.formatter_color = ColorFormatter(no_color=False)
        self.formatter_no_color = ColorFormatter(no_color=True)

    def test_colorize_with_color_enabled(self):
        """Test text colorization when colors are enabled."""
        result = self.formatter_color.colorize("test", "red")
        # Should contain ANSI codes if color is supported
        if self.formatter_color.capabilities.supports_color:
            self.assertIn("\033[", result)
            self.assertIn("test", result)
        else:
            self.assertEqual(result, "test")

    def test_colorize_with_color_disabled(self):
        """Test text colorization when colors are disabled."""
        result = self.formatter_no_color.colorize("test", "red", bold=True)
        self.assertEqual(result, "test")  # Should return plain text

    def test_colorize_with_bold(self):
        """Test bold text formatting."""
        result = self.formatter_color.colorize("test", "blue", bold=True)
        self.assertIn("test", result)

    def test_progress_bar_formatting(self):
        """Test progress bar generation."""
        result = self.formatter_color.progress_bar(50, 100, width=20)
        self.assertIn("[", result)
        self.assertIn("]", result)
        # Should be approximately the right length (plus ANSI codes)
        self.assertGreater(len(result), 20)

    def test_progress_bar_zero_total(self):
        """Test progress bar with zero total."""
        result = self.formatter_color.progress_bar(0, 0, width=10)
        self.assertIn("[", result)
        self.assertIn("]", result)

    def test_format_message_all_levels(self):
        """Test message formatting for all severity levels."""
        levels = [
            MessageLevel.DEBUG,
            MessageLevel.INFO,
            MessageLevel.SUCCESS,
            MessageLevel.WARNING,
            MessageLevel.ERROR,
            MessageLevel.CRITICAL,
        ]

        for level in levels:
            result = self.formatter_color.format_message("test message", level)
            self.assertIn("test message", result)
            # Should have some kind of prefix/indicator
            self.assertGreater(len(result), len("test message"))

    def test_highlight_filename(self):
        """Test filename highlighting."""
        result = self.formatter_color.highlight_filename("test.pdf")
        self.assertIn("test.pdf", result)

    def test_format_time(self):
        """Test time formatting."""
        # Test seconds
        result = self.formatter_color.format_time(45)
        self.assertIn("45s", result)

        # Test minutes
        result = self.formatter_color.format_time(125)  # 2m05s
        self.assertIn("2m", result)
        self.assertIn("05s", result)

        # Test hours
        result = self.formatter_color.format_time(3725)  # 1h02m
        self.assertIn("1h", result)
        self.assertIn("02m", result)

    def test_unicode_fallback(self):
        """Test Unicode fallback for unsupported terminals."""
        # Create formatter with explicit Unicode disabled
        formatter_no_unicode = ColorFormatter(no_color=False)
        # Directly set the internal flag to simulate no Unicode support
        formatter_no_unicode.capabilities._supports_unicode = False

        # Test progress bar fallback
        result = formatter_no_unicode.progress_bar(50, 100, width=10)
        self.assertNotIn("█", result)  # Should not contain Unicode
        self.assertNotIn("░", result)  # Should not contain Unicode
        self.assertIn("#", result)  # Should contain ASCII alternative

        # Test message formatting fallback
        result = formatter_no_unicode.format_message("test", MessageLevel.SUCCESS)
        self.assertNotIn("✅", result)  # Should not contain Unicode emoji
        self.assertIn("[OK]", result)  # Should contain ASCII alternative


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_get_terminal_capabilities(self):
        """Test get_terminal_capabilities function."""
        capabilities = get_terminal_capabilities()
        self.assertIsInstance(capabilities, TerminalCapabilities)

    def test_create_formatter(self):
        """Test create_formatter function."""
        formatter = create_formatter()
        self.assertIsInstance(formatter, ColorFormatter)

        formatter_no_color = create_formatter(no_color=True)
        self.assertTrue(formatter_no_color.no_color)


class TestCrossPlatformCompatibility(unittest.TestCase):
    """Test cross-platform compatibility."""

    @patch("sys.platform", "win32")
    def test_windows_color_detection(self):
        """Test color detection on Windows."""
        capabilities = TerminalCapabilities()
        capabilities._supports_color = None  # Force re-detection

        # Should not crash on Windows
        result = capabilities.supports_color
        self.assertIsInstance(result, bool)

    @patch("sys.platform", "linux")
    def test_linux_color_detection(self):
        """Test color detection on Linux."""
        capabilities = TerminalCapabilities()
        capabilities._supports_color = None  # Force re-detection

        result = capabilities.supports_color
        self.assertIsInstance(result, bool)

    @patch.dict(os.environ, {"TERM": "xterm-256color"})
    def test_xterm_color_support(self):
        """Test color support detection with xterm."""
        capabilities = TerminalCapabilities()
        capabilities._supports_color = None  # Force re-detection

        # xterm should support colors if isatty() returns True
        with patch("sys.stdout.isatty", return_value=True):
            self.assertTrue(capabilities.supports_color)


if __name__ == "__main__":
    unittest.main()
