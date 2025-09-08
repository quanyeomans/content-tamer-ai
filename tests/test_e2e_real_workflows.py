"""
Real E2E User Workflow Tests

Tests that use the actual application API (organize_content) to validate 
complete user journeys from start to finish. These tests mirror the 
actual CLI usage patterns described in the README.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import shutil
from pathlib import Path
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from core.application import organize_content
from core.directory_manager import ensure_default_directories


class TestRealUserWorkflows(unittest.TestCase):
    """Real E2E tests using the actual application API."""
    
    def setUp(self):
        """Set up test environment with temporary directories and test files."""
        self.test_dir = tempfile.mkdtemp(prefix="e2e_test_")
        self.input_dir = os.path.join(self.test_dir, 'input')
        self.processed_dir = os.path.join(self.test_dir, 'processed')
        self.unprocessed_dir = os.path.join(self.test_dir, 'unprocessed')
        
        # Create directory structure
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.unprocessed_dir, exist_ok=True)
        
        # Create realistic test files (not just empty files)
        self.create_test_files()
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """Create realistic test files that mimic user documents."""
        # Create 2 image files (easier to process than PDFs for E2E tests)
        img_file1 = os.path.join(self.input_dir, 'IMG_5432.jpg')
        with open(img_file1, 'wb') as f:
            # Minimal JPEG header that won't cause processing errors
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9')
        
        img_file2 = os.path.join(self.input_dir, 'Screenshot_2024-01-15.png')  
        with open(img_file2, 'wb') as f:
            # Minimal PNG header
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDAT\x08\x1dc\xf8\x00\x00\x00\x01\x00\x01u\x1b\xe0Y\x00\x00\x00\x00IEND\xaeB`\x82')
        
        img_file3 = os.path.join(self.input_dir, 'document_scan.jpg')
        with open(img_file3, 'wb') as f:
            # Another minimal JPEG
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9')
        
        self.test_files = ['IMG_5432.jpg', 'Screenshot_2024-01-15.png', 'document_scan.jpg']
    
    @patch('core.application._setup_display_manager')
    @patch('core.application.get_api_details')
    @patch('core.application.AIProviderFactory.create')
    def test_golden_path_user_workflow(self, mock_ai_factory, mock_get_api, mock_display_setup):
        """
        E2E Test: Golden path user workflow
        
        Journey: User has API key → drops files in input → runs content-tamer-ai → finds organized files
        Mirrors: README quick start example
        """
        # Mock API key (user has already set OPENAI_API_KEY)
        mock_get_api.return_value = 'sk-test1234567890abcdef1234567890abcdef12345678'
        
        # Mock AI provider with realistic responses
        mock_ai_provider = MagicMock()
        mock_ai_provider.generate_filename.side_effect = [
            'company_abc_consulting_invoice_jan_2024',
            'abc_company_consulting_services_receipt_january_2024', 
            'screenshot_application_interface_mobile_app'
        ]
        mock_ai_factory.return_value = mock_ai_provider
        
        # Mock display manager to avoid Rich I/O conflicts
        from tests.utils.test_display_manager import TestDisplayManager
        mock_display_manager = TestDisplayManager()
        mock_display_setup.return_value = mock_display_manager
        
        # Verify initial state
        self.assertEqual(len(os.listdir(self.input_dir)), 3, "Should start with 3 test files")
        self.assertEqual(len(os.listdir(self.processed_dir)), 0, "Processed dir should be empty")
        
        # Execute the main application workflow (this is what users actually run)
        success = organize_content(
            input_dir=self.input_dir,
            unprocessed_dir=self.unprocessed_dir,
            renamed_dir=self.processed_dir,
            provider='openai',
            model='gpt-4o',
            display_options={'quiet': True, 'no_color': True}
        )
        
        # Verify workflow completed successfully  
        self.assertTrue(success, "organize_content should return True for successful processing")
        
        # Verify files were processed (README promise: "intelligently renamed files in data/processed/")
        processed_files = os.listdir(self.processed_dir)
        self.assertGreaterEqual(len(processed_files), 3, "Should have at least 3 processed files")
        
        # Verify input directory is empty (files moved, not copied)
        input_files = os.listdir(self.input_dir)
        self.assertEqual(len(input_files), 0, "Input directory should be empty after processing")
        
        # Verify AI was called for each original file
        self.assertEqual(mock_ai_provider.generate_filename.call_count, 3, 
                        "AI should be called once per original file")
        
        # Verify meaningful filenames were applied - check that AI-generated names appear
        processed_content = ' '.join(processed_files)
        self.assertIn('company_abc_consulting_invoice_jan_2024', processed_content, 
                     "Should contain first AI-generated filename")
        self.assertIn('abc_company_consulting_services_receipt_january_2024', processed_content,
                     "Should contain second AI-generated filename")
        self.assertIn('screenshot_application_interface_mobile_app', processed_content,
                     "Should contain third AI-generated filename")
    
    @patch('core.application._setup_display_manager')
    @patch('core.application.get_api_details')
    @patch('core.application.AIProviderFactory.create')
    def test_mixed_success_failure_workflow(self, mock_ai_factory, mock_get_api, mock_display_setup):
        """
        E2E Test: Mixed success/failure workflow
        
        Journey: Some files succeed, some fail → user sees clear results → failed files in unprocessed
        """
        # Mock API key
        mock_get_api.return_value = 'sk-test1234567890abcdef1234567890abcdef12345678'
        
        # Mock display manager to avoid Rich I/O conflicts
        from tests.utils.test_display_manager import TestDisplayManager
        mock_display_manager = TestDisplayManager()
        mock_display_setup.return_value = mock_display_manager
        
        # Mock AI provider with mixed results
        mock_ai_provider = MagicMock()
        mock_ai_provider.generate_filename.side_effect = [
            'successful_document_analysis',  # First file succeeds
            Exception("AI service temporarily unavailable"),  # Second file fails
            'another_successful_analysis'  # Third file succeeds
        ]
        mock_ai_factory.return_value = mock_ai_provider
        
        # Execute workflow 
        success = organize_content(
            input_dir=self.input_dir,
            unprocessed_dir=self.unprocessed_dir,
            renamed_dir=self.processed_dir,
            provider='openai',
            model='gpt-4o',
            display_options={'quiet': True, 'no_color': True}
        )
        
        # Mixed results should still return True (partial success)
        self.assertTrue(success, "organize_content should return True for partial success")
        
        # Verify successful files in processed directory
        processed_files = os.listdir(self.processed_dir)
        self.assertEqual(len(processed_files), 2, "Should have 2 successfully processed files")
        
        # Verify failed files in unprocessed directory 
        unprocessed_files = os.listdir(self.unprocessed_dir)
        self.assertEqual(len(unprocessed_files), 1, "Should have 1 failed file in unprocessed")
        
        # Verify input directory is empty (all files moved somewhere)
        input_files = os.listdir(self.input_dir)
        self.assertEqual(len(input_files), 0, "Input directory should be empty")
    
    @patch('core.application._setup_display_manager')
    @patch('core.application.get_api_details')
    @patch('core.application.AIProviderFactory.create')  
    def test_first_time_setup_workflow(self, mock_ai_factory, mock_get_api, mock_display_setup):
        """
        E2E Test: First-time user setup workflow
        
        Journey: User runs content-tamer-ai → prompted for API key → processing begins
        """
        # Simulate first-time user (no API key initially, then provides one)
        mock_get_api.side_effect = [
            None,  # First call: no API key set
            'sk-test1234567890abcdef1234567890abcdef12345678'  # Second call: user provided key
        ]
        
        # Mock display manager to avoid Rich I/O conflicts
        from tests.utils.test_display_manager import TestDisplayManager
        mock_display_manager = TestDisplayManager()
        mock_display_setup.return_value = mock_display_manager
        
        # Mock AI provider
        mock_ai_provider = MagicMock()
        mock_ai_provider.generate_filename.return_value = 'first_time_user_document'
        mock_ai_factory.return_value = mock_ai_provider
        
        # Execute workflow (should handle missing API key gracefully)
        success = organize_content(
            input_dir=self.input_dir,
            unprocessed_dir=self.unprocessed_dir,
            renamed_dir=self.processed_dir,
            provider='openai',
            model='gpt-4o', 
            display_options={'quiet': True, 'no_color': True}
        )
        
        # Should succeed after API key setup
        self.assertTrue(success, "Should succeed after API key is provided")
        
        # Verify API key was requested (called twice - once failed, once succeeded)
        self.assertEqual(mock_get_api.call_count, 2, "Should attempt to get API key twice")
        
        # Verify processing completed
        processed_files = os.listdir(self.processed_dir)
        self.assertEqual(len(processed_files), 3, "All files should be processed after setup")
    
    def test_directory_structure_creation(self):
        """
        E2E Test: Directory structure creation
        
        Journey: User runs ensure_default_directories → directories are created
        """
        # Test that the application can create its directory structure
        input_dir, processed_dir, unprocessed_dir = ensure_default_directories()
        
        # Verify directories were created and are valid paths
        self.assertTrue(os.path.exists(input_dir), "Input directory should be created")
        self.assertTrue(os.path.exists(processed_dir), "Processed directory should be created") 
        self.assertTrue(os.path.exists(unprocessed_dir), "Unprocessed directory should be created")
        
        # Verify they are writable
        test_file = os.path.join(input_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        self.assertTrue(os.path.exists(test_file), "Should be able to write to input directory")
        os.remove(test_file)


class TestUserJourneyEdgeCases(unittest.TestCase):
    """Test edge cases in user workflows."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="e2e_edge_test_")
        self.input_dir = os.path.join(self.test_dir, 'input')
        self.processed_dir = os.path.join(self.test_dir, 'processed')
        self.unprocessed_dir = os.path.join(self.test_dir, 'unprocessed')
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.unprocessed_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('core.application._setup_display_manager')
    @patch('core.application.get_api_details')
    @patch('core.application.AIProviderFactory.create')
    def test_empty_input_directory_workflow(self, mock_ai_factory, mock_get_api, mock_display_setup):
        """
        E2E Test: Empty input directory workflow
        
        Journey: User runs content-tamer-ai with no files → graceful completion
        """
        # Mock API key
        mock_get_api.return_value = 'sk-test1234567890abcdef1234567890abcdef12345678'
        
        # Mock display manager to avoid Rich I/O conflicts
        from tests.utils.test_display_manager import TestDisplayManager
        mock_display_manager = TestDisplayManager()
        mock_display_setup.return_value = mock_display_manager
        
        # Mock AI provider (shouldn't be called)
        mock_ai_provider = MagicMock()
        mock_ai_factory.return_value = mock_ai_provider
        
        # Execute with empty input directory
        success = organize_content(
            input_dir=self.input_dir,
            unprocessed_dir=self.unprocessed_dir,
            renamed_dir=self.processed_dir,
            provider='openai',
            model='gpt-4o',
            display_options={'quiet': True, 'no_color': True}
        )
        
        # Should complete successfully even with no files
        self.assertTrue(success, "Should succeed with empty input directory")
        
        # AI should not be called
        self.assertEqual(mock_ai_provider.generate_filename.call_count, 0, 
                        "AI should not be called with no files")
        
        # Directories should remain empty
        self.assertEqual(len(os.listdir(self.input_dir)), 0, "Input should remain empty")
        self.assertEqual(len(os.listdir(self.processed_dir)), 0, "Processed should remain empty")
        self.assertEqual(len(os.listdir(self.unprocessed_dir)), 0, "Unprocessed should remain empty")


if __name__ == '__main__':
    unittest.main()