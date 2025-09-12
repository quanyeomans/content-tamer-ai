"""
Unit tests for ModelNameMapper.

Tests the bidirectional mapping between internal and Ollama model name formats.
"""

import unittest

from src.shared.infrastructure.model_name_mapper import ModelNameMapper


class TestModelNameMapper(unittest.TestCase):
    """Test model name mapping functionality."""

    def test_to_ollama_format_known_models(self):
        """Test conversion of known models to Ollama format."""
        test_cases = [
            ("llama3.1-8b", "llama3.1:8b"),
            ("llama3.2-3b", "llama3.2:3b"),
            ("mistral-7b", "mistral:7b"),
            ("gemma-2-2b", "gemma2:2b"),
            ("gemma2-2b", "gemma2:2b"),  # Alternative format
        ]
        
        for internal, expected_ollama in test_cases:
            with self.subTest(internal=internal):
                result = ModelNameMapper.to_ollama_format(internal)
                self.assertEqual(result, expected_ollama)

    def test_to_ollama_format_unknown_models(self):
        """Test automatic conversion for unknown models."""
        test_cases = [
            ("unknown-2b", "unknown:2b"),  # Auto-converts hyphen to colon for size
            ("llama4-10b", "llama4:10b"),  # Auto-converts
            ("custom:model", "custom:model"),  # Already in Ollama format
            ("no-number", "no-number"),  # No conversion if no number suffix
            ("model-latest", "model:latest"),  # Converts 'latest' tag
        ]
        
        for model, expected in test_cases:
            with self.subTest(model=model):
                result = ModelNameMapper.to_ollama_format(model)
                self.assertEqual(result, expected)

    def test_to_internal_format_known_models(self):
        """Test conversion from Ollama format to internal format."""
        test_cases = [
            ("llama3.1:8b", "llama3.1-8b"),
            ("llama3.2:3b", "llama3.2-3b"),
            ("mistral:7b", "mistral-7b"),
            ("gemma2:2b", "gemma2-2b"),  # Note: maps to gemma2-2b not gemma-2-2b
        ]
        
        for ollama, expected_internal in test_cases:
            with self.subTest(ollama=ollama):
                result = ModelNameMapper.to_internal_format(ollama)
                self.assertEqual(result, expected_internal)

    def test_to_internal_format_unknown_models(self):
        """Test automatic conversion for unknown Ollama models."""
        test_cases = [
            ("unknown:model", "unknown-model"),  # Auto-converts colon to hyphen
            ("llama4:10b", "llama4-10b"),  # Auto-converts
            ("custom-model", "custom-model"),  # Already in internal format
        ]
        
        for model, expected in test_cases:
            with self.subTest(model=model):
                result = ModelNameMapper.to_internal_format(model)
                self.assertEqual(result, expected)

    def test_bidirectional_mapping_consistency(self):
        """Test that mappings are consistent in both directions."""
        # Note: gemma-2-2b -> gemma2:2b -> gemma2-2b (not back to gemma-2-2b)
        # This is expected behavior as gemma2-2b is the canonical internal format
        test_cases = [
            ("llama3.1-8b", "llama3.1:8b", "llama3.1-8b"),
            ("llama3.2-3b", "llama3.2:3b", "llama3.2-3b"),
            ("mistral-7b", "mistral:7b", "mistral-7b"),
            ("gemma-2-2b", "gemma2:2b", "gemma2-2b"),  # Different but expected
            ("gemma2-2b", "gemma2:2b", "gemma2-2b"),  # Canonical form
        ]
        
        for internal, expected_ollama, expected_back in test_cases:
            with self.subTest(internal=internal):
                ollama = ModelNameMapper.to_ollama_format(internal)
                self.assertEqual(ollama, expected_ollama)
                back_to_internal = ModelNameMapper.to_internal_format(ollama)
                self.assertEqual(back_to_internal, expected_back)

    def test_none_input_handling(self):
        """Test that None input is handled gracefully."""
        self.assertIsNone(ModelNameMapper.to_ollama_format(None))
        self.assertIsNone(ModelNameMapper.to_internal_format(None))

    def test_empty_string_handling(self):
        """Test that empty strings are handled properly."""
        self.assertEqual(ModelNameMapper.to_ollama_format(""), "")
        self.assertEqual(ModelNameMapper.to_internal_format(""), "")

    def test_case_sensitivity(self):
        """Test that model names are case-sensitive but auto-conversion still works."""
        # Unknown models with uppercase still get auto-converted
        self.assertEqual(ModelNameMapper.to_ollama_format("LLAMA3.1-8B"), "LLAMA3.1:8B")
        self.assertEqual(ModelNameMapper.to_internal_format("LLAMA3.1:8B"), "LLAMA3.1-8B")


if __name__ == "__main__":
    unittest.main()