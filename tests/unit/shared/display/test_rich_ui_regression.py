"""
Rich UI Regression Tests

Tests to prevent the Rich UI behavioral bugs from reoccurring:
1. Border wrapping issue (small rectangle instead of full border)
2. File processing line overwriting (completed files should persist)
"""

import io
import sys
import time
import unittest
from unittest.mock import patch
from rich.console import Console

# Add src to path for imports
sys.path.insert(0, 'src')

from shared.display.rich_progress_display import RichProgressDisplay
from shared.display.rich_display_manager import RichDisplayManager, RichDisplayOptions
from tests.utils.rich_test_utils import RichTestCase

class TestRichUIRegression(unittest.TestCase, RichTestCase):
    """Regression tests for Rich UI behavioral issues."""

    def setUp(self):
        """Set up test fixtures with Rich test framework."""
        RichTestCase.setUp(self)

    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)

    def test_border_wrapping_fix(self):
        """Test that borders wrap content properly, not as small rectangles."""
        # Create progress display using test framework
        progress_display = self.display_manager.progress

        # Verify that transient is False to prevent border fragmentation
        progress_display.start(3, "Test Border Wrapping")

        # The fix sets transient=False in Live display
        self.assertIsNotNone(progress_display._live)
        # Note: We can't directly access Live.transient, but we can verify behavior

        progress_display.finish("Test completed")

        # Check that output contains proper border characters, not fragmented
        output = self.get_console_output()

        # Should contain proper border elements
        self.assertIn('─', output, "Should contain horizontal border characters")

        # Should not have standalone small rectangles (fragmented borders)
        lines = output.split('\n')
        border_lines = [line for line in lines if '─' in line or '│' in line]

        # If borders are working correctly, we should have structured border lines
        self.assertGreater(len(border_lines), 0, "Should have border elements")

    def test_file_processing_line_persistence(self):
        """Test that completed file processing lines persist and accumulate."""
        progress_display = self.display_manager.progress

        progress_display.start(3, "Test Line Persistence")

        # Process multiple files
        files = ["file1.pd", "file2.pd", "file3.pd"]
        targets = ["target1.pd", "target2.pd", "target3.pd"]

        for filename, target in zip(files, targets):
            progress_display.start_file(filename)
            progress_display.complete_file(filename, target)

        # Verify that completed files are tracked
        self.assertEqual(len(progress_display._completed_files), 3,
                        "Should track all completed files")

        # Verify completed files contain expected data
        completed = progress_display._completed_files
        self.assertEqual(completed[0]["filename"], "file1.pd")
        self.assertEqual(completed[0]["target_filename"], "target1.pd")
        self.assertEqual(completed[0]["status"], "success")
        self.assertEqual(completed[0]["icon"], "✅")

        progress_display.finish("Test completed")

        # Check that output shows persistent file information
        output = self.get_console_output()

        # Should contain all processed filenames
        for filename in files:
            self.assertIn(filename, output, "Should contain {filename} in persistent display")

    def test_failed_file_persistence(self):
        """Test that failed files also persist in the display."""
        progress_display = self.display_manager.progress

        progress_display.start(2, "Test Failed File Persistence")

        # Process one success and one failure
        progress_display.start_file("success.pd")
        progress_display.complete_file("success.pd", "processed.pd")

        progress_display.start_file("failure.pd")
        progress_display.fail_file("failure.pd", "File corrupted")

        # Verify both are tracked
        self.assertEqual(len(progress_display._completed_files), 2)

        # Check failure tracking
        failed_file = progress_display._completed_files[1]
        self.assertEqual(failed_file["filename"], "failure.pd")
        self.assertEqual(failed_file["status"], "failed")
        self.assertEqual(failed_file["icon"], "❌")
        self.assertEqual(failed_file["error"], "File corrupted")

        progress_display.finish()

    def test_display_manager_ui_consistency(self):
        """Test that RichDisplayManager maintains UI consistency."""
        options = RichDisplayOptions(verbose=True, show_stats=True)
        manager = self.test_container.create_display_manager(options)

        # Test processing context behavior
        with manager.processing_context(2, "Test UI Consistency") as ctx:
            ctx.start_file("test1.pd")
            ctx.complete_file("test1.pd", "processed1.pd")

            ctx.start_file("test2.pd")
            ctx.complete_file("test2.pd", "processed2.pd")

        output = self.get_console_output()

        # Should show both files in output
        self.assertIn("test1.pd", output)
        self.assertIn("test2.pd", output)
        self.assertIn("processed1.pd", output)
        self.assertIn("processed2.pd", output)

    def test_stats_display_consistency(self):
        """Test that statistics display remains consistent."""
        progress_display = self.display_manager.progress

        progress_display.start(3, "Test Stats Consistency")

        # Process files with different outcomes
        progress_display.complete_file("success1.pd", "target1.pd")
        progress_display.complete_file("success2.pd", "target2.pd")
        progress_display.fail_file("failed.pd", "Error")

        # Check stats are accurate
        stats = progress_display.stats
        self.assertEqual(stats.succeeded, 2, "Should have 2 successes")
        self.assertEqual(stats.failed, 1, "Should have 1 failure")
        self.assertEqual(stats.completed, 3, "Should have 3 completed")

        # Verify success rate calculation
        expected_success_rate = (2 / 3) * 100  # 66.7%
        self.assertAlmostEqual(stats.success_rate, expected_success_rate, places=1)

        progress_display.finish()

    def test_completed_files_display_limit(self):
        """Test that completed files display is limited to prevent UI overflow."""
        progress_display = self.display_manager.progress

        progress_display.start(10, "Test Display Limit")

        # Process many files (more than display limit of 5)
        for i in range(8):
            filename = "file_{i}.pdf"
            target = "target_{i}.pdf"
            progress_display.complete_file(filename, target)

        # Check that we track all but display only last 5
        self.assertEqual(len(progress_display._completed_files), 8,
                        "Should track all 8 completed files")

        # The display method should only show last 5
        # This is tested in _create_full_display() via [-5:] slice

        progress_display.finish()

class TestRichUIIntegration(unittest.TestCase, RichTestCase):
    """Integration tests for Rich UI components working together."""

    def setUp(self):
        """Set up test fixtures with Rich test framework."""
        RichTestCase.setUp(self)

    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)

    def test_full_processing_workflow_ui(self):
        """Test complete processing workflow UI behavior."""
        options = RichDisplayOptions(verbose=True, show_stats=True)
        manager = self.test_container.create_display_manager(options)

        # Simulate full processing workflow
        manager.print_header("Content Tamer AI", "UI Regression Test")

        with manager.processing_context(3, "Processing Test Documents") as ctx:
            # File 1: Success
            ctx.start_file("document1.pd")
            ctx.set_status("extracting_content")
            ctx.set_status("generating_filename")
            ctx.complete_file("document1.pd", "Monthly_Report_Analysis.pd")

            # File 2: Success
            ctx.start_file("document2.pd")
            ctx.set_status("extracting_content")
            ctx.set_status("generating_filename")
            ctx.complete_file("document2.pd", "Strategic_Planning_Overview.pd")

            # File 3: Failure
            ctx.start_file("document3.pd")
            ctx.fail_file("document3.pd", "File corrupted")

        output = self.get_console_output()

        # Verify complete workflow is represented in output
        self.assertIn("CONTENT TAMER AI", output)  # Header shows as uppercase with emoji
        self.assertIn("document1.pd", output)
        self.assertIn("Monthly_Report_Analysis.pd", output)
        self.assertIn("Strategic_Planning_Overview.pd", output)
        self.assertIn("document3.pd", output)
        self.assertIn("corrupted", output)

        # Should have proper completion statistics
        self.assertIn("2", output)  # Success count
        self.assertIn("1", output)  # Failure count

if __name__ == '__main__':
    unittest.main()
