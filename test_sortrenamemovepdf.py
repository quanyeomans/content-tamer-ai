import unittest
import os
import shutil
import time
from unittest.mock import patch, MagicMock, mock_open

# To test the script, we need to import it.
# We will assume the script is in the same directory and can be imported.
import sortrenamemovepdf as srm

class TestFilenameUtils(unittest.TestCase):
    """Tests for utility functions that manipulate filenames and strings."""

    def test_validate_and_trim_filename(self):
        """Tests the filename cleaning and validation logic."""
        self.assertEqual(srm.validate_and_trim_filename("Valid_Filename_123"), "Valid_Filename_123")
        # Should remove leading/trailing whitespace and invalid characters
        self.assertEqual(srm.validate_and_trim_filename("  file-with-spaces!@#$  "), "filewithspaces")
        # Should handle unicode characters
        self.assertEqual(srm.validate_and_trim_filename("你好世界_document"), "_document")
        # Should truncate long filenames
        self.assertEqual(len(srm.validate_and_trim_filename("a" * 200)), 160)
        # Should return a placeholder for empty or invalid names
        self.assertTrue(srm.validate_and_trim_filename("").startswith("empty_file_"))
        self.assertTrue(srm.validate_and_trim_filename("!@#$%^&*()").startswith("invalid_name_"))

    @patch('os.path.exists')
    def test_handle_duplicate_filename(self, mock_exists):
        """Tests the logic for appending numbers to duplicate filenames."""
        # Case 1: No duplicate exists
        mock_exists.return_value = False
        self.assertEqual(srm.handle_duplicate_filename("test_file", "/fake/dir"), "test_file")
        mock_exists.assert_called_with(os.path.join("/fake/dir", "test_file.pdf"))

        mock_exists.reset_mock()
        mock_exists.side_effect = [True, False]
        self.assertEqual(srm.handle_duplicate_filename("test_file", "/fake/dir"), "test_file_1")
        self.assertEqual(mock_exists.call_count, 2)

        # Case 3: Multiple duplicates exist
        mock_exists.reset_mock()
        mock_exists.side_effect = [True, True, True, False]
        self.assertEqual(srm.handle_duplicate_filename("test_file", "/fake/dir"), "test_file_3")
        self.assertEqual(mock_exists.call_count, 4)

class TestContentHandling(unittest.TestCase):
    """Tests for functions that handle file content, like text extraction and truncation."""

    def test_truncate_content_to_token_limit(self):
        """Tests that content is truncated correctly based on token count."""
        # This requires the tokenizer, which is a global variable in the script.
        long_text = "word " * 20000
        # The exact token count can be tricky, but it should be less than or equal to the max.
        truncated = srm.truncate_content_to_token_limit(long_text, srm.MAX_LENGTH)
        self.assertLessEqual(len(srm.ENCODING.encode(truncated)), srm.MAX_LENGTH)

        short_text = "This is a short text that is well within the token limit."
        self.assertEqual(srm.truncate_content_to_token_limit(short_text, srm.MAX_LENGTH), short_text)

class TestFileProcessing(unittest.TestCase):
    """Tests the core file processing and moving logic."""

    def setUp(self):
        """Set up a temporary directory structure for testing file operations."""
        self.test_dir = "temp_test_workspace"
        self.input_dir = os.path.join(self.test_dir, "input")
        self.renamed_dir = os.path.join(self.test_dir, "renamed")
        self.corrupted_dir = os.path.join(self.test_dir, "corrupted")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.renamed_dir, exist_ok=True)
        os.makedirs(self.corrupted_dir, exist_ok=True)

        # Create a dummy PDF file to be processed
        self.dummy_pdf_path = os.path.join(self.input_dir, "dummy.pdf")
        with open(self.dummy_pdf_path, "w") as f:
            f.write("dummy pdf content")

    def tearDown(self):
        """Remove the temporary directory structure after tests are complete."""
        shutil.rmtree(self.test_dir)

    @patch('sortrenamemovepdf.get_new_filename_with_retry')
    @patch('sortrenamemovepdf.extract_text_and_image')
    def test_process_pdf_success(self, mock_extract, mock_get_filename):
        """Tests the successful processing of a single PDF file."""
        mock_extract.return_value = ("some extracted text", None)
        mock_get_filename.return_value = "new_filename_from_ai"

        # Mock the progress bar and progress file
        pbar = MagicMock()
        mock_progress_file = mock_open()

        with patch('builtins.open', mock_progress_file):
            with open('dummy_progress', 'a') as progress_f:
                # Mock file locking as it's platform-specific
                with patch('sortrenamemovepdf.lock_file'), patch('sortrenamemovepdf.unlock_file'):
                    srm.process_pdf(self.dummy_pdf_path, "dummy.pdf", self.corrupted_dir, self.renamed_dir, pbar, progress_f)

        # Verify the file was moved to the 'renamed' directory
        self.assertFalse(os.path.exists(self.dummy_pdf_path))
        self.assertTrue(os.path.exists(os.path.join(self.renamed_dir, "new_filename_from_ai.pdf")))
        # Verify the progress bar was updated
        pbar.update.assert_called_once_with(1)
        # Verify progress was written to the log
        progress_f.write.assert_called_with("dummy.pdf\n")

    @patch('sortrenamemovepdf.extract_text_and_image')
    def test_process_pdf_corrupted(self, mock_extract):
        """Tests that a corrupted PDF is moved to the 'corrupted' directory."""
        from PyPDF2.errors import PdfReadError
        mock_extract.side_effect = PdfReadError("This is a test error for a corrupted PDF")

        pbar = MagicMock()
        mock_progress_file = mock_open()

        with patch('builtins.open', mock_progress_file):
            with open('dummy_progress', 'a') as progress_f:
                with patch('sortrenamemovepdf.lock_file'), patch('sortrenamemovepdf.unlock_file'):
                    srm.process_pdf(self.dummy_pdf_path, "dummy.pdf", self.corrupted_dir, self.renamed_dir, pbar, progress_f)

        # Verify the file was moved to the 'corrupted' directory
        self.assertFalse(os.path.exists(self.dummy_pdf_path))
        self.assertTrue(os.path.exists(os.path.join(self.corrupted_dir, "dummy.pdf")))
        pbar.update.assert_called_once_with(1)
        progress_f.write.assert_called_with("dummy.pdf\n")

    @patch('sortrenamemovepdf.get_filename_from_ai')
    def test_get_new_filename_with_retry_success(self, mock_get_filename_from_ai):
        """Tests the retry mechanism for the AI call, succeeding on the first try."""
        mock_get_filename_from_ai.return_value = "successful_name"
        result = srm.get_new_filename_with_retry("pdf content")
        self.assertEqual(result, "successful_name")
        mock_get_filename_from_ai.assert_called_once()

    @patch('sortrenamemovepdf.get_filename_from_ai')
    @patch('time.sleep', return_value=None) # Avoid actual sleeping during tests
    def test_get_new_filename_with_retry_failure(self, mock_sleep, mock_get_filename_from_ai):
        """Tests that the retry mechanism fails gracefully after max retries."""
        mock_get_filename_from_ai.side_effect = Exception("API Error")
        timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        result = srm.get_new_filename_with_retry("pdf content", max_retries=2)
        self.assertEqual(result, f"untitled_document_{timestamp}")
        self.assertEqual(mock_get_filename_from_ai.call_count, 2)


if __name__ == '__main__':
    unittest.main()
