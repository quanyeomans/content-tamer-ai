"""
Tests for file organization and management utilities.
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from file_organizer import FileManager, FilenameHandler, FileOrganizer, ProgressTracker


class TestFilenameHandler(unittest.TestCase):
    """Test filename validation and handling."""

    def test_validate_and_trim_filename(self):
        """Test filename cleaning and validation logic."""
        handler = FilenameHandler()

        # Valid filename should remain unchanged
        self.assertEqual(
            handler.validate_and_trim_filename("Valid_Filename_123"),
            "Valid_Filename_123",
        )

        # Should remove invalid characters
        self.assertEqual(
            handler.validate_and_trim_filename("file-with-spaces!@#$"), "filewithspaces"
        )

        # Should handle unicode characters
        self.assertEqual(handler.validate_and_trim_filename("你好世界_document"), "_document")

        # Should truncate long filenames
        long_name = "a" * 200
        result = handler.validate_and_trim_filename(long_name)
        self.assertEqual(len(result), 160)

        # Should return placeholder for empty names
        result = handler.validate_and_trim_filename("")
        self.assertTrue(result.startswith("empty_file_"))

        # Should return placeholder for invalid names
        result = handler.validate_and_trim_filename("!@#$%^&*()")
        self.assertTrue(result.startswith("invalid_name_"))

    @patch("os.path.exists")
    def test_handle_duplicate_filename(self, mock_exists):
        """Test logic for appending numbers to duplicate filenames."""
        handler = FilenameHandler()

        # No duplicate exists
        mock_exists.return_value = False
        result = handler.handle_duplicate_filename("test_file", "/fake/dir", ".pdf")
        self.assertEqual(result, "test_file")

        # One duplicate exists
        mock_exists.side_effect = [True, False]
        result = handler.handle_duplicate_filename("test_file", "/fake/dir", ".pdf")
        self.assertEqual(result, "test_file_1")

        # Multiple duplicates exist
        mock_exists.side_effect = [True, True, True, False]
        result = handler.handle_duplicate_filename("test_file", "/fake/dir", ".pdf")
        self.assertEqual(result, "test_file_3")


class TestProgressTracker(unittest.TestCase):
    """Test progress tracking functionality."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.progress_file = os.path.join(self.temp_dir, ".progress")
        self.input_dir = os.path.join(self.temp_dir, "input")
        os.makedirs(self.input_dir, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_load_progress_empty(self):
        """Test loading progress when no progress file exists."""
        tracker = ProgressTracker()
        progress = tracker.load_progress(self.progress_file, self.input_dir)
        self.assertEqual(progress, set())

    def test_load_progress_with_data(self):
        """Test loading progress with existing data."""
        # Create progress file with some data
        with open(self.progress_file, "w") as f:
            f.write("file1.pdf\nfile2.pdf\n")

        tracker = ProgressTracker()
        progress = tracker.load_progress(self.progress_file, self.input_dir)
        self.assertEqual(progress, {"file1.pdf", "file2.pdf"})

    def test_record_progress(self):
        """Test recording progress with file locking."""
        tracker = ProgressTracker()
        file_manager = FileManager()

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            progress_f = mock_file()
            with patch.object(file_manager, "lock_file"), patch.object(file_manager, "unlock_file"):
                tracker.record_progress(progress_f, "test.pdf", file_manager)

        progress_f.write.assert_called_with("test.pdf\n")
        progress_f.flush.assert_called_once()


class TestFileOrganizer(unittest.TestCase):
    """Test file organization functionality."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_create_directories(self):
        """Test directory creation."""
        dir1 = os.path.join(self.temp_dir, "dir1")
        dir2 = os.path.join(self.temp_dir, "dir2")

        self.organizer.create_directories(dir1, dir2)

        self.assertTrue(os.path.exists(dir1))
        self.assertTrue(os.path.exists(dir2))

    def test_get_file_stats(self):
        """Test file statistics gathering."""
        # Create some test files
        test_files = [
            ("file1.pdf", "pdf content"),
            ("file2.txt", "text content"),
            ("file3.pdf", "more pdf content"),
        ]

        for filename, content in test_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)

        stats = self.organizer.get_file_stats(self.temp_dir)

        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_extension"][".pdf"], 2)
        self.assertEqual(stats["by_extension"][".txt"], 1)

    def test_get_file_stats_empty_dir(self):
        """Test file statistics for empty directory."""
        stats = self.organizer.get_file_stats(self.temp_dir)
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["by_extension"], {})

    def test_organize_by_content_type(self):
        """Test content type organization."""
        test_files = ["doc1.pdf", "image1.png", "sheet1.xlsx"]
        result = self.organizer.organize_by_content_type(test_files, self.temp_dir)

        self.assertEqual(result["documents"], ["doc1.pdf"])
        self.assertEqual(result["images"], ["image1.png"])
        self.assertEqual(result["other"], ["sheet1.xlsx"])

    def test_create_domain_folders(self):
        """Test domain folder creation."""
        domains = ["work", "personal", "finance"]
        result = self.organizer.create_domain_folders(self.temp_dir, domains)

        for domain in domains:
            domain_path = os.path.join(self.temp_dir, domain)
            self.assertTrue(os.path.exists(domain_path))
            self.assertEqual(result[domain], domain_path)


class TestFileManager(unittest.TestCase):
    """Test file management operations."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = FileManager()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_safe_move_success(self):
        """Test successful file move."""
        src_file = os.path.join(self.temp_dir, "source.txt")
        dst_file = os.path.join(self.temp_dir, "destination.txt")

        # Create source file
        with open(src_file, "w") as f:
            f.write("test content")

        # Move file
        self.manager.safe_move(src_file, dst_file)

        # Verify move
        self.assertFalse(os.path.exists(src_file))
        self.assertTrue(os.path.exists(dst_file))

        with open(dst_file, "r") as f:
            self.assertEqual(f.read(), "test content")

    @patch("time.sleep")  # Speed up test
    @patch("shutil.move")
    @patch("shutil.copy2")
    @patch("os.remove")
    def test_safe_move_fallback(self, mock_remove, mock_copy2, mock_move, mock_sleep):
        """Test file move with fallback to copy-then-delete."""
        # Simulate move failure, then successful copy/remove
        mock_move.side_effect = OSError("Move failed")

        self.manager.safe_move("src", "dst")

        # Verify fallback was used
        self.assertEqual(mock_move.call_count, 3)  # 3 attempts
        mock_copy2.assert_called_once_with("src", "dst")
        mock_remove.assert_called_once_with("src")


if __name__ == "__main__":
    unittest.main()
