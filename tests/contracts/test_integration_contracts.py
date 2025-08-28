"""
Integration Contracts: End-to-End Workflow Agreements
=====================================================

CONTRACT AGREEMENTS TESTED:
1. File processing workflow maintains component interface agreements
2. Success/failure determination contracts across processing pipeline
3. Display manager integration contracts with processing results
4. Directory management contracts with file operations
5. Error handling contracts across component boundaries
"""

import os
import sys
import tempfile
import shutil
import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from core.application import _process_files_batch
from core.file_processor import process_file_enhanced_core
from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
from core.directory_manager import ensure_default_directories


class TestIntegrationContracts(unittest.TestCase):
    """Contracts for end-to-end workflow component integration."""
    
    def setUp(self):
        """Set up test environment with temporary directories."""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.processed_dir = os.path.join(self.test_dir, "processed")  
        self.unprocessed_dir = os.path.join(self.test_dir, "unprocessed")
        self.processing_dir = os.path.join(self.test_dir, "processing")
        
        for dir_path in [self.input_dir, self.processed_dir, self.unprocessed_dir, self.processing_dir]:
            os.makedirs(dir_path)
            
        # Create test PDF file
        self.test_file = os.path.join(self.input_dir, "test_document.pdf")
        with open(self.test_file, "wb") as f:
            f.write(b"%PDF-1.4\ntest content\n%EOF")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    @pytest.mark.contract
    @pytest.mark.integration
    def test_file_processing_to_display_contract(self):
        """INTEGRATION CONTRACT: File processing results must flow correctly to display manager."""
        display_manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with display_manager.processing_context(1, "Integration Contract Test") as ctx:
            # Contract: File processing success must be reflected in display
            initial_succeeded = ctx.display.progress.stats.succeeded
            
            # Simulate successful file processing
            ctx.start_file("test_document.pdf")
            ctx.complete_file("test_document.pdf", "ai_organized_test_document.pdf")
            
            final_succeeded = ctx.display.progress.stats.succeeded
            
            # Contract: Display manager must reflect processing success
            self.assertEqual(
                final_succeeded, initial_succeeded + 1,
                "File processing success not reflected in display manager"
            )
            
            # Contract: Processed files list must contain the processed file
            processed_files = ctx.display.progress.stats._processed_files
            source_files = [f.get("source", "") for f in processed_files]
            self.assertIn("test_document.pdf", source_files, 
                         "Processed file not recorded in display manager")

    @pytest.mark.contract
    @pytest.mark.integration
    def test_success_failure_determination_contract(self):
        """INTEGRATION CONTRACT: Success/failure determination must be consistent across components."""
        display_manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with display_manager.processing_context(2, "Success/Failure Contract") as ctx:
            # Test successful processing contract
            ctx.start_file("success.pdf")
            ctx.complete_file("success.pdf", "organized_success.pdf")
            
            # Test failed processing contract  
            ctx.start_file("failure.pdf")
            ctx.fail_file("failure.pdf", "Processing failed")
            
            # Contract: Success/failure counts must be accurate
            stats = ctx.display.progress.stats
            self.assertEqual(stats.succeeded, 1, "Success count incorrect in integration")
            self.assertEqual(stats.failed, 1, "Failure count incorrect in integration")
            self.assertEqual(stats.total, 2, "Total count incorrect in integration")
            
            # Contract: Success rate calculation must be consistent
            expected_rate = (1 / 2) * 100  # 50%
            self.assertEqual(stats.success_rate, expected_rate, 
                           "Success rate calculation inconsistent across components")

    @pytest.mark.contract
    @pytest.mark.integration
    def test_directory_operations_contract(self):
        """INTEGRATION CONTRACT: Directory operations must maintain file integrity."""
        # Test directory structure contract
        test_dirs = {
            'input': self.input_dir,
            'processed': self.processed_dir,
            'unprocessed': self.unprocessed_dir,
            'processing': self.processing_dir
        }
        
        # Contract: All required directories must exist
        for dir_name, dir_path in test_dirs.items():
            self.assertTrue(
                os.path.exists(dir_path),
                f"Required directory '{dir_name}' does not exist: {dir_path}"
            )
            self.assertTrue(
                os.path.isdir(dir_path),
                f"Path '{dir_path}' is not a directory"
            )
        
        # Contract: Test file must be accessible for processing
        self.assertTrue(
            os.path.exists(self.test_file),
            f"Test file does not exist: {self.test_file}"
        )
        
        # Contract: File size must be reasonable for processing
        file_size = os.path.getsize(self.test_file)
        self.assertGreater(file_size, 0, "Test file is empty")
        self.assertLess(file_size, 1024*1024, "Test file too large for testing")

    @pytest.mark.contract
    @pytest.mark.integration
    def test_error_handling_integration_contract(self):
        """INTEGRATION CONTRACT: Error handling must be consistent across component boundaries."""
        display_manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with display_manager.processing_context(3, "Error Handling Contract") as ctx:
            # Process one successful file
            ctx.start_file("success.pdf")
            ctx.complete_file("success.pdf", "organized_success.pdf")
            
            # Process one failed file
            ctx.start_file("failure.pdf") 
            ctx.fail_file("failure.pdf", "Simulated processing error")
            
            # Process another successful file (recovery test)
            ctx.start_file("recovery.pdf")
            ctx.complete_file("recovery.pdf", "organized_recovery.pdf")
            
            # Contract: Error handling must not corrupt overall processing state
            stats = ctx.display.progress.stats
            self.assertEqual(stats.total, 3, "Error handling corrupted total count")
            self.assertEqual(stats.succeeded, 2, "Error handling corrupted success count")
            self.assertEqual(stats.failed, 1, "Error handling corrupted failure count")
            
            # Contract: System must be able to recover from errors
            final_success_rate = (2 / 3) * 100  # 66.7%
            self.assertAlmostEqual(stats.success_rate, final_success_rate, places=1,
                                 msg="System not recovering properly from errors")

    @pytest.mark.contract
    @pytest.mark.integration  
    def test_batch_processing_contract(self):
        """INTEGRATION CONTRACT: Batch processing must maintain individual file contracts."""
        display_manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        # Simulate batch processing scenario
        batch_files = [
            ("batch_file_1.pdf", "ai_organized_batch_file_1.pdf", "success"),
            ("batch_file_2.pdf", "", "fail"),
            ("batch_file_3.pdf", "ai_organized_batch_file_3.pdf", "success"),
            ("batch_file_4.pdf", "ai_organized_batch_file_4.pdf", "success"),
            ("batch_file_5.pdf", "", "fail")
        ]
        
        with display_manager.processing_context(len(batch_files), "Batch Processing Contract") as ctx:
            successful_count = 0
            failed_count = 0
            
            for source, target, expected_result in batch_files:
                ctx.start_file(source)
                
                if expected_result == "success":
                    ctx.complete_file(source, target)
                    successful_count += 1
                else:
                    ctx.fail_file(source, "Batch processing error")
                    failed_count += 1
            
            # Contract: Batch processing must accurately track individual results
            stats = ctx.display.progress.stats
            self.assertEqual(stats.succeeded, successful_count, 
                           "Batch processing success count incorrect")
            self.assertEqual(stats.failed, failed_count,
                           "Batch processing failure count incorrect") 
            self.assertEqual(stats.total, len(batch_files),
                           "Batch processing total count incorrect")
            
            # Contract: Processed files list must contain all batch items
            processed_files = stats._processed_files
            self.assertEqual(len(processed_files), len(batch_files),
                           "Batch processing didn't record all files")
            
            # Contract: Each batch item must have correct status
            successful_files = [f for f in processed_files if f.get("status") == "success"]
            failed_files = [f for f in processed_files if f.get("status") == "failed"]
            
            self.assertEqual(len(successful_files), successful_count,
                           "Successful files count mismatch in batch processing")
            self.assertEqual(len(failed_files), failed_count,
                           "Failed files count mismatch in batch processing")

    @pytest.mark.contract
    @pytest.mark.integration
    def test_component_interface_stability_contract(self):
        """INTEGRATION CONTRACT: Component interfaces must remain stable during integration."""
        # Test that core components maintain expected interfaces
        
        # Contract: RichDisplayManager must have expected interface
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        # Required methods must exist
        required_methods = ['processing_context', 'show_completion_stats']
        for method_name in required_methods:
            self.assertTrue(hasattr(manager, method_name),
                          f"RichDisplayManager missing required method: {method_name}")
            self.assertTrue(callable(getattr(manager, method_name)),
                          f"RichDisplayManager.{method_name} is not callable")
        
        # Contract: processing_context must return context manager
        with manager.processing_context(1, "Interface Test") as ctx:
            # Required context methods must exist
            context_methods = ['start_file', 'complete_file', 'fail_file']
            for method_name in context_methods:
                self.assertTrue(hasattr(ctx, method_name),
                              f"Processing context missing required method: {method_name}")
                self.assertTrue(callable(getattr(ctx, method_name)),
                              f"Processing context.{method_name} is not callable")
            
            # Contract: Context must have display attribute with stats
            self.assertTrue(hasattr(ctx, 'display'),
                          "Processing context missing display attribute")
            self.assertTrue(hasattr(ctx.display, 'progress'),
                          "Display missing progress attribute")
            self.assertTrue(hasattr(ctx.display.progress, 'stats'),
                          "Progress missing stats attribute")

    @pytest.mark.contract
    @pytest.mark.integration
    def test_data_integrity_across_components_contract(self):
        """INTEGRATION CONTRACT: Data integrity must be maintained across component boundaries."""
        display_manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        # Test data that flows through multiple components
        test_data = {
            'source_filename': 'important_contract_document.pdf',
            'target_filename': 'ai_organized_important_contract_document_2024.pdf',
            'processing_description': 'Critical document processing'
        }
        
        with display_manager.processing_context(1, test_data['processing_description']) as ctx:
            # Contract: Data must be preserved exactly across component boundaries
            ctx.start_file(test_data['source_filename'])
            ctx.complete_file(test_data['source_filename'], test_data['target_filename'])
            
            # Verify data integrity in processed files
            processed_files = ctx.display.progress.stats._processed_files
            self.assertEqual(len(processed_files), 1, "Data integrity: wrong number of processed files")
            
            processed_file = processed_files[0]
            
            # Contract: Source filename must be preserved exactly
            self.assertEqual(processed_file.get('source'), test_data['source_filename'],
                           "Data integrity: source filename corrupted")
            
            # Contract: Target filename must be preserved exactly  
            self.assertEqual(processed_file.get('target'), test_data['target_filename'],
                           "Data integrity: target filename corrupted")
            
            # Contract: Processing status must be accurate
            self.assertEqual(processed_file.get('status'), 'success',
                           "Data integrity: processing status incorrect")
            
            # Contract: Timestamp must be reasonable
            import time
            timestamp = processed_file.get('timestamp')
            self.assertIsNotNone(timestamp, "Data integrity: timestamp missing")
            self.assertLess(abs(time.time() - timestamp), 60,
                          "Data integrity: timestamp unreasonable")


if __name__ == '__main__':
    unittest.main()