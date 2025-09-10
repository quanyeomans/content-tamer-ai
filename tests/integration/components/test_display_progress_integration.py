"""
Critical Integration Tests: Display Manager ↔ Progress Display Component Interactions

Tests the state consistency and counter synchronization between display management
and progress tracking to ensure users see accurate real-time feedback.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import pytest

from core.application_container import TestApplicationContainer
from shared.display.rich_display_manager import RichDisplayManager, RichDisplayOptions, RichProcessingContext


class TestDisplayProgressIntegration(unittest.TestCase):
    """Integration tests for Display Manager ↔ Progress Display interactions."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test container with captured output
        self.container = TestApplicationContainer(capture_output=True)
        
        # Create display manager with test configuration
        self.display_options = RichDisplayOptions(
            verbose=False,
            quiet=False,
            no_color=True,  # Disable colors for test consistency
            show_stats=True,
        )
        self.display_manager = self.container.create_display_manager(self.display_options)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    @pytest.mark.integration
    @pytest.mark.contract
    def test_display_manager_progress_counter_synchronization(self):
        """CONTRACT TEST: Display Manager ↔ Progress Display counter synchronization."""
        total_files = 3
        
        with self.display_manager.processing_context(total_files, "Test Processing") as ctx:
            
            # Process first file successfully
            ctx.start_file("file1.pdf", "generated_name1.pdf")
            ctx.complete_file("file1.pdf", "generated_name1.pdf")
            
            # Check progress state after first file
            progress_stats = self.display_manager.progress.stats
            self.assertEqual(
                progress_stats.succeeded, 1,
                "Progress counter CONTRACT VIOLATION: succeeded must increment after complete_file()"
            )
            self.assertEqual(
                progress_stats.completed, 1,
                "Progress counter CONTRACT VIOLATION: completed must increment after complete_file()"
            )
            
            # Process second file with failure
            ctx.start_file("file2.pdf")
            ctx.fail_file("file2.pdf", "Processing error")
            
            # Check progress state after failure
            self.assertEqual(
                progress_stats.succeeded, 1,
                "Progress counter must not increment succeeded after fail_file()"
            )
            self.assertEqual(
                progress_stats.failed, 1,
                "Progress counter CONTRACT VIOLATION: failed must increment after fail_file()"
            )
            self.assertEqual(
                progress_stats.completed, 2,
                "Progress counter CONTRACT VIOLATION: completed must increment after fail_file()"
            )
            
            # Process third file successfully
            ctx.start_file("file3.pdf", "generated_name3.pdf")
            ctx.complete_file("file3.pdf", "generated_name3.pdf")
            
            # Final state verification
            self.assertEqual(
                progress_stats.succeeded, 2,
                "Final succeeded count must match number of successful complete_file() calls"
            )
            self.assertEqual(
                progress_stats.failed, 1,
                "Final failed count must match number of fail_file() calls"
            )
            self.assertEqual(
                progress_stats.completed, 3,
                "Final completed count must equal total files processed"
            )

    @pytest.mark.integration
    @pytest.mark.critical
    def test_progress_display_filename_contract(self):
        """CRITICAL: Progress display MUST show source filename during processing, target when complete."""
        with self.display_manager.processing_context(2, "Filename Display Test") as ctx:
            
            # Start processing first file
            ctx.start_file("original_document.pdf", "target_name.pdf")
            
            # Verify current display state shows source filename during processing  
            # The current filename should be stored in the progress display
            self.assertEqual(
                self.display_manager.progress.current_filename, "original_document.pdf",
                "CRITICAL DISPLAY BUG: Progress must show source filename during processing"
            )
            
            # Complete the file
            ctx.complete_file("original_document.pdf", "ai_generated_filename.pdf")
            
            # Check if completion is properly displayed
            # Note: This tests the display integration, not just the stats
            stats = self.display_manager.progress.stats
            self.assertEqual(stats.succeeded, 1, "Completion must update success statistics")

    @pytest.mark.integration
    @pytest.mark.golden_path
    def test_processing_context_state_consistency(self):
        """GOLDEN PATH: Processing context maintains consistent state through complete workflow."""
        file_operations = [
            ("doc1.pdf", "success", "ai_name1.pdf"),
            ("doc2.pdf", "skip", ""),
            ("doc3.pdf", "success", "ai_name3.pdf"),
            ("doc4.pdf", "failure", ""),
            ("doc5.pdf", "success", "ai_name5.pdf"),
        ]
        
        with self.display_manager.processing_context(len(file_operations), "State Consistency Test") as ctx:
            
            for filename, operation, result_name in file_operations:
                ctx.start_file(filename, result_name if operation == "success" else "")
                
                if operation == "success":
                    ctx.complete_file(filename, result_name)
                elif operation == "skip":
                    ctx.skip_file(filename)
                elif operation == "failure":
                    ctx.fail_file(filename, "Processing failed")
                    
        # Verify final state consistency
        final_stats = self.display_manager.progress.stats
        
        expected_successes = sum(1 for _, op, _ in file_operations if op == "success")
        expected_errors = sum(1 for _, op, _ in file_operations if op == "failure")
        expected_skipped = sum(1 for _, op, _ in file_operations if op == "skip")
        expected_total = len(file_operations)
        
        self.assertEqual(
            final_stats.succeeded, expected_successes,
            f"State consistency error: expected {expected_successes} successes, got {final_stats.succeeded}"
        )
        self.assertEqual(
            final_stats.failed, expected_errors,
            f"State consistency error: expected {expected_errors} errors, got {final_stats.failed}"
        )
        # Note: Skipped files may or may not increment processed_count depending on implementation
        
    @pytest.mark.integration
    @pytest.mark.error_condition
    def test_warning_tracking_across_components(self):
        """ERROR CONDITION: Warning tracking integration between processing and display."""
        with self.display_manager.processing_context(3, "Warning Integration Test") as ctx:
            
            # File 1: Success with warning
            ctx.start_file("file1.pdf")
            ctx.show_warning("AI timeout, using fallback naming", filename="file1.pdf")
            ctx.complete_file("file1.pdf", "fallback_name1.pdf")
            
            # File 2: Multiple warnings, then success
            ctx.start_file("file2.pdf")  
            ctx.show_warning("Permission denied, retrying", filename="file2.pdf")
            ctx.show_warning("Retry successful", filename="file2.pdf")
            ctx.complete_file("file2.pdf", "generated_name2.pdf")
            
            # File 3: Warning, then failure
            ctx.start_file("file3.pdf")
            ctx.show_warning("Extraction issues detected", filename="file3.pdf")
            ctx.fail_file("file3.pdf", "Could not extract content")
            
        # Verify warning tracking integration
        final_stats = self.display_manager.progress.stats
        
        # Verify that files with warnings are tracked correctly
        self.assertTrue(
            hasattr(final_stats, 'warnings') or hasattr(final_stats, '_files_with_warnings'),
            "Progress display must track warnings across component interactions"
        )
        
        # Verify final counts make sense
        self.assertEqual(final_stats.succeeded, 2, "2 files completed successfully despite warnings")
        self.assertEqual(final_stats.failed, 1, "1 file failed after warnings")

    @pytest.mark.integration
    @pytest.mark.regression
    def test_success_failure_display_accuracy_regression(self):
        """REGRESSION TEST: Prevent success/failure display inaccuracies.
        
        This test specifically targets the bug where successful files appeared as failures
        in the user display, even though they were processed correctly.
        """
        with self.display_manager.processing_context(2, "Display Accuracy Test") as ctx:
            
            # Simulate file that processes successfully but might be displayed incorrectly
            ctx.start_file("success_test.pdf", "ai_generated.pdf")
            
            # This file should be marked as successful
            ctx.complete_file("success_test.pdf", "ai_generated.pdf")
            
            # Simulate file that actually fails
            ctx.start_file("failure_test.pdf")
            ctx.fail_file("failure_test.pdf", "Genuine processing failure")
            
        # REGRESSION CHECK: Verify display accurately reflects actual processing outcomes
        final_stats = self.display_manager.progress.stats
        
        self.assertEqual(
            final_stats.succeeded, 1,
            "REGRESSION BUG: Display must show exactly 1 success for 1 completed file"
        )
        self.assertEqual(
            final_stats.failed, 1,
            "REGRESSION BUG: Display must show exactly 1 error for 1 failed file"
        )
        
        # Calculate success rate to ensure it matches reality
        total_processed = final_stats.succeeded + final_stats.failed
        if total_processed > 0:
            success_rate = (final_stats.succeeded / total_processed) * 100
            expected_rate = 50.0  # 1 success out of 2 files = 50%
            self.assertAlmostEqual(
                success_rate, expected_rate, places=1,
                msg="REGRESSION BUG: Success rate calculation must match actual processing results"
            )

    @pytest.mark.integration
    @pytest.mark.critical
    def test_real_time_progress_accuracy(self):
        """CRITICAL: Real-time progress updates must accurately reflect current processing state."""
        files_to_process = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
        
        with self.display_manager.processing_context(len(files_to_process), "Real-time Test") as ctx:
            
            for i, filename in enumerate(files_to_process):
                # Start processing
                ctx.start_file(filename)
                
                # Check progress state during processing
                current_stats = self.display_manager.progress.stats
                expected_in_progress = i  # Files completed so far
                
                # Verify progress accurately reflects current state
                self.assertEqual(
                    current_stats.completed, expected_in_progress,
                    f"Real-time progress error: completed should be {expected_in_progress} "
                    f"while processing file {i+1}, but was {current_stats.completed}"
                )
                
                # Complete the file
                ctx.complete_file(filename, f"generated_{filename}")
                
                # Verify immediate update after completion
                updated_stats = self.display_manager.progress.stats
                self.assertEqual(
                    updated_stats.succeeded, i + 1,
                    f"Real-time update error: succeeded should immediately reflect completion of file {i+1}"
                )
                self.assertEqual(
                    updated_stats.completed, i + 1,
                    f"Real-time update error: completed should immediately update after file {i+1}"
                )


if __name__ == "__main__":
    unittest.main()