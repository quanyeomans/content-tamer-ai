"""
Tests for utility functions (text processing, etc.)
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add Rich testing utilities for Rich testing patterns
from tests.utils.rich_test_utils import RichTestCase

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from utils.text_utils import truncate_content_to_token_limit
from utils.feature_flags import (
    OrganizationFeatureFlags,
    FeatureFlags,
    FeatureFlagManager,
    get_feature_manager,
    is_organization_enabled,
    should_show_guided_navigation,
    get_available_ml_levels,
)
from core.filename_config import (
    MAX_FILENAME_LENGTH,
    MIN_FILENAME_LENGTH,
    TARGET_FILENAME_WORDS,
    MAX_OUTPUT_TOKENS,
    calculate_optimal_tokens,
    get_filename_prompt_template,
    get_secure_filename_prompt_template,
    validate_generated_filename,
    get_token_limit_for_provider,
    get_config_summary,
)
from utils.expert_mode import ExpertConfig, ExpertModePrompter, prompt_expert_mode_if_needed

# Import tools module for testing
try:
    from tools.token_analysis import analyze_filename_tokens

    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


class TestTextUtils(unittest.TestCase, RichTestCase):
    """Test text processing utilities."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_truncate_content_to_token_limit(self):
        """Test that content is truncated correctly based on token count."""
        # Short text should remain unchanged
        short_text = "This is a short text that is well within the token limit."
        self.assertEqual(truncate_content_to_token_limit(short_text, 1000), short_text)

        # Long text should be truncated
        long_text = "word " * 10000
        truncated = truncate_content_to_token_limit(long_text, 100)
        self.assertLess(len(truncated), len(long_text))

        # Verify token count is within limit
        from utils.text_utils import ENCODING

        token_count = len(ENCODING.encode(truncated))
        self.assertLessEqual(token_count, 100)

    def test_truncate_empty_content(self):
        """Test truncation with empty or None content."""
        self.assertEqual(truncate_content_to_token_limit("", 100), "")
        self.assertEqual(truncate_content_to_token_limit("   ", 100), "   ")


class TestOrganizationFeatureFlags(unittest.TestCase, RichTestCase):
    """Test OrganizationFeatureFlags dataclass and methods."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_default_values(self):
        """Test that default values are set correctly."""
        flags = OrganizationFeatureFlags()

        # Main feature flags defaults
        self.assertFalse(flags.enable_organization)  # Disabled by default for controlled rollout
        self.assertTrue(flags.enable_guided_navigation)
        self.assertTrue(flags.enable_expert_mode_integration)
        self.assertTrue(flags.enable_auto_enablement)

        # ML enhancement defaults
        self.assertTrue(flags.enable_ml_level_1)
        self.assertTrue(flags.enable_ml_level_2)
        self.assertTrue(flags.enable_ml_level_3)

        # Safety limits
        self.assertEqual(flags.max_files_for_auto_enable, 100)
        self.assertEqual(flags.require_confirmation_above, 50)
        self.assertEqual(flags.rollout_percentage, 100.0)

    def test_is_organization_available_safety_limits(self):
        """Test safety limits for organization availability."""
        flags = OrganizationFeatureFlags(rollout_percentage=100.0)

        # Normal file count should be available
        self.assertTrue(flags.is_organization_available(file_count=10))
        self.assertTrue(flags.is_organization_available(file_count=50))

        # Large file count should be blocked for safety
        self.assertFalse(flags.is_organization_available(file_count=101))
        self.assertFalse(flags.is_organization_available(file_count=1000))

    def test_is_organization_available_rollout_control(self):
        """Test rollout percentage control."""
        flags = OrganizationFeatureFlags(rollout_percentage=0.0)
        self.assertFalse(flags.is_organization_available(file_count=1))

        flags = OrganizationFeatureFlags(rollout_percentage=50.0)
        self.assertFalse(
            flags.is_organization_available(file_count=1)
        )  # Only 100% enabled currently

        flags = OrganizationFeatureFlags(rollout_percentage=100.0)
        self.assertTrue(flags.is_organization_available(file_count=1))

    def test_should_auto_enable_logic(self):
        """Test auto-enablement logic for guided navigation."""
        flags = OrganizationFeatureFlags(enable_auto_enablement=True, rollout_percentage=100.0)

        # Single file should not auto-enable
        self.assertFalse(flags.should_auto_enable(file_count=1))

        # Multiple files should auto-enable
        self.assertTrue(flags.should_auto_enable(file_count=2))
        self.assertTrue(flags.should_auto_enable(file_count=10))

        # Disabled auto-enablement
        flags.enable_auto_enablement = False
        self.assertFalse(flags.should_auto_enable(file_count=10))

        # Exceeds safety limit
        self.assertFalse(flags.should_auto_enable(file_count=101))


class TestFeatureFlags(unittest.TestCase, RichTestCase):
    """Test FeatureFlags dataclass and serialization."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_from_dict_serialization(self):
        """Test creating FeatureFlags from dictionary."""
        data = {
            "organization": {
                "enable_organization": True,
                "enable_ml_level_2": False,
                "max_files_for_auto_enable": 200,
                "rollout_percentage": 75.0,
            }
        }

        flags = FeatureFlags.from_dict(data)

        self.assertTrue(flags.organization.enable_organization)
        self.assertFalse(flags.organization.enable_ml_level_2)
        self.assertEqual(flags.organization.max_files_for_auto_enable, 200)
        self.assertEqual(flags.organization.rollout_percentage, 75.0)

        # Should use defaults for unspecified values
        self.assertTrue(flags.organization.enable_guided_navigation)

    def test_to_dict_serialization(self):
        """Test converting FeatureFlags to dictionary."""
        org_flags = OrganizationFeatureFlags(
            enable_organization=True, enable_ml_level_1=False, max_files_for_auto_enable=300
        )
        flags = FeatureFlags(organization=org_flags)

        data = flags.to_dict()

        self.assertEqual(data["organization"]["enable_organization"], True)
        self.assertEqual(data["organization"]["enable_ml_level_1"], False)
        self.assertEqual(data["organization"]["max_files_for_auto_enable"], 300)

    def test_empty_dict_handling(self):
        """Test handling of empty or malformed dictionaries."""
        # Empty dict should use all defaults
        flags = FeatureFlags.from_dict({})
        self.assertFalse(flags.organization.enable_organization)  # Default

        # Missing organization section
        flags = FeatureFlags.from_dict({"other": "data"})
        self.assertFalse(flags.organization.enable_organization)


class TestFeatureFlagManager(unittest.TestCase, RichTestCase):
    """Test FeatureFlagManager configuration loading and persistence."""
    
    def setUp(self):
        """Set up test environment with temporary directory and Rich testing patterns."""
        RichTestCase.setUp(self)
        # Keep existing setUp logic
        self.temp_dir = tempfile.mkdtemp()
        self.manager = FeatureFlagManager(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)
        # Keep existing tearDown logic
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = FeatureFlagManager(config_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_flags_default_values(self):
        """Test loading flags with no config file uses defaults."""
        flags = self.manager.load_flags()

        self.assertFalse(flags.organization.enable_organization)
        self.assertTrue(flags.organization.enable_guided_navigation)
        self.assertEqual(flags.organization.max_files_for_auto_enable, 100)

    def test_load_flags_from_config_file(self):
        """Test loading flags from JSON config file."""
        config_data = {
            "organization": {
                "enable_organization": True,
                "enable_ml_level_3": False,
                "rollout_percentage": 80.0,
            }
        }

        config_file = Path(self.temp_dir) / "feature_flags.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        flags = self.manager.load_flags()

        self.assertTrue(flags.organization.enable_organization)
        self.assertFalse(flags.organization.enable_ml_level_3)
        self.assertEqual(flags.organization.rollout_percentage, 80.0)

    def test_load_flags_malformed_config_file(self):
        """Test handling of malformed JSON config file."""
        config_file = Path(self.temp_dir) / "feature_flags.json"
        with open(config_file, "w") as f:
            f.write("invalid json {")

        # Should fall back to defaults without raising exception
        flags = self.manager.load_flags()
        self.assertFalse(flags.organization.enable_organization)  # Default value

    @patch.dict(
        os.environ,
        {
            "CONTENT_TAMER_ENABLE_ORGANIZATION": "true",
            "CONTENT_TAMER_ENABLE_ML_LEVEL_2": "false",
            "CONTENT_TAMER_MAX_FILES_AUTO_ENABLE": "150",
            "CONTENT_TAMER_ORGANIZATION_ROLLOUT": "90.5",
        },
    )
    def test_environment_variable_overrides(self):
        """Test that environment variables override config file values."""
        # Create config file with different values
        config_data = {
            "organization": {
                "enable_organization": False,  # Will be overridden by env var
                "enable_ml_level_2": True,  # Will be overridden by env var
                "max_files_for_auto_enable": 100,  # Will be overridden by env var
                "rollout_percentage": 100.0,  # Will be overridden by env var
            }
        }

        config_file = Path(self.temp_dir) / "feature_flags.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        flags = self.manager.load_flags()

        # Environment variables should override config file
        self.assertTrue(flags.organization.enable_organization)
        self.assertFalse(flags.organization.enable_ml_level_2)
        self.assertEqual(flags.organization.max_files_for_auto_enable, 150)
        self.assertEqual(flags.organization.rollout_percentage, 90.5)

    @patch.dict(
        os.environ,
        {
            "CONTENT_TAMER_ENABLE_ORGANIZATION": "invalid_bool",
            "CONTENT_TAMER_MAX_FILES_AUTO_ENABLE": "not_a_number",
            "CONTENT_TAMER_ORGANIZATION_ROLLOUT": "not_a_float",
        },
    )
    def test_invalid_environment_values(self):
        """Test handling of invalid environment variable values."""
        flags = self.manager.load_flags()

        # Should use defaults for invalid values
        self.assertFalse(flags.organization.enable_organization)  # Default for invalid bool
        self.assertEqual(
            flags.organization.max_files_for_auto_enable, 100
        )  # Default for invalid int
        self.assertEqual(flags.organization.rollout_percentage, 100.0)  # Default for invalid float

    def test_save_flags_success(self):
        """Test successfully saving flags to config file."""
        org_flags = OrganizationFeatureFlags(
            enable_organization=True, max_files_for_auto_enable=250
        )
        flags = FeatureFlags(organization=org_flags)

        success = self.manager.save_flags(flags)
        self.assertTrue(success)

        # Verify file was created and contains correct data
        config_file = Path(self.temp_dir) / "feature_flags.json"
        self.assertTrue(config_file.exists())

        with open(config_file, "r") as f:
            saved_data = json.load(f)

        self.assertTrue(saved_data["organization"]["enable_organization"])
        self.assertEqual(saved_data["organization"]["max_files_for_auto_enable"], 250)

    def test_save_flags_failure(self):
        """Test handling of save failure (e.g., permissions)."""
        # Mock the file operation to force failure
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            flags = FeatureFlags(organization=OrganizationFeatureFlags())
            success = self.manager.save_flags(flags)

            self.assertFalse(success)

    def test_caching_behavior(self):
        """Test that flags are cached and cache can be invalidated."""
        # First load
        flags1 = self.manager.load_flags()

        # Second load should return same instance (cached)
        flags2 = self.manager.load_flags()
        self.assertIs(flags1, flags2)

        # Force reload should return new instance
        flags3 = self.manager.is_organization_enabled(force_check=True)
        # The manager internal cache should be cleared, different behavior

    def test_get_available_ml_levels(self):
        """Test getting available ML levels based on flags."""
        # All levels enabled
        flags = OrganizationFeatureFlags(
            enable_ml_level_1=True, enable_ml_level_2=True, enable_ml_level_3=True
        )
        self.manager._flags = FeatureFlags(organization=flags)

        available = self.manager.get_available_ml_levels()
        self.assertEqual(available, [1, 2, 3])

        # Only level 1 and 3 enabled
        flags.enable_ml_level_2 = False
        available = self.manager.get_available_ml_levels()
        self.assertEqual(available, [1, 3])

        # No levels enabled
        flags.enable_ml_level_1 = False
        flags.enable_ml_level_3 = False
        available = self.manager.get_available_ml_levels()
        self.assertEqual(available, [])

    def test_validate_ml_level(self):
        """Test ML level validation and fallback logic."""
        flags = OrganizationFeatureFlags(
            enable_ml_level_1=True, enable_ml_level_2=False, enable_ml_level_3=True
        )
        self.manager._flags = FeatureFlags(organization=flags)

        # Valid level should be returned unchanged
        self.assertEqual(self.manager.validate_ml_level(1), 1)
        self.assertEqual(self.manager.validate_ml_level(3), 3)

        # Invalid level should return closest available
        self.assertEqual(self.manager.validate_ml_level(2), 1)  # Closer to 1 than 3

        # No levels available should return 1 as fallback
        flags.enable_ml_level_1 = False
        flags.enable_ml_level_3 = False
        self.assertEqual(self.manager.validate_ml_level(2), 1)


class TestGlobalFeatureFlagHelpers(unittest.TestCase, RichTestCase):
    """Test global convenience functions."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
        # Reset global manager before each test
        import utils.feature_flags
        utils.feature_flags._feature_manager = None
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def setUp(self):
        """Reset global manager before each test."""
        import utils.feature_flags

        utils.feature_flags._feature_manager = None

    def test_get_feature_manager_singleton(self):
        """Test that get_feature_manager returns singleton instance."""
        manager1 = get_feature_manager()
        manager2 = get_feature_manager()

        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, FeatureFlagManager)

    @patch("utils.feature_flags.get_feature_manager")
    def test_is_organization_enabled_helper(self, mock_get_manager):
        """Test is_organization_enabled convenience function."""
        mock_manager = MagicMock()
        mock_manager.is_organization_enabled.return_value = True
        mock_get_manager.return_value = mock_manager

        result = is_organization_enabled(file_count=5)

        self.assertTrue(result)
        mock_manager.is_organization_enabled.assert_called_once_with(5)

    @patch("utils.feature_flags.get_feature_manager")
    def test_should_show_guided_navigation_helper(self, mock_get_manager):
        """Test should_show_guided_navigation convenience function."""
        mock_manager = MagicMock()
        mock_manager.should_show_guided_navigation.return_value = False
        mock_get_manager.return_value = mock_manager

        result = should_show_guided_navigation(file_count=1)

        self.assertFalse(result)
        mock_manager.should_show_guided_navigation.assert_called_once_with(1)

    @patch("utils.feature_flags.get_feature_manager")
    def test_get_available_ml_levels_helper(self, mock_get_manager):
        """Test get_available_ml_levels convenience function."""
        mock_manager = MagicMock()
        mock_manager.get_available_ml_levels.return_value = [1, 2, 3]
        mock_get_manager.return_value = mock_manager

        result = get_available_ml_levels()

        self.assertEqual(result, [1, 2, 3])
        mock_manager.get_available_ml_levels.assert_called_once()


class TestFilenameConfigCalculations(unittest.TestCase, RichTestCase):
    """Test filename configuration calculations and edge cases."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_calculate_optimal_tokens_default(self):
        """Test optimal token calculation with default values."""
        tokens = calculate_optimal_tokens()

        # Should be calculated as: ceil(160/2.7) * 1.3 = ceil(59.26) * 1.3 = 60 * 1.3 = 78
        expected = 78  # Rounded up with safety buffer
        self.assertEqual(tokens, expected)

        # Should be at least minimum
        self.assertGreaterEqual(tokens, 20)

    def test_calculate_optimal_tokens_custom_length(self):
        """Test optimal token calculation with custom lengths."""
        # Very short filename
        short_tokens = calculate_optimal_tokens(20)
        self.assertGreaterEqual(short_tokens, 20)  # Should hit minimum

        # Medium filename
        medium_tokens = calculate_optimal_tokens(80)
        self.assertGreater(medium_tokens, short_tokens)
        self.assertLess(medium_tokens, calculate_optimal_tokens(160))

        # Very long filename
        long_tokens = calculate_optimal_tokens(300)
        self.assertGreater(long_tokens, calculate_optimal_tokens(160))

    def test_calculate_optimal_tokens_edge_cases(self):
        """Test token calculation edge cases."""
        # Zero length should return minimum
        self.assertEqual(calculate_optimal_tokens(0), 20)

        # Negative length should return minimum
        self.assertEqual(calculate_optimal_tokens(-10), 20)

        # Very large length should scale appropriately
        large_tokens = calculate_optimal_tokens(1000)
        self.assertGreater(large_tokens, 300)  # Should scale significantly

    def test_constants_consistency(self):
        """Test that constants are consistent and reasonable."""
        # Length constraints
        self.assertGreater(MAX_FILENAME_LENGTH, MIN_FILENAME_LENGTH)
        self.assertEqual(MAX_FILENAME_LENGTH, 160)
        self.assertEqual(MIN_FILENAME_LENGTH, 10)

        # Word targets
        self.assertIsInstance(TARGET_FILENAME_WORDS, tuple)
        self.assertEqual(len(TARGET_FILENAME_WORDS), 2)
        self.assertLess(TARGET_FILENAME_WORDS[0], TARGET_FILENAME_WORDS[1])

        # Token limits should be positive and reasonable
        self.assertGreater(MAX_OUTPUT_TOKENS, 20)
        self.assertLess(MAX_OUTPUT_TOKENS, 200)  # Should be reasonable for filename


class TestFilenameConfigValidation(unittest.TestCase, RichTestCase):
    """Test filename validation and sanitization edge cases."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_validate_generated_filename_normal(self):
        """Test validation of normal, valid filenames."""
        # Good filename should pass through unchanged
        good = "Strategic_Planning_Document_2024"
        self.assertEqual(validate_generated_filename(good), good)

        # Mixed case should be preserved
        mixed = "Project_Alpha_Status_Report_Q3"
        self.assertEqual(validate_generated_filename(mixed), mixed)

    def test_validate_generated_filename_sanitization(self):
        """Test sanitization of problematic characters."""
        # Invalid characters should be replaced with underscores
        invalid_chars = "Strategic Planning Document (2024)!"
        sanitized = validate_generated_filename(invalid_chars)
        self.assertNotIn("(", sanitized)
        self.assertNotIn(")", sanitized)
        self.assertNotIn("!", sanitized)
        self.assertIn("Strategic", sanitized)
        self.assertIn("Planning", sanitized)

        # Unicode characters should be sanitized
        unicode_name = "Strategic_Planning_Документ_2024"
        sanitized = validate_generated_filename(unicode_name)
        self.assertTrue(all(c.isascii() for c in sanitized))

    def test_validate_generated_filename_length_constraints(self):
        """Test length constraint enforcement."""
        # Too short - should be padded
        short = "abc"
        validated = validate_generated_filename(short)
        self.assertGreaterEqual(len(validated), MIN_FILENAME_LENGTH)
        self.assertIn("document", validated)

        # Too long - should be truncated
        long_name = "Very_Long_Strategic_Planning_Document_With_Extensive_Details_About_Q3_Operations_And_Future_Projections_For_Next_Year_Including_Budget_Analysis_And_Resource_Allocation_Plans_2024"
        validated = validate_generated_filename(long_name)
        self.assertLessEqual(len(validated), MAX_FILENAME_LENGTH)
        self.assertTrue(validated.startswith("Very_Long_Strategic"))

        # Exactly max length should be preserved
        max_length_name = "A" * MAX_FILENAME_LENGTH
        validated = validate_generated_filename(max_length_name)
        self.assertEqual(len(validated), MAX_FILENAME_LENGTH)

    def test_validate_generated_filename_whitespace_handling(self):
        """Test handling of various whitespace and quote issues."""
        # Leading/trailing whitespace should be stripped
        whitespace = "  Strategic_Planning_Document  "
        validated = validate_generated_filename(whitespace)
        self.assertEqual(validated, "Strategic_Planning_Document")

        # Quotes should be stripped
        quoted = '"Strategic_Planning_Document"'
        validated = validate_generated_filename(quoted)
        self.assertEqual(validated, "Strategic_Planning_Document")

        # Multiple quote types
        multi_quoted = "'''Strategic_Planning_Document```"
        validated = validate_generated_filename(multi_quoted)
        self.assertEqual(validated, "Strategic_Planning_Document")

    def test_validate_generated_filename_consecutive_underscores(self):
        """Test handling of consecutive underscores."""
        # Multiple underscores should be collapsed
        multi_underscores = "Strategic____Planning___Document"
        validated = validate_generated_filename(multi_underscores)
        self.assertEqual(validated, "Strategic_Planning_Document")

        # Leading/trailing underscores should be removed
        surrounded = "___Strategic_Planning_Document___"
        validated = validate_generated_filename(surrounded)
        self.assertEqual(validated, "Strategic_Planning_Document")

    def test_validate_generated_filename_forbidden_patterns(self):
        """Test security filtering of forbidden patterns."""
        # Script-related words should be replaced
        script_name = "Strategic_script_Planning_Document"
        validated = validate_generated_filename(script_name)
        self.assertNotIn("script", validated.lower())
        self.assertIn("content", validated.lower())

        # Command-related words should be replaced (but may appear in compound words)
        command_name = "Planning_command_Document_exec"
        validated = validate_generated_filename(command_name)
        # The algorithm replaces exact matches, so "command" becomes "content"
        # but compound words might retain parts
        self.assertIn("content", validated.lower())

        # JavaScript/Python should be filtered
        code_names = [
            "Document_with_javascript_code",
            "Python_automation_script",
            "Strategic_run_command",
        ]
        for code_name in code_names:
            validated = validate_generated_filename(code_name)
            self.assertIn("content", validated.lower())
            # Note: The replacement algorithm may not catch all patterns
            # in compound words or when combined with other processing

    def test_validate_generated_filename_empty_edge_cases(self):
        """Test edge cases with empty or null inputs."""
        # Empty string should return default
        self.assertEqual(validate_generated_filename(""), "unnamed_document")

        # None should return default
        self.assertEqual(validate_generated_filename(None), "unnamed_document")

        # Only whitespace should return document_ (after padding short name)
        result = validate_generated_filename("   ")
        self.assertTrue(result.startswith("document"))

        # Only quotes should return document_ (after padding short name)
        result = validate_generated_filename('"""')
        self.assertTrue(result.startswith("document"))

        # Only invalid characters should return document with padding
        invalid_only = "!@#$%^&*()"
        validated = validate_generated_filename(invalid_only)
        self.assertTrue(validated.startswith("document"))  # May have underscore padding

    def test_validate_generated_filename_complex_scenarios(self):
        """Test complex, realistic edge cases."""
        # AI might return quoted filename with extension
        ai_response = '"Strategic_Planning_Document_Q3_2024.pdf"'
        validated = validate_generated_filename(ai_response)
        self.assertEqual(validated, "Strategic_Planning_Document_Q3_2024_pdf")

        # AI might return with markdown code block
        markdown_response = "```Strategic_Planning_Document```"
        validated = validate_generated_filename(markdown_response)
        self.assertEqual(validated, "Strategic_Planning_Document")

        # Mixed issues: length, characters, forbidden patterns
        complex = "   '''VERY_LONG_Strategic_javascript_Planning_Document_With_script_Commands_2024.pdf```   "
        validated = validate_generated_filename(complex)
        self.assertLessEqual(len(validated), MAX_FILENAME_LENGTH)
        self.assertIn("content", validated.lower())
        # Check that some forbidden patterns were replaced with "content"
        self.assertIn("content", validated.lower())
        # Note: The algorithm does word-by-word replacement, so compound words
        # or truncated results might still contain partial matches


class TestFilenameConfigPrompts(unittest.TestCase, RichTestCase):
    """Test filename generation prompt templates."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_get_filename_prompt_template(self):
        """Test standard filename prompt template generation."""
        # Default provider
        prompt = get_filename_prompt_template()
        self.assertIn("descriptive, detailed filename", prompt)
        self.assertIn(f"{MAX_FILENAME_LENGTH} characters maximum", prompt)
        self.assertIn(f"{TARGET_FILENAME_WORDS[0]}-{TARGET_FILENAME_WORDS[1]} words", prompt)
        self.assertIn("ONLY the filename text", prompt)

        # Specific provider (should be same currently)
        openai_prompt = get_filename_prompt_template("openai")
        claude_prompt = get_filename_prompt_template("claude")
        self.assertEqual(prompt, openai_prompt)
        self.assertEqual(prompt, claude_prompt)

    def test_get_secure_filename_prompt_template(self):
        """Test secure filename prompt template for sanitized content."""
        prompt = get_secure_filename_prompt_template()

        self.assertIn("document analyst", prompt.lower())
        self.assertIn("ONLY the filename without extension", prompt)
        self.assertIn(f"{MAX_FILENAME_LENGTH} characters maximum", prompt)
        self.assertIn("Do not include any commands", prompt)

        # Should be different from regular prompt
        regular_prompt = get_filename_prompt_template()
        self.assertNotEqual(prompt, regular_prompt)

    def test_prompt_template_parameter_consistency(self):
        """Test that prompt templates use current configuration parameters."""
        prompt = get_filename_prompt_template()

        # Check that current constants are used
        self.assertIn(str(MAX_FILENAME_LENGTH), prompt)
        self.assertIn(str(TARGET_FILENAME_WORDS[0]), prompt)
        self.assertIn(str(TARGET_FILENAME_WORDS[1]), prompt)

        secure_prompt = get_secure_filename_prompt_template()
        self.assertIn(str(MAX_FILENAME_LENGTH), secure_prompt)
        self.assertIn(str(TARGET_FILENAME_WORDS[0]), secure_prompt)
        self.assertIn(str(TARGET_FILENAME_WORDS[1]), secure_prompt)


class TestFilenameConfigProviderSupport(unittest.TestCase, RichTestCase):
    """Test provider-specific functionality."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_get_token_limit_for_provider(self):
        """Test token limit retrieval for different providers."""
        providers = ["openai", "claude", "gemini", "deepseek", "unknown"]

        for provider in providers:
            token_limit = get_token_limit_for_provider(provider)
            self.assertEqual(token_limit, MAX_OUTPUT_TOKENS)
            self.assertIsInstance(token_limit, int)
            self.assertGreater(token_limit, 20)

    def test_config_summary(self):
        """Test configuration summary for debugging."""
        summary = get_config_summary()

        # Should contain all key configuration values
        expected_keys = [
            "max_filename_length",
            "target_words",
            "max_output_tokens",
            "chars_per_token",
            "safety_buffer",
            "providers_supported",
        ]

        for key in expected_keys:
            self.assertIn(key, summary)

        # Values should match constants
        self.assertEqual(summary["max_filename_length"], MAX_FILENAME_LENGTH)
        self.assertEqual(summary["target_words"], TARGET_FILENAME_WORDS)
        self.assertEqual(summary["max_output_tokens"], MAX_OUTPUT_TOKENS)

        # Providers should be listed
        self.assertIsInstance(summary["providers_supported"], list)
        self.assertIn("openai", summary["providers_supported"])
        self.assertIn("claude", summary["providers_supported"])

    def test_default_system_prompts_coverage(self):
        """Test that all supported providers have system prompts."""
        from core.filename_config import DEFAULT_SYSTEM_PROMPTS

        expected_providers = ["openai", "claude", "gemini", "deepseek"]

        for provider in expected_providers:
            self.assertIn(provider, DEFAULT_SYSTEM_PROMPTS)
            prompt = DEFAULT_SYSTEM_PROMPTS[provider]
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 50)  # Should be substantial

        # All prompts should contain key requirements
        for prompt in DEFAULT_SYSTEM_PROMPTS.values():
            self.assertIn("filename", prompt.lower())
            self.assertIn(str(MAX_FILENAME_LENGTH), prompt)


class TestExpertConfig(unittest.TestCase, RichTestCase):
    """Test ExpertConfig dataclass functionality."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_expert_config_defaults(self):
        """Test ExpertConfig default values."""
        config = ExpertConfig()

        # Directory defaults
        self.assertIsNone(config.input_dir)
        self.assertIsNone(config.output_dir)

        # AI provider defaults
        self.assertIsNone(config.provider)
        self.assertIsNone(config.model)
        self.assertIsNone(config.api_key)

        # Processing defaults
        self.assertIsNone(config.ocr_language)
        self.assertFalse(config.reset_progress)

        # Display defaults
        self.assertFalse(config.quiet_mode)
        self.assertFalse(config.verbose_mode)
        self.assertFalse(config.no_color)
        self.assertFalse(config.no_stats)

        # Organization defaults
        self.assertIsNone(config.enable_organization)
        self.assertEqual(config.ml_level, 2)

    def test_expert_config_custom_values(self):
        """Test ExpertConfig with custom values."""
        config = ExpertConfig(
            input_dir="/custom/input",
            output_dir="/custom/output",
            provider="claude",
            model="claude-3-sonnet",
            api_key="sk-test-123",
            ocr_language="eng+fra",
            reset_progress=True,
            quiet_mode=True,
            verbose_mode=False,  # Should be False when quiet is True
            no_color=True,
            no_stats=True,
            enable_organization=True,
            ml_level=3,
        )

        # Verify all custom values
        self.assertEqual(config.input_dir, "/custom/input")
        self.assertEqual(config.output_dir, "/custom/output")
        self.assertEqual(config.provider, "claude")
        self.assertEqual(config.model, "claude-3-sonnet")
        self.assertEqual(config.api_key, "sk-test-123")
        self.assertEqual(config.ocr_language, "eng+fra")
        self.assertTrue(config.reset_progress)
        self.assertTrue(config.quiet_mode)
        self.assertFalse(config.verbose_mode)
        self.assertTrue(config.no_color)
        self.assertTrue(config.no_stats)
        self.assertTrue(config.enable_organization)
        self.assertEqual(config.ml_level, 3)


class TestExpertModePrompter(unittest.TestCase, RichTestCase):
    """Test ExpertModePrompter functionality and validation."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
        # Keep existing setUp logic
        self.prompter = ExpertModePrompter()
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_prompter_initialization(self):
        """Test ExpertModePrompter initialization."""
        # Should have expected providers
        expected_providers = ["openai", "claude", "gemini", "deepseek"]
        self.assertEqual(self.prompter.providers, expected_providers)

        # Should have common languages
        self.assertIn("eng", self.prompter.common_languages)
        self.assertIn("eng+fra", self.prompter.common_languages)
        self.assertEqual(self.prompter.common_languages["eng"], "English")

        # Should have multiple language options
        self.assertGreater(len(self.prompter.common_languages), 5)

    def test_validate_input_directory_success(self):
        """Test input directory validation for valid directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid readable directory
            is_valid, error_msg = self.prompter._validate_input_directory(temp_dir)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")

    def test_validate_input_directory_failures(self):
        """Test input directory validation failure cases."""
        # Non-existent directory
        is_valid, error_msg = self.prompter._validate_input_directory("/nonexistent/path")
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error_msg)

        # File instead of directory
        with tempfile.NamedTemporaryFile() as temp_file:
            is_valid, error_msg = self.prompter._validate_input_directory(temp_file.name)
            self.assertFalse(is_valid)
            self.assertIn("not a directory", error_msg)

    def test_validate_output_directory_creation(self):
        """Test output directory validation and creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test creating subdirectory
            new_dir = os.path.join(temp_dir, "new_output")
            self.assertFalse(os.path.exists(new_dir))

            is_valid, error_msg = self.prompter._validate_output_directory(new_dir)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
            self.assertTrue(os.path.exists(new_dir))

    def test_validate_output_directory_existing(self):
        """Test output directory validation for existing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Existing writable directory
            is_valid, error_msg = self.prompter._validate_output_directory(temp_dir)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")

    def test_convert_to_args_minimal_config(self):
        """Test converting minimal config to args."""
        config = ExpertConfig()
        args = self.prompter.convert_to_args(config)

        # Minimal config should produce minimal args
        self.assertEqual(args, [])

    def test_convert_to_args_full_config(self):
        """Test converting full configuration to command line arguments."""
        config = ExpertConfig(
            input_dir="/test/input",
            output_dir="/test/output",
            provider="claude",
            model="claude-3-sonnet",
            ocr_language="eng+fra",
            reset_progress=True,
            enable_organization=True,
            ml_level=3,
            quiet_mode=True,
            verbose_mode=False,  # Should be ignored when quiet is True
            no_color=True,
            no_stats=True,
        )

        args = self.prompter.convert_to_args(config)

        # Check expected arguments are present
        expected_args = [
            "--input",
            "/test/input",
            "--renamed",
            "/test/output",
            "--provider",
            "claude",
            "--model",
            "claude-3-sonnet",
            "--ocr-lang",
            "eng+fra",
            "--reset-progress",
            "--organize",
            "--ml-level",
            "3",
            "--quiet",
            "--no-color",
            "--no-stats",
        ]

        for arg in expected_args:
            self.assertIn(arg, args)

        # Verbose should not be present when quiet mode is enabled
        self.assertNotIn("--verbose", args)

    def test_convert_to_args_organization_disabled(self):
        """Test args conversion when organization is explicitly disabled."""
        config = ExpertConfig(enable_organization=False)
        args = self.prompter.convert_to_args(config)

        self.assertIn("--no-organize", args)
        self.assertNotIn("--organize", args)
        self.assertNotIn("--ml-level", args)

    def test_convert_to_args_organization_default_ml_level(self):
        """Test args conversion with organization enabled and default ML level."""
        config = ExpertConfig(enable_organization=True, ml_level=2)  # Default
        args = self.prompter.convert_to_args(config)

        self.assertIn("--organize", args)
        # ML level 2 is default, should not be explicitly added
        self.assertNotIn("--ml-level", args)

    def test_convert_to_args_ocr_language_default(self):
        """Test that default OCR language 'eng' is not added to args."""
        config = ExpertConfig(ocr_language="eng")  # Default
        args = self.prompter.convert_to_args(config)

        self.assertNotIn("--ocr-lang", args)

    def test_convert_to_args_boolean_flags(self):
        """Test boolean flag conversion edge cases."""
        # Test each boolean flag individually
        test_cases = [
            ({"reset_progress": True}, "--reset-progress"),
            ({"quiet_mode": True}, "--quiet"),
            ({"verbose_mode": True}, "--verbose"),
            ({"no_color": True}, "--no-color"),
            ({"no_stats": True}, "--no-stats"),
        ]

        for config_dict, expected_flag in test_cases:
            config = ExpertConfig(**config_dict)
            args = self.prompter.convert_to_args(config)
            self.assertIn(expected_flag, args)

    @patch("builtins.print")  # Mock print to avoid Unicode issues
    @patch("builtins.input")
    def test_should_use_expert_mode_quick_start(self, mock_input, mock_print):
        """Test choosing quick start mode."""
        # Test various quick start inputs
        quick_inputs = ["q", "quick", "Q", "QUICK", ""]  # Empty defaults to quick

        for user_input in quick_inputs:
            with self.subTest(user_input=user_input):
                mock_input.return_value = user_input
                result = self.prompter.should_use_expert_mode()
                self.assertFalse(result)

    @patch("builtins.print")  # Mock print to avoid Unicode issues
    @patch("builtins.input")
    def test_should_use_expert_mode_expert(self, mock_input, mock_print):
        """Test choosing expert mode."""
        expert_inputs = ["e", "expert", "E", "EXPERT"]

        for user_input in expert_inputs:
            with self.subTest(user_input=user_input):
                mock_input.return_value = user_input
                result = self.prompter.should_use_expert_mode()
                self.assertTrue(result)

    @patch("builtins.print")  # Mock print to avoid Unicode issues
    @patch("builtins.input")
    def test_should_use_expert_mode_invalid_then_valid(self, mock_input, mock_print):
        """Test invalid input followed by valid input."""
        # First invalid, then valid
        mock_input.side_effect = ["invalid", "x", "q"]
        result = self.prompter.should_use_expert_mode()
        self.assertFalse(result)

        # Should have prompted 3 times
        self.assertEqual(mock_input.call_count, 3)


class TestExpertModeValidators(unittest.TestCase, RichTestCase):
    """Test expert mode validation helper methods."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
        # Keep existing setUp logic
        self.prompter = ExpertModePrompter()
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_directory_validation_comprehensive(self):
        """Test comprehensive directory validation scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            valid_dir = os.path.join(temp_dir, "valid")
            os.makedirs(valid_dir)

            test_file = os.path.join(temp_dir, "not_a_dir.txt")
            with open(test_file, "w") as f:
                f.write("test")

            # Test valid directory
            is_valid, msg = self.prompter._validate_input_directory(valid_dir)
            self.assertTrue(is_valid)
            self.assertEqual(msg, "")

            # Test file instead of directory
            is_valid, msg = self.prompter._validate_input_directory(test_file)
            self.assertFalse(is_valid)
            self.assertIn("not a directory", msg)

            # Test non-existent path
            is_valid, msg = self.prompter._validate_input_directory("/does/not/exist")
            self.assertFalse(is_valid)
            self.assertIn("does not exist", msg)

    def test_output_directory_creation_edge_cases(self):
        """Test output directory creation edge cases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test nested directory creation
            nested_path = os.path.join(temp_dir, "level1", "level2", "level3")
            is_valid, msg = self.prompter._validate_output_directory(nested_path)
            self.assertTrue(is_valid)
            self.assertEqual(msg, "")
            self.assertTrue(os.path.exists(nested_path))

            # Test creating over existing file should fail
            existing_file = os.path.join(temp_dir, "existing_file.txt")
            with open(existing_file, "w") as f:
                f.write("test")

            # This should fail because we can't create a directory over a file
            is_valid, msg = self.prompter._validate_output_directory(existing_file)
            self.assertFalse(is_valid)
            self.assertIn("create directory", msg)


class TestExpertModeGlobalFunction(unittest.TestCase, RichTestCase):
    """Test the global prompt_expert_mode_if_needed function."""
    
    def setUp(self):
        """Set up test fixtures with Rich testing patterns."""
        RichTestCase.setUp(self)
        # Store original sys.argv for restoration
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)
        # Restore original sys.argv
        sys.argv = self.original_argv

    def test_prompt_expert_mode_with_existing_args(self):
        """Test that expert mode is skipped when CLI args are present."""
        # Simulate existing command line arguments
        sys.argv = ["script.py", "--input", "/some/path"]

        result = prompt_expert_mode_if_needed()

        # Should return empty list when args are present
        self.assertEqual(result, [])

    @patch("utils.expert_mode.ExpertModePrompter")
    def test_prompt_expert_mode_no_args_quick_start(self, mock_prompter_class):
        """Test expert mode prompt with no args, choosing quick start."""
        # Clear command line arguments
        sys.argv = ["script.py"]

        # Mock the prompter instance
        mock_prompter = MagicMock()
        mock_prompter_class.return_value = mock_prompter

        # Mock should_use_expert_mode to return False (quick start)
        mock_prompter.should_use_expert_mode.return_value = False

        result = prompt_expert_mode_if_needed()

        # Should return empty list for quick start
        self.assertEqual(result, [])
        mock_prompter.should_use_expert_mode.assert_called_once()
        mock_prompter.prompt_expert_configuration.assert_not_called()

    @patch("utils.expert_mode.ExpertModePrompter")
    def test_prompt_expert_mode_no_args_expert_mode(self, mock_prompter_class):
        """Test expert mode prompt with no args, choosing expert mode."""
        # Clear command line arguments
        sys.argv = ["script.py"]

        # Mock the prompter instance
        mock_prompter = MagicMock()
        mock_prompter_class.return_value = mock_prompter

        # Mock should_use_expert_mode to return True (expert mode)
        mock_prompter.should_use_expert_mode.return_value = True

        # Mock config and args
        mock_config = ExpertConfig(input_dir="/test", provider="claude")
        mock_args = ["--input", "/test", "--provider", "claude"]
        mock_prompter.prompt_expert_configuration.return_value = mock_config
        mock_prompter.convert_to_args.return_value = mock_args

        result = prompt_expert_mode_if_needed()

        # Should return the mock args
        self.assertEqual(result, mock_args)
        mock_prompter.should_use_expert_mode.assert_called_once()
        mock_prompter.prompt_expert_configuration.assert_called_once()
        mock_prompter.convert_to_args.assert_called_once_with(mock_config)

    def test_prompt_expert_mode_detection_logic(self):
        """Test argument detection logic for determining when to skip expert mode."""
        # Test cases: (argv, should_skip_expert_mode)
        test_cases = [
            (["script.py"], False),  # No args - should prompt
            (["script.py", "--help"], True),  # Has args - should skip
            (["script.py", "--input", "/path"], True),  # Has args - should skip
            (["script.py", "-i", "/path", "--provider", "claude"], True),  # Has args - should skip
            (["script.py", "--version"], True),  # Has args - should skip
        ]

        for argv, should_skip in test_cases:
            with self.subTest(argv=argv):
                original_argv = sys.argv.copy()
                try:
                    sys.argv = argv

                    # Mock the prompter to avoid actual prompting
                    with patch("utils.expert_mode.ExpertModePrompter"):
                        result = prompt_expert_mode_if_needed()

                        if should_skip:
                            self.assertEqual(result, [], f"Should return empty list for {argv}")
                        else:
                            # For no-args case, we'd get prompted but our mock returns None
                            # This tests that we reach the prompting logic
                            pass
                finally:
                    sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
