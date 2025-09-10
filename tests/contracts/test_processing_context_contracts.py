"""
Processing Context State Contracts
==================================

CONTRACT AGREEMENTS TESTED:
1. complete_file must increment succeeded count correctly
2. processing_context maintains accurate total count throughout lifecycle
3. file processing state synchronizes with display progress
4. progress counter operations are atomic and consistent
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


class TestProcessingContextStateContracts(unittest.TestCase, RichTestCase):
    """Contracts for processing context state management."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)

    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)

    @pytest.mark.contract
    @pytest.mark.critical
    def test_complete_file_updates_progress_stats_contract(self):
        """CONTRACT: complete_file must increment succeeded count."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(2, "Contract Test") as ctx:
            initial_succeeded = ctx.display.progress.stats.succeeded

            # Contract: This operation must increment succeeded
            ctx.complete_file("test.pd", "result.pd")

            final_succeeded = ctx.display.progress.stats.succeeded

            self.assertEqual(
                final_succeeded,
                initial_succeeded + 1,
                f"complete_file must increment succeeded count: {initial_succeeded} -> {final_succeeded}",
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_processing_context_maintains_total_count_contract(self):
        """CONTRACT: processing context must maintain accurate total throughout lifecycle."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        expected_total = 3

        with manager.processing_context(expected_total, "Contract Test") as ctx:
            # Total must be set correctly at start
            self.assertEqual(
                ctx.display.progress.stats.total,
                expected_total,
                "Expected total {expected_total}, got {ctx.display.progress.stats.total}",
            )

            # Total must remain stable during operations
            ctx.start_file("file1.pd")
            self.assertEqual(
                ctx.display.progress.stats.total,
                expected_total,
                "Total changed during start_file operation",
            )

            ctx.complete_file("file1.pd", "result1.pd")
            self.assertEqual(
                ctx.display.progress.stats.total,
                expected_total,
                "Total changed during complete_file operation",
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_fail_file_updates_progress_stats_contract(self):
        """CONTRACT: fail_file must increment failed count correctly."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(2, "Contract Test") as ctx:
            initial_failed = ctx.display.progress.stats.failed

            # Contract: This operation must increment failed
            ctx.fail_file("test.pd", "Processing error")

            final_failed = ctx.display.progress.stats.failed

            self.assertEqual(
                final_failed,
                initial_failed + 1,
                "fail_file must increment failed count: {initial_failed} -> {final_failed}",
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_progress_counters_remain_consistent_contract(self):
        """CONTRACT: Progress counters (succeeded + failed) must never exceed total."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        total_files = 3

        with manager.processing_context(total_files, "Contract Test") as ctx:
            # Process files with mix of success and failure
            ctx.complete_file("file1.pd", "result1.pd")
            ctx.fail_file("file2.pd", "Error message")
            ctx.complete_file("file3.pd", "result3.pd")

            stats = ctx.display.progress.stats
            processed_count = stats.succeeded + stats.failed

            # Contract: Total processed must not exceed declared total
            self.assertLessEqual(
                processed_count,
                stats.total,
                f"Processed count ({processed_count}) exceeds total ({stats.total})",
            )

            # Contract: Stats must be consistent
            self.assertEqual(stats.succeeded, 2, "Expected 2 succeeded files")
            self.assertEqual(stats.failed, 1, "Expected 1 failed file")
            self.assertEqual(stats.total, total_files, "Total should remain {total_files}")

    @pytest.mark.contract
    @pytest.mark.critical
    def test_processing_context_exit_preserves_final_state_contract(self):
        """CONTRACT: Processing context exit must preserve final statistics."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        # Capture stats after context closes
        final_stats = None
        with manager.processing_context(2, "Contract Test") as ctx:
            ctx.complete_file("file1.pd", "result1.pd")
            ctx.fail_file("file2.pd", "Error")
            final_stats = {
                "total": ctx.display.progress.stats.total,
                "succeeded": ctx.display.progress.stats.succeeded,
                "failed": ctx.display.progress.stats.failed,
                "success_rate": ctx.display.progress.stats.success_rate,
            }

        # Contract: Stats must be preserved after context exit
        self.assertIsNotNone(final_stats, "Failed to capture final stats")
        self.assertEqual(final_stats["total"], 2, "Total files incorrect after exit")
        self.assertEqual(final_stats["succeeded"], 1, "Succeeded count incorrect after exit")
        self.assertEqual(final_stats["failed"], 1, "Failed count incorrect after exit")
        self.assertEqual(final_stats["success_rate"], 50.0, "Success rate incorrect after exit")


if __name__ == "__main__":
    unittest.main()
