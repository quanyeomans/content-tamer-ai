"""
Core Contract Tests - Optimized Performance Version
===================================================

CONTRACT AGREEMENTS TESTED:
1. Essential component interface agreements
2. Critical data flow contracts
3. Regression prevention for known bugs
4. Performance-optimized without Rich display I/O issues

This is the production-ready contract test suite optimized for:
- <5 second execution time
- Zero I/O conflicts
- Essential contract coverage
- Pre-commit hook compatibility
"""

import os
import sys
import unittest

import pytest

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

# Only import what we need to avoid I/O issues
from shared.display.rich_progress_display import RichProgressStats

class TestCoreContracts(unittest.TestCase):
    """Core contracts essential for preventing regressions."""

    @pytest.mark.contract
    @pytest.mark.critical
    def test_progress_stats_interface_contract(self):
        """CONTRACT: Progress stats must provide required attributes."""
        stats = RichProgressStats()

        # Required attributes must exist
        required_attributes = ['total', 'succeeded', 'failed', 'warnings', 'success_rate']

        for attr in required_attributes:
            self.assertTrue(
                hasattr(stats, attr),
                "progress.stats missing required attribute: {attr}"
            )

            # Must be numeric types
            value = getattr(stats, attr)
            self.assertIsInstance(
                value, (int, float),
                "progress.stats.{attr} must be numeric, got {type(value)}"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_success_rate_calculation_contract(self):
        """CONTRACT: Success rate calculation must be accurate."""
        stats = RichProgressStats()

        # Test scenarios
        test_cases = [
            (4, 4, 100.0),  # Perfect success
            (4, 2, 50.0),   # Half success
            (3, 1, 33.3),   # One third success
            (1, 0, 0.0),    # No success
        ]

        for total, succeeded, expected_rate in test_cases:
            stats.total = total
            stats.succeeded = succeeded
            stats.failed = total - succeeded

            # Contract: Success rate must be calculated correctly
            calculated_rate = stats.success_rate

            self.assertAlmostEqual(
                calculated_rate, expected_rate, places=1,
                msg="Success rate incorrect for {succeeded}/{total}: expected {expected_rate}%, got {calculated_rate}%"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_counter_increment_contract(self):
        """CONTRACT: Progress counters must increment correctly."""
        stats = RichProgressStats()
        stats.total = 5

        initial_succeeded = stats.succeeded
        initial_failed = stats.failed

        # Contract: Success increment
        stats.succeeded += 1
        self.assertEqual(
            stats.succeeded, initial_succeeded + 1,
            "Success counter increment failed"
        )

        # Contract: Failure increment
        stats.failed += 1
        self.assertEqual(
            stats.failed, initial_failed + 1,
            "Failure counter increment failed"
        )

        # Contract: Counters don't exceed total
        total_processed = stats.succeeded + stats.failed
        self.assertLessEqual(
            total_processed, stats.total,
            "Processed count {total_processed} exceeds total {stats.total}"
        )

    @pytest.mark.contract
    @pytest.mark.regression
    def test_no_zero_success_rate_with_successes_contract(self):
        """REGRESSION CONTRACT: Prevents 0.0% success rate when files succeeded."""
        stats = RichProgressStats()

        # Test the exact regression scenario
        stats.total = 2
        stats.succeeded = 2
        stats.failed = 0

        # Contract: Success rate must not be 0.0 when there are successful files
        calculated_rate = stats.success_rate

        self.assertGreater(
            calculated_rate, 0.0,
            "Success rate showing 0.0% despite successful files (regression)"
        )
        self.assertEqual(
            calculated_rate, 100.0,
            "Success rate calculation incorrect: expected 100.0%, got {calculated_rate}%"
        )

    @pytest.mark.contract
    @pytest.mark.regression
    def test_progress_stats_initialization_contract(self):
        """REGRESSION CONTRACT: Prevents stats remaining uninitialized."""
        stats = RichProgressStats()

        # Contract: Stats must be initialized to reasonable defaults
        self.assertIsInstance(stats.total, (int, float), "Total not initialized to numeric")
        self.assertIsInstance(stats.succeeded, (int, float), "Succeeded not initialized to numeric")
        self.assertIsInstance(stats.failed, (int, float), "Failed not initialized to numeric")
        self.assertIsInstance(stats.warnings, (int, float), "Warnings not initialized to numeric")

        # Contract: Initial values must be reasonable
        self.assertGreaterEqual(stats.total, 0, "Total initialized to negative value")
        self.assertGreaterEqual(stats.succeeded, 0, "Succeeded initialized to negative value")
        self.assertGreaterEqual(stats.failed, 0, "Failed initialized to negative value")
        self.assertGreaterEqual(stats.warnings, 0, "Warnings initialized to negative value")

    @pytest.mark.contract
    @pytest.mark.critical
    def test_processed_files_list_contract(self):
        """CONTRACT: Processed files list must maintain data integrity."""
        stats = RichProgressStats()

        # Contract: Processed files list must exist and be iterable
        self.assertTrue(
            hasattr(stats, '_processed_files'),
            "Processed files list missing from stats"
        )

        processed_files = stats._processed_files
        self.assertIsInstance(
            processed_files, list,
            "Processed files must be a list, got {type(processed_files)}"
        )

        # Contract: Can add file data without error
        test_file = {
            "source": "test.pdf",
            "target": "organized_test.pdf",
            "status": "success",
            "timestamp": 1234567890
        }

        processed_files.append(test_file)

        # Contract: Added data is preserved exactly
        self.assertEqual(len(processed_files), 1, "File not added to processed files list")
        added_file = processed_files[0]
        self.assertEqual(added_file["source"], "test.pd", "Source filename not preserved")
        self.assertEqual(added_file["target"], "organized_test.pd", "Target filename not preserved")
        self.assertEqual(added_file["status"], "success", "Status not preserved")

    @pytest.mark.contract
    @pytest.mark.critical
    def test_data_format_consistency_contract(self):
        """CONTRACT: Data formats must remain consistent across operations."""
        stats = RichProgressStats()

        # Contract: Stats format must be consistent for completion data
        completion_data = {
            'total': stats.total,
            'succeeded': stats.succeeded,
            'failed': stats.failed,
            'success_rate': stats.success_rate
        }

        # Contract: All completion data must be serializable (for display)
        for key, value in completion_data.items():
            self.assertIsInstance(
                value, (int, float, str),
                "Completion data '{key}' not serializable: {type(value)}"
            )

        # Contract: Data types must be consistent
        self.assertIsInstance(completion_data['total'], (int, float))
        self.assertIsInstance(completion_data['succeeded'], (int, float))
        self.assertIsInstance(completion_data['failed'], (int, float))
        self.assertIsInstance(completion_data['success_rate'], (int, float))

    @pytest.mark.contract
    @pytest.mark.critical
    def test_batch_processing_counter_consistency_contract(self):
        """CONTRACT: Batch processing must maintain counter consistency."""
        stats = RichProgressStats()
        stats.total = 10

        # Simulate batch processing
        batch_operations = [
            ("success", 1, 0),
            ("success", 1, 0),
            ("failure", 0, 1),
            ("success", 1, 0),
            ("failure", 0, 1),
            ("success", 1, 0)
        ]

        for operation, success_inc, fail_inc in batch_operations:
            stats.succeeded += success_inc
            stats.failed += fail_inc

            # Contract: Counters must remain consistent after each operation
            total_processed = stats.succeeded + stats.failed

            self.assertLessEqual(
                total_processed, stats.total,
                "Batch processing: processed {total_processed} exceeds total {stats.total}"
            )

            # Contract: Success rate must be calculable at any point
            if total_processed > 0:
                expected_rate = (stats.succeeded / total_processed) * 100
                actual_rate = stats.success_rate

                self.assertIsInstance(
                    actual_rate, (int, float),
                    "Success rate not numeric during batch processing: {type(actual_rate)}"
                )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_mixed_results_accuracy_contract(self):
        """CONTRACT: Mixed success/failure results must be accurately represented."""
        stats = RichProgressStats()

        # Test complex mixed scenario
        stats.total = 7
        stats.succeeded = 4
        stats.failed = 2
        stats.warnings = 1

        # Contract: Mixed results calculations must be accurate
        expected_success_rate = (4 / 7) * 100  # 57.1% (4 succeeded out of 7 total)
        actual_success_rate = stats.success_rate

        self.assertAlmostEqual(
            actual_success_rate, expected_success_rate, places=1,
            msg="Mixed results success rate incorrect: expected {expected_success_rate}%, got {actual_success_rate}%"
        )

        # Contract: All counters must be reasonable
        total_processed = stats.succeeded + stats.failed
        self.assertLessEqual(total_processed, stats.total, "Processed exceeds total in mixed results")
        self.assertGreaterEqual(stats.warnings, 0, "Warnings count negative in mixed results")

if __name__ == '__main__':
    unittest.main()
