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
import pytest
import unittest

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions


class TestDataFlowContracts(unittest.TestCase):
    """Contracts ensuring data flows correctly from processing to user display."""
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_file_success_flows_to_progress_stats_contract(self):
        """CONTRACT: Successful file processing must increment progress.stats.succeeded."""
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(3, "Data Flow Test") as ctx:
            initial_succeeded = ctx.display.progress.stats.succeeded
            
            # Contract: File success must flow to progress stats
            ctx.complete_file("test1.pdf", "result1.pdf")
            
            final_succeeded = ctx.display.progress.stats.succeeded
            
            self.assertEqual(
                final_succeeded, initial_succeeded + 1,
                "File success did not flow to progress.stats.succeeded"
            )

    @pytest.mark.contract  
    @pytest.mark.critical
    def test_file_failure_flows_to_progress_stats_contract(self):
        """CONTRACT: Failed file processing must increment progress.stats.failed."""
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(3, "Data Flow Test") as ctx:
            initial_failed = ctx.display.progress.stats.failed
            
            # Contract: File failure must flow to progress stats
            ctx.fail_file("test1.pdf", "Processing error")
            
            final_failed = ctx.display.progress.stats.failed
            
            self.assertEqual(
                final_failed, initial_failed + 1,
                "File failure did not flow to progress.stats.failed"
            )

    @pytest.mark.contract
    @pytest.mark.critical  
    def test_progress_stats_sync_with_success_rate_contract(self):
        """CONTRACT: Progress stats must automatically sync with calculated success rate."""
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(4, "Data Flow Test") as ctx:
            # Process mixed results: 3 success, 1 failure = 75%
            ctx.complete_file("success1.pdf", "result1.pdf")
            ctx.complete_file("success2.pdf", "result2.pdf") 
            ctx.complete_file("success3.pdf", "result3.pdf")
            ctx.fail_file("failure1.pdf", "Error")
            
            # Contract: Success rate must automatically sync with progress stats
            stats = ctx.display.progress.stats
            expected_rate = (stats.succeeded / stats.total) * 100
            
            self.assertEqual(
                stats.success_rate, expected_rate,
                f"Success rate {stats.success_rate}% doesn't match calculated {expected_rate}%"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_processed_files_list_reflects_actual_processing_contract(self):
        """CONTRACT: Processed files list must contain all actually processed files."""
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        processed_filenames = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
        
        with manager.processing_context(len(processed_filenames), "Data Flow Test") as ctx:
            # Process files with known names
            ctx.complete_file(processed_filenames[0], "result1.pdf")
            ctx.fail_file(processed_filenames[1], "Processing error")
            ctx.complete_file(processed_filenames[2], "result3.pdf")
            
            # Contract: All processed files must appear in processed files list
            processed_files = ctx.display.progress.stats._processed_files
            source_files = [f.get("source", "") for f in processed_files]
            
            for filename in processed_filenames:
                self.assertIn(
                    filename, source_files,
                    f"Processed file '{filename}' not found in processed files list"
                )

    @pytest.mark.contract
    @pytest.mark.critical  
    def test_error_details_flow_to_completion_stats_contract(self):
        """CONTRACT: Error details from processing must be available for completion display."""
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(2, "Data Flow Test") as ctx:
            ctx.complete_file("success.pdf", "result.pdf")
            ctx.fail_file("failure.pdf", "Specific processing error")
            
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
                failed_file.get("source"), "failure.pdf",
                "Failed file source not properly recorded"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_target_filename_data_flow_contract(self):
        """CONTRACT: Target filenames must flow from processing to completion display.""" 
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        target_filenames = ["organized_document_1.pdf", "organized_document_2.pdf"]
        
        with manager.processing_context(len(target_filenames), "Data Flow Test") as ctx:
            ctx.complete_file("input1.pdf", target_filenames[0])
            ctx.complete_file("input2.pdf", target_filenames[1])
            
            # Contract: Target filenames must be preserved in data flow
            processed_files = ctx.display.progress.stats._processed_files
            successful_files = [f for f in processed_files if f.get("status") == "success"]
            recorded_targets = [f.get("target", "") for f in successful_files]
            
            for target in target_filenames:
                self.assertIn(
                    target, recorded_targets,
                    f"Target filename '{target}' not preserved in data flow"
                )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_processing_timestamps_data_flow_contract(self):
        """CONTRACT: Processing timestamps must be recorded for completion analysis."""
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(1, "Data Flow Test") as ctx:
            import time
            start_time = time.time()
            
            ctx.complete_file("timestamped.pdf", "result.pdf")
            
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
                f"Recorded timestamp {recorded_timestamp} outside processing window [{start_time}, {end_time}]"
            )

    @pytest.mark.contract
    @pytest.mark.critical
    def test_counter_synchronization_across_operations_contract(self):
        """CONTRACT: All progress counters must remain synchronized during operations."""
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(5, "Data Flow Test") as ctx:
            # Mix of operations to test synchronization
            operations = [
                ("success1.pdf", "result1.pdf", "complete"),
                ("failure1.pdf", "", "fail"),
                ("success2.pdf", "result2.pdf", "complete"),
                ("failure2.pdf", "", "fail"), 
                ("success3.pdf", "result3.pdf", "complete")
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
                    f"Total processed ({total_processed}) exceeds declared total ({stats.total})"
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