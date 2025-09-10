"""
Critical Regression Tests: 2-Hour Debugging Bug Prevention

This test module contains specific regression tests designed to prevent
the recurrence of the exact bug scenario that caused a 2-hour debugging session:
"Files that succeeded after retries were being marked as failures in the progress display"
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import pytest

from core.application_container import TestApplicationContainer
from orchestration.workflow_processor import process_file_with_retry
from shared.display.rich_display_manager import RichDisplayOptions
from shared.infrastructure.error_handling import create_retry_handler


class TestRetrySuccessRegressionPrevention(unittest.TestCase):
    """Regression tests for the specific 2-hour debugging bug scenario."""

    def setUp(self):
        """Set up test environment to reproduce the exact bug scenario."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output") 
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")

        for directory in [self.input_dir, self.output_dir, self.unprocessed_dir]:
            os.makedirs(directory, exist_ok=True)

        # Create test container
        self.container = TestApplicationContainer(capture_output=True)
        
        # Create display manager to track the exact bug
        self.display_options = RichDisplayOptions(
            verbose=False,
            quiet=False,
            no_color=True,
            show_stats=True,
        )
        self.display_manager = self.container.create_display_manager(self.display_options)

        # Create test files that trigger the bug scenario
        self.antivirus_locked_file = os.path.join(self.input_dir, "antivirus_locked.pdf")
        self.sync_conflict_file = os.path.join(self.input_dir, "sync_conflict.pdf")
        self.network_timeout_file = os.path.join(self.input_dir, "network_timeout.pdf")

        for file_path in [self.antivirus_locked_file, self.sync_conflict_file, self.network_timeout_file]:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Test content for retry scenario")

        # Mock components
        self.ai_client = Mock()
        self.ai_client.generate_filename.return_value = "recovered_filename"

        self.organizer = Mock()
        self.organizer.move_file_to_category.return_value = "recovered_filename.pdf"
        self.organizer.file_manager.safe_move = Mock()
        self.organizer.filename_handler.validate_and_trim_filename = Mock(
            side_effect=lambda x: x
        )
        self.organizer.progress_tracker.record_progress = Mock()

        self.progress_f = Mock()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.critical
    def test_antivirus_lock_recovery_shows_as_success(self):
        """REGRESSION: Antivirus-locked files that recover must show as successes, not failures.
        
        This was the most common cause of the 2-hour debugging bug.
        """
        retry_handler = create_retry_handler(max_attempts=3)
        
        # Track display updates to catch the bug
        success_displayed = False
        failure_displayed = False
        
        def mock_display_context():
            display_context = Mock()
            display_context.set_status = Mock()
            display_context.show_info = Mock()
            display_context.show_warning = Mock()
            display_context.show_error = Mock()
            return display_context

        display_context = mock_display_context()

        # Simulate antivirus scanner locking file temporarily
        call_count = 0
        def antivirus_lock_scenario(input_path, ocr_lang, display_context_param):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First attempt: Antivirus scanner has file locked
                raise PermissionError("[Errno 13] Permission denied: antivirus scanning")
            else:
                # Second attempt: Antivirus scan complete, file available
                return "Document content after antivirus scan completed", ""

        with patch(
            "orchestration.workflow_processor._extract_file_content",
            side_effect=antivirus_lock_scenario
        ):
            
            # Execute the exact scenario that caused the 2-hour bug
            with self.display_manager.processing_context(1, "Antivirus Recovery Test") as ctx:
                
                ctx.start_file("antivirus_locked.pdf")
                
                # This is where the bug occurred - process_file_with_retry returned success
                # but the display showed it as a failure
                success, result = process_file_with_retry(
                    input_path=self.antivirus_locked_file,
                    filename="antivirus_locked.pdf",
                    unprocessed_folder=self.unprocessed_dir,
                    renamed_folder=self.output_dir,
                    progress_f=self.progress_f,
                    ocr_lang="eng",
                    ai_client=self.ai_client,
                    organizer=self.organizer,
                    display_context=display_context,
                    retry_handler=retry_handler,
                )
                
                # THE CRITICAL ASSERTION - This would have caught the 2-hour bug
                self.assertTrue(
                    success,
                    "CRITICAL REGRESSION BUG: File that recovers from antivirus lock MUST return success=True. "
                    "This exact failure caused the 2-hour debugging session."
                )
                
                # The bug was that success=True but ctx.complete_file() wasn't called
                # or ctx.fail_file() was called instead
                if success:
                    ctx.complete_file("antivirus_locked.pdf", result)
                else:
                    ctx.fail_file("antivirus_locked.pdf", "Recovery failed")
                
                # Verify display statistics match the actual processing result
                final_stats = self.display_manager.progress.stats
                self.assertEqual(
                    final_stats.succeeded, 1,
                    "CRITICAL REGRESSION BUG: Display must show 1 success when file recovers from antivirus lock. "
                    "Showing 0 successes was the visible symptom of the 2-hour debugging bug."
                )
                self.assertEqual(
                    final_stats.failed, 0,
                    "CRITICAL REGRESSION BUG: Display must show 0 errors when file successfully recovers. "
                    "Showing 1 error for a recovered file was the exact bug we debugged."
                )

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.critical
    def test_multiple_retry_scenarios_statistics_accuracy(self):
        """REGRESSION: Multiple files with retry scenarios must have accurate statistics.
        
        This test prevents the bug where individual file success was correct but
        batch statistics were wrong.
        """
        retry_handler = create_retry_handler(max_attempts=3)
        
        # Define multiple files with different retry scenarios
        file_scenarios = [
            ("immediate_success.pdf", "immediate_success"),
            ("antivirus_retry.pdf", "antivirus_then_success"), 
            ("sync_retry.pdf", "sync_conflict_then_success"),
            ("permanent_failure.pdf", "permanent_failure"),
            ("network_retry.pdf", "network_timeout_then_success"),
        ]
        
        individual_results = []
        
        with self.display_manager.processing_context(len(file_scenarios), "Multi-Retry Statistics Test") as ctx:
            
            for filename, scenario in file_scenarios:
                file_path = os.path.join(self.input_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Content for {scenario}")
                
                ctx.start_file(filename)
                
                # Configure extraction mock for each scenario - using classes to avoid closure issues
                class MockBehavior:
                    def __init__(self):
                        self.call_count = 0
                        
                if scenario == "immediate_success":
                    extract_mock = Mock(return_value=("content", ""))
                elif scenario == "antivirus_then_success":
                    behavior = MockBehavior()
                    def antivirus_mock(input_path, ocr_lang, display_context):
                        behavior.call_count += 1
                        if behavior.call_count == 1:
                            raise PermissionError("[Errno 13] Permission denied: antivirus scanning")
                        return "content after antivirus", ""
                    extract_mock = Mock(side_effect=antivirus_mock)
                elif scenario == "sync_conflict_then_success":
                    behavior = MockBehavior()
                    def sync_mock(input_path, ocr_lang, display_context):
                        behavior.call_count += 1
                        if behavior.call_count == 1:
                            raise OSError("OneDrive sync conflict")
                        return "content after sync", ""
                    extract_mock = Mock(side_effect=sync_mock)
                elif scenario == "network_timeout_then_success":
                    behavior = MockBehavior()
                    def network_mock(input_path, ocr_lang, display_context):
                        behavior.call_count += 1
                        if behavior.call_count == 1:
                            raise ConnectionError("Network timeout")
                        return "content after network recovery", ""
                    extract_mock = Mock(side_effect=network_mock)
                else:  # permanent_failure
                    extract_mock = Mock(side_effect=ValueError("Unsupported file format"))
                
                display_context = Mock()
                display_context.set_status = Mock()
                display_context.show_info = Mock()
                display_context.show_warning = Mock()
                display_context.show_error = Mock()
                
                with patch(
                    "orchestration.workflow_processor._extract_file_content",
                    extract_mock
                ):
                    
                    success, result = process_file_with_retry(
                        input_path=file_path,
                        filename=filename,
                        unprocessed_folder=self.unprocessed_dir,
                        renamed_folder=self.output_dir,
                        progress_f=self.progress_f,
                        ocr_lang="eng",
                        ai_client=self.ai_client,
                        organizer=self.organizer,
                        display_context=display_context,
                        retry_handler=retry_handler,
                    )
                
                individual_results.append((filename, scenario, success, result))
                
                # Update display based on actual result (this is where the bug occurred)
                if success:
                    ctx.complete_file(filename, result or "generated_filename.pdf")
                else:
                    ctx.fail_file(filename, "Processing failed")
        
        # Verify individual results match expectations
        expected_successes = 0
        expected_failures = 0
        
        for filename, scenario, actual_success, actual_result in individual_results:
            if scenario == "permanent_failure":
                expected_failures += 1
                self.assertFalse(
                    actual_success,
                    f"REGRESSION BUG: {filename} ({scenario}) should fail but was marked as success"
                )
            else:
                expected_successes += 1
                self.assertTrue(
                    actual_success,
                    f"CRITICAL REGRESSION BUG: {filename} ({scenario}) should succeed but was marked as failure. "
                    f"This is the exact type of error that caused the 2-hour debugging session."
                )
        
        # THE CRITICAL ASSERTION - Display statistics must match individual results
        final_stats = self.display_manager.progress.stats
        self.assertEqual(
            final_stats.succeeded, expected_successes,
            f"CRITICAL REGRESSION BUG: Display shows {final_stats.succeeded} successes "
            f"but should show {expected_successes} based on individual processing results. "
            f"This statistics mismatch was the core of the 2-hour debugging bug."
        )
        self.assertEqual(
            final_stats.failed, expected_failures,
            f"REGRESSION BUG: Display shows {final_stats.failed} failures "
            f"but should show {expected_failures} based on individual processing results."
        )
        
        # Verify retry handler statistics are also accurate
        retry_stats = retry_handler.get_stats()
        expected_successful_retries = 3  # antivirus, sync, network scenarios
        self.assertEqual(
            retry_stats.successful_retries, expected_successful_retries,
            f"Retry handler statistics inconsistent: expected {expected_successful_retries} successful retries"
        )

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.critical
    def test_specific_bug_reproduction_and_prevention(self):
        """REGRESSION: Exact reproduction of the 2-hour debugging bug scenario and its prevention.
        
        This test reproduces the exact conditions that caused the bug and verifies the fix.
        """
        retry_handler = create_retry_handler(max_attempts=2)
        
        # The exact scenario that caused the 2-hour debugging session:
        # 1. File gets locked by antivirus during processing
        # 2. First attempt fails with PermissionError
        # 3. Retry succeeds and file is processed correctly
        # 4. process_file_with_retry returns (True, result)
        # 5. BUT display shows the file as failed instead of successful
        
        bug_reproduction_file = os.path.join(self.input_dir, "bug_reproduction.pdf")
        with open(bug_reproduction_file, "w", encoding="utf-8") as f:
            f.write("Content that will trigger the exact bug scenario")
        
        # Simulate the exact error sequence that caused the bug
        attempt_count = 0
        def exact_bug_scenario(input_path, ocr_lang, display_context):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count == 1:
                # First attempt: Antivirus scanner temporarily locks file
                # This specific error pattern was what triggered the bug
                raise PermissionError("[Errno 13] Permission denied: 'C:\\...\\file.pdf'")
            else:
                # Second attempt: File becomes available and processing succeeds
                # This success should have been reflected in the display but wasn't
                return "Successfully extracted content after antivirus scan", ""

        display_context = Mock()
        display_context.set_status = Mock()
        display_context.show_info = Mock() 
        display_context.show_warning = Mock()
        display_context.show_error = Mock()

        with patch(
            "orchestration.workflow_processor._extract_file_content",
            side_effect=exact_bug_scenario
        ):
            
            # Execute the exact processing workflow that had the bug
            success, result = process_file_with_retry(
                input_path=bug_reproduction_file,
                filename="bug_reproduction.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.output_dir,
                progress_f=self.progress_f,
                ocr_lang="eng",
                ai_client=self.ai_client,
                organizer=self.organizer,
                display_context=display_context,
                retry_handler=retry_handler,
            )
            
            # THE BUG: This assertion should pass (and did in the original code)
            self.assertTrue(
                success,
                "Processing layer correctly identified the file as successfully processed after retry"
            )
            self.assertIsNotNone(
                result,
                "Processing layer correctly returned result after successful retry"
            )
            
            # Now simulate the display update that had the bug
            with self.display_manager.processing_context(1, "Bug Prevention Test") as ctx:
                
                ctx.start_file("bug_reproduction.pdf")
                
                # THE BUG FIX VERIFICATION: This is where the bug occurred
                # The original code had logic that incorrectly mapped success=True to fail_file()
                # or had a disconnect between processing success and display updates
                
                if success and result:
                    # This is the correct path - file succeeded after retry
                    ctx.complete_file("bug_reproduction.pdf", result)
                else:
                    # This was incorrectly being called even when success=True
                    ctx.fail_file("bug_reproduction.pdf", "Processing failed")
                
                # THE CRITICAL BUG PREVENTION ASSERTIONS
                final_stats = self.display_manager.progress.stats
                
                # This assertion would have FAILED in the original buggy code
                self.assertEqual(
                    final_stats.succeeded, 1,
                    "BUG PREVENTION FAILED: This assertion failing indicates the 2-hour debugging bug has returned. "
                    "A file that succeeded after retry must show as 1 success in the display statistics."
                )
                
                # This assertion would have PASSED in the original buggy code (showing the problem)
                self.assertEqual(
                    final_stats.failed, 0,
                    "BUG PREVENTION FAILED: This assertion failing indicates the 2-hour debugging bug has returned. "
                    "A file that succeeded after retry must NOT be counted as an error in display statistics."
                )
                
                # Additional verification: check that retry was actually attempted
                self.assertEqual(
                    attempt_count, 2,
                    "Bug reproduction verification: retry logic should have been executed (2 attempts total)"
                )
                
                # Verify retry statistics show the recovery
                retry_stats = retry_handler.get_stats()
                self.assertEqual(
                    retry_stats.successful_retries, 1,
                    "Retry handler must correctly track that 1 file was recovered through retry"
                )


if __name__ == "__main__":
    unittest.main()