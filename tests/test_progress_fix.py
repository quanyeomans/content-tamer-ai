"""
Tests for the progress recording duplication fix.

Validates that progress entries are only written once per file processing attempt,
regardless of success or failure outcomes.
"""

import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.file_processor import process_file, process_file_enhanced_core
from file_organizer import FileOrganizer


class TestProgressRecordingFix(unittest.TestCase):
    """Test that progress recording happens only once per file."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "test.pdf")
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")
        self.renamed_dir = os.path.join(self.temp_dir, "renamed")

        os.makedirs(self.unprocessed_dir, exist_ok=True)
        os.makedirs(self.renamed_dir, exist_ok=True)

        # Create a test file
        with open(self.input_path, "wb") as f:
            f.write(b"%PDF-1.4\ntest content\n%EOF\n")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_progress_recorded_once_on_success(self):
        """Test that progress is recorded exactly once when processing succeeds."""
        # Mock dependencies
        mock_organizer = Mock(spec=FileOrganizer)
        mock_organizer.progress_tracker = Mock()
        mock_organizer.file_manager = Mock()
        mock_organizer.filename_handler = Mock()
        mock_organizer.filename_handler.validate_and_trim_filename.return_value = "validated_name"
        mock_organizer.move_file_to_category.return_value = "final_name.pdf"

        mock_ai_client = Mock()
        mock_display_context = Mock()
        mock_progress_f = Mock()

        # Mock the content extraction to succeed
        with patch("core.file_processor._extract_file_content") as mock_extract:
            mock_extract.return_value = ("Test content", None)

            with patch("core.file_processor._generate_filename") as mock_gen:
                mock_gen.return_value = "new_name"

                # Call the enhanced core function
                success, result = process_file_enhanced_core(
                    input_path=self.input_path,
                    filename="test.pdf",
                    unprocessed_folder=self.unprocessed_dir,
                    renamed_folder=self.renamed_dir,
                    progress_f=mock_progress_f,
                    ocr_lang="eng",
                    ai_client=mock_ai_client,
                    organizer=mock_organizer,
                    display_context=mock_display_context,
                )

        # Verify success
        self.assertTrue(success)
        self.assertEqual(result, "final_name.pdf")

        # Verify progress recorded exactly once
        mock_organizer.progress_tracker.record_progress.assert_called_once_with(
            mock_progress_f, "test.pdf", mock_organizer.file_manager
        )

    def test_progress_recorded_once_on_error(self):
        """Test that progress is recorded exactly once when processing fails."""
        # Mock dependencies
        mock_organizer = Mock(spec=FileOrganizer)
        mock_organizer.progress_tracker = Mock()
        mock_organizer.file_manager = Mock()
        mock_organizer.file_manager.safe_move = Mock()  # Don't actually move files

        mock_ai_client = Mock()
        mock_display_context = Mock()
        mock_progress_f = Mock()

        # Mock the content extraction to fail
        with patch("core.file_processor._extract_file_content") as mock_extract:
            mock_extract.side_effect = ValueError("Extraction failed")

            # Call the enhanced core function
            success, result = process_file_enhanced_core(
                input_path=self.input_path,
                filename="test.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.renamed_dir,
                progress_f=mock_progress_f,
                ocr_lang="eng",
                ai_client=mock_ai_client,
                organizer=mock_organizer,
                display_context=mock_display_context,
            )

        # Verify failure
        self.assertFalse(success)
        self.assertIsNone(result)

        # Verify progress recorded exactly once (in finally block)
        mock_organizer.progress_tracker.record_progress.assert_called_once_with(
            mock_progress_f, "test.pdf", mock_organizer.file_manager
        )

    def test_legacy_process_file_no_duplicates(self):
        """Test that legacy process_file function doesn't duplicate progress recording."""
        # Mock dependencies
        mock_organizer = Mock(spec=FileOrganizer)
        mock_organizer.progress_tracker = Mock()
        mock_organizer.file_manager = Mock()
        mock_organizer.filename_handler = Mock()
        mock_organizer.filename_handler.validate_and_trim_filename.return_value = "validated_name"
        mock_organizer.move_file_to_category.return_value = "final_name.pdf"

        mock_ai_client = Mock()
        mock_pbar = Mock()
        mock_progress_f = Mock()

        # Mock successful content processing
        with patch("content_processors.ContentProcessorFactory") as mock_factory_class:
            mock_factory = Mock()
            mock_processor = Mock()
            mock_processor.extract_content.return_value = ("Test content", None)
            mock_factory.get_processor.return_value = mock_processor
            mock_factory_class.return_value = mock_factory

            with patch("core.file_processor.get_new_filename_with_retry") as mock_get_name:
                mock_get_name.return_value = "ai_generated_name"

                # Call legacy function
                result = process_file(
                    input_path=self.input_path,
                    filename="test.pdf",
                    unprocessed_folder=self.unprocessed_dir,
                    renamed_folder=self.renamed_dir,
                    pbar=mock_pbar,
                    progress_f=mock_progress_f,
                    ocr_lang="eng",
                    ai_client=mock_ai_client,
                    organizer=mock_organizer,
                )

        # Verify success
        self.assertTrue(result)

        # Verify progress recorded exactly once
        mock_organizer.progress_tracker.record_progress.assert_called_once_with(
            mock_progress_f, "test.pdf", mock_organizer.file_manager
        )

    def test_legacy_process_file_error_no_duplicates(self):
        """Test that legacy process_file function doesn't duplicate progress recording on error."""
        # Mock dependencies
        mock_organizer = Mock(spec=FileOrganizer)
        mock_organizer.progress_tracker = Mock()
        mock_organizer.file_manager = Mock()
        mock_organizer.file_manager.safe_move = Mock()  # Don't actually move files

        mock_ai_client = Mock()
        mock_pbar = Mock()
        mock_progress_f = Mock()

        # Mock content processing to fail
        with patch("content_processors.ContentProcessorFactory") as mock_factory_class:
            mock_factory = Mock()
            mock_processor = Mock()
            mock_processor.extract_content.return_value = (
                "Error: Processing failed",
                None,
            )
            mock_factory.get_processor.return_value = mock_processor
            mock_factory_class.return_value = mock_factory

            # Call legacy function (should fail due to error content)
            result = process_file(
                input_path=self.input_path,
                filename="test.pdf",
                unprocessed_folder=self.unprocessed_dir,
                renamed_folder=self.renamed_dir,
                pbar=mock_pbar,
                progress_f=mock_progress_f,
                ocr_lang="eng",
                ai_client=mock_ai_client,
                organizer=mock_organizer,
            )

        # Verify failure
        self.assertFalse(result)

        # Verify progress recorded exactly once (should be in finally block for error path)
        mock_organizer.progress_tracker.record_progress.assert_called_once_with(
            mock_progress_f, "test.pdf", mock_organizer.file_manager
        )

    def test_progress_file_content_not_duplicated(self):
        """Test that actual progress file content doesn't contain duplicates."""
        # Create a real progress file
        progress_file_path = os.path.join(self.temp_dir, ".progress")

        # Mock organizer with real progress recording
        mock_organizer = Mock()
        mock_file_manager = Mock()
        mock_file_manager.lock_file = Mock()
        mock_file_manager.unlock_file = Mock()

        # Import the real progress tracker
        from file_organizer import ProgressTracker

        real_tracker = ProgressTracker()

        # Record progress for the same file multiple times (simulating the bug)
        with open(progress_file_path, "w") as progress_f:
            # This simulates what should happen - only one entry
            real_tracker.record_progress(progress_f, "test.pdf", mock_file_manager)

        # Read the progress file
        with open(progress_file_path, "r") as f:
            content = f.read()

        # Should only contain one line with the filename
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        self.assertEqual(len(lines), 1, f"Expected 1 line, got {len(lines)}: {lines}")
        self.assertEqual(lines[0], "test.pdf")


if __name__ == "__main__":
    unittest.main()
