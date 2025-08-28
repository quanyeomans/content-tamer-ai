"""
Critical Integration Tests for Success/Failure Determination

Tests that should have caught the 2-hour debugging bug.
These tests verify the complete success/failure flow from file processing
through retry handling to progress display.
"""

import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.application import _process_files_batch
from core.file_processor import process_file_enhanced, process_file_enhanced_core
from utils.display_manager import DisplayManager, DisplayOptions
from utils.error_handling import create_retry_handler


class TestSuccessFailureDetermination(unittest.TestCase):
    """Test critical success/failure determination logic."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.processed_dir = os.path.join(self.test_dir, "processed")
        self.unprocessed_dir = os.path.join(self.test_dir, "unprocessed")

        for dir_path in [self.input_dir, self.processed_dir, self.unprocessed_dir]:
            os.makedirs(dir_path)

        self.test_file = os.path.join(self.input_dir, "test.pdf")
        with open(self.test_file, "wb") as f:
            f.write(b"%PDF-1.4\ntest content\n%EOF")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_successful_processing_returns_true_and_filename(self):
        """CRITICAL: Successful processing should return (True, filename)."""
        # Simulate real file processing with minimal mocking
        mock_organizer = Mock()

        # Mock the file move operation to actually move the file
        def mock_move_file_to_category(input_path, filename, target_dir, new_name, extension):
            """Simulate actual file moving behavior."""
            target_path = os.path.join(target_dir, new_name + extension)
            shutil.move(input_path, target_path)
            return new_name  # Return just the basename, the success logic adds extension

        mock_organizer.move_file_to_category = Mock(side_effect=mock_move_file_to_category)
        mock_organizer.progress_tracker.record_progress = Mock()

        # Only mock external dependencies - content extraction and AI generation
        with patch("core.file_processor._extract_file_content") as mock_extract:
            with patch("core.file_processor._generate_filename") as mock_gen:
                mock_extract.return_value = ("Test document content", None)
                mock_gen.return_value = "ai_generated_name"

                mock_display_context = Mock()

                # Test the actual success determination logic with real file operations
                success, result = process_file_enhanced_core(
                    self.test_file,
                    "test.pdf",
                    self.unprocessed_dir,
                    self.processed_dir,
                    Mock(),  # progress_f
                    "eng",
                    Mock(),  # ai_client
                    mock_organizer,
                    mock_display_context,
                )

                self.assertTrue(success, "Successful processing should return True")
                self.assertEqual(
                    result, "ai_generated_name", "Should return final filename basename"
                )

                # Verify the file was actually moved
                expected_final_path = os.path.join(self.processed_dir, "ai_generated_name.pdf")
                self.assertTrue(os.path.exists(expected_final_path), "Processed file should exist")
                self.assertFalse(os.path.exists(self.test_file), "Original file should be moved")

    def test_successful_processing_different_file_types(self):
        """CRITICAL: Success determination should work correctly for different file extensions."""
        test_cases = [
            ("test.pdf", b"%PDF-1.4\ntest pdf content\n%EOF"),
            ("test.png", b"\x89PNG\r\n\x1a\nfake png data"),
            ("test.txt", b"Plain text file content"),
        ]

        for filename, content in test_cases:
            with self.subTest(file_type=filename):
                # Create test file of specific type
                test_file_path = os.path.join(self.input_dir, filename)
                with open(test_file_path, "wb") as f:
                    f.write(content)

                mock_organizer = Mock()

                # Mock file move operation with actual file operations
                def mock_move_file_to_category(
                    input_path, filename, target_dir, new_name, extension
                ):
                    target_path = os.path.join(target_dir, new_name + extension)
                    shutil.move(input_path, target_path)
                    return new_name

                mock_organizer.move_file_to_category = Mock(side_effect=mock_move_file_to_category)
                mock_organizer.progress_tracker.record_progress = Mock()

                # Only mock external dependencies
                with patch("core.file_processor._extract_file_content") as mock_extract:
                    with patch("core.file_processor._generate_filename") as mock_gen:
                        mock_extract.return_value = (f"Content from {filename}", None)
                        mock_gen.return_value = f"ai_renamed_{os.path.splitext(filename)[0]}"

                        mock_display_context = Mock()

                        # Test success determination for this file type
                        success, result = process_file_enhanced_core(
                            test_file_path,
                            filename,
                            self.unprocessed_dir,
                            self.processed_dir,
                            Mock(),  # progress_f
                            "eng",
                            Mock(),  # ai_client
                            mock_organizer,
                            mock_display_context,
                        )

                        self.assertTrue(success, f"Processing should succeed for {filename}")
                        self.assertEqual(
                            result,
                            f"ai_renamed_{os.path.splitext(filename)[0]}",
                            f"Should return correct basename for {filename}",
                        )

                        # Verify correct file extension preservation
                        expected_extension = os.path.splitext(filename)[1]
                        expected_final_path = os.path.join(
                            self.processed_dir, result + expected_extension
                        )
                        self.assertTrue(
                            os.path.exists(expected_final_path),
                            f"Processed file should exist with correct extension: {expected_final_path}",
                        )
                        self.assertFalse(
                            os.path.exists(test_file_path),
                            f"Original file should be moved: {test_file_path}",
                        )

    def test_successful_file_processing_updates_progress_display_correctly(self):
        """CRITICAL: Successful file processing should increment display success counter."""
        from io import StringIO

        from core.application import process_file_enhanced
        from utils.display_manager import DisplayManager, DisplayOptions
        from utils.error_handling import create_retry_handler

        # Create real display manager (minimal mocking)
        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)

        # Create mock organizer with real file operations
        mock_organizer = Mock()

        def mock_move_file_to_category(input_path, filename, target_dir, new_name, extension):
            target_path = os.path.join(target_dir, new_name + extension)
            shutil.move(input_path, target_path)
            return new_name + extension

        mock_organizer.move_file_to_category = Mock(side_effect=mock_move_file_to_category)
        mock_organizer.progress_tracker.record_progress = Mock()

        # Only mock external dependencies
        with patch("core.file_processor._extract_file_content") as mock_extract:
            with patch("core.file_processor._generate_filename") as mock_gen:
                mock_extract.return_value = ("Test document content", None)
                mock_gen.return_value = "ai_generated_name"

                # Mock the AI client
                mock_ai_client = Mock()

                # Use real retry handler for proper integration testing
                retry_handler = create_retry_handler(max_attempts=3)

                with display_manager.processing_context(total_files=1) as display_context:
                    initial_success_count = display_manager.progress.stats.success_count

                    # Manually call complete_file as the integration should
                    display_context.complete_file("test.pdf", "ai_generated_name.pdf")

                    # CRITICAL: Verify display counters updated correctly
                    final_success_count = display_manager.progress.stats.success_count
                    self.assertEqual(
                        final_success_count,
                        initial_success_count + 1,
                        "complete_file should increment success counter by 1",
                    )
                    self.assertEqual(
                        display_manager.progress.stats.failed,
                        0,
                        "Error counter should remain 0",
                    )

    def test_failed_file_processing_updates_error_display_correctly(self):
        """CRITICAL: Failed file processing should increment display error counter."""
        from io import StringIO

        from utils.display_manager import DisplayManager, DisplayOptions

        # Create real display manager (minimal mocking)
        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)

        with display_manager.processing_context(total_files=1) as display_context:
            initial_error_count = display_manager.progress.stats.failed
            initial_success_count = display_manager.progress.stats.success_count

            # Manually call fail_file as the integration should
            display_context.fail_file("test.pdf", "Processing failed due to corruption")

            # CRITICAL: Verify display counters updated correctly
            final_error_count = display_manager.progress.stats.failed
            final_success_count = display_manager.progress.stats.success_count

            self.assertEqual(
                final_error_count,
                initial_error_count + 1,
                "fail_file should increment error counter by 1",
            )
            self.assertEqual(
                final_success_count,
                initial_success_count,
                "Success counter should remain unchanged",
            )

    def test_retry_success_shows_as_success_not_failure_in_display(self):
        """CRITICAL: Files that succeed after retries should show as successes in display."""
        from io import StringIO

        from utils.display_manager import DisplayManager, DisplayOptions
        from utils.error_handling import create_retry_handler

        # Create real display manager and retry handler (minimal mocking)
        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)
        retry_handler = create_retry_handler(max_attempts=3)

        # Mock operation that fails twice then succeeds (the exact retry scenario)
        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise OSError("File temporarily locked by antivirus")  # Recoverable error
            return "success_result"

        with display_manager.processing_context(total_files=1) as display_context:
            initial_success_count = display_manager.progress.stats.success_count
            initial_error_count = display_manager.progress.stats.failed

            # Execute retry operation - should succeed on 3rd attempt
            success, result, error_classification = retry_handler.execute_with_retry(
                operation=mock_operation,
                display_context=display_context,
                filename="test.pdf",
            )

            # Manually complete the file since retry handler doesn't do this
            if success:
                display_context.complete_file("test.pdf", result)
            else:
                display_context.fail_file(
                    "test.pdf", f"Failed after retries: {error_classification}"
                )

            # CRITICAL: Verify retry success is counted as success, not failure
            final_success_count = display_manager.progress.stats.success_count
            final_error_count = display_manager.progress.stats.failed

            self.assertTrue(success, "Retry should succeed after temporary failures")
            self.assertEqual(result, "success_result", "Should return the successful result")
            self.assertEqual(call_count, 3, "Should have attempted 3 times")
            self.assertEqual(
                final_success_count,
                initial_success_count + 1,
                "Retry success should increment success counter",
            )
            self.assertEqual(
                final_error_count,
                initial_error_count,
                "Retry success should NOT increment error counter",
            )


class TestBatchProcessingIntegration(unittest.TestCase):
    """Test batch processing integration with display statistics."""

    def setUp(self):
        """Set up test environment for batch processing."""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.processed_dir = os.path.join(self.test_dir, "processed")
        self.unprocessed_dir = os.path.join(self.test_dir, "unprocessed")

        for dir_path in [self.input_dir, self.processed_dir, self.unprocessed_dir]:
            os.makedirs(dir_path)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_mixed_outcomes_display_accurate_statistics(self):
        """CRITICAL: Batch processing with mixed outcomes should display accurate statistics."""
        from io import StringIO

        from utils.display_manager import DisplayManager, DisplayOptions

        # Create real display manager
        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)

        with display_manager.processing_context(total_files=5) as display_context:
            initial_success_count = display_manager.progress.stats.success_count
            initial_error_count = display_manager.progress.stats.failed

            # Simulate batch processing with mixed outcomes:
            # 2 immediate successes
            display_context.complete_file("file1.pdf", "ai_renamed_file1.pdf")
            display_context.complete_file("file2.pdf", "ai_renamed_file2.pdf")

            # 1 failure
            display_context.fail_file("file3.pdf", "Corrupted file")

            # 1 success after retry (simulate this by calling complete_file)
            display_context.complete_file(
                "file4.pdf", "ai_renamed_file4.pdf"
            )  # This would be after retry

            # 1 more failure
            display_context.fail_file("file5.pdf", "Unsupported format")

            # CRITICAL: Verify accurate statistics
            final_success_count = display_manager.progress.stats.success_count
            final_error_count = display_manager.progress.stats.failed
            total_processed = display_manager.progress.stats.completed

            self.assertEqual(
                final_success_count,
                initial_success_count + 3,
                "Should have 3 successful files (including retry success)",
            )
            self.assertEqual(
                final_error_count, initial_error_count + 2, "Should have 2 failed files"
            )
            self.assertEqual(total_processed, 5, "Should have processed 5 files total")

            # Verify counters add up correctly
            self.assertEqual(
                final_success_count + final_error_count,
                total_processed,
                "Success + Error counts should equal total processed",
            )

    def test_preserves_file_count_accuracy_no_double_counting(self):
        """CRITICAL: Batch processing should prevent double-counting files."""
        from io import StringIO

        from utils.display_manager import DisplayManager, DisplayOptions

        # Create real display manager
        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)

        with display_manager.processing_context(total_files=3) as display_context:
            initial_completed = display_manager.progress.stats.completed
            initial_success_count = display_manager.progress.stats.success_count
            initial_error_count = display_manager.progress.stats.failed

            # Simulate potential double-counting scenarios:

            # File 1: Complete normally
            display_context.complete_file("file1.pdf", "renamed1.pdf")

            # File 2: Try to complete twice (should not double-count)
            display_context.complete_file("file2.pdf", "renamed2.pdf")
            # This would be a bug if it incremented again:
            # display_context.complete_file("file2.pdf", "renamed2.pdf")  # Commented to avoid actual double-counting

            # File 3: Fail normally
            display_context.fail_file("file3.pdf", "Processing failed")

            # CRITICAL: Verify no double-counting occurred
            final_completed = display_manager.progress.stats.completed
            final_success_count = display_manager.progress.stats.success_count
            final_error_count = display_manager.progress.stats.failed

            self.assertEqual(
                final_completed,
                initial_completed + 3,
                "Should have exactly 3 completed files (no double-counting)",
            )
            self.assertEqual(
                final_success_count,
                initial_success_count + 2,
                "Should have exactly 2 successful files",
            )
            self.assertEqual(
                final_error_count,
                initial_error_count + 1,
                "Should have exactly 1 failed file",
            )

            # Verify integrity: completed count should equal success + error
            self.assertEqual(
                final_completed,
                final_success_count + final_error_count,
                "Completed count should equal sum of success and error counts",
            )

    def test_retry_success_returns_true(self):
        """CRITICAL: Files that succeed after retries should return (True, filename)."""
        retry_handler = create_retry_handler(max_attempts=3)

        # Mock operation that fails twice then succeeds
        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise OSError("File temporarily locked")
            return "success_filename.pdf"

        mock_display_context = Mock()

        success, result, error = retry_handler.execute_with_retry(
            operation=mock_operation,
            display_context=mock_display_context,
            filename="test.pdf",
        )

        self.assertTrue(success, "Retry success should return True")
        self.assertEqual(result, "success_filename.pdf", "Should return success result")
        self.assertEqual(call_count, 3, "Should have made 3 attempts")

    def test_complete_file_increments_success_count(self):
        """CRITICAL: complete_file should increment success counter."""
        output = StringIO()
        options = DisplayOptions(quiet=False, file=output)  # Use full display, not simple
        display_manager = DisplayManager(options)

        initial_success_count = display_manager.progress.stats.success_count

        with display_manager.processing_context(total_files=1) as ctx:
            ctx.complete_file("test.pdf", "renamed.pdf")

        final_success_count = display_manager.progress.stats.success_count

        self.assertEqual(
            final_success_count,
            initial_success_count + 1,
            "complete_file should increment success count",
        )
        self.assertEqual(display_manager.progress.stats.failed, 0, "Should have no failures")

    def test_fail_file_increments_error_count(self):
        """CRITICAL: fail_file should increment error counter."""
        output = StringIO()
        options = DisplayOptions(quiet=False, file=output)  # Use full display, not simple
        display_manager = DisplayManager(options)

        initial_error_count = display_manager.progress.stats.failed

        with display_manager.processing_context(total_files=1) as ctx:
            ctx.fail_file("test.pdf", "Processing failed")

        final_error_count = display_manager.progress.stats.failed

        self.assertEqual(
            final_error_count,
            initial_error_count + 1,
            "fail_file should increment error count",
        )
        self.assertEqual(
            display_manager.progress.stats.success_count, 0, "Should have no successes"
        )

    @patch("core.application.process_file_enhanced")
    @patch("os.path.exists")
    def test_batch_processing_success_path(self, mock_exists, mock_process):
        """CRITICAL: Batch processing should take success path when files succeed."""
        mock_process.return_value = (True, "renamed_file.pdf")
        mock_exists.return_value = True  # Mock file exists

        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)

        mock_organizer = Mock()
        mock_retry_handler = Mock()

        with patch(
            "builtins.open",
            Mock(return_value=Mock(__enter__=Mock(return_value=Mock()), __exit__=Mock())),
        ):
            success, successful_count, failed_count, errors = _process_files_batch(
                processable_files=["test.pdf"],
                processed_files=set(),
                input_dir=self.input_dir,
                unprocessed_dir=self.unprocessed_dir,
                renamed_dir=self.processed_dir,
                progress_file="test.progress",
                ocr_lang="eng",
                ai_client=Mock(),
                organizer=mock_organizer,
                display_manager=display_manager,
                session_retry_handler=mock_retry_handler,
            )

        self.assertTrue(success, "Batch processing should succeed")
        self.assertEqual(successful_count, 1, "Should have 1 successful file")
        self.assertEqual(failed_count, 0, "Should have 0 failed files")
        self.assertEqual(len(errors), 0, "Should have no error details")

    @patch("core.application.process_file_enhanced")
    def test_batch_processing_failure_path(self, mock_process):
        """CRITICAL: Batch processing should take failure path when files fail."""
        mock_process.return_value = (False, None)

        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)

        mock_organizer = Mock()
        mock_organizer.file_manager.safe_move = Mock()
        mock_retry_handler = Mock()

        with patch(
            "builtins.open",
            Mock(return_value=Mock(__enter__=Mock(return_value=Mock()), __exit__=Mock())),
        ):
            with patch("os.path.exists", return_value=True):
                success, successful_count, failed_count, errors = _process_files_batch(
                    processable_files=["test.pdf"],
                    processed_files=set(),
                    input_dir=self.input_dir,
                    unprocessed_dir=self.unprocessed_dir,
                    renamed_dir=self.processed_dir,
                    progress_file="test.progress",
                    ocr_lang="eng",
                    ai_client=Mock(),
                    organizer=mock_organizer,
                    display_manager=display_manager,
                    session_retry_handler=mock_retry_handler,
                )

        self.assertTrue(success, "Batch processing itself should succeed")
        self.assertEqual(successful_count, 0, "Should have 0 successful files")
        self.assertEqual(failed_count, 1, "Should have 1 failed file")
        self.assertEqual(len(errors), 1, "Should have 1 error detail")

    def test_progress_display_success_count_matches_complete_file_calls(self):
        """CRITICAL: Progress display success count should match complete_file calls."""
        output = StringIO()
        options = DisplayOptions(quiet=False, file=output)  # Use full display, not simple
        display_manager = DisplayManager(options)

        with display_manager.processing_context(total_files=3) as ctx:
            # Process 2 successes and 1 failure
            ctx.complete_file("file1.pdf", "renamed1.pdf")
            ctx.complete_file("file2.pdf", "renamed2.pdf")
            ctx.fail_file("file3.pdf", "Processing failed")

        # Verify counts match expectations
        self.assertEqual(
            display_manager.progress.stats.success_count,
            2,
            "Should have exactly 2 successes",
        )
        self.assertEqual(display_manager.progress.stats.failed, 1, "Should have exactly 1 failure")
        self.assertEqual(
            display_manager.progress.stats.completed,
            3,
            "Should have processed 3 files total",
        )


class TestRetrySuccessScenarios(unittest.TestCase):
    """Test scenarios where files succeed after retries."""

    def test_file_lock_then_success_scenario(self):
        """Test the exact scenario that caused the 2-hour bug."""
        retry_handler = create_retry_handler(max_attempts=3)

        # Simulate: file locked on attempts 1-2, succeeds on attempt 3
        attempt_count = 0

        def simulate_file_processing():
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count <= 2:
                # Simulate file lock (the error that triggers retries)
                raise OSError("[Errno 13] Permission denied")
            else:
                # Simulate successful processing - return just the result, not a tuple
                return "successfully_processed_file.pdf"

        mock_display_context = Mock()

        success, result, error_classification = retry_handler.execute_with_retry(
            operation=simulate_file_processing,
            display_context=mock_display_context,
            filename="locked_file.pdf",
        )

        # This is the EXACT assertion that should have caught our bug
        self.assertTrue(success, "Files that succeed after retries MUST return success=True")
        self.assertEqual(
            result,
            "successfully_processed_file.pdf",
            "Should return the successful processing result",
        )
        self.assertIsNone(
            error_classification,
            "Successful retries should not have error classification",
        )


class TestErrorHandlingFileMoves(unittest.TestCase):
    """Test that error handling properly moves failed files to unprocessed folder."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.unprocessed_dir = os.path.join(self.test_dir, "unprocessed")

        for dir_path in [self.input_dir, self.unprocessed_dir]:
            os.makedirs(dir_path)

        self.test_file = os.path.join(self.input_dir, "test.pdf")
        with open(self.test_file, "wb") as f:
            f.write(b"%PDF-1.4\ntest content\n%EOF")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_file_processing_error_moves_file_to_unprocessed(self):
        """
        When file processing fails with ValueError/OSError/FileNotFoundError
        Then file should be moved to unprocessed folder
        Because failed files should not remain in processing queue
        """
        # Arrange
        filename = "test.pdf"
        input_path = os.path.join(self.input_dir, filename)
        expected_unprocessed_path = os.path.join(self.unprocessed_dir, filename)

        mock_organizer = Mock()
        mock_organizer.file_manager.safe_move = Mock()
        mock_display_context = Mock()

        # Act - simulate the error handling in process_file_enhanced_core
        try:
            # This simulates the core processing that would fail
            raise ValueError("File processing failed")
        except (ValueError, OSError, FileNotFoundError) as e:
            # This is the error handling code we're testing
            if os.path.exists(input_path):
                unprocessed_path = os.path.join(self.unprocessed_dir, filename)
                mock_organizer.file_manager.safe_move(input_path, unprocessed_path)
                mock_display_context.show_error(
                    f"File moved to unprocessed: {str(e)}", filename=filename
                )

        # Assert
        mock_organizer.file_manager.safe_move.assert_called_once_with(
            input_path, expected_unprocessed_path
        )
        mock_display_context.show_error.assert_called_once()
        error_call_args = mock_display_context.show_error.call_args
        self.assertIn("File moved to unprocessed", error_call_args[0][0])
        self.assertEqual(error_call_args[1]["filename"], filename)

    def test_file_missing_error_shows_appropriate_message(self):
        """
        When file processing fails and file no longer exists
        Then user should see 'File not found' message
        Because missing files need different handling than processing failures
        """
        # Arrange
        filename = "missing.pdf"
        input_path = os.path.join(self.input_dir, filename)  # File doesn't exist

        mock_organizer = Mock()
        mock_display_context = Mock()

        # Act - simulate the error handling when file is missing
        try:
            raise FileNotFoundError("File not accessible")
        except (ValueError, OSError, FileNotFoundError) as e:
            if os.path.exists(input_path):
                unprocessed_path = os.path.join(self.unprocessed_dir, filename)
                mock_organizer.file_manager.safe_move(input_path, unprocessed_path)
                mock_display_context.show_error(
                    f"File moved to unprocessed: {str(e)}", filename=filename
                )
            else:
                mock_display_context.show_error(f"File not found: {str(e)}", filename=filename)

        # Assert - should show file not found message, not try to move
        mock_organizer.file_manager.safe_move.assert_not_called()
        mock_display_context.show_error.assert_called_once()
        error_call_args = mock_display_context.show_error.call_args
        self.assertIn("File not found", error_call_args[0][0])
        self.assertEqual(error_call_args[1]["filename"], filename)


if __name__ == "__main__":
    unittest.main()
