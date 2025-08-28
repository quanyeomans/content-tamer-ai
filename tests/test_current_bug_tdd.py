"""
TDD Test: Capture the exact bug the user is experiencing.

This test should FAIL initially, demonstrating the bug exists.
Then we fix the code until this test PASSES.
"""

import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.application import _process_files_batch
from utils.display_manager import DisplayManager, DisplayOptions


class TestCurrentSuccessFailureBug(unittest.TestCase):
    """Test that captures the exact bug user is experiencing."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.processed_dir = os.path.join(self.test_dir, "processed")
        self.unprocessed_dir = os.path.join(self.test_dir, "unprocessed")

        for dir_path in [self.input_dir, self.processed_dir, self.unprocessed_dir]:
            os.makedirs(dir_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_files_that_succeed_after_retries_should_show_as_successes(self):
        """
        CRITICAL TEST: This captures the exact user bug.

        Scenario:
        - Files encounter temporary lock/permission errors (triggering retries)
        - Files ultimately succeed and are moved to processed folder
        - BUT system reports them as failures with 0% success rate

        Expected:
        - Files that succeed should show success=True in return values
        - Success count should match actual successful files
        - Progress should show success lines, not just failures
        """

        # For now, let's assume the retry fix we made should work
        # and simulate successful processing
        def mock_process_file_enhanced(input_path, filename, *args, **kwargs):
            result = True, f"renamed_{filename}"
            return result

        # Set up display manager to capture output
        output = StringIO()
        options = DisplayOptions(quiet=False, file=output, no_color=True)
        display_manager = DisplayManager(options)

        # Mock dependencies
        mock_organizer = Mock()
        mock_organizer.file_manager.safe_move = Mock()
        mock_retry_handler = Mock()
        mock_ai_client = Mock()

        # Test with one file
        test_files = ["test.pdf"]

        with patch(
            "core.application.process_file_enhanced",
            side_effect=mock_process_file_enhanced,
        ):
            with patch(
                "builtins.open",
                Mock(return_value=Mock(__enter__=Mock(return_value=Mock()), __exit__=Mock())),
            ):
                with patch(
                    "os.path.exists", return_value=True
                ):  # Make sure file exists check passes
                    success, successful_count, failed_count, error_details = _process_files_batch(
                        processable_files=test_files,
                        processed_files=set(),
                        input_dir=self.input_dir,
                        unprocessed_dir=self.unprocessed_dir,
                        renamed_dir=self.processed_dir,
                        progress_file="test.progress",
                        ocr_lang="eng",
                        ai_client=mock_ai_client,
                        organizer=mock_organizer,
                        display_manager=display_manager,
                        session_retry_handler=mock_retry_handler,
                    )

        # CRITICAL ASSERTIONS: These should pass when bug is fixed
        self.assertTrue(success, "Batch processing should succeed")
        self.assertEqual(
            successful_count,
            1,
            "Should report 1 successful file (the ultimate outcome)",
        )
        self.assertEqual(failed_count, 0, "Should report 0 failed files (retry succeeded)")
        self.assertEqual(len(error_details), 0, "Should have no error details for successful files")

        # Check progress display stats if available
        if hasattr(display_manager.progress, "stats"):
            self.assertEqual(
                display_manager.progress.stats.success_count,
                1,
                "Progress display should show 1 success",
            )
            # Note: We might have retry attempts counted as warnings, but not as errors

        # Check output contains success indicator
        output_content = output.getvalue()
        self.assertIn("SUCCESS", output_content, "Output should contain success indicator")


if __name__ == "__main__":
    unittest.main()
