"""
Tests for Configuration Manager

Tests the headless configuration management without UI dependencies.
Validates configuration loading, merging, and validation.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.interfaces.programmatic.cli_arguments import ParsedArguments
from src.interfaces.programmatic.configuration_manager import (
    ConfigurationManager,
    ProcessingConfiguration,
)


class TestConfigurationManager(unittest.TestCase):
    """Test headless configuration management."""

    def setUp(self):
        """Set up test configuration manager with temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.config_dir = Path(self.temp_dir.name) / "config"
        self.manager = ConfigurationManager(self.config_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_default_configuration(self):
        """Test default configuration is created correctly."""
        config = self.manager._get_default_configuration()  # pylint: disable=protected-access

        self.assertIsInstance(config, ProcessingConfiguration)
        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.ocr_language, "eng")
        self.assertEqual(config.ml_level, 2)
        self.assertFalse(config.organization_enabled)
        self.assertFalse(config.quiet_mode)

    def test_load_configuration_no_file(self):
        """Test loading configuration when no file exists."""
        config = self.manager.load_configuration()

        # Should return default configuration
        self.assertIsInstance(config, ProcessingConfiguration)
        self.assertEqual(config.provider, "openai")

    def test_save_and_load_configuration(self):
        """Test saving and loading configuration."""
        # Create test configuration
        config = ProcessingConfiguration(
            input_dir="/test/input",
            output_dir="/test/output",
            provider="claude",
            model="claude-3.5-sonnet",
            organization_enabled=True,
            ml_level=3,
        )

        # Save configuration
        success = self.manager.save_configuration(config)
        self.assertTrue(success)
        self.assertTrue(self.manager.config_file.exists())

        # Load configuration
        loaded_config = self.manager.load_configuration()

        self.assertEqual(loaded_config.input_dir, "/test/input")
        self.assertEqual(loaded_config.output_dir, "/test/output")
        self.assertEqual(loaded_config.provider, "claude")
        self.assertEqual(loaded_config.model, "claude-3.5-sonnet")
        self.assertTrue(loaded_config.organization_enabled)
        self.assertEqual(loaded_config.ml_level, 3)

    @patch.dict(
        os.environ,
        {
            "CONTENT_TAMER_PROVIDER": "gemini",
            "CONTENT_TAMER_ML_LEVEL": "1",
            "CONTENT_TAMER_QUIET": "true",
            "GEMINI_API_KEY": "test-gemini-key",
        },
    )
    def test_environment_variable_loading(self):
        """Test configuration loading from environment variables."""
        config = self.manager.load_configuration()

        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.ml_level, 1)
        self.assertTrue(config.quiet_mode)
        self.assertEqual(config.api_key, "test-gemini-key")

    def test_configuration_precedence(self):
        """Test configuration precedence: CLI args > env vars > config file > defaults."""
        # Create config file
        file_config = ProcessingConfiguration(
            input_dir="/test",
            output_dir="/test",
            provider="openai",
            ml_level=2,
            organization_enabled=True,
        )
        self.manager.save_configuration(file_config)

        # Set environment variables
        with patch.dict(
            os.environ, {"CONTENT_TAMER_PROVIDER": "claude", "CONTENT_TAMER_ML_LEVEL": "3"}
        ):
            # Create CLI arguments
            cli_args = ParsedArguments(
                input_dir="/test", output_dir="/test", provider="gemini", model="gemini-2.0-flash"
            )

            # Load with all sources
            config = self.manager.load_configuration(cli_args)

            # CLI args should have highest precedence
            self.assertEqual(config.provider, "gemini")
            self.assertEqual(config.model, "gemini-2.0-flash")

            # Env var should override file config
            self.assertEqual(config.ml_level, 3)

            # File config should be used where not overridden
            self.assertTrue(config.organization_enabled)

    def test_configuration_validation_success(self):
        """Test validation passes for valid configuration."""
        with tempfile.TemporaryDirectory() as temp_input, tempfile.TemporaryDirectory() as temp_output:

            config = ProcessingConfiguration(
                input_dir=temp_input, output_dir=temp_output, provider="openai", api_key="test-key"
            )

            errors = self.manager.validate_configuration(config)
            self.assertEqual(errors, [])

    def test_configuration_validation_errors(self):
        """Test validation catches configuration errors."""
        config = ProcessingConfiguration(
            input_dir="/nonexistent/input",
            output_dir="/readonly/output",
            provider="",
            api_key=None,
            ml_level=5,  # Invalid
        )

        errors = self.manager.validate_configuration(config)

        # Should have multiple errors
        self.assertGreater(len(errors), 0)

        # Check for specific error types
        error_text = " ".join(errors).lower()
        self.assertIn("directory does not exist", error_text)
        self.assertIn("provider", error_text)
        self.assertIn("ml level", error_text)

    @patch.dict(os.environ, {}, clear=True)  # Clear environment
    def test_api_key_validation(self):
        """Test API key validation for different providers."""
        with tempfile.TemporaryDirectory() as temp_input, tempfile.TemporaryDirectory() as temp_output:

            # Test without API key or environment variable
            config = ProcessingConfiguration(
                input_dir=temp_input, output_dir=temp_output, provider="openai", api_key=None
            )

            errors = self.manager.validate_configuration(config)
            self.assertTrue(any("API key required" in error for error in errors))

            # Test with API key
            config.api_key = "test-key"
            errors = self.manager.validate_configuration(config)
            self.assertFalse(any("API key required" in error for error in errors))

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"})
    def test_api_key_from_environment(self):
        """Test API key loading from environment variable."""
        with tempfile.TemporaryDirectory() as temp_input, tempfile.TemporaryDirectory() as temp_output:

            config = ProcessingConfiguration(
                input_dir=temp_input, output_dir=temp_output, provider="openai", api_key=None
            )

            # Should pass validation with environment API key
            errors = self.manager.validate_configuration(config)
            self.assertFalse(any("API key required" in error for error in errors))

    def test_export_configuration_json(self):
        """Test configuration export to JSON."""
        config = ProcessingConfiguration(
            input_dir="/test/input", output_dir="/test/output", provider="claude"
        )

        json_export = self.manager.export_configuration(config, "json")

        # Should be valid JSON
        parsed = json.loads(json_export)
        self.assertEqual(parsed["input_dir"], "/test/input")
        self.assertEqual(parsed["provider"], "claude")

    def test_export_configuration_env(self):
        """Test configuration export to environment variable format."""
        config = ProcessingConfiguration(input_dir="/test/input", provider="openai", ml_level=2)

        env_export = self.manager.export_configuration(config, "env")

        self.assertIn("export CONTENT_TAMER_INPUT_DIR='/test/input'", env_export)
        self.assertIn("export CONTENT_TAMER_PROVIDER='openai'", env_export)
        self.assertIn("export CONTENT_TAMER_ML_LEVEL='2'", env_export)

    def test_export_unsupported_format(self):
        """Test export with unsupported format raises error."""
        config = ProcessingConfiguration(input_dir="/test", output_dir="/test")

        with self.assertRaises(ValueError) as cm:
            self.manager.export_configuration(config, "unsupported")

        self.assertIn("Unsupported export format", str(cm.exception))

    def test_load_from_dict(self):
        """Test loading configuration from dictionary."""
        config_dict = {
            "input_dir": "/test/input",
            "output_dir": "/test/output",
            "provider": "claude",
            "organization_enabled": True,
            "ml_level": 3,
        }

        config = self.manager.load_from_dict(config_dict)

        self.assertEqual(config.input_dir, "/test/input")
        self.assertEqual(config.provider, "claude")
        self.assertTrue(config.organization_enabled)
        self.assertEqual(config.ml_level, 3)

    def test_load_from_invalid_dict(self):
        """Test loading from invalid dictionary raises error."""
        invalid_dict = {"invalid_field": "value", "ml_level": "not_an_int"}  # Wrong type

        with self.assertRaises(ValueError):
            self.manager.load_from_dict(invalid_dict)

    def test_configuration_summary(self):
        """Test configuration summary generation."""
        config = ProcessingConfiguration(
            input_dir="/test/input",
            output_dir="/test/output",
            provider="openai",
            model="gpt-4o",
            organization_enabled=True,
            quiet_mode=True,
        )

        summary = self.manager.get_configuration_summary(config)

        self.assertIn("Input Directory", summary)
        self.assertEqual(summary["Input Directory"], "/test/input")
        self.assertEqual(summary["AI Provider"], "openai")
        self.assertEqual(summary["AI Model"], "gpt-4o")
        self.assertEqual(summary["Organization"], "Enabled")
        self.assertEqual(summary["Display Mode"], "Quiet")

    def test_merge_command_line_arguments(self):
        """Test merging command line arguments with configuration."""
        # Base configuration
        config = ProcessingConfiguration(
            input_dir="/test",
            output_dir="/test",
            provider="openai",
            ml_level=2,
            organization_enabled=False,
        )

        # CLI arguments
        cli_args = ParsedArguments(
            input_dir="/test",
            output_dir="/test",
            provider="claude",  # Should override
            model="claude-3.5-sonnet",  # Should be added
            organize=True,  # Should enable organization
            ml_level=3,  # Should override
        )

        merged_config = self.manager._merge_command_line_arguments(
            config, cli_args
        )  # pylint: disable=protected-access

        self.assertEqual(merged_config.provider, "claude")
        self.assertEqual(merged_config.model, "claude-3.5-sonnet")
        self.assertTrue(merged_config.organization_enabled)
        self.assertEqual(merged_config.ml_level, 3)

    def test_quiet_overrides_verbose(self):
        """Test that quiet mode overrides verbose mode."""
        config = ProcessingConfiguration(verbose_mode=True)

        cli_args = ParsedArguments(quiet_mode=True, verbose_mode=True)

        merged_config = self.manager._merge_command_line_arguments(
            config, cli_args
        )  # pylint: disable=protected-access

        self.assertTrue(merged_config.quiet_mode)
        self.assertFalse(merged_config.verbose_mode)


class TestProcessingConfiguration(unittest.TestCase):
    """Test ProcessingConfiguration dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ProcessingConfiguration(input_dir="/test/input", output_dir="/test/output")

        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.ocr_language, "eng")
        self.assertEqual(config.ml_level, 2)
        self.assertFalse(config.organization_enabled)
        self.assertFalse(config.quiet_mode)
        self.assertFalse(config.verbose_mode)
        self.assertIsNone(config.unprocessed_dir)
        self.assertIsNone(config.model)
        self.assertIsNone(config.api_key)

    def test_field_assignment(self):
        """Test all fields can be assigned."""
        config = ProcessingConfiguration(
            input_dir="/test/input",
            output_dir="/test/output",
            unprocessed_dir="/test/unprocessed",
            provider="claude",
            model="claude-3.5-sonnet",
            api_key="test-key",
            ocr_language="eng+fra",
            reset_progress=True,
            organization_enabled=True,
            ml_level=3,
            quiet_mode=True,
            verbose_mode=False,
            feature_flags={"test": True},
            version="2.0",
        )

        self.assertEqual(config.input_dir, "/test/input")
        self.assertEqual(config.output_dir, "/test/output")
        self.assertEqual(config.unprocessed_dir, "/test/unprocessed")
        self.assertEqual(config.provider, "claude")
        self.assertEqual(config.model, "claude-3.5-sonnet")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.ocr_language, "eng+fra")
        self.assertTrue(config.reset_progress)
        self.assertTrue(config.organization_enabled)
        self.assertEqual(config.ml_level, 3)
        self.assertTrue(config.quiet_mode)
        self.assertFalse(config.verbose_mode)
        self.assertEqual(config.feature_flags["test"], True)
        self.assertEqual(config.version, "2.0")


if __name__ == "__main__":
    unittest.main()
