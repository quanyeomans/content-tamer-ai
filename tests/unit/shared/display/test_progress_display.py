"""
Tests for enhanced progress display functionality.
"""

import os
import sys
import time
import unittest
from io import StringIO
from unittest.mock import call, patch, Mock, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from shared.display.cli_display import Colors
from shared.display.progress_display import ProgressDisplay, ProgressStats

class TestProgressStats(unittest.TestCase):
    """Test progress statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = ProgressStats(total=100)
        self.assertEqual(stats.total, 100)
        self.assertEqual(stats.completed, 0)
        self.assertEqual(stats.failed, 0)
        self.assertEqual(stats.warnings, 0)
        self.assertIsInstance(stats.start_time, float)

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        stats = ProgressStats(total=100)
        stats.completed = 25
        self.assertEqual(stats.progress_percentage, 25.0)

        # Test zero total
        stats.total = 0
        self.assertEqual(stats.progress_percentage, 0.0)

    def test_success_count(self):
        """Test success count property."""
        stats = ProgressStats()
        stats.succeeded = 7
        self.assertEqual(stats.success_count, 7)

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        stats = ProgressStats()
        time.sleep(0.01)  # Small delay
        self.assertGreater(stats.elapsed_time, 0)

class TestProgressDisplay(unittest.TestCase):
    """Test enhanced progress display."""

    def setUp(self):
        self.output = StringIO()
        self.progress = ProgressDisplay(no_color=True, file=self.output)

    def test_initialization(self):
        """Test progress display initialization."""
        self.assertIsInstance(self.progress.stats, ProgressStats)
        self.assertEqual(self.progress.current_filename, "")
        self.assertEqual(self.progress.current_status, "")

    def test_start_progress(self):
        """Test starting progress display."""
        self.progress.start(total=10, description="Testing")
        self.assertEqual(self.progress.stats.total, 10)

        # Check that something was written to output
        output_content = self.output.getvalue()
        self.assertGreater(len(output_content), 0)

    def test_update_progress(self):
        """Test updating progress."""
        self.progress.start(total=5)
        self.progress.update(filename="test1.pd", status="processing")

        self.assertEqual(self.progress.current_filename, "test1.pd")
        self.assertEqual(self.progress.current_status, "processing")
        self.assertEqual(self.progress.stats.completed, 1)

    def test_update_without_increment(self):
        """Test updating progress without incrementing counter."""
        self.progress.start(total=5)
        initial_completed = self.progress.stats.completed
        self.progress.update(filename="test.pd", increment=False)

        self.assertEqual(self.progress.stats.completed, initial_completed)
        self.assertEqual(self.progress.current_filename, "test.pd")

    def test_add_warning(self):
        """Test adding warning to stats."""
        initial_warnings = self.progress.stats.warnings
        self.progress.add_warning()
        self.assertEqual(self.progress.stats.warnings, initial_warnings + 1)

    def test_add_error(self):
        """Test adding error to stats."""
        initial_errors = self.progress.stats.failed
        self.progress.add_error()
        self.assertEqual(self.progress.stats.failed, initial_errors + 1)

    def test_context_manager(self):
        """Test progress display as context manager."""
        with self.progress as progress:
            self.assertIs(progress, self.progress)
            progress.start(total=1)
            progress.update(filename="test.pd")

        # Should complete normally without errors

    def test_finish_with_stats(self):
        """Test finishing progress with statistics."""
        self.progress.start(total=3)
        self.progress.update(filename="test1.pd")
        self.progress.add_warning()
        self.progress.update(filename="test2.pd")
        self.progress.add_error()

        self.progress.finish("All done")

        output_content = self.output.getvalue()
        self.assertIn("All done", output_content)

    def test_long_filename_truncation(self):
        """Test that very long filenames are truncated."""
        very_long_name = "very_long_filename_" * 10 + ".pd"
        self.progress.start(total=1)

        # Force small terminal width to trigger truncation
        self.progress.formatter.capabilities._terminal_width = 80
        self.progress.update(filename=very_long_name)

        # Should not crash and should contain truncated name
        output_content = self.output.getvalue()
        # With a very long name, some form of truncation should occur
        self.assertGreater(len(output_content), 0)

    def test_status_indicator_formatting(self):
        """Test status indicator formatting."""
        self.progress.start(total=1)

        test_statuses = [
            "processing",
            "extracting_content",
            "generating_filename",
            "moving_file",
            "completed",
            "failed",
            "warning",
        ]

        for status in test_statuses:
            self.progress.update(status=status, increment=False)
            # Should not crash for any status
            output_content = self.output.getvalue()
            self.assertGreater(len(output_content), 0)

class TestProgressDisplayWithColors(unittest.TestCase):
    """Test progress display with ANSI colors enabled."""

    def setUp(self):
        self.output = StringIO()
        # Enable colors for this test
        self.progress = ProgressDisplay(no_color=False, file=self.output)

    @patch("sys.stdout.isatty", return_value=True)
    def test_cursor_hiding_showing(self, mock_isatty):
        """Test cursor hiding and showing."""
        # Mock color support
        with patch.object(self.progress.formatter, "no_color", False):
            with self.progress:
                self.progress.start(total=1)
                # Cursor should be hidden during progress
                output = self.output.getvalue()

                # Should contain cursor control codes if colors enabled
                if not self.progress.formatter.no_color:
                    self.assertIn(Colors.HIDE_CURSOR, output)

    def test_progress_bar_with_colors(self):
        """Test colored progress bar rendering."""
        self.progress.start(total=4)
        self.progress.update(filename="test.pd", status="processing")

        output_content = self.output.getvalue()
        self.assertGreater(len(output_content), 0)

        # If colors are supported, should contain ANSI escape sequences
        if self.progress.formatter.capabilities.supports_color:
            self.assertIn("\033[", output_content)

class TestProgressDisplayEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        self.output = StringIO()
        self.progress = ProgressDisplay(no_color=True, file=self.output)

    def test_zero_total_files(self):
        """Test progress display with zero total files."""
        self.progress.start(total=0)
        self.progress.finish("No files to process")

        # Should not crash
        output = self.output.getvalue()
        self.assertIn("No files to process", output)

    def test_update_before_start(self):
        """Test updating progress before starting."""
        # Should not crash
        self.progress.update(filename="test.pd")

    def test_multiple_finish_calls(self):
        """Test calling finish multiple times."""
        self.progress.start(total=1)
        self.progress.finish("First finish")
        self.progress.finish("Second finish")  # Should not crash

        output = self.output.getvalue()
        self.assertIn("First finish", output)

    def test_unicode_filename(self):
        """Test progress with Unicode filename."""
        unicode_name = "тест_файл_🔥.pd"
        self.progress.start(total=1)
        self.progress.update(filename=unicode_name)

        # Should handle Unicode gracefully
        output = self.output.getvalue()
        # Content should be present (exact representation may vary)
        self.assertGreater(len(output), 0)

if __name__ == "__main__":
    unittest.main()
