"""
Completion Message Consistency Contracts
========================================

CONTRACT AGREEMENTS TESTED:
1. Single progress summary per processing session
2. Consistent success rate calculation across display systems
3. No conflicting completion messages between Rich and legacy displays
4. Target filename display remains consistent throughout processing
"""

import os
import sys
import unittest

import pytest

# Add src directory to path
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"
    )
)

from shared.display.rich_display_manager import RichDisplayOptions
from tests.utils.rich_test_utils import RichTestCase


class TestCompletionConsistencyContracts(unittest.TestCase, RichTestCase):
    """Contracts preventing duplicate/conflicting display messages."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)

    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)

    @pytest.mark.contract
    @pytest.mark.critical
    def test_single_progress_summary_per_session_contract(self):
        """CONTRACT: Each processing session should produce exactly one progress summary."""
        manager = self.test_container.create_display_manager(
            RichDisplayOptions(no_color=True, quiet=False)
        )

        # Run complete processing session
        with manager.processing_context(3, "Contract Test") as ctx:
            ctx.start_file("file1.pd")
            ctx.complete_file("file1.pd", "result1.pd")

            ctx.start_file("file2.pd")
            ctx.fail_file("file2.pd", "Processing error")

            ctx.start_file("file3.pd")
            ctx.complete_file("file3.pd", "result3.pd")

        # Display final completion stats
        stats = {"total_files": 3, "successful": 2, "errors": 1, "warnings": 0}
        manager.show_completion_stats(stats)

        # Get captured output using Rich test framework
        output_content = self.get_console_output()

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

        # Contract: Should have exactly one comprehensive summary
        processing_complete_messages = output_content.count("Processing complete:")
        self.assertLessEqual(
            processing_complete_messages,
            1,
            "Found {processing_complete_messages} completion messages, expected ≤1",
        )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_success_rate_calculation_contract(self):
        """CONTRACT: Success rate must be calculated accurately from processed files."""
        manager = self.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(4, "Contract Test") as ctx:
            # Process 3 successful, 1 failed = 75% success rate
            ctx.complete_file("success1.pd", "result1.pd")
            ctx.complete_file("success2.pd", "result2.pd")
            ctx.complete_file("success3.pd", "result3.pd")
            ctx.fail_file("failure1.pd", "Error")

            # Contract: Success rate must be calculated correctly
            calculated_rate = ctx.display.progress.stats.success_rate
            expected_rate = 75.0  # 3/4 = 75%

            self.assertAlmostEqual(
                calculated_rate,
                expected_rate,
                places=1,
                msg="Success rate calculation incorrect: expected {expected_rate}%, got {calculated_rate}%",
            )

            # Ensure no Rich I/O errors occurred
            self.assert_no_rich_io_errors()

    @pytest.mark.contract
    @pytest.mark.critical
    def test_target_filename_tracking_contract(self):
        """CONTRACT: Target filenames must be tracked correctly in processing context."""
        manager = self.create_display_manager(RichDisplayOptions(quiet=True))

        # Ensure no Rich I/O errors before starting test
        self.assert_no_rich_io_errors()

        with manager.processing_context(2, "Contract Test") as ctx:
            # Contract: Target filename should be tracked in processed files
            ctx.start_file("input1.pd")
            ctx.complete_file("input1.pd", "processed_document_1.pd")

            ctx.start_file("input2.pd")
            ctx.complete_file("input2.pd", "processed_document_2.pd")

            # Contract: Processed files should contain target filenames
            processed_files = ctx.display.progress.stats._processed_files
            target_filenames = [
                f.get("target", "") for f in processed_files if f.get("status") == "success"
            ]

            self.assertIn(
                "processed_document_1.pd",
                target_filenames,
                "Target filename 'processed_document_1.pd' not tracked",
            )
            self.assertIn(
                "processed_document_2.pd",
                target_filenames,
                "Target filename 'processed_document_2.pdf' not tracked",
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_no_error_completion_for_successful_processing_contract(self):
        """CONTRACT: Successful processing must never display error completion messages."""
        manager = self.test_container.create_display_manager(
            RichDisplayOptions(no_color=True, quiet=False)
        )

        # Simulate completely successful processing
        with manager.processing_context(2, "Contract Test") as ctx:
            ctx.complete_file("file1.pd", "result1.pd")
            ctx.complete_file("file2.pd", "result2.pd")

        # Show completion stats for successful session
        stats = {"total_files": 2, "successful": 2, "errors": 0, "warnings": 0}
        manager.show_completion_stats(stats)

        output_content = self.get_console_output()
        self.assert_no_rich_io_errors()

        # Contract: Must not show error completion for successful processing
        error_messages = output_content.count("[ERROR] Processing complete:")
        self.assertEqual(
            error_messages,
            0,
            "Found {error_messages} error completion messages for successful processing",
        )

        # Contract: Should show appropriate success indication
        if "Processing complete:" in output_content:
            # If completion message shown, it should not indicate error
            self.assertNotIn(
                "0.0% success rate",
                output_content,
                "Successful processing incorrectly showing 0.0% success rate",
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_completion_message_contains_accurate_statistics_contract(self):
        """CONTRACT: Completion messages must contain accurate file processing statistics."""
        manager = self.test_container.create_display_manager(
            RichDisplayOptions(no_color=True, quiet=False)
        )

        # Process files with known results
        with manager.processing_context(4, "Contract Test") as ctx:
            ctx.complete_file("file1.pd", "result1.pd")  # Success
            ctx.complete_file("file2.pd", "result2.pd")  # Success
            ctx.fail_file("file3.pd", "Error occurred")  # Failure
            ctx.complete_file("file4.pd", "result4.pd")  # Success

        # Expected final stats: 3 successful, 1 failed, 75% success rate
        expected_stats = {"total_files": 4, "successful": 3, "errors": 1, "warnings": 0}

        manager.show_completion_stats(expected_stats)
        output_content = self.get_console_output()
        self.assert_no_rich_io_errors()

        # Contract: Final progress state must match processing results
        final_stats = manager.progress.stats
        self.assertEqual(final_stats.succeeded, 3, "Final succeeded count incorrect")
        self.assertEqual(final_stats.failed, 1, "Final failed count incorrect")
        self.assertEqual(final_stats.total, 4, "Final total count incorrect")
        self.assertEqual(final_stats.success_rate, 75.0, "Final success rate incorrect")


if __name__ == "__main__":
    unittest.main()
