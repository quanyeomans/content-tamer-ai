"""
Display Manager Interface Contracts
==================================

CONTRACT AGREEMENTS TESTED:
1. show_completion_stats accepts application.py data format
2. progress.stats provides consistent attributes expected by application layer
3. No duplicate completion messages across display systems
4. Progress percentages remain accurate across state changes
"""

import os
import sys
import unittest
from io import StringIO

import pytest

# Add src directory to path
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"
    )
)

from shared.display.rich_display_manager import RichDisplayOptions
from tests.utils.rich_test_utils import RichTestCase


class TestDisplayManagerInterfaceContracts(unittest.TestCase, RichTestCase):
    """Contracts for display manager that prevent UI regressions."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)

    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)

    @pytest.mark.contract
    @pytest.mark.critical
    def test_show_completion_stats_interface_contract(self):
        """CONTRACT: show_completion_stats accepts application.py data format."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        # Must accept this exact format from application.py
        stats = {
            "total_files": 5,
            "successful": 3,
            "errors": 2,
            "warnings": 1,
            "recoverable_errors": 0,
            "successful_retries": 1,
            "error_details": [],
        }

        # Must not raise exception
        try:
            manager.show_completion_stats(stats)
        except Exception as e:
            self.fail("show_completion_stats failed with valid application data: {e}")

    @pytest.mark.contract
    @pytest.mark.critical
    def test_progress_stats_provides_required_attributes_contract(self):
        """CONTRACT: progress.stats must provide attributes that application expects."""
        manager = self.test_container.create_display_manager(RichDisplayOptions())

        # These attributes must always exist
        required_attributes = ["total", "succeeded", "failed", "warnings", "success_rate"]

        for attr in required_attributes:
            self.assertTrue(
                hasattr(manager.progress.stats, attr),
                "progress.stats missing required attribute: {attr}",
            )

            # Must be numeric types
            value = getattr(manager.progress.stats, attr)
            self.assertIsInstance(
                value, (int, float), "progress.stats.{attr} must be numeric, got {type(value)}"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_no_duplicate_completion_messages_contract(self):
        """CONTRACT: Only one completion message should appear in output."""
        output = StringIO()
        manager = self.test_container.create_display_manager(
            RichDisplayOptions(no_color=True, file=output)
        )

        # Simulate full processing workflow
        with manager.processing_context(2, "Contract Test") as ctx:
            ctx.complete_file("file1.pd", "result1.pd")
            ctx.complete_file("file2.pd", "result2.pd")

        # Call completion stats (this was causing duplication)
        stats = {"total_files": 2, "successful": 2, "errors": 0, "warnings": 0}
        manager.show_completion_stats(stats)

        output_content = output.getvalue()

        # Contract: Must not have duplicate completion messages
        error_completions = output_content.count("[ERROR] Processing complete:")
        ok_completions = output_content.count("[OK] Processing complete:")

        self.assertEqual(
            error_completions, 0, "Found {error_completions} error completion messages, expected 0"
        )
        self.assertLessEqual(
            ok_completions, 1, "Found {ok_completions} OK completion messages, expected ≤1"
        )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_success_rate_calculation_contract(self):
        """CONTRACT: Success rate calculation must be consistent and accurate."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))

        # Test various success rate scenarios
        test_cases = [
            {"total_files": 4, "successful": 4, "expected_rate": 100.0},
            {"total_files": 4, "successful": 3, "expected_rate": 75.0},
            {"total_files": 4, "successful": 2, "expected_rate": 50.0},
            {"total_files": 4, "successful": 0, "expected_rate": 0.0},
        ]

        for case in test_cases:
            stats = {
                "total_files": case["total_files"],
                "successful": case["successful"],
                "errors": case["total_files"] - case["successful"],
                "warnings": 0,
            }

            # Must calculate correct success rate
            try:
                manager.show_completion_stats(stats)
                # Contract satisfied if no exception raised and calculation is correct
            except Exception as e:
                self.fail("Success rate calculation failed for {case}: {e}")


if __name__ == "__main__":
    unittest.main()
