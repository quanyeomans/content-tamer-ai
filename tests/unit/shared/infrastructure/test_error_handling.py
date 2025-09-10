"""
Tests for enhanced error handling and retry logic.

Tests the new error classification, retry mechanisms, and user-friendly
messaging for recoverable filesystem errors.
"""

import errno
import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from shared.infrastructure.error_handling import create_retry_handler


class TestRetryHandler(unittest.TestCase):
    """Test retry handling functionality."""

    def setUp(self):
        """Set up test retry handler."""
        self.retry_handler = create_retry_handler(max_attempts=3)

    def test_windows_antivirus_scenario(self):
        """Test typical Windows antivirus scanning scenario."""
        call_count = 0

        def antivirus_scan_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError(errno.EACCES, "Permission denied - file in use by another process")
            return "Success"

        # Mock display context
        mock_display = Mock()

        # Test with recoverable failure that eventually succeeds
        success, result, error_class = self.retry_handler.execute_with_retry(
            antivirus_scan_operation, mock_display, "test_file.pdf"
        )

        self.assertTrue(success)
        self.assertEqual(result, "Success")
        self.assertEqual(call_count, 3)
        self.assertIsNone(error_class)

    def test_permanent_failure(self):
        """Test handling of permanent failures."""

        def always_fails():
            raise OSError(errno.ENOENT, "File not found")

        # Mock display context
        mock_display = Mock()

        # Test with permanent failure - should return False and error classification
        success, result, error_class = self.retry_handler.execute_with_retry(
            always_fails, mock_display, "test_file.pdf"
        )

        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIsNotNone(error_class)


if __name__ == "__main__":
    unittest.main()
