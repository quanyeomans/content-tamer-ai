"""
Critical Integration Tests: Retry Handler ↔ Batch Processing Component Interactions

Tests the contract and state consistency between retry handling and batch processing
components to ensure user-observable behavior matches actual processing results.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import pytest

from core.application_container import TestApplicationContainer
from orchestration.workflow_processor import process_file_with_retry
from shared.infrastructure.error_handling import create_retry_handler


class TestRetryBatchProcessingIntegration(unittest.TestCase):
    """Integration tests for Retry Handler ↔ Batch Processing interactions."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")

        for directory in [self.input_dir, self.output_dir, self.unprocessed_dir]:
            os.makedirs(directory, exist_ok=True)

        # Create test container
        self.container = TestApplicationContainer(capture_output=True)

        # Mock components
        self.ai_client = Mock()
        self.ai_client.generate_filename.return_value = "generated_filename"

        self.organizer = Mock()
        self.organizer.move_file_to_category.return_value = "final_filename.pdf"
        self.organizer.file_manager.safe_move = Mock()
        self.organizer.filename_handler.validate_and_trim_filename = Mock(
            side_effect=lambda x: x
        )
        self.organizer.progress_tracker.record_progress = Mock()

        self.progress_f = Mock()

        # Mock display context that tracks state changes
        self.display_context = Mock()
        self.status_history = []
        self.message_history = []

        def track_status(status, **kwargs):
            self.status_history.append(status)

        def track_info(message, **kwargs):
            self.message_history.append(("info", message))

        def track_warning(message, **kwargs):
            self.message_history.append(("warning", message))

        def track_error(message, **kwargs):
            self.message_history.append(("error", message))

        self.display_context.set_status = Mock(side_effect=track_status)
        self.display_context.show_info = Mock(side_effect=track_info)
        self.display_context.show_warning = Mock(side_effect=track_warning)
        self.display_context.show_error = Mock(side_effect=track_error)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    @pytest.mark.integration
    @pytest.mark.contract
    def test_retry_handler_contract_on_success(self):
        """CONTRACT TEST: Retry handler MUST return (True, result) when operation succeeds."""
        retry_handler = create_retry_handler(max_attempts=2)
        test_file = os.path.join(self.input_dir, "test.pdf")

        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        with patch("orchestration.workflow_processor._extract_file_content") as mock_extract:
            mock_extract.return_value = ("content", "")

            # Act: Process file that should succeed on first attempt
            success, result = process_file_with_retry(
                input_path=test_file,
                filename="test.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.output_dir,
                progress_f=self.progress_f,
                ocr_lang="eng",
                ai_client=self.ai_client,
                organizer=self.organizer,
                display_context=self.display_context,
                retry_handler=retry_handler,
            )

            # Assert: Contract verification
            self.assertTrue(
                success,
                "Retry handler CONTRACT VIOLATION: Must return (True, result) when operation succeeds",
            )
            self.assertIsNotNone(
                result,
                "Retry handler CONTRACT VIOLATION: Must return non-None result on success",
            )

            # Assert: Retry stats reflect single success
            stats = retry_handler.get_stats()
            self.assertEqual(stats.total_attempts, 1, "Single success should record 1 attempt")
            self.assertEqual(stats.successful_retries, 0, "First-attempt success is not a retry")

    @pytest.mark.integration
    @pytest.mark.contract
    def test_batch_processing_respects_retry_results(self):
        """CONTRACT TEST: Batch processing MUST respect retry handler return values."""
        retry_handler = create_retry_handler(max_attempts=3)

        # Create test files with different outcomes
        test_files = []
        for i, outcome in enumerate(["success", "retry_success", "failure"]):
            file_path = os.path.join(self.input_dir, f"{outcome}_{i}.pdf")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"content for {outcome}")
            test_files.append((file_path, f"{outcome}_{i}.pdf", outcome))

        batch_results = []

        for file_path, filename, expected_outcome in test_files:
            # Configure different extraction behavior per file
            if expected_outcome == "success":
                mock_behavior = Mock(return_value=("content", ""))
            elif expected_outcome == "retry_success":
                # Create a side effect that fails once, then succeeds
                call_count = [0]  # Use list to allow modification in nested function
                
                def retry_mock(input_path, ocr_lang, display_context):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        # Create a PermissionError with the right errno for classification
                        error = PermissionError("File is temporarily locked")
                        error.errno = 13  # EACCES - Permission denied
                        raise error
                    return ("content after retry", "")

                mock_behavior = Mock(side_effect=retry_mock)
            else:  # failure
                mock_behavior = Mock(side_effect=ValueError("Permanent error"))

            with patch(
                "orchestration.workflow_processor._extract_file_content", mock_behavior
            ):

                # Process individual file
                success, result = process_file_with_retry(
                    input_path=file_path,
                    filename=filename,
                    unprocessed_folder=self.unprocessed_dir,
                    renamed_folder=self.output_dir,
                    progress_f=self.progress_f,
                    ocr_lang="eng",
                    ai_client=self.ai_client,
                    organizer=self.organizer,
                    display_context=self.display_context,
                    retry_handler=retry_handler,
                )

                batch_results.append((filename, expected_outcome, success, result))

        # Assert: Batch processing CONTRACT - results match expectations
        for filename, expected_outcome, actual_success, actual_result in batch_results:
            if expected_outcome in ["success", "retry_success"]:
                self.assertTrue(
                    actual_success,
                    f"Batch processing CONTRACT VIOLATION: {filename} with {expected_outcome} "
                    f"must be processed as successful by batch processor",
                )
                self.assertIsNotNone(
                    actual_result,
                    f"Successful {expected_outcome} must yield result for {filename}",
                )
            else:  # failure
                self.assertFalse(
                    actual_success,
                    f"Batch processing CONTRACT VIOLATION: {filename} with permanent failure "
                    f"must be processed as failed by batch processor",
                )

        # Assert: Overall retry handler statistics are accurate
        stats = retry_handler.get_stats()
        self.assertEqual(
            stats.successful_retries,
            1,
            "Batch should show exactly 1 successful retry (retry_success file)",
        )
        self.assertEqual(
            stats.files_with_recoverable_issues,
            1,
            "Batch should track 1 file with recoverable issues",
        )

    @pytest.mark.integration
    @pytest.mark.critical
    def test_display_manager_reflects_retry_handler_results(self):
        """CRITICAL: Display counts MUST match actual retry handler processing results."""
        retry_handler = create_retry_handler(max_attempts=2)

        # Create file that will succeed after retry
        test_file = os.path.join(self.input_dir, "retry_test.pdf")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # Simulate temporary error followed by success
        call_count = 0

        def mock_temporary_then_success(input_path, ocr_lang, display_context):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise PermissionError("File is temporarily locked by antivirus")
            return "extracted content", ""

        with patch(
            "orchestration.workflow_processor._extract_file_content",
            side_effect=mock_temporary_then_success,
        ):

            # Act: Process file with retry scenario
            success, result = process_file_with_retry(
                input_path=test_file,
                filename="retry_test.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.output_dir,
                progress_f=self.progress_f,
                ocr_lang="eng",
                ai_client=self.ai_client,
                organizer=self.organizer,
                display_context=self.display_context,
                retry_handler=retry_handler,
            )

            # Assert: Success result matches display expectations
            self.assertTrue(
                success,
                "CRITICAL DISPLAY BUG: File succeeding after retry must be reported as success",
            )

            # Assert: Display context received correct state transitions
            self.assertIn(
                "retrying",
                self.status_history,
                "Display must show 'retrying' status during retry attempts",
            )
            self.assertIn(
                "recovered",
                self.status_history,
                "Display must show 'recovered' status after successful retry",
            )

            # Assert: User sees appropriate messaging
            success_messages = [
                msg for msg_type, msg in self.message_history if "Successfully processed" in msg
            ]
            self.assertTrue(
                len(success_messages) > 0,
                "User must see confirmation of successful retry recovery",
            )

            # Assert: Retry handler statistics match display expectations
            stats = retry_handler.get_stats()
            self.assertEqual(
                stats.successful_retries,
                1,
                "Display statistics must match retry handler: 1 successful retry",
            )

    @pytest.mark.integration
    @pytest.mark.golden_path
    def test_mixed_batch_processing_state_consistency(self):
        """GOLDEN PATH: Process mix of success/retry/failure with consistent state tracking."""
        retry_handler = create_retry_handler(max_attempts=2)

        # Create batch of files with different scenarios
        file_scenarios = [
            ("immediate_success.pdf", "success"),
            ("retry_success.pdf", "retry_then_success"),
            ("permanent_failure.pdf", "failure"),
            ("another_success.pdf", "success"),
        ]

        batch_results = []
        all_status_changes = []
        all_messages = []

        for filename, scenario in file_scenarios:
            file_path = os.path.join(self.input_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"content for {scenario}")

            # Reset tracking for this file
            self.status_history.clear()
            self.message_history.clear()

            # Configure mock behavior for scenario
            if scenario == "success":
                extract_mock = Mock(return_value=("content", ""))
            elif scenario == "retry_then_success":
                call_count = 0

                def retry_mock(input_path, ocr_lang, display_context):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise PermissionError("File is temporarily locked")
                    return "content after retry", ""

                extract_mock = Mock(side_effect=retry_mock)
            else:  # failure
                extract_mock = Mock(side_effect=ValueError("Permanent error"))

            with patch(
                "orchestration.workflow_processor._extract_file_content", extract_mock
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
                    display_context=self.display_context,
                    retry_handler=retry_handler,
                )

                # Track results and state changes
                batch_results.append((filename, scenario, success, result))
                all_status_changes.extend([(filename, status) for status in self.status_history])
                all_messages.extend([(filename, msg_type, msg) for msg_type, msg in self.message_history])

        # Assert: Each file's result matches its expected scenario
        for filename, expected_scenario, actual_success, actual_result in batch_results:
            if expected_scenario in ["success", "retry_then_success"]:
                self.assertTrue(
                    actual_success,
                    f"Mixed batch consistency error: {filename} ({expected_scenario}) "
                    f"should succeed but was marked as failure",
                )
            else:  # failure
                self.assertFalse(
                    actual_success,
                    f"Mixed batch consistency error: {filename} ({expected_scenario}) "
                    f"should fail but was marked as success",
                )

        # Assert: Overall batch statistics are consistent
        stats = retry_handler.get_stats()
        expected_successes = sum(
            1 for _, scenario, success, _ in batch_results if scenario == "retry_then_success" and success
        )
        self.assertEqual(
            stats.successful_retries,
            expected_successes,
            f"Batch retry statistics inconsistent: expected {expected_successes} successful retries",
        )

        # Assert: State transitions make sense
        retry_statuses = [
            status for filename, status in all_status_changes if status in ["retrying", "recovered"]
        ]
        self.assertTrue(
            len(retry_statuses) > 0,
            "Mixed batch should show retry state transitions for retry_then_success file",
        )


if __name__ == "__main__":
    unittest.main()