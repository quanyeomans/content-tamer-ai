"""
End-to-End User Workflow Tests

Complete user journey tests from initial setup through file processing completion.
These tests address critical E2E coverage gaps identified in the test strategy analysis.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from core.application import organize_content
from core.file_processor import process_file_enhanced
from core.directory_manager import ensure_default_directories
from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
from ai_providers import AIProviderFactory


class TestE2EUserWorkflows(unittest.TestCase):
    """End-to-end tests for complete user workflows."""
    
    def setUp(self):
        """Set up test environment with temporary directories and files."""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, 'input')
        self.processed_dir = os.path.join(self.test_dir, 'processed')
        self.unprocessed_dir = os.path.join(self.test_dir, 'unprocessed')
        
        # Create directory structure
        os.makedirs(self.input_dir)
        os.makedirs(self.processed_dir)
        os.makedirs(self.unprocessed_dir)
        
        # Create test PDF files
        self.test_files = []
        for i in range(3):
            filename = f'test_document_{i+1}.pdf'
            filepath = os.path.join(self.input_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f'Test PDF content for document {i+1}\n' * 20)
            self.test_files.append(filename)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('builtins.input')
    @patch('ai_providers.OpenAIProvider.generate_filename')
    def test_first_time_user_complete_workflow(self, mock_generate, mock_input):
        """
        E2E Test: First-time user complete workflow
        
        Journey: No API key → API key input → provider setup → file processing → completion
        """
        # Mock user inputs for API key setup
        mock_input.side_effect = [
            'sk-test1234567890abcdef1234567890abcdef12345678',  # API key input
            'y'  # Confirm processing
        ]
        
        # Mock AI provider response
        mock_generate.return_value = 'AI_Generated_Document_Analysis.pdf'
        
        # Create directory manager (simulates fresh user setup)
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        # Create display manager in quiet mode for testing
        display_manager = DisplayManager(quiet=True)
        
        # Create file processor (this triggers the full workflow)
        processor = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',  # Will be auto-detected from API key
            model='gpt-4o-mini',
            api_key=None  # Forces API key input workflow
        )
        
        # Execute the complete workflow
        stats = processor.process_files()
        
        # Verify complete workflow executed successfully
        self.assertIsNotNone(stats, "Processing stats should be returned")
        self.assertGreater(stats['successful'], 0, "Should have successful processed files")
        
        # Verify API key was set up correctly
        self.assertIsNotNone(processor.provider, "Provider should be initialized")
        
        # Verify files were processed
        processed_files = os.listdir(self.processed_dir)
        self.assertGreater(len(processed_files), 0, "Should have processed files")
        
        # Verify input directory is cleaned up
        remaining_files = [f for f in os.listdir(self.input_dir) 
                          if f.endswith('.pdf')]
        self.assertEqual(len(remaining_files), 0, "Input directory should be empty")
        
        # Verify mock was called for each file
        self.assertEqual(mock_generate.call_count, 3, "Should process all 3 files")
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    @patch('ai_providers.ClaudeProvider.generate_filename')
    def test_multi_provider_workflow(self, mock_claude, mock_openai):
        """
        E2E Test: Multi-provider workflow
        
        Tests switching between different AI providers in the same session
        """
        # Set up API keys for both providers
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890abcdef1234567890abcdef12345678'
        os.environ['CLAUDE_API_KEY'] = 'sk-ant-test1234567890abcdef1234567890abcdef'
        
        # Mock provider responses with different naming patterns
        mock_openai.return_value = 'OpenAI_Generated_Filename.pdf'
        mock_claude.return_value = 'Claude_Generated_Analysis.pdf'
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        # Test with OpenAI first
        processor_openai = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',
            model='gpt-4o-mini'
        )
        
        # Process first file with OpenAI
        stats_openai = processor_openai.process_files()
        
        # Create new test file for Claude
        claude_file = os.path.join(self.input_dir, 'claude_test.pdf')
        with open(claude_file, 'w') as f:
            f.write('Test content for Claude processing\n' * 20)
        
        # Test with Claude
        processor_claude = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='claude',
            model='claude-3-5-sonnet-20241022'
        )
        
        stats_claude = processor_claude.process_files()
        
        # Verify both providers worked
        self.assertGreater(stats_openai['successful'], 0, "OpenAI should process files")
        self.assertGreater(stats_claude['successful'], 0, "Claude should process files")
        
        # Verify different naming patterns were used
        mock_openai.assert_called()
        mock_claude.assert_called()
        
        # Verify processed files exist
        processed_files = os.listdir(self.processed_dir)
        self.assertGreater(len(processed_files), 3, "Should have files from both providers")
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    @patch('time.sleep')  # Speed up retry delays
    def test_error_recovery_workflow(self, mock_sleep, mock_generate):
        """
        E2E Test: Error recovery workflow
        
        Tests system behavior when encountering errors and recovering
        """
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890abcdef1234567890abcdef12345678'
        
        # Mock API to fail first, then succeed
        mock_generate.side_effect = [
            Exception("API rate limit exceeded"),  # First call fails
            Exception("Temporary network error"),   # Second call fails  
            'Recovered_Document_Analysis.pdf',      # Third call succeeds
            'Second_Document_Success.pdf',          # Fourth call succeeds
            'Third_Document_Success.pdf'            # Fifth call succeeds
        ]
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        processor = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',
            model='gpt-4o-mini',
            max_retries=3  # Allow retries for error recovery
        )
        
        # Execute processing with error recovery
        stats = processor.process_files()
        
        # Verify error recovery worked
        self.assertIsNotNone(stats, "Should return stats even with initial errors")
        
        # Should have some successful files after recovery
        self.assertGreater(stats['successful'], 0, "Should recover and process files")
        
        # Verify retry mechanism was used
        self.assertGreaterEqual(mock_generate.call_count, 3, "Should retry failed calls")
    
    @patch('shutil.move')  # Mock file operations to test file lock scenarios
    @patch('ai_providers.OpenAIProvider.generate_filename')
    def test_file_lock_recovery_workflow(self, mock_generate, mock_move):
        """
        E2E Test: File lock recovery workflow
        
        Tests recovery when files are locked (e.g., by antivirus)
        """
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890abcdef1234567890abcdef12345678'
        
        mock_generate.return_value = 'Unlocked_Document.pdf'
        
        # Simulate file lock on first attempt, success on second
        mock_move.side_effect = [
            PermissionError("File is locked by another process"),  # First attempt
            None,  # Second attempt succeeds
            None,  # Third file succeeds immediately
            None   # Fourth file succeeds immediately
        ]
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        processor = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',
            model='gpt-4o-mini'
        )
        
        # Execute processing with file lock recovery
        stats = processor.process_files()
        
        # Verify file lock recovery
        self.assertIsNotNone(stats, "Should handle file lock scenarios")
        
        # Should eventually succeed after retry
        self.assertGreaterEqual(stats['successful'], 2, "Should recover from file locks")
    
    @patch('builtins.input')
    @patch('ai_providers.OpenAIProvider.generate_filename')
    def test_mixed_success_failure_workflow(self, mock_generate, mock_input):
        """
        E2E Test: Mixed success and failure workflow
        
        Tests system behavior with mix of successful and failed files
        """
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890abcdef1234567890abcdef12345678'
        
        # Create one corrupted file
        corrupted_file = os.path.join(self.input_dir, 'corrupted.pdf')
        with open(corrupted_file, 'wb') as f:
            f.write(b'Not a valid PDF file - corrupted content')
        
        # Mock responses: success for normal files, failure for corrupted
        mock_generate.side_effect = [
            'Successfully_Processed_1.pdf',
            'Successfully_Processed_2.pdf', 
            'Successfully_Processed_3.pdf',
            Exception("Failed to extract text from corrupted file")
        ]
        
        mock_input.return_value = 'y'  # Confirm processing
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        processor = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',
            model='gpt-4o-mini'
        )
        
        # Execute mixed workflow
        stats = processor.process_files()
        
        # Verify mixed results handling
        self.assertEqual(stats['successful'], 3, "Should process 3 valid files")
        self.assertEqual(stats['failed'], 1, "Should fail on 1 corrupted file")
        self.assertEqual(stats['total_files'], 4, "Should attempt all 4 files")
        
        # Verify success rate calculation
        expected_rate = (3 / 4) * 100  # 75%
        self.assertAlmostEqual(stats['success_rate'], expected_rate, places=1)
        
        # Verify file organization
        processed_files = os.listdir(self.processed_dir)
        unprocessed_files = os.listdir(self.unprocessed_dir)
        
        self.assertEqual(len(processed_files), 3, "Should have 3 successfully processed files")
        self.assertEqual(len(unprocessed_files), 1, "Should have 1 failed file in unprocessed")
    
    def test_directory_validation_workflow(self):
        """
        E2E Test: Directory validation workflow
        
        Tests system behavior with invalid directory configurations
        """
        # Test with non-existent input directory
        invalid_input_dir = '/nonexistent/input'
        
        with self.assertRaises(FileNotFoundError):
            DirectoryManager(
                input_folder=invalid_input_dir,
                processed_folder=self.processed_dir,
                unprocessed_folder=self.unprocessed_dir
            )
        
        # Test with permission-denied directory
        restricted_dir = os.path.join(self.test_dir, 'restricted')
        os.makedirs(restricted_dir, mode=0o000)  # No permissions
        
        try:
            # This should handle permission errors gracefully
            directory_manager = DirectoryManager(
                input_folder=self.input_dir,
                processed_folder=restricted_dir,  # No write permission
                unprocessed_folder=self.unprocessed_dir
            )
            
            display_manager = DisplayManager(quiet=True)
            
            processor = FileProcessor(
                directory_manager=directory_manager,
                display_manager=display_manager,
                provider='openai',
                model='gpt-4o-mini'
            )
            
            # Should handle permission errors gracefully
            stats = processor.process_files()
            self.assertIsNotNone(stats, "Should return stats even with permission errors")
            
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_dir, 0o755)


class TestE2EIntegrationScenarios(unittest.TestCase):
    """Integration scenarios testing multiple system components together."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, 'input')
        self.processed_dir = os.path.join(self.test_dir, 'processed')
        self.unprocessed_dir = os.path.join(self.test_dir, 'unprocessed')
        
        os.makedirs(self.input_dir)
        os.makedirs(self.processed_dir)
        os.makedirs(self.unprocessed_dir)
    
    def tearDown(self):
        """Clean up integration test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    def test_large_batch_processing_workflow(self, mock_generate):
        """
        E2E Test: Large batch processing workflow
        
        Tests system performance and stability with many files
        """
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890abcdef1234567890abcdef12345678'
        
        # Create 10 test files for batch processing
        test_files = []
        for i in range(10):
            filename = f'batch_document_{i+1:02d}.pdf'
            filepath = os.path.join(self.input_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f'Batch test document {i+1} content\n' * 10)
            test_files.append(filename)
        
        # Mock AI responses for all files
        mock_generate.side_effect = [
            f'Batch_Processed_Document_{i+1:02d}.pdf' for i in range(10)
        ]
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        processor = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',
            model='gpt-4o-mini'
        )
        
        # Execute batch processing
        stats = processor.process_files()
        
        # Verify batch processing completed successfully
        self.assertEqual(stats['successful'], 10, "Should process all 10 files")
        self.assertEqual(stats['failed'], 0, "Should have no failures")
        self.assertEqual(stats['total_files'], 10, "Should process 10 total files")
        self.assertEqual(stats['success_rate'], 100.0, "Should have 100% success rate")
        
        # Verify all files were processed
        processed_files = os.listdir(self.processed_dir)
        self.assertEqual(len(processed_files), 10, "Should have 10 processed files")
        
        # Verify input directory is empty
        remaining_input = [f for f in os.listdir(self.input_dir) if f.endswith('.pdf')]
        self.assertEqual(len(remaining_input), 0, "Input directory should be empty")


if __name__ == '__main__':
    # Run with verbose output to see E2E test progress
    unittest.main(verbosity=2)