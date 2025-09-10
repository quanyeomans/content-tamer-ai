"""
Critical Integration Tests: File Processing Success Determination Flow

This test module addresses the critical gap identified in TESTING_STRATEGY.md:
"Files that succeeded after retries were being marked as failures in the progress display"

These tests would have caught the 2-hour debugging bug scenario.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import pytest

from core.application_container import TestApplicationContainer
from orchestration.workflow_processor import (
    process_file_enhanced_core,
    process_file_with_retry,
)
from shared.infrastructure.error_handling import create_retry_handler


class TestFileProcessingSuccessFlow(unittest.TestCase):
    """Integration tests for file processing success determination."""

    def setUp(self):
        """Set up test environment with real file operations."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")

        # Create directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.unprocessed_dir, exist_ok=True)

        # Create test container
        self.container = TestApplicationContainer(capture_output=True)

        # Create test file with content
        self.test_file_path = os.path.join(self.input_dir, "test_document.pdf")
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("Test PDF content")

        # Mock AI client
        self.ai_client = Mock()
        self.ai_client.generate_filename.return_value = "test_generated_filename"

        # Mock organizer with real file manager
        self.organizer = Mock()
        self.organizer.move_file_to_category.return_value = "test_generated_filename.pdf"
        self.organizer.file_manager.safe_move = Mock(side_effect=self._mock_file_move)
        self.organizer.filename_handler.validate_and_trim_filename = Mock(
            side_effect=lambda x: x
        )
        self.organizer.progress_tracker.record_progress = Mock()

        # Mock display context
        self.display_context = Mock()
        self.display_context.set_status = Mock()
        self.display_context.show_warning = Mock()
        self.display_context.show_error = Mock()
        self.display_context.show_info = Mock()

        # Mock progress file
        self.progress_f = Mock()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def _mock_file_move(self, source, dest):
        """Mock file move operation that performs real filesystem operations."""
        if os.path.exists(source):
            import shutil

            shutil.move(source, dest)
        return dest

    @pytest.mark.integration
    @pytest.mark.critical
    def test_file_processing_success_determination_core_success(self):
        """CRITICAL: Test that successful processing is correctly identified.
        
        This test would have caught the 2-hour debugging bug where successful
        files were marked as failures.
        """
        with patch("orchestration.workflow_processor._extract_file_content") as mock_extract:
            mock_extract.return_value = ("Extracted content", "")

            # Act: Process file that should succeed
            success, result = process_file_enhanced_core(
                input_path=self.test_file_path,
                filename="test_document.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.output_dir,
                progress_f=self.progress_f,
                ocr_lang="eng",
                ai_client=self.ai_client,
                organizer=self.organizer,
                display_context=self.display_context,
            )

            # Assert: Success determination is accurate
            self.assertTrue(
                success,
                "File that processes successfully must return success=True - not doing so was the 2-hour debugging bug",
            )
            self.assertIsNotNone(
                result,
                "Successful processing must return a result (the new filename)",
            )
            self.assertEqual(result, "test_generated_filename.pdf")

            # Assert: File operations were called correctly
            self.organizer.move_file_to_category.assert_called_once()
            self.ai_client.generate_filename.assert_called_once()

            # Assert: No error handling paths were taken
            self.display_context.show_error.assert_not_called()

    @pytest.mark.integration
    @pytest.mark.critical
    def test_file_processing_success_after_retry_scenario(self):
        """CRITICAL: Test that files succeeding after retries show as successes.
        
        This is the exact scenario that caused the 2-hour debugging session.
        """
        retry_handler = create_retry_handler(max_attempts=2)

        # Mock extraction to fail first, succeed second time
        call_count = 0

        def mock_extract_with_retry(input_path, ocr_lang, display_context):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First attempt fails with recoverable error
                raise PermissionError("Permission denied")  # errno 13 - recoverable
            else:
                # Second attempt succeeds
                return "Extracted content", ""

        with patch(
            "orchestration.workflow_processor._extract_file_content", side_effect=mock_extract_with_retry
        ):

            # Act: Process file that fails first, succeeds on retry
            success, result = process_file_with_retry(
                input_path=self.test_file_path,
                filename="test_document.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.output_dir,
                progress_f=self.progress_f,
                ocr_lang="eng",
                ai_client=self.ai_client,
                organizer=self.organizer,
                display_context=self.display_context,
                retry_handler=retry_handler,
            )

            # Assert: File that succeeds after retry must show as successful
            self.assertTrue(
                success,
                "File that succeeds after retry MUST be marked as success - "
                "this was the exact bug that caused 2-hour debugging session",
            )
            self.assertIsNotNone(
                result,
                "Successful retry must return a result (the new filename)",
            )

            # Assert: Retry logic was executed (show_info called with retry message)
            self.display_context.show_info.assert_called()
            retry_calls = [call for call in self.display_context.show_info.call_args_list]
            self.assertTrue(
                any("Successfully processed after retry" in str(call) for call in retry_calls),
                "User must see confirmation that file was recovered after retry",
            )

    @pytest.mark.integration
    @pytest.mark.golden_path
    def test_batch_success_statistics_accuracy(self):
        """Test that progress statistics accurately reflect processing results."""
        # Create multiple test files
        test_files = []
        for i in range(3):
            file_path = os.path.join(self.input_dir, f"test_file_{i}.pdf")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Test content {i}")
            test_files.append((file_path, f"test_file_{i}.pdf"))

        success_count = 0
        results = []

        with patch("orchestration.workflow_processor._extract_file_content") as mock_extract:
            mock_extract.return_value = ("Extracted content", "")

            # Process all files
            for file_path, filename in test_files:
                success, result = process_file_enhanced_core(
                    input_path=file_path,
                    filename=filename,
                    unprocessed_folder=self.unprocessed_dir,
                    renamed_folder=self.output_dir,
                    progress_f=self.progress_f,
                    ocr_lang="eng",
                    ai_client=self.ai_client,
                    organizer=self.organizer,
                    display_context=self.display_context,
                )
                results.append((success, result))
                if success:
                    success_count += 1

        # Assert: All files processed successfully
        self.assertEqual(success_count, 3, "All test files should process successfully")
        self.assertTrue(
            all(success for success, _ in results),
            "Each individual file processing must return success=True for accurate statistics",
        )

    @pytest.mark.integration
    @pytest.mark.error_condition
    def test_permanent_failure_determination_accuracy(self):
        """Test that permanently failed files are correctly identified as failures."""
        with patch("orchestration.workflow_processor._extract_file_content") as mock_extract:
            # Make extraction fail with permanent error (unsupported format)
            mock_extract.side_effect = ValueError("Unsupported file format")

            # Act: Process file that should permanently fail
            success, result = process_file_enhanced_core(
                input_path=self.test_file_path,
                filename="test_document.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.output_dir,
                progress_f=self.progress_f,
                ocr_lang="eng",
                ai_client=self.ai_client,
                organizer=self.organizer,
                display_context=self.display_context,
            )

            # Assert: Permanent failure is correctly identified
            self.assertFalse(
                success,
                "File that permanently fails must return success=False",
            )
            self.assertIsNone(
                result,
                "Failed processing must not return a result",
            )

            # Assert: File was moved to unprocessed folder
            self.organizer.file_manager.safe_move.assert_called_with(
                self.test_file_path, os.path.join(self.unprocessed_dir, "test_document.pdf")
            )

            # Assert: Error message was shown
            self.display_context.show_error.assert_called()

    @pytest.mark.integration
    @pytest.mark.regression
    def test_retry_success_display_integration(self):
        """REGRESSION TEST: Prevent files succeeding after retries from showing as failures.
        
        This specific test prevents the 2-hour debugging bug from recurring.
        """
        retry_handler = create_retry_handler(max_attempts=3)

        # Simulate antivirus scan causing temporary permission error
        call_count = 0

        def mock_extract_antivirus_scenario(input_path, ocr_lang, display_context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:  # First attempt fails
                raise PermissionError("[Errno 13] Permission denied: access denied")  # Simulates antivirus lock
            else:  # Second attempt succeeds
                return "Document content after antivirus scan", ""

        with patch(
            "orchestration.workflow_processor._extract_file_content",
            side_effect=mock_extract_antivirus_scenario,
        ):

            # Act: Process file with antivirus lock scenario
            success, result = process_file_with_retry(
                input_path=self.test_file_path,
                filename="antivirus_locked.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.output_dir,
                progress_f=self.progress_f,
                ocr_lang="eng",
                ai_client=self.ai_client,
                organizer=self.organizer,
                display_context=self.display_context,
                retry_handler=retry_handler,
            )

            # Assert: CRITICAL - Success after retry must be reported correctly
            self.assertTrue(
                success,
                "REGRESSION BUG: Files that succeed after antivirus/temporary errors "
                "must be reported as successful, not failed",
            )

            # Assert: Retry statistics are accurate
            stats = retry_handler.get_stats()
            self.assertEqual(
                stats.successful_retries,
                1,
                "Retry handler must accurately track successful recovery",
            )
            self.assertEqual(
                stats.files_with_recoverable_issues,
                1,
                "Must track files that had recoverable issues for user reporting",
            )

            # Assert: User sees appropriate recovery messaging
            info_calls = self.display_context.show_info.call_args_list
            recovery_message_found = any(
                "Successfully processed after retry" in str(call) for call in info_calls
            )
            self.assertTrue(
                recovery_message_found,
                "User must be informed when files recover after temporary issues",
            )


if __name__ == "__main__":
    unittest.main()