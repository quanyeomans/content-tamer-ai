"""
Tests for enhanced error handling and retry logic.

Tests the new error classification, retry mechanisms, and user-friendly
messaging for recoverable filesystem errors.
"""

import errno
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from io import StringIO

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.error_handling import (
    ErrorType, ErrorClassifier, RetryHandler, create_retry_handler,
    ErrorClassification, RetryStats
)


class TestErrorClassification(unittest.TestCase):
    """Test error classification system."""
    
    def test_permission_denied_classification(self):
        """Test that permission denied errors are classified as recoverable."""
        # Test with errno
        perm_error = OSError(errno.EACCES, "Permission denied")
        classification = ErrorClassifier.classify_error(perm_error)
        
        self.assertEqual(classification.error_type, ErrorType.RECOVERABLE_PERMISSION)
        self.assertTrue(classification.is_recoverable)
        self.assertTrue(classification.retry_recommended)
        self.assertIn("antivirus", classification.user_message.lower())
        
    def test_permission_denied_string_classification(self):
        """Test permission denied detection by string matching."""
        perm_error = Exception("[Errno 13] Permission denied")
        classification = ErrorClassifier.classify_error(perm_error)
        
        self.assertEqual(classification.error_type, ErrorType.RECOVERABLE_PERMISSION)
        self.assertTrue(classification.is_recoverable)
        
    def test_file_locked_classification(self):
        """Test file in use/locked errors."""
        lock_error = OSError(errno.EBUSY, "File is being used by another process")
        classification = ErrorClassifier.classify_error(lock_error)
        
        self.assertEqual(classification.error_type, ErrorType.FILE_LOCKED)
        self.assertTrue(classification.is_recoverable)
        self.assertIn("another application", classification.user_message.lower())
        
    def test_sync_conflict_classification(self):
        """Test cloud sync conflict detection."""
        sync_error = Exception("OneDrive sync conflict detected")
        classification = ErrorClassifier.classify_error(sync_error)
        
        self.assertEqual(classification.error_type, ErrorType.SYNC_CONFLICT)
        self.assertTrue(classification.is_recoverable)
        self.assertIn("sync", classification.user_message.lower())
        
    def test_permanent_error_classification(self):
        """Test that genuine errors are classified as permanent."""
        real_error = ValueError("Invalid file format")
        classification = ErrorClassifier.classify_error(real_error)
        
        self.assertEqual(classification.error_type, ErrorType.PERMANENT_ERROR)
        self.assertFalse(classification.is_recoverable)
        self.assertFalse(classification.retry_recommended)
        
    def test_unsupported_format_classification(self):
        """Test unsupported file format detection."""
        format_error = Exception("Unsupported file format")
        classification = ErrorClassifier.classify_error(format_error)
        
        self.assertEqual(classification.error_type, ErrorType.UNSUPPORTED_FORMAT)
        self.assertFalse(classification.is_recoverable)


class TestRetryHandler(unittest.TestCase):
    """Test retry handler functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()
        self.display_context = MagicMock()
        self.retry_handler = RetryHandler(max_attempts=3, base_wait_time=0.1)
        
    def test_successful_first_attempt(self):
        """Test operation succeeds on first attempt."""
        def successful_operation():
            return "success"
        
        success, result, error = self.retry_handler.execute_with_retry(
            operation=successful_operation,
            display_context=self.display_context,
            filename="test.pdf"
        )
        
        self.assertTrue(success)
        self.assertEqual(result, "success")
        self.assertIsNone(error)
        self.assertEqual(self.retry_handler.get_stats().total_attempts, 1)
        
    def test_recoverable_error_with_retry_success(self):
        """Test recoverable error that succeeds on retry."""
        attempt_count = 0
        
        def failing_then_success_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise OSError(errno.EACCES, "Permission denied")
            return "success_after_retry"
        
        with patch('time.sleep'):  # Skip actual sleep in tests
            success, result, error = self.retry_handler.execute_with_retry(
                operation=failing_then_success_operation,
                display_context=self.display_context,
                filename="test.pdf"
            )
        
        self.assertTrue(success)
        self.assertEqual(result, "success_after_retry")
        self.assertIsNone(error)
        self.assertEqual(self.retry_handler.get_stats().successful_retries, 1)
        self.assertEqual(self.retry_handler.get_stats().recoverable_errors_encountered, 1)
        
        # Verify display context was called appropriately
        self.display_context.set_status.assert_any_call("retrying")
        self.display_context.set_status.assert_any_call("recovered")
        self.display_context.show_info.assert_any_call("✅ Successfully processed after retry")
        
    def test_permanent_error_no_retry(self):
        """Test permanent errors are not retried."""
        def permanent_failure_operation():
            raise ValueError("Unsupported file format")
        
        success, result, error = self.retry_handler.execute_with_retry(
            operation=permanent_failure_operation,
            display_context=self.display_context,
            filename="test.pdf"
        )
        
        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, ErrorType.UNSUPPORTED_FORMAT)
        self.assertEqual(self.retry_handler.get_stats().permanent_errors, 1)
        
        # Verify permanent error handling
        self.display_context.set_status.assert_called_with("failed")
        
    def test_recoverable_error_exhausted_retries(self):
        """Test recoverable error that fails all retry attempts."""
        def always_failing_operation():
            raise OSError(errno.EACCES, "Permission denied")
        
        with patch('time.sleep'):  # Skip actual sleep in tests
            success, result, error = self.retry_handler.execute_with_retry(
                operation=always_failing_operation,
                display_context=self.display_context,
                filename="test.pdf"
            )
        
        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, ErrorType.RECOVERABLE_PERMISSION)
        
        # Should have tried 3 times (max_attempts)
        stats = self.retry_handler.get_stats()
        self.assertEqual(stats.recoverable_errors_encountered, 2)  # Two retry decisions made
        self.assertEqual(stats.failed_retries, 1)  # Final failure counts as failed retry
        
    def test_session_summary_formatting(self):
        """Test session summary message formatting."""
        # Simulate some successful retries
        self.retry_handler.stats.successful_retries = 2
        self.retry_handler.stats.files_with_recoverable_issues = 3
        
        summary = self.retry_handler.format_session_summary()
        
        self.assertIn("2 files recovered", summary)
        self.assertIn("3 files had temporary", summary)
        self.assertIn("antivirus", summary)
        
    def test_empty_session_summary(self):
        """Test session summary when no errors occurred."""
        summary = self.retry_handler.format_session_summary()
        self.assertEqual(summary, "")


class TestRetryHandlerFactory(unittest.TestCase):
    """Test retry handler factory function."""
    
    def test_create_retry_handler(self):
        """Test factory creates properly configured retry handler."""
        handler = create_retry_handler(max_attempts=5)
        
        self.assertIsInstance(handler, RetryHandler)
        self.assertEqual(handler.max_attempts, 5)
        self.assertEqual(handler.base_wait_time, 1.0)
        
    def test_default_retry_handler(self):
        """Test factory creates handler with default settings."""
        handler = create_retry_handler()
        
        self.assertEqual(handler.max_attempts, 3)
        self.assertEqual(handler.base_wait_time, 1.0)


class TestRetryStats(unittest.TestCase):
    """Test retry statistics tracking."""
    
    def setUp(self):
        """Set up test environment."""
        self.stats = RetryStats()
        
    def test_initial_stats(self):
        """Test initial statistics are zero."""
        self.assertEqual(self.stats.total_attempts, 0)
        self.assertEqual(self.stats.successful_retries, 0)
        self.assertEqual(self.stats.failed_retries, 0)
        self.assertEqual(self.stats.recoverable_errors_encountered, 0)
        self.assertEqual(self.stats.permanent_errors, 0)
        
    def test_add_attempt_tracking(self):
        """Test attempt tracking."""
        self.stats.add_attempt(success=True, was_retry=False)
        self.stats.add_attempt(success=True, was_retry=True)
        self.stats.add_attempt(success=False, was_retry=True)
        
        self.assertEqual(self.stats.total_attempts, 3)
        self.assertEqual(self.stats.successful_retries, 1)
        self.assertEqual(self.stats.failed_retries, 1)
        
    def test_error_type_tracking(self):
        """Test tracking different error types."""
        self.stats.add_recoverable_error()
        self.stats.add_recoverable_error()
        self.stats.add_permanent_error()
        
        self.assertEqual(self.stats.recoverable_errors_encountered, 2)
        self.assertEqual(self.stats.permanent_errors, 1)


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic error scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.display_context = MagicMock()
        self.retry_handler = create_retry_handler(max_attempts=3)
        
    def test_windows_antivirus_scenario(self):
        """Test typical Windows antivirus scanning scenario."""
        call_count = 0
        
        def antivirus_scan_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fails twice, succeeds third time
                raise OSError(errno.EACCES, "Permission denied")
            return "processed_successfully"
        
        with patch('time.sleep'):  # Skip sleep in tests
            success, result, error = self.retry_handler.execute_with_retry(
                operation=antivirus_scan_operation,
                display_context=self.display_context,
                filename="document.pdf"
            )
        
        self.assertTrue(success)
        self.assertEqual(result, "processed_successfully")
        self.assertEqual(call_count, 3)
        
        # Check user-friendly messaging
        self.display_context.show_info.assert_any_call(
            "⏳ File temporarily locked (likely antivirus scan or sync), retrying..."
        )
        self.display_context.show_info.assert_any_call(
            "✅ Successfully processed after retry"
        )
        
    def test_onedrive_sync_scenario(self):
        """Test OneDrive sync conflict scenario."""
        def sync_conflict_operation():
            raise Exception("OneDrive sync conflict: file is being synchronized")
        
        success, result, error = self.retry_handler.execute_with_retry(
            operation=sync_conflict_operation,
            display_context=self.display_context,
            filename="synced_document.pdf"
        )
        
        self.assertFalse(success)
        self.assertEqual(error.error_type, ErrorType.SYNC_CONFLICT)
        
        # Should show appropriate sync-related message
        self.display_context.show_info.assert_any_call(
            "⏳ Cloud sync conflict detected, retrying..."
        )


if __name__ == '__main__':
    unittest.main()