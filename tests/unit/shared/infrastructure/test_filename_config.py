#!/usr/bin/env python3
"""
Tests for Filename Configuration in Shared Infrastructure

Tests the filename configuration functionality without domain dependencies.
"""

import unittest
import os
import sys

# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

# Import from shared infrastructure (correct layer)
from shared.infrastructure.filename_config import (
    DEFAULT_SYSTEM_PROMPTS,
    get_secure_filename_prompt_template,
    get_token_limit_for_provider,
    validate_generated_filename,
    MAX_FILENAME_LENGTH,
    MIN_FILENAME_LENGTH,
)

class TestFilenameValidation(unittest.TestCase):
    """Test filename validation and sanitization."""

    def test_validate_generated_filename_normal(self):
        """Test validation of normal filenames."""
        valid_filenames = [
            "Financial_Report_Q1_2024",
            "Meeting_Notes_January_15",
            "Invoice_123456_CompanyName"
        ]

        for filename in valid_filenames:
            result = validate_generated_filename(filename)
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)

    def test_validate_generated_filename_length_constraints(self):
        """Test filename length constraint validation."""
        # Test very long filename
        long_filename = "A" * 300  # Exceeds MAX_FILENAME_LENGTH
        result = validate_generated_filename(long_filename)

        self.assertLessEqual(len(result), MAX_FILENAME_LENGTH)

        # Test very short filename
        short_filename = "AB"  # Below MIN_FILENAME_LENGTH
        result = validate_generated_filename(short_filename)

        self.assertGreaterEqual(len(result), MIN_FILENAME_LENGTH)

    def test_validate_generated_filename_forbidden_patterns(self):
        """Test removal of forbidden patterns."""
        problematic_filenames = [
            "file<name>with<forbidden>",
            'file"with"quotes',
            "file|with|pipes",
            "file?with?questions"
        ]

        for filename in problematic_filenames:
            result = validate_generated_filename(filename)

            # Should not contain forbidden characters
            self.assertNotIn("<", result)
            self.assertNotIn(">", result)
            self.assertNotIn('"', result)
            self.assertNotIn("|", result)
            self.assertNotIn("?", result)

class TestProviderConfiguration(unittest.TestCase):
    """Test provider-specific configuration."""

    def test_default_system_prompts_coverage(self):
        """Test system prompts are defined for all providers."""
        expected_providers = ["openai", "claude", "gemini", "deepseek", "local", "default"]

        for provider in expected_providers:
            self.assertIn(provider, DEFAULT_SYSTEM_PROMPTS)
            prompt = DEFAULT_SYSTEM_PROMPTS[provider]
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 0)

    def test_get_token_limit_for_provider(self):
        """Test token limits are defined for providers."""
        providers = ["openai", "claude", "gemini", "deepseek", "local"]

        for provider in providers:
            limit = get_token_limit_for_provider(provider)
            self.assertIsInstance(limit, int)
            self.assertGreater(limit, 0)
            self.assertLessEqual(limit, 1000)  # Reasonable upper bound

    def test_get_secure_filename_prompt_template(self):
        """Test secure prompt templates."""
        providers = ["openai", "claude", "gemini"]

        for provider in providers:
            template = get_secure_filename_prompt_template(provider)
            self.assertIsInstance(template, str)
            self.assertGreater(len(template), 0)
            # Should contain security guidance
            self.assertIn("filename", template.lower())

class TestFilenameConfigConstants(unittest.TestCase):
    """Test filename configuration constants."""

    def test_constants_consistency(self):
        """Test that constants are consistent and reasonable."""
        # Length constraints should be sensible
        self.assertLess(MIN_FILENAME_LENGTH, MAX_FILENAME_LENGTH)
        self.assertGreater(MIN_FILENAME_LENGTH, 0)
        self.assertLess(MAX_FILENAME_LENGTH, 300)  # Filesystem limits

        # Constants should be integers
        self.assertIsInstance(MAX_FILENAME_LENGTH, int)
        self.assertIsInstance(MIN_FILENAME_LENGTH, int)

    def test_system_prompts_structure(self):
        """Test system prompts dictionary structure."""
        self.assertIsInstance(DEFAULT_SYSTEM_PROMPTS, dict)
        self.assertGreater(len(DEFAULT_SYSTEM_PROMPTS), 0)

        # Should have default fallback
        self.assertIn("default", DEFAULT_SYSTEM_PROMPTS)

if __name__ == "__main__":
    unittest.main()
