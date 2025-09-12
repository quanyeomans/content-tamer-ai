"""
Integration tests for progress bar updates.

Tests the complete progress bar pipeline showing file-by-file processing
with extraction, analysis, and organization phases.
"""

import unittest
from unittest.mock import MagicMock, patch, call
import tempfile
import os

from src.orchestration.application_kernel import ApplicationKernel
from src.interfaces.programmatic.configuration_manager import ProcessingConfiguration
from src.core.application_container import ApplicationContainer


class TestProgressBarIntegration(unittest.TestCase):
    """Integration tests for progress bar updates during processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)
        
        # Create test files
        self.test_files = []
        for i in range(3):
            test_file = os.path.join(self.input_dir, f"test_{i}.pdf")
            with open(test_file, 'wb') as f:
                f.write(b'%PDF-1.4\ntest content')
            self.test_files.append(test_file)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.shared.display.unified_display_manager.UnifiedDisplayManager')
    def test_progress_bar_shows_file_by_file_updates(self, mock_display_manager_class):
        """Test that progress bar updates for each file with proper stages."""
        # Create mock display manager
        mock_display = MagicMock()
        mock_display_manager_class.return_value = mock_display
        
        # Track progress updates
        progress_updates = []
        
        def capture_update(progress_id, current, total, message):
            progress_updates.append({
                'current': current,
                'total': total,
                'message': message
            })
        
        mock_display.update_progress.side_effect = capture_update
        mock_display.start_progress.return_value = "test_progress_id"
        
        # Create configuration
        config = ProcessingConfiguration(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            provider="local",
            model="llama3.1-8b",
            api_key=None,
            organization_enabled=False,
            quiet_mode=False,
        )
        
        # Create kernel with mocked display
        container = ApplicationContainer()
        kernel = container.create_application_kernel()
        
        # Replace display manager with mock
        kernel.display_manager = mock_display
        
        # Mock content service to avoid actual processing
        mock_content_service = MagicMock()
        mock_content_service.process_document_complete.return_value = {
            "ready_for_ai": True,
            "ai_ready_content": "test content",
            "metadata": {}
        }
        kernel.content_service = mock_content_service
        
        # Mock AI service
        mock_ai_service = MagicMock()
        mock_ai_result = MagicMock()
        mock_ai_result.status.value = "success"
        mock_ai_result.content = "test_filename.pdf"
        mock_ai_service.generate_filename_with_ai.return_value = mock_ai_result
        kernel.ai_service = mock_ai_service
        
        # Execute processing
        kernel.execute_processing(config)
        
        # Verify progress bar was started
        mock_display.start_progress.assert_called_once_with("Processing documents")
        
        # Verify we got updates for each file with all three stages
        self.assertGreaterEqual(len(progress_updates), 9)  # 3 files * 3 stages minimum
        
        # Check that we have the expected stages for each file
        stages_seen = {
            "extracting": 0,
            "analyzing": 0,
            "organizing": 0
        }
        
        for update in progress_updates:
            message = update['message'].lower()
            if "[1/3] extracting:" in message:
                stages_seen["extracting"] += 1
            elif "[2/3] analyzing:" in message:
                stages_seen["analyzing"] += 1
            elif "[3/3] organizing:" in message:
                stages_seen["organizing"] += 1
        
        # Each stage should appear once per file
        self.assertEqual(stages_seen["extracting"], 3)
        self.assertEqual(stages_seen["analyzing"], 3)
        self.assertEqual(stages_seen["organizing"], 3)
        
        # Verify progress bar was finished
        mock_display.finish_progress.assert_called_once()

    @patch('src.shared.display.unified_display_manager.UnifiedDisplayManager')
    def test_progress_bar_with_retry_logic(self, mock_display_manager_class):
        """Test that progress bar shows retry attempts."""
        # Create mock display manager
        mock_display = MagicMock()
        mock_display_manager_class.return_value = mock_display
        
        # Track warnings
        warnings = []
        mock_display.warning.side_effect = lambda msg: warnings.append(msg)
        mock_display.start_progress.return_value = "test_progress_id"
        
        # Create configuration
        config = ProcessingConfiguration(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            provider="local",
            model="llama3.1-8b",
            api_key=None,
            organization_enabled=False,
            quiet_mode=False,
        )
        
        # Create kernel
        container = ApplicationContainer()
        kernel = container.create_application_kernel()
        kernel.display_manager = mock_display
        
        # Mock content service
        mock_content_service = MagicMock()
        mock_content_service.process_document_complete.return_value = {
            "ready_for_ai": True,
            "ai_ready_content": "test content",
            "metadata": {}
        }
        kernel.content_service = mock_content_service
        
        # Mock AI service to fail first two times, succeed on third
        mock_ai_service = MagicMock()
        mock_ai_result_fail = MagicMock()
        mock_ai_result_fail.status.value = "failed"
        mock_ai_result_fail.error = "Temporary error"
        
        mock_ai_result_success = MagicMock()
        mock_ai_result_success.status.value = "success"
        mock_ai_result_success.content = "test_filename.pdf"
        
        # Simulate retries
        mock_ai_service.generate_filename_with_ai.side_effect = [
            mock_ai_result_fail,  # First attempt fails
            mock_ai_result_fail,  # Second attempt fails
            mock_ai_result_success,  # Third attempt succeeds
        ] * 3  # For 3 test files
        
        kernel.ai_service = mock_ai_service
        
        # Execute processing
        kernel.execute_processing(config)
        
        # Check that retry warnings were shown
        retry_warnings = [w for w in warnings if "Retry" in w]
        self.assertGreater(len(retry_warnings), 0)
        
        # Verify retry messages have proper format
        for warning in retry_warnings:
            self.assertRegex(warning, r"Retry \d/3 for test_\d\.pdf")

    @patch('src.domains.content.content_service.ContentService')
    def test_extraction_progress_callback(self, mock_content_service_class):
        """Test that extraction phase uses progress callback."""
        mock_content_service = MagicMock()
        mock_content_service_class.return_value = mock_content_service
        
        # Track callback usage
        callback_used = False
        
        def batch_process_with_callback(documents, progress_callback=None):
            nonlocal callback_used
            if progress_callback:
                callback_used = True
                # Simulate progress updates
                for i, doc in enumerate(documents):
                    progress_callback(i + 1, len(documents), f"Extracting: {os.path.basename(doc)}")
            
            return {doc: {"ready_for_ai": True, "ai_ready_content": "test"} for doc in documents}
        
        mock_content_service.batch_process_documents.side_effect = batch_process_with_callback
        
        # Create configuration
        config = ProcessingConfiguration(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            provider="local",
            model="llama3.1-8b",
            api_key=None,
            organization_enabled=False,
            quiet_mode=False,
        )
        
        # Create kernel
        container = ApplicationContainer()
        kernel = container.create_application_kernel()
        
        # Mock AI service to avoid actual AI calls
        mock_ai_service = MagicMock()
        mock_ai_result = MagicMock()
        mock_ai_result.status.value = "success"
        mock_ai_result.content = "test_filename.pdf"
        mock_ai_service.generate_filename_with_ai.return_value = mock_ai_result
        kernel.ai_service = mock_ai_service
        
        # Execute processing
        kernel.execute_processing(config)
        
        # Verify callback was used during extraction
        self.assertTrue(callback_used, "Progress callback was not used during extraction")


if __name__ == "__main__":
    unittest.main()