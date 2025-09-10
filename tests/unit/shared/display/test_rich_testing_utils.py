"""
Tests for Rich testing utilities.

Validates that our Rich testing patterns work correctly.
"""

import os
import sys
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from tests.utils.rich_test_utils import (
    RichTestCase,
    capture_console_output,
    create_test_console,
    create_test_container,
    reset_console_manager,
)


class TestRichTestingUtilities(unittest.TestCase, RichTestCase):
    """Test the Rich testing utilities themselves."""

    def setUp(self):
        """Set up test case with Rich testing patterns."""
        # Call RichTestCase setUp explicitly
        RichTestCase.setUp(self)

    def tearDown(self):
        """Clean up after test."""
        # Call RichTestCase tearDown explicitly
        RichTestCase.tearDown(self)

    def test_create_test_console(self):
        """Test that create_test_console creates proper test console."""
        console = create_test_console()

        # Should have StringIO file for capture
        self.assertTrue(hasattr(console.file, "getvalue"))

        # Should be configured for testing (check actual available attributes)
        self.assertEqual(console.width, 80)
        self.assertFalse(console.is_terminal)  # Should not think it's a real terminal

    def test_console_output_capture(self):
        """Test that console output is properly captured."""
        console = create_test_console()

        # Initially empty
        output = capture_console_output(console)
        self.assertEqual(output, "")

        # After printing, should capture output
        console.print("Test message")
        output = capture_console_output(console)
        self.assertIn("Test message", output)

    def test_create_test_container(self):
        """Test that create_test_container works."""
        container = create_test_container()

        # Should have console property
        self.assertTrue(hasattr(container, "console"))

        # Console should be test-friendly
        self.assertTrue(hasattr(container.console.file, "getvalue"))

    def test_rich_test_case_setup(self):
        """Test that RichTestCase setUp works correctly."""
        # These should be available from setUp
        self.assertTrue(hasattr(self, "test_console"))
        self.assertTrue(hasattr(self, "test_container"))
        self.assertTrue(hasattr(self, "display_manager"))
        self.assertTrue(hasattr(self, "display_options"))

    def test_console_output_assertions(self):
        """Test console output assertion methods."""
        # Test assert_console_contains
        self.display_manager.info("Test info message")
        self.assert_console_contains("Test info message")

        # Clear and test assert_console_not_contains
        self.clear_console_output()
        self.display_manager.info("Different message")
        self.assert_console_not_contains("Test info message")
        self.assert_console_contains("Different message")

    def test_console_output_clearing(self):
        """Test that console output can be cleared."""
        # Add some output
        self.display_manager.info("Initial message")
        self.assert_console_contains("Initial message")

        # Clear and verify empty
        self.clear_console_output()
        output = self.get_console_output()
        self.assertEqual(output.strip(), "")

    def test_console_lines_parsing(self):
        """Test that console output can be parsed into lines."""
        self.display_manager.info("Line 1")
        self.display_manager.info("Line 2")
        self.display_manager.info("Line 3")

        lines = self.get_console_lines()
        self.assertGreaterEqual(len(lines), 3)  # Should have at least our 3 lines

        # Check that our messages are in the lines
        all_text = " ".join(lines)
        self.assertIn("Line 1", all_text)
        self.assertIn("Line 2", all_text)
        self.assertIn("Line 3", all_text)

    def test_console_manager_reset(self):
        """Test that console manager can be reset for test isolation."""
        # This should not raise an exception
        reset_console_manager()

        # Should be able to create new container after reset
        new_container = create_test_container()
        self.assertTrue(hasattr(new_container, "console"))


if __name__ == "__main__":
    unittest.main()
