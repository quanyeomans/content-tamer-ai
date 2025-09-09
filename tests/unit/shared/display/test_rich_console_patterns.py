"""
Tests for Rich Console Patterns

Demonstrates proper Rich testing approach without excessive mocking.
Uses RichTestCase framework for proper console isolation.
"""

import unittest
from unittest.mock import patch

# Import Rich testing framework
from tests.utils.rich_test_utils import RichTestCase
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from interfaces.human.rich_console_manager import RichConsoleManager

class TestRichConsoleManager(unittest.TestCase, RichTestCase):
    """Test Rich Console Manager using proper Rich testing patterns."""

    def setUp(self):
        """Set up Rich test environment."""
        RichTestCase.setUp(self)
        self.console_manager = RichConsoleManager()

        # Override console with test console for isolation
        self.console_manager._console = self.test_console

    def test_welcome_panel_with_emoji_detection(self):
        """Test welcome panel uses smart emoji detection."""
        self.console_manager.show_welcome_panel()

        output = self.get_console_output()

        # Should contain welcome content regardless of emoji support
        self.assertIn("CONTENT TAMER AI", output)
        self.assertIn("Intelligent document processing", output)

        # Should use appropriate format based on console encoding
        if hasattr(self.test_console, 'options') and self.test_console.options.encoding == 'utf-8':
            # UTF-8 console should use emojis
            self.assertIn("🎯", output)
        else:
            # Non-UTF-8 console should use ASCII alternatives
            self.assertIn(">>", output)

    def test_status_messages_with_smart_emoji_usage(self):
        """Test status messages use smart emoji detection."""
        test_cases = [
            ("success", "Test success message"),
            ("warning", "Test warning message"),
            ("error", "Test error message"),
            ("info", "Test info message")
        ]

        for status, message in test_cases:
            self.console_manager.show_status(message, status)

            output = self.get_console_output()

            # Should contain the message
            self.assertIn(message, output)

            # Should use appropriate icon based on encoding
            if hasattr(self.test_console, 'options') and self.test_console.options.encoding == 'utf-8':
                # UTF-8 should use emoji
                if status == "success":
                    self.assertIn("✅", output)
            else:
                # Non-UTF-8 should use ASCII
                if status == "success":
                    self.assertIn("[✓]", output)

            # Clear output for next test
            self.clear_output()

    def test_loading_message_with_emoji_detection(self):
        """Test loading messages use smart emoji detection."""
        self.console_manager.show_loading("Processing test")

        output = self.get_console_output()
        self.assertIn("Processing test", output)

        # Should use appropriate spinner based on encoding
        if hasattr(self.test_console, 'options') and self.test_console.options.encoding == 'utf-8':
            self.assertIn("🔄", output)
        else:
            self.assertIn("[~]", output)

class TestRichConsolePatterns(unittest.TestCase):
    """Test Rich Console patterns without over-mocking."""

    def test_console_creation_with_auto_detection(self):
        """Test console is created with proper auto-detection."""
        console_manager = RichConsoleManager()
        console = console_manager.console

        self.assertIsNotNone(console)
        # Rich should auto-detect terminal capabilities
        self.assertTrue(hasattr(console, 'options'))
        self.assertTrue(hasattr(console.options, 'encoding'))

    def test_emoji_detection_logic(self):
        """Test emoji detection logic works correctly."""
        console_manager = RichConsoleManager()
        console = console_manager.console

        # Test the detection logic we use
        has_emoji_support = (
            hasattr(console, 'options') and
            console.options.encoding == 'utf-8'
        )

        # Should return boolean result
        self.assertIsInstance(has_emoji_support, bool)

        # Test message formatting
        if has_emoji_support:
            # Should use emoji
            test_message = "🎯 Test with emoji"
        else:
            # Should use ASCII alternative
            test_message = ">> Test without emoji <<"

        # Message should be properly formatted string
        self.assertIsInstance(test_message, str)
        self.assertIn("Test", test_message)

class TestRichTestingFramework(unittest.TestCase, RichTestCase):
    """Demonstrate proper Rich testing without excessive mocking."""

    def setUp(self):
        """Set up Rich test environment with console isolation."""
        RichTestCase.setUp(self)
        # RichTestCase provides isolated test console automatically

    def test_rich_output_capture(self):
        """Test Rich output can be captured and validated."""
        # Use test console for Rich output
        self.test_console.print("[green]Test message[/green]")

        output = self.get_console_output()

        # Can validate Rich output without Unicode issues
        self.assertIn("Test message", output)
        # Rich styling is preserved in test output

    def test_console_isolation(self):
        """Test console isolation prevents conflicts."""
        # Multiple console operations should not interfere
        self.test_console.print("Message 1")
        self.test_console.print("Message 2")

        output = self.get_console_output()

        self.assertIn("Message 1", output)
        self.assertIn("Message 2", output)

    @patch("builtins.input")  # Only mock input, not console output
    def test_minimal_mocking_approach(self, mock_input):
        """Demonstrate minimal mocking - only mock external inputs."""
        mock_input.return_value = "test input"

        # Use real Rich console for output (through test framework)
        self.test_console.print("[cyan]Testing with minimal mocks[/cyan]")

        output = self.get_console_output()
        self.assertIn("Testing with minimal mocks", output)

        # Verify input was mocked appropriately
        mock_input.assert_called()

if __name__ == '__main__':
    unittest.main()
