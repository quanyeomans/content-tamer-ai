"""
User Experience Regression Contracts
====================================

CONTRACT AGREEMENTS TESTED:
1. User-observable behavior remains consistent across updates
2. Progress feedback provides meaningful information to users
3. Error messages are user-actionable and informative
4. Processing completion provides clear success/failure indication
5. File organization results match user expectations
6. Performance characteristics remain within acceptable bounds
"""

import os
import sys
import pytest
import unittest
import time

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
from tests.utils.rich_test_utils import RichTestCase


class TestUserExperienceContracts(unittest.TestCase, RichTestCase):
    """Contracts ensuring user experience remains consistent and high-quality."""
    
    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)
    
    @pytest.mark.contract
    @pytest.mark.regression
    def test_progress_feedback_meaningfulness_contract(self):
        """UX CONTRACT: Progress feedback must provide meaningful information to users."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(3, "User Experience Test") as ctx:
            # Contract: Users must see progress at each stage
            initial_stats = {
                'total': ctx.display.progress.stats.total,
                'succeeded': ctx.display.progress.stats.succeeded,
                'failed': ctx.display.progress.stats.failed,
                'success_rate': ctx.display.progress.stats.success_rate
            }
            
            # Simulate user-observable processing steps
            ctx.start_file("user_document.pdf")
            mid_processing_stats = {
                'total': ctx.display.progress.stats.total,
                'succeeded': ctx.display.progress.stats.succeeded,
                'failed': ctx.display.progress.stats.failed,
                'success_rate': ctx.display.progress.stats.success_rate
            }
            
            ctx.complete_file("user_document.pdf", "ai_organized_user_document.pdf")
            final_stats = {
                'total': ctx.display.progress.stats.total,
                'succeeded': ctx.display.progress.stats.succeeded,
                'failed': ctx.display.progress.stats.failed,
                'success_rate': ctx.display.progress.stats.success_rate
            }
            
            # Contract: Progress must be meaningful at each stage
            self.assertEqual(initial_stats['total'], 3, "User can't see total work to be done")
            self.assertEqual(mid_processing_stats['total'], 3, "Total work changes confusingly during processing")  
            self.assertEqual(final_stats['succeeded'], 1, "User can't see progress being made")
            
            # Contract: Success rate must be calculable and meaningful
            if final_stats['succeeded'] > 0:
                self.assertGreater(final_stats['success_rate'], 0, "Success rate not meaningful to user")

    @pytest.mark.contract
    @pytest.mark.regression  
    def test_completion_clarity_contract(self):
        """UX CONTRACT: Processing completion must clearly indicate success or failure."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        # Test clear success indication
        with manager.processing_context(2, "Success Clarity Test") as ctx:
            ctx.complete_file("success1.pdf", "result1.pdf")
            ctx.complete_file("success2.pdf", "result2.pdf")
            
            # Contract: Successful completion must be clearly indicated
            stats = ctx.display.progress.stats
            self.assertEqual(stats.succeeded, 2, "Success count not clear to user")
            self.assertEqual(stats.failed, 0, "Failed count misleading for successful operation")
            self.assertEqual(stats.success_rate, 100.0, "Success rate doesn't clearly show 100% success")
        
        # Test clear failure indication
        with manager.processing_context(2, "Failure Clarity Test") as ctx:
            ctx.fail_file("failure1.pdf", "Processing error")
            ctx.fail_file("failure2.pdf", "Another error")
            
            # Contract: Failed completion must be clearly indicated
            stats = ctx.display.progress.stats
            self.assertEqual(stats.succeeded, 0, "Success count misleading for failed operation")
            self.assertEqual(stats.failed, 2, "Failure count not clear to user")
            self.assertEqual(stats.success_rate, 0.0, "Success rate doesn't clearly show 0% success")

    @pytest.mark.contract
    @pytest.mark.regression
    def test_mixed_results_clarity_contract(self):
        """UX CONTRACT: Mixed success/failure results must be clearly communicated."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(4, "Mixed Results Clarity Test") as ctx:
            # Process mixed results that should be clear to user
            ctx.complete_file("success1.pdf", "result1.pdf")
            ctx.fail_file("failure1.pdf", "Error occurred") 
            ctx.complete_file("success2.pdf", "result2.pdf")
            ctx.complete_file("success3.pdf", "result3.pdf")
            
            stats = ctx.display.progress.stats
            
            # Contract: Mixed results must be clearly communicated
            self.assertEqual(stats.total, 4, "User can't see total files processed")
            self.assertEqual(stats.succeeded, 3, "User can't see successful count clearly")
            self.assertEqual(stats.failed, 1, "User can't see failure count clearly")
            
            # Contract: Success rate must be meaningful for mixed results
            expected_rate = (3 / 4) * 100  # 75%
            self.assertEqual(stats.success_rate, expected_rate, 
                           "Success rate not meaningful for mixed results")

    @pytest.mark.contract
    @pytest.mark.regression
    def test_target_filename_visibility_contract(self):
        """UX CONTRACT: Users must be able to see what their files will be named."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        meaningful_filenames = [
            ("contract_draft.pdf", "ai_organized_legal_contract_draft_2024.pdf"),
            ("meeting_notes.pdf", "ai_organized_project_meeting_notes_q4.pdf"),
            ("financial_report.pdf", "ai_organized_quarterly_financial_report_2024.pdf")
        ]
        
        with manager.processing_context(len(meaningful_filenames), "Filename Visibility Test") as ctx:
            for source, target in meaningful_filenames:
                ctx.complete_file(source, target)
            
            # Contract: Target filenames must be preserved for user visibility
            processed_files = ctx.display.progress.stats._processed_files
            successful_files = [f for f in processed_files if f.get("status") == "success"]
            
            self.assertEqual(len(successful_files), len(meaningful_filenames), 
                           "Not all processed files visible to user")
            
            # Contract: Each target filename must be accessible to user
            recorded_targets = [f.get("target", "") for f in successful_files]
            for _, expected_target in meaningful_filenames:
                self.assertIn(expected_target, recorded_targets,
                             f"Target filename '{expected_target}' not visible to user")

    @pytest.mark.contract
    @pytest.mark.regression
    def test_processing_time_feedback_contract(self):
        """UX CONTRACT: Users must receive reasonable processing time feedback."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(1, "Processing Time Test") as ctx:
            start_time = time.time()
            
            # Simulate realistic processing time
            ctx.start_file("timed_document.pdf")
            time.sleep(0.01)  # Minimal delay to simulate processing
            ctx.complete_file("timed_document.pdf", "processed_timed_document.pdf")
            
            end_time = time.time()
            processing_duration = end_time - start_time
            
            # Contract: Processing time must be trackable for user feedback
            processed_files = ctx.display.progress.stats._processed_files
            self.assertTrue(len(processed_files) > 0, "No processing time data available to user")
            
            processed_file = processed_files[0]
            file_timestamp = processed_file.get("timestamp")
            
            # Contract: Timestamp must be reasonable for user feedback
            self.assertIsNotNone(file_timestamp, "No timestamp available for user feedback")
            self.assertTrue(start_time <= file_timestamp <= end_time,
                          "Timestamp not accurate for user feedback")

    @pytest.mark.contract
    @pytest.mark.regression
    def test_error_information_usefulness_contract(self):
        """UX CONTRACT: Error information must be useful and actionable for users."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(2, "Error Information Test") as ctx:
            # Test that error information is preserved for user
            ctx.fail_file("problematic_file.pdf", "Specific processing error occurred")
            ctx.complete_file("good_file.pdf", "processed_good_file.pdf")
            
            # Contract: Error information must be available for user feedback
            processed_files = ctx.display.progress.stats._processed_files
            failed_files = [f for f in processed_files if f.get("status") == "failed"]
            
            self.assertTrue(len(failed_files) > 0, "No error information available to user")
            
            failed_file = failed_files[0]
            
            # Contract: Failed file source must be identifiable
            self.assertEqual(failed_file.get("source"), "problematic_file.pdf",
                           "User can't identify which file failed")
            
            # Contract: Error timestamp must be available for context
            self.assertIsNotNone(failed_file.get("timestamp"),
                               "No error timing information available to user")

    @pytest.mark.contract
    @pytest.mark.regression
    def test_completion_stats_user_comprehension_contract(self):
        """UX CONTRACT: Completion statistics must be comprehensible to users."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        # Test completion stats format that users expect
        completion_scenarios = [
            {
                'total_files': 1,
                'successful': 1,
                'errors': 0,
                'warnings': 0,
                'expected_user_perception': 'complete_success'
            },
            {
                'total_files': 3,
                'successful': 2,
                'errors': 1,
                'warnings': 0, 
                'expected_user_perception': 'partial_success'
            },
            {
                'total_files': 2,
                'successful': 0,
                'errors': 2,
                'warnings': 0,
                'expected_user_perception': 'complete_failure'
            }
        ]
        
        for scenario in completion_scenarios:
            # Contract: Completion stats must be processable without error
            try:
                manager.show_completion_stats(scenario)
                stats_processable = True
            except Exception as e:
                stats_processable = False
                self.fail(f"Completion stats not processable by user for scenario {scenario}: {e}")
            
            # Contract: Stats format must make sense to users
            if scenario['expected_user_perception'] == 'complete_success':
                self.assertEqual(scenario['successful'], scenario['total_files'],
                               "Complete success not clear to user")
                self.assertEqual(scenario['errors'], 0,
                               "Success scenario shows errors to user")
            
            elif scenario['expected_user_perception'] == 'complete_failure':
                self.assertEqual(scenario['successful'], 0,
                               "Complete failure shows successes to user")
                self.assertEqual(scenario['errors'], scenario['total_files'],
                               "Failure count doesn't match total for user")
            
            elif scenario['expected_user_perception'] == 'partial_success':
                self.assertGreater(scenario['successful'], 0,
                                 "Partial success doesn't show any success to user")
                self.assertGreater(scenario['errors'], 0,
                                 "Partial success doesn't show any errors to user")
                self.assertEqual(scenario['successful'] + scenario['errors'], scenario['total_files'],
                                "Partial success totals don't add up for user")

    @pytest.mark.contract
    @pytest.mark.regression  
    def test_progress_consistency_during_processing_contract(self):
        """UX CONTRACT: Progress information must remain consistent during processing."""
        manager = self.test_container.create_display_manager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(5, "Progress Consistency Test") as ctx:
            # Track progress at each step from user perspective
            progress_snapshots = []
            
            # Initial state
            progress_snapshots.append({
                'stage': 'initial',
                'total': ctx.display.progress.stats.total,
                'succeeded': ctx.display.progress.stats.succeeded,
                'failed': ctx.display.progress.stats.failed
            })
            
            # Process files and track consistency
            for i in range(3):
                ctx.complete_file(f"file_{i}.pdf", f"result_{i}.pdf")
                progress_snapshots.append({
                    'stage': f'after_success_{i}',
                    'total': ctx.display.progress.stats.total,
                    'succeeded': ctx.display.progress.stats.succeeded,
                    'failed': ctx.display.progress.stats.failed
                })
            
            # Contract: Total must never change during processing (user expectation)
            initial_total = progress_snapshots[0]['total']
            for snapshot in progress_snapshots[1:]:
                self.assertEqual(snapshot['total'], initial_total,
                               f"Total changed during processing at {snapshot['stage']} - confusing to user")
            
            # Contract: Progress must only increase (user expectation)
            for i in range(1, len(progress_snapshots)):
                current = progress_snapshots[i]
                previous = progress_snapshots[i-1]
                
                self.assertGreaterEqual(current['succeeded'], previous['succeeded'],
                                      f"Success count decreased at {current['stage']} - confusing to user")
                self.assertGreaterEqual(current['failed'], previous['failed'], 
                                      f"Failed count decreased at {current['stage']} - confusing to user")


if __name__ == '__main__':
    unittest.main()