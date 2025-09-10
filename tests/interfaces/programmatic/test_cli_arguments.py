"""
Tests for Pure CLI Argument Parsing

Tests the argument parsing functionality without UI dependencies.
Validates programmatic interface for automation use cases.
"""

import unittest

from src.interfaces.programmatic.cli_arguments import ParsedArguments, PureCLIParser


class TestPureCLIParser(unittest.TestCase):
    """Test pure CLI argument parsing without UI coupling."""

    def setUp(self):
        """Set up test parser."""
        self.parser = PureCLIParser()

    def test_default_arguments(self):
        """Test parsing with no arguments uses defaults."""
        args = self.parser.parse_args([])

        self.assertEqual(args.provider, "openai")
        self.assertEqual(args.ocr_language, "eng")
        self.assertEqual(args.ml_level, 2)
        self.assertEqual(args.command_type, "process")
        self.assertFalse(args.exit_after_command)

    def test_basic_file_arguments(self):
        """Test basic file path arguments."""
        test_args = ["--input", "/test/input", "--renamed", "/test/output"]

        args = self.parser.parse_args(test_args)

        self.assertEqual(args.input_dir, "/test/input")
        self.assertEqual(args.output_dir, "/test/output")
        self.assertEqual(args.command_type, "process")

    def test_ai_provider_arguments(self):
        """Test AI provider and model arguments."""
        test_args = [
            "--provider",
            "claude",
            "--model",
            "claude-3.5-sonnet",
            "--api-key",
            "test-key",
        ]

        args = self.parser.parse_args(test_args)

        self.assertEqual(args.provider, "claude")
        self.assertEqual(args.model, "claude-3.5-sonnet")
        self.assertEqual(args.api_key, "test-key")

    def test_organization_arguments(self):
        """Test organization-related arguments."""
        test_args = ["--organize", "--ml-level", "3"]

        args = self.parser.parse_args(test_args)

        self.assertTrue(args.organize)
        self.assertEqual(args.ml_level, 3)
        self.assertFalse(args.no_organize)

    def test_display_arguments(self):
        """Test display mode arguments."""
        # Test quiet mode
        quiet_args = ["--quiet"]
        args = self.parser.parse_args(quiet_args)
        self.assertTrue(args.quiet_mode)
        self.assertFalse(args.verbose_mode)

        # Test verbose mode
        verbose_args = ["--verbose"]
        args = self.parser.parse_args(verbose_args)
        self.assertFalse(args.quiet_mode)
        self.assertTrue(args.verbose_mode)

    def test_information_commands(self):
        """Test information commands set correct command type."""
        # Test list models
        args = self.parser.parse_args(["--list-models"])
        self.assertTrue(args.list_models)
        self.assertEqual(args.command_type, "info")
        self.assertTrue(args.exit_after_command)

        # Test feature flags
        args = self.parser.parse_args(["--show-feature-flags"])
        self.assertTrue(args.show_feature_flags)
        self.assertEqual(args.command_type, "info")
        self.assertTrue(args.exit_after_command)

    def test_setup_commands(self):
        """Test setup commands set correct command type."""
        # Test local LLM setup
        args = self.parser.parse_args(["--setup-local-llm"])
        self.assertTrue(args.setup_local_llm)
        self.assertEqual(args.command_type, "setup")
        self.assertTrue(args.exit_after_command)

        # Test model download
        args = self.parser.parse_args(["--download-model", "gemma2:2b"])
        self.assertEqual(args.download_model, "gemma2:2b")
        self.assertEqual(args.command_type, "setup")
        self.assertTrue(args.exit_after_command)

    def test_management_commands(self):
        """Test management commands set correct command type."""
        # Test dependency check
        args = self.parser.parse_args(["--check-dependencies"])
        self.assertTrue(args.check_dependencies)
        self.assertEqual(args.command_type, "manage")
        self.assertTrue(args.exit_after_command)

        # Test dependency configuration
        args = self.parser.parse_args(["--configure-dependency", "tesseract", "/usr/bin/tesseract"])
        self.assertEqual(args.configure_dependency, ["tesseract", "/usr/bin/tesseract"])
        self.assertEqual(args.command_type, "manage")
        self.assertTrue(args.exit_after_command)

    def test_argument_validation_success(self):
        """Test validation passes for valid arguments."""
        args = ParsedArguments(
            input_dir="/test/input",
            output_dir="/test/output",
            provider="openai",
            api_key="test-key",
        )

        errors = self.parser.validate_args(args)
        self.assertEqual(errors, [])

    def test_argument_validation_conflicts(self):
        """Test validation catches conflicting arguments."""
        # Test conflicting organization arguments
        args = ParsedArguments(organize=True, no_organize=True)
        errors = self.parser.validate_args(args)
        self.assertIn("Cannot specify both --organize and --no-organize", errors)

        # Test conflicting display modes
        args = ParsedArguments(quiet_mode=True, verbose_mode=True)
        errors = self.parser.validate_args(args)
        self.assertIn("Cannot specify both --quiet and --verbose modes", errors)

        # Test conflicting feature flags
        args = ParsedArguments(
            enable_organization_features=True, disable_organization_features=True
        )
        errors = self.parser.validate_args(args)
        self.assertIn("Cannot both enable and disable organization features", errors)

    def test_quiet_mode_validation(self):
        """Test quiet mode requires API key for processing."""
        args = ParsedArguments(quiet_mode=True, command_type="process", api_key=None)

        errors = self.parser.validate_args(args)
        self.assertIn("Quiet mode requires --api-key for headless operation", errors)

        # Should pass with API key
        args.api_key = "test-key"
        errors = self.parser.validate_args(args)
        self.assertNotIn("Quiet mode requires --api-key for headless operation", errors)

    def test_dependency_configuration_validation(self):
        """Test dependency configuration validation."""
        # Invalid number of arguments
        args = ParsedArguments(configure_dependency=["tesseract"])
        errors = self.parser.validate_args(args)
        self.assertIn("--configure-dependency requires exactly 2 arguments: NAME PATH", errors)

        # Valid configuration
        args = ParsedArguments(configure_dependency=["tesseract", "/usr/bin/tesseract"])
        errors = self.parser.validate_args(args)
        self.assertNotIn("--configure-dependency requires exactly 2 arguments", errors)

    def test_help_text_generation(self):
        """Test help text is generated correctly."""
        help_text = self.parser.get_help_text()

        self.assertIn("Content Tamer AI", help_text)
        self.assertIn("--input", help_text)
        self.assertIn("--provider", help_text)
        self.assertIn("--organize", help_text)

    def test_usage_text_generation(self):
        """Test usage text is generated correctly."""
        usage_text = self.parser.get_usage_text()

        self.assertIn("usage:", usage_text.lower())
        self.assertIn("content-tamer-ai", usage_text.lower())


class TestParsedArguments(unittest.TestCase):
    """Test ParsedArguments dataclass functionality."""

    def test_default_values(self):
        """Test default values are set correctly."""
        args = ParsedArguments()

        self.assertEqual(args.provider, "openai")
        self.assertEqual(args.ocr_language, "eng")
        self.assertEqual(args.ml_level, 2)
        self.assertEqual(args.command_type, "process")
        self.assertFalse(args.exit_after_command)

    def test_field_assignment(self):
        """Test fields can be assigned correctly."""
        args = ParsedArguments(
            input_dir="/test/input",
            output_dir="/test/output",
            provider="claude",
            model="claude-3.5-sonnet",
            organize=True,
            ml_level=3,
        )

        self.assertEqual(args.input_dir, "/test/input")
        self.assertEqual(args.output_dir, "/test/output")
        self.assertEqual(args.provider, "claude")
        self.assertEqual(args.model, "claude-3.5-sonnet")
        self.assertTrue(args.organize)
        self.assertEqual(args.ml_level, 3)

    def test_boolean_fields(self):
        """Test boolean fields work correctly."""
        args = ParsedArguments(
            organize=True,
            no_organize=False,
            quiet_mode=True,
            verbose_mode=False,
            reset_progress=True,
        )

        self.assertTrue(args.organize)
        self.assertFalse(args.no_organize)
        self.assertTrue(args.quiet_mode)
        self.assertFalse(args.verbose_mode)
        self.assertTrue(args.reset_progress)

    def test_optional_fields(self):
        """Test optional fields can be None."""
        args = ParsedArguments()

        self.assertIsNone(args.input_dir)
        self.assertIsNone(args.output_dir)
        self.assertIsNone(args.model)
        self.assertIsNone(args.api_key)
        self.assertIsNone(args.download_model)
        self.assertIsNone(args.configure_dependency)


if __name__ == "__main__":
    unittest.main()
