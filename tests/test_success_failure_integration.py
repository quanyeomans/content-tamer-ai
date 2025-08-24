"""
Critical Integration Tests for Success/Failure Determination

Tests that should have caught the 2-hour debugging bug.
These tests verify the complete success/failure flow from file processing
through retry handling to progress display.
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch, Mock
from io import StringIO

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from core.file_processor import process_file_enhanced, process_file_enhanced_core
from utils.error_handling import create_retry_handler
from utils.display_manager import DisplayManager, DisplayOptions
from core.application import _process_files_batch


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
        with open(self.test_file, 'wb') as f:
            f.write(b'%PDF-1.4\ntest content\n%EOF')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_successful_processing_returns_true_and_filename(self):
        """CRITICAL: Successful processing should return (True, filename)."""
        mock_organizer = Mock()
        mock_organizer.file_manager.safe_move = Mock()
        
        # Mock successful content extraction and filename generation
        with patch('core.file_processor._extract_file_content') as mock_extract:
            with patch('core.file_processor._generate_filename') as mock_gen:
                with patch('core.file_processor._move_file_only') as mock_move:
                    mock_extract.return_value = ("content", None)
                    mock_gen.return_value = "generated_name"
                    mock_move.return_value = "final_name.pdf"
                    
                    mock_display_context = Mock()
                    
                    success, result = process_file_enhanced_core(
                        self.test_file,
                        "test.pdf",
                        self.unprocessed_dir,
                        self.processed_dir,
                        Mock(),  # progress_f
                        "eng",
                        Mock(),  # ai_client
                        mock_organizer,
                        mock_display_context
                    )
                    
                    self.assertTrue(success, "Successful processing should return True")
                    self.assertEqual(result, "final_name.pdf", "Should return final filename")

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
            filename="test.pdf"
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
        
        self.assertEqual(final_success_count, initial_success_count + 1,
                        "complete_file should increment success count")
        self.assertEqual(display_manager.progress.stats.failed, 0,
                        "Should have no failures")

    def test_fail_file_increments_error_count(self):
        """CRITICAL: fail_file should increment error counter."""
        output = StringIO()
        options = DisplayOptions(quiet=False, file=output)  # Use full display, not simple
        display_manager = DisplayManager(options)
        
        initial_error_count = display_manager.progress.stats.failed
        
        with display_manager.processing_context(total_files=1) as ctx:
            ctx.fail_file("test.pdf", "Processing failed")
            
        final_error_count = display_manager.progress.stats.failed
        
        self.assertEqual(final_error_count, initial_error_count + 1,
                        "fail_file should increment error count")
        self.assertEqual(display_manager.progress.stats.success_count, 0,
                        "Should have no successes")

    @patch('core.application.process_file_enhanced')
    def test_batch_processing_success_path(self, mock_process):
        """CRITICAL: Batch processing should take success path when files succeed."""
        mock_process.return_value = (True, "renamed_file.pdf")
        
        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)
        
        mock_organizer = Mock()
        mock_retry_handler = Mock()
        
        with patch('builtins.open', Mock(return_value=Mock(__enter__=Mock(return_value=Mock()), __exit__=Mock()))):
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
                session_retry_handler=mock_retry_handler
            )
        
        self.assertTrue(success, "Batch processing should succeed")
        self.assertEqual(successful_count, 1, "Should have 1 successful file")
        self.assertEqual(failed_count, 0, "Should have 0 failed files")
        self.assertEqual(len(errors), 0, "Should have no error details")

    @patch('core.application.process_file_enhanced')
    def test_batch_processing_failure_path(self, mock_process):
        """CRITICAL: Batch processing should take failure path when files fail."""
        mock_process.return_value = (False, None)
        
        output = StringIO()
        options = DisplayOptions(quiet=True, file=output)
        display_manager = DisplayManager(options)
        
        mock_organizer = Mock()
        mock_organizer.file_manager.safe_move = Mock()
        mock_retry_handler = Mock()
        
        with patch('builtins.open', Mock(return_value=Mock(__enter__=Mock(return_value=Mock()), __exit__=Mock()))):
            with patch('os.path.exists', return_value=True):
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
                    session_retry_handler=mock_retry_handler
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
        self.assertEqual(display_manager.progress.stats.success_count, 2,
                        "Should have exactly 2 successes")
        self.assertEqual(display_manager.progress.stats.failed, 1,
                        "Should have exactly 1 failure")
        self.assertEqual(display_manager.progress.stats.completed, 3,
                        "Should have processed 3 files total")


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
            filename="locked_file.pdf"
        )
        
        # This is the EXACT assertion that should have caught our bug
        self.assertTrue(success, 
                       "Files that succeed after retries MUST return success=True")
        self.assertEqual(result, "successfully_processed_file.pdf",
                        "Should return the successful processing result")
        self.assertIsNone(error_classification,
                         "Successful retries should not have error classification")


if __name__ == '__main__':
    unittest.main()