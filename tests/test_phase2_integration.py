"""
Integration tests for Phase 2 CLI enhancements with backward compatibility validation.
"""

import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, mock_open, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ai_providers import AIProviderFactory
from core.application import organize_content
from core.cli_parser import _print_capabilities, parse_arguments
from core.directory_manager import ensure_default_directories
from core.file_processor import (
    get_new_filename_with_retry_enhanced,
    process_file_enhanced,
)
from main import main
from utils.display_manager import DisplayManager


class TestPhase2BackwardCompatibility(unittest.TestCase):
    """Test that Phase 2 enhancements maintain backward compatibility."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.processed_dir = os.path.join(self.temp_dir, "processed")
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")

        # Create directories
        os.makedirs(self.input_dir)
        os.makedirs(self.processed_dir)
        os.makedirs(self.unprocessed_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_organize_content_without_display_options(self):
        """Test that organize_content works without display_options parameter."""
        # This tests the original API signature still works
        with patch("core.application.AIProviderFactory") as mock_factory, patch(
            "core.application.get_api_details"
        ) as mock_get_api, patch("os.listdir") as mock_listdir:

            mock_get_api.return_value = "test_key"
            mock_factory.get_default_model.return_value = "test-model"
            mock_factory.create.return_value = MagicMock()
            mock_listdir.return_value = []  # No files to process

            # Call with original signature (no display_options)
            result = organize_content(
                self.input_dir,
                self.unprocessed_dir,
                self.processed_dir,
                provider="openai",
                model="test-model",
            )

            # Should complete successfully
            self.assertTrue(result)

    def test_organize_content_with_display_options(self):
        """Test that organize_content works with new display_options parameter."""
        with patch("core.application.AIProviderFactory") as mock_factory, patch(
            "core.application.get_api_details"
        ) as mock_get_api, patch("os.listdir") as mock_listdir:

            mock_get_api.return_value = "test_key"
            mock_factory.get_default_model.return_value = "test-model"
            mock_factory.create.return_value = MagicMock()
            mock_listdir.return_value = []

            display_options = {
                "verbose": True,
                "quiet": False,
                "no_color": True,
                "show_stats": True,
            }

            # Call with new signature
            result = organize_content(
                self.input_dir,
                self.unprocessed_dir,
                self.processed_dir,
                provider="openai",
                model="test-model",
                display_options=display_options,
            )

            self.assertTrue(result)

    def test_display_options_default_to_none(self):
        """Test that display_options defaults to None and works correctly."""
        with patch("core.application.AIProviderFactory") as mock_factory, patch(
            "core.application.get_api_details"
        ) as mock_get_api, patch("os.listdir") as mock_listdir:

            mock_get_api.return_value = "test_key"
            mock_factory.get_default_model.return_value = "test-model"
            mock_factory.create.return_value = MagicMock()
            mock_listdir.return_value = []

            # Call without display_options (should default to None)
            result = organize_content(self.input_dir, self.unprocessed_dir, self.processed_dir)

            self.assertTrue(result)


class TestPhase2CLIArguments(unittest.TestCase):
    """Test new CLI arguments for Phase 2."""

    def test_new_display_arguments_exist(self):
        """Test that new display arguments are properly defined."""
        with patch("sys.argv", ["main.py", "--help"]):
            with self.assertRaises(SystemExit):
                with patch("sys.stdout", StringIO()) as mock_stdout:
                    parse_arguments()
                    help_text = mock_stdout.getvalue()

                    # Should contain new arguments
                    self.assertIn("--quiet", help_text)
                    self.assertIn("--verbose", help_text)
                    self.assertIn("--no-color", help_text)
                    self.assertIn("--no-stats", help_text)

    def test_quiet_argument_parsing(self):
        """Test quiet argument parsing."""
        with patch("sys.argv", ["main.py", "--quiet"]):
            args = parse_arguments()
            self.assertTrue(args.quiet)

    def test_verbose_argument_parsing(self):
        """Test verbose argument parsing."""
        with patch("sys.argv", ["main.py", "--verbose"]):
            args = parse_arguments()
            self.assertTrue(args.verbose)

    def test_short_form_arguments(self):
        """Test short form arguments work."""
        with patch("sys.argv", ["main.py", "-q", "-v"]):
            args = parse_arguments()
            self.assertTrue(args.quiet)
            self.assertTrue(args.verbose)


class TestPhase2MainFunction(unittest.TestCase):
    """Test main function integration with Phase 2 enhancements."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_quiet_verbose_mode_basic_functionality(self):
        """Test that quiet and verbose modes are properly configured in argument parsing."""
        # Test quiet mode argument parsing
        with patch("sys.argv", ["main.py", "--quiet"]):
            args = parse_arguments()
            self.assertTrue(args.quiet)
            self.assertFalse(args.verbose)

        # Test verbose mode argument parsing
        with patch("sys.argv", ["main.py", "--verbose"]):
            args = parse_arguments()
            self.assertFalse(args.quiet)
            self.assertTrue(args.verbose)


class TestPhase2ErrorHandling(unittest.TestCase):
    """Test error handling in Phase 2 enhancements."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_organize_content_handles_display_manager_errors(self):
        """Test that organize_content handles DisplayManager errors gracefully."""
        input_dir = os.path.join(self.temp_dir, "input")
        os.makedirs(input_dir)

        with patch("utils.display_manager.DisplayManager") as mock_display_manager:
            # Make DisplayManager constructor raise an exception
            mock_display_manager.side_effect = Exception("Display error")

            with self.assertRaises(Exception):
                organize_content(
                    input_dir,
                    self.temp_dir,
                    self.temp_dir,
                    display_options={"quiet": True},
                )

    def test_invalid_display_options_handled(self):
        """Test that invalid display options are handled gracefully."""
        input_dir = os.path.join(self.temp_dir, "input")
        os.makedirs(input_dir)

        with patch("core.application.AIProviderFactory") as mock_factory, patch(
            "core.application.get_api_details"
        ) as mock_get_api, patch("os.listdir") as mock_listdir:

            mock_get_api.return_value = "test_key"
            mock_factory.get_default_model.return_value = "test-model"
            mock_factory.create.return_value = MagicMock()
            mock_listdir.return_value = []

            # Pass invalid display options
            invalid_options = {"invalid_option": True, "another_invalid": "value"}

            # Should not crash, should ignore invalid options
            result = organize_content(
                input_dir, self.temp_dir, self.temp_dir, display_options=invalid_options
            )

            self.assertTrue(result)


class TestPhase2FileProcessing(unittest.TestCase):
    """Test file processing with enhanced display integration."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_process_file_enhanced_signature(self):
        """Test that process_file_enhanced has correct signature."""
        from main import process_file_enhanced

        # Check that function exists and can be imported
        self.assertTrue(callable(process_file_enhanced))

        # Check that function has the expected parameters
        import inspect

        sig = inspect.signature(process_file_enhanced)
        expected_params = {
            "input_path",
            "filename",
            "unprocessed_folder",
            "renamed_folder",
            "progress_f",
            "ocr_lang",
            "ai_client",
            "organizer",
            "display_context",
        }
        actual_params = set(sig.parameters.keys())
        self.assertTrue(expected_params.issubset(actual_params))

    def test_enhanced_retry_function_exists(self):
        """Test that enhanced retry function exists."""
        from main import get_new_filename_with_retry_enhanced

        self.assertTrue(callable(get_new_filename_with_retry_enhanced))

        # Check signature includes display_context parameter
        import inspect

        sig = inspect.signature(get_new_filename_with_retry_enhanced)
        self.assertIn("display_context", sig.parameters)


if __name__ == "__main__":
    unittest.main()
