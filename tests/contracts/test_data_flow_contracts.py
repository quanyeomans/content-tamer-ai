"""
Data Flow Contracts: Progress → Display → User
=============================================

CONTRACT AGREEMENTS TESTED:
1. File processing results flow correctly to progress statistics
2. Progress statistics sync with display output
3. Display output reflects actual processing state
4. User-visible information matches internal processing results
5. Error states propagate correctly through the data flow
"""

import os
import sys
import unittest

import pytest

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

# Import from parent tests directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.display.rich_display_manager import RichDisplayOptions
from tests.utils.rich_test_utils import RichTestCase

class TestDataFlowContracts(unittest.TestCase, RichTestCase):
    """Contracts ensuring data flows correctly from processing to user display."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)

    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)

    @pytest.mark.contract
    @pytest.mark.critical
    def test_file_success_flows_to_progress_stats_contract(self):
        """CONTRACT: Successful file processing must increment progress.stats.succeeded."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(3, "Data Flow Test") as ctx:
            initial_succeeded = ctx.display.progress.stats.succeeded

            # Contract: File success must flow to progress stats
            ctx.complete_file("test1.pd", "result1.pd")

            final_succeeded = ctx.display.progress.stats.succeeded

            self.assertEqual(
                final_succeeded, initial_succeeded + 1,
                "File success did not flow to progress.stats.succeeded"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_file_failure_flows_to_progress_stats_contract(self):
        """CONTRACT: Failed file processing must increment progress.stats.failed."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(3, "Data Flow Test") as ctx:
            initial_failed = ctx.display.progress.stats.failed

            # Contract: File failure must flow to progress stats
            ctx.fail_file("test1.pd", "Processing error")

            final_failed = ctx.display.progress.stats.failed

            self.assertEqual(
                final_failed, initial_failed + 1,
                "File failure did not flow to progress.stats.failed"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_progress_stats_sync_with_success_rate_contract(self):
        """CONTRACT: Progress stats must automatically sync with calculated success rate."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(4, "Data Flow Test") as ctx:
            # Process mixed results: 3 success, 1 failure = 75%
            ctx.complete_file("success1.pd", "result1.pd")
            ctx.complete_file("success2.pd", "result2.pd")
            ctx.complete_file("success3.pd", "result3.pd")
            ctx.fail_file("failure1.pd", "Error")

            # Contract: Success rate must automatically sync with progress stats
            stats = ctx.display.progress.stats
            expected_rate = (stats.succeeded / stats.total) * 100

            self.assertEqual(
                stats.success_rate, expected_rate,
                "Success rate {stats.success_rate}% doesn't match calculated {expected_rate}%"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_processed_files_list_reflects_actual_processing_contract(self):
        """CONTRACT: Processed files list must contain all actually processed files."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        processed_filenames = ["doc1.pd", "doc2.pd", "doc3.pd"]

        with manager.processing_context(len(processed_filenames), "Data Flow Test") as ctx:
            # Process files with known names
            ctx.complete_file(processed_filenames[0], "result1.pd")
            ctx.fail_file(processed_filenames[1], "Processing error")
            ctx.complete_file(processed_filenames[2], "result3.pd")

            # Contract: All processed files must appear in processed files list
            processed_files = ctx.display.progress.stats._processed_files
            source_files = [f.get("source", "") for f in processed_files]

            for filename in processed_filenames:
                self.assertIn(
                    filename, source_files,
                    "Processed file '{filename}' not found in processed files list"
                )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_error_details_flow_to_completion_stats_contract(self):
        """CONTRACT: Error details from processing must be available for completion display."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(2, "Data Flow Test") as ctx:
            ctx.complete_file("success.pd", "result.pd")
            ctx.fail_file("failure.pd", "Specific processing error")

            # Contract: Error information must be available for completion stats
            processed_files = ctx.display.progress.stats._processed_files
            failed_files = [f for f in processed_files if f.get("status") == "failed"]

            self.assertTrue(
                len(failed_files) > 0,
                "Failed files not recorded in processed files for completion stats"
            )

            # Contract: Failed file information must be accessible
            failed_file = failed_files[0]
            self.assertEqual(
                failed_file.get("source"), "failure.pd",
                "Failed file source not properly recorded"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_target_filename_data_flow_contract(self):
        """CONTRACT: Target filenames must flow from processing to completion display."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        target_filenames = ["organized_document_1.pd", "organized_document_2.pd"]

        with manager.processing_context(len(target_filenames), "Data Flow Test") as ctx:
            ctx.complete_file("input1.pd", target_filenames[0])
            ctx.complete_file("input2.pd", target_filenames[1])

            # Contract: Target filenames must be preserved in data flow
            processed_files = ctx.display.progress.stats._processed_files
            successful_files = [f for f in processed_files if f.get("status") == "success"]
            recorded_targets = [f.get("target", "") for f in successful_files]

            for target in target_filenames:
                self.assertIn(
                    target, recorded_targets,
                    "Target filename '{target}' not preserved in data flow"
                )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_processing_timestamps_data_flow_contract(self):
        """CONTRACT: Processing timestamps must be recorded for completion analysis."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(1, "Data Flow Test") as ctx:
            import time
            start_time = time.time()

            ctx.complete_file("timestamped.pd", "result.pd")

            end_time = time.time()

            # Contract: Processing timestamps must be recorded
            processed_files = ctx.display.progress.stats._processed_files
            self.assertTrue(
                len(processed_files) > 0,
                "No processed files recorded for timestamp verification"
            )

            processed_file = processed_files[0]
            recorded_timestamp = processed_file.get("timestamp")

            self.assertIsNotNone(
                recorded_timestamp,
                "Processing timestamp not recorded in data flow"
            )

            self.assertTrue(
                start_time <= recorded_timestamp <= end_time,
                "Recorded timestamp {recorded_timestamp} outside processing window [{start_time}, {end_time}]"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_counter_synchronization_across_operations_contract(self):
        """CONTRACT: All progress counters must remain synchronized during operations."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        with manager.processing_context(5, "Data Flow Test") as ctx:
            # Mix of operations to test synchronization
            operations = [
                ("success1.pd", "result1.pd", "complete"),
                ("failure1.pd", "", "fail"),
                ("success2.pd", "result2.pd", "complete"),
                ("failure2.pd", "", "fail"),
                ("success3.pd", "result3.pd", "complete")
            ]

            for filename, target, operation in operations:
                if operation == "complete":
                    ctx.complete_file(filename, target)
                else:
                    ctx.fail_file(filename, "Error message")

                # Contract: Counters must remain synchronized after each operation
                stats = ctx.display.progress.stats
                total_processed = stats.succeeded + stats.failed

                self.assertLessEqual(
                    total_processed, stats.total,
                    "Total processed ({total_processed}) exceeds declared total ({stats.total})"
                )

                # Contract: Success rate must be calculable at any point
                if total_processed > 0:
                    expected_rate = (stats.succeeded / total_processed) * 100
                    self.assertIsInstance(
                        stats.success_rate, (int, float),
                        "Success rate is not numeric during processing"
                    )

if __name__ == '__main__':
    unittest.main()
