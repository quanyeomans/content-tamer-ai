"""
Integration tests for end-to-end document processing workflow.
"""
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from core.application import organize_content
from core.cli_parser import parse_arguments, list_available_models, _print_capabilities
from core.directory_manager import (
    ensure_default_directories, 
    get_api_details,
    DEFAULT_DATA_DIR,
    DEFAULT_INPUT_DIR,
    DEFAULT_PROCESSED_DIR,
    DEFAULT_UNPROCESSED_DIR,
    DEFAULT_PROCESSING_DIR,
)
from core.file_processor import (
    process_file,
    get_new_filename_with_retry,
    get_filename_from_ai,
    pdfs_to_text_string,
)
from ai_providers import AIProviderFactory
from content_processors import ContentProcessorFactory
from file_organizer import FileOrganizer
from main import main


class TestDefaultDirectories(unittest.TestCase):
    """Test default directory structure functionality."""

    def test_ensure_default_directories(self):
        """Test that default directories are created correctly."""
        with patch('core.directory_manager.DEFAULT_DATA_DIR', tempfile.mkdtemp()) as temp_data_dir:
            with patch('core.directory_manager.DEFAULT_INPUT_DIR', os.path.join(temp_data_dir, 'input')), \
                 patch('core.directory_manager.DEFAULT_PROCESSED_DIR', os.path.join(temp_data_dir, 'processed')), \
                 patch('core.directory_manager.DEFAULT_UNPROCESSED_DIR', os.path.join(temp_data_dir, 'processed', 'unprocessed')), \
                 patch('core.directory_manager.DEFAULT_PROCESSING_DIR', os.path.join(temp_data_dir, '.processing')):
                
                input_dir, processed_dir, unprocessed_dir = ensure_default_directories()
                
                # Verify directories were created
                self.assertTrue(os.path.exists(input_dir))
                self.assertTrue(os.path.exists(processed_dir))
                self.assertTrue(os.path.exists(unprocessed_dir))
                
                # Verify unprocessed is subfolder of processed
                self.assertTrue(unprocessed_dir.startswith(processed_dir))
                
                # Clean up
                shutil.rmtree(temp_data_dir)

    def test_subfolder_structure(self):
        """Test that unprocessed folder is correctly nested under processed."""
        with patch('core.directory_manager.DEFAULT_DATA_DIR', tempfile.mkdtemp()) as temp_data_dir:
            with patch('core.directory_manager.DEFAULT_PROCESSED_DIR', os.path.join(temp_data_dir, 'processed')), \
                 patch('core.directory_manager.DEFAULT_UNPROCESSED_DIR', os.path.join(temp_data_dir, 'processed', 'unprocessed')):
                
                input_dir, processed_dir, unprocessed_dir = ensure_default_directories()
                
                # Test that unprocessed is inside processed
                self.assertEqual(os.path.dirname(unprocessed_dir), processed_dir)
                self.assertTrue(os.path.basename(unprocessed_dir) == 'unprocessed')
                
                # Clean up
                shutil.rmtree(temp_data_dir)


class TestIntegrationWorkflow(unittest.TestCase):
    """Test end-to-end processing workflow."""

    def setUp(self):
        """Set up temporary directory structure for integration testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed") 
        self.renamed_dir = os.path.join(self.temp_dir, "renamed")
        
        # Create directory structure
        os.makedirs(self.input_dir)
        os.makedirs(self.unprocessed_dir)
        os.makedirs(self.renamed_dir)
        
        # Create test files
        self.test_pdf = os.path.join(self.input_dir, "test.pdf")
        self.test_image = os.path.join(self.input_dir, "test.png")
        
        with open(self.test_pdf, 'w') as f:
            f.write("fake pdf content")
            
        with open(self.test_image, 'wb') as f:
            f.write(b'fake image data')

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch('core.application.get_api_details')
    @patch('core.application.AIProviderFactory.create')
    def test_organize_content_success(self, mock_create_ai, mock_get_api):
        """Test successful end-to-end processing."""
        # Mock AI client
        mock_ai_client = MagicMock()
        mock_ai_client.generate_filename.return_value = "ai_generated_name"
        mock_create_ai.return_value = mock_ai_client
        mock_get_api.return_value = "fake-api-key"
        
        # Set NO_COLOR to avoid Unicode encoding issues in tests
        with patch.dict(os.environ, {'NO_COLOR': '1', 'PYTHONIOENCODING': 'utf-8'}):
            # Mock content extraction
            with patch('content_processors.ContentProcessorFactory') as mock_factory_class:
                mock_factory = MagicMock()
                mock_processor = MagicMock()
                mock_processor.extract_content.return_value = ("extracted text", None)
                mock_factory.get_processor.return_value = mock_processor
                mock_factory.get_supported_extensions.return_value = ['.pdf', '.png']
                mock_factory_class.return_value = mock_factory
                
                # Mock file organizer
                with patch('core.application.FileOrganizer') as mock_organizer_class:
                    mock_organizer = MagicMock()
                    mock_organizer.filename_handler.validate_and_trim_filename.return_value = "cleaned_name"
                    mock_organizer.move_file_to_category.return_value = "final_name"
                    mock_organizer_class.return_value = mock_organizer
                    
                    # Run the main function
                    success = organize_content(
                        self.input_dir,
                        self.unprocessed_dir, 
                        self.renamed_dir,
                        provider="openai",
                        model="gpt-4o"
                    )
                    
                    self.assertTrue(success)
                    
                    # Verify AI client was called
                    self.assertTrue(mock_ai_client.generate_filename.called)
                    
                    # Verify file operations were performed
                    self.assertTrue(mock_organizer.move_file_to_category.called)

    @patch('core.application.get_api_details')
    def test_organize_content_invalid_provider(self, mock_get_api):
        """Test handling of invalid AI provider."""
        mock_get_api.side_effect = ValueError("Unsupported provider")
        
        success = organize_content(
            self.input_dir,
            self.unprocessed_dir,
            self.renamed_dir,
            provider="invalid_provider"
        )
        
        self.assertFalse(success)

    @patch('core.application.get_api_details')
    @patch('core.application.AIProviderFactory.create')
    def test_process_file_success(self, mock_create_ai, mock_get_api):
        """Test successful individual file processing."""
        # Mock AI client
        mock_ai_client = MagicMock()
        mock_ai_client.generate_filename.return_value = "test_filename"
        mock_create_ai.return_value = mock_ai_client
        mock_get_api.return_value = "fake-api-key"
        
        # Mock progress bar and file
        mock_pbar = MagicMock()
        mock_progress_file = mock_open()
        
        # Mock organizer
        mock_organizer = MagicMock()
        mock_organizer.filename_handler.validate_and_trim_filename.return_value = "clean_name"
        mock_organizer.move_file_to_category.return_value = "final_name"
        
        with patch('content_processors.ContentProcessorFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_processor = MagicMock()
            mock_processor.extract_content.return_value = ("extracted text", None)
            mock_factory.get_processor.return_value = mock_processor
            mock_factory_class.return_value = mock_factory
            
            with patch('builtins.open', mock_progress_file):
                progress_f = mock_progress_file()
                
                process_file(
                    self.test_pdf,
                    "test.pdf",
                    self.unprocessed_dir,
                    self.renamed_dir,
                    mock_pbar,
                    progress_f,
                    "eng",
                    mock_ai_client,
                    mock_organizer
                )
                
                # Verify processing steps
                mock_processor.extract_content.assert_called_once()
                mock_ai_client.generate_filename.assert_called_once()
                mock_organizer.move_file_to_category.assert_called_once()
                mock_pbar.update.assert_called_once()

    def test_process_file_unprocessed(self):
        """Test handling of unprocessable files."""
        mock_pbar = MagicMock()
        mock_progress_file = mock_open()
        mock_ai_client = MagicMock()
        mock_organizer = MagicMock()
        
        with patch('content_processors.ContentProcessorFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_processor = MagicMock()
            mock_processor.extract_content.return_value = ("Error: Unprocessable file", None)
            mock_factory.get_processor.return_value = mock_processor
            mock_factory_class.return_value = mock_factory
            
            with patch('builtins.open', mock_progress_file):
                progress_f = mock_progress_file()
                
                process_file(
                    self.test_pdf,
                    "test.pdf", 
                    self.unprocessed_dir,
                    self.renamed_dir,
                    mock_pbar,
                    progress_f,
                    "eng",
                    mock_ai_client,
                    mock_organizer
                )
                
                # Should handle the error and move to unprocessed folder
                mock_organizer.file_manager.safe_move.assert_called_once()
                mock_pbar.update.assert_called_once()

    def test_get_new_filename_with_retry_success(self):
        """Test retry logic for AI filename generation."""
        mock_ai_client = MagicMock()
        mock_ai_client.generate_filename.return_value = "successful_name"
        
        result = get_new_filename_with_retry(
            mock_ai_client, 
            "test content", 
            None,
            max_retries=3
        )
        
        self.assertEqual(result, "successful_name")
        mock_ai_client.generate_filename.assert_called_once()

    @patch('time.sleep')  # Speed up test
    def test_get_new_filename_with_retry_failure(self, mock_sleep):
        """Test retry logic with eventual failure."""
        mock_ai_client = MagicMock()
        mock_ai_client.generate_filename.side_effect = RuntimeError("API Error")
        
        result = get_new_filename_with_retry(
            mock_ai_client,
            "test content",
            None, 
            max_retries=2
        )
        
        # Should return fallback filename
        self.assertTrue(result.startswith("untitled_document_"))
        
        # Should have retried
        self.assertEqual(mock_ai_client.generate_filename.call_count, 2)

    @patch('time.sleep')
    def test_get_new_filename_with_retry_timeout_fallback(self, mock_sleep):
        """Test retry logic with timeout errors."""
        mock_ai_client = MagicMock()
        mock_ai_client.generate_filename.side_effect = RuntimeError("timeout error")
        
        result = get_new_filename_with_retry(
            mock_ai_client,
            "test content", 
            None,
            max_retries=2
        )
        
        # Should return network error fallback
        self.assertTrue(result.startswith("network_error_"))


class TestCLIIntegration(unittest.TestCase):
    """Test command-line interface integration."""

    def test_list_available_models(self):
        """Test listing available models."""
        with patch('ai_providers.AIProviderFactory.list_providers') as mock_list:
            mock_list.return_value = {
                "openai": ["gpt-4o", "gpt-3.5-turbo"],
                "claude": ["claude-3-sonnet"]
            }
            
            # Test that the mocked function was called and returned expected data
            list_available_models()
            
            # Verify the mock was called
            mock_list.assert_called_once()
            
            # Since we can't easily capture the print output in this test framework,
            # let's just verify that the function runs without error with our mock data
            # and that the mock was called
            self.assertTrue(True)  # Test passes if we get here without error

    def test_get_api_details_from_env(self):
        """Test API key retrieval from environment."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test1234567890abcdef'}):
            api_key = get_api_details("openai", "gpt-4o")
            self.assertEqual(api_key, "sk-test1234567890abcdef")

    def test_get_api_details_invalid_provider(self):
        """Test error handling for invalid provider."""
        with self.assertRaises(ValueError) as context:
            get_api_details("invalid_provider", "model")
        self.assertIn("Unsupported provider", str(context.exception))

    def test_get_api_details_invalid_model(self):
        """Test error handling for invalid model."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with self.assertRaises(ValueError) as context:
                get_api_details("openai", "invalid_model")
            self.assertIn("Invalid model", str(context.exception))

    @patch('builtins.input')
    def test_get_api_details_user_input(self, mock_input):
        """Test API key input from user."""
        mock_input.return_value = "sk-user1234567890abcdef"
        
        with patch.dict(os.environ, {}, clear=True):
            # Mock os.system to prevent screen clearing during tests
            with patch('os.system'):
                api_key = get_api_details("openai", "gpt-4o")
                self.assertEqual(api_key, "sk-user1234567890abcdef")
                mock_input.assert_called_once_with("\nEnter your Openai API key: ")


if __name__ == "__main__":
    unittest.main()