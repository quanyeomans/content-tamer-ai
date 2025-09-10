"""
Tests for Provider Service

Tests unified AI provider management and factory functionality.
"""

import os
import unittest
from unittest.mock import MagicMock, Mock, patch

from src.domains.ai_integration.provider_service import (
    ProviderCapabilities,
    ProviderConfiguration,
    ProviderService,
)


class TestProviderConfiguration(unittest.TestCase):
    """Test provider configuration constants."""

    def test_ai_providers_structure(self):
        """Test AI_PROVIDERS has correct structure."""
        providers = ProviderConfiguration.AI_PROVIDERS

        self.assertIsInstance(providers, dict)
        self.assertIn("openai", providers)
        self.assertIn("claude", providers)
        self.assertIn("gemini", providers)
        self.assertIn("local", providers)

        # Each provider should have a list of models
        for provider, models in providers.items():
            self.assertIsInstance(models, list)
            self.assertGreater(len(models), 0)

    def test_default_models_structure(self):
        """Test DEFAULT_MODELS has correct structure."""
        defaults = ProviderConfiguration.DEFAULT_MODELS

        self.assertIsInstance(defaults, dict)

        # Each provider in AI_PROVIDERS should have a default
        for provider in ProviderConfiguration.AI_PROVIDERS.keys():
            self.assertIn(provider, defaults)

            # Default model should be in the provider's model list
            default_model = defaults[provider]
            self.assertIn(default_model, ProviderConfiguration.AI_PROVIDERS[provider])


class TestProviderCapabilities(unittest.TestCase):
    """Test provider capability detection."""

    @patch("src.domains.ai_integration.provider_service.get_dependency_manager")
    def test_detect_available_providers(self, mock_get_dep_manager):
        """Test provider availability detection."""
        # Mock dependency manager
        mock_dep_manager = Mock()
        mock_dep_manager.find_dependency.return_value = "/usr/bin/ollama"
        mock_get_dep_manager.return_value = mock_dep_manager

        with patch("builtins.__import__") as mock_import:
            # Mock successful imports for all providers
            mock_import.return_value = Mock()

            capabilities = ProviderCapabilities.detect_available_providers()

            self.assertIsInstance(capabilities, dict)
            self.assertIn("openai", capabilities)
            self.assertIn("claude", capabilities)
            self.assertIn("gemini", capabilities)
            self.assertIn("deepseek", capabilities)
            self.assertIn("local", capabilities)

    def test_validate_provider_model_combination_valid(self):
        """Test validation of valid provider/model combinations."""
        # Test valid combinations
        valid = ProviderCapabilities.validate_provider_model_combination("openai", "gpt-4o")
        self.assertTrue(valid)

        valid = ProviderCapabilities.validate_provider_model_combination(
            "claude", "claude-3.5-sonnet"
        )
        self.assertTrue(valid)

    def test_validate_provider_model_combination_invalid(self):
        """Test validation rejects invalid combinations."""
        # Test invalid provider
        valid = ProviderCapabilities.validate_provider_model_combination(
            "invalid_provider", "model"
        )
        self.assertFalse(valid)

        # Test invalid model for valid provider
        valid = ProviderCapabilities.validate_provider_model_combination("openai", "invalid_model")
        self.assertFalse(valid)

    def test_get_provider_requirements(self):
        """Test getting provider requirements."""
        # Test OpenAI requirements
        openai_req = ProviderCapabilities.get_provider_requirements("openai")
        self.assertIsInstance(openai_req, dict)
        self.assertTrue(openai_req.get("api_key_required", False))
        self.assertEqual(openai_req.get("environment_var"), "OPENAI_API_KEY")

        # Test local requirements (no API key)
        local_req = ProviderCapabilities.get_provider_requirements("local")
        self.assertFalse(local_req.get("api_key_required", True))
        self.assertIsNone(local_req.get("environment_var"))

        # Test unknown provider
        unknown_req = ProviderCapabilities.get_provider_requirements("unknown")
        self.assertEqual(unknown_req, {})


class TestProviderService(unittest.TestCase):
    """Test provider service functionality."""

    def setUp(self):
        """Set up provider service."""
        self.service = ProviderService()

    @patch.object(ProviderCapabilities, "detect_available_providers")
    def test_get_available_providers(self, mock_detect):
        """Test getting available providers."""
        mock_detect.return_value = {"openai": True, "claude": True, "gemini": False, "local": False}

        # Clear cache to force re-detection
        self.service._capabilities_cache = None

        available = self.service.get_available_providers()

        self.assertIn("openai", available)
        self.assertIn("claude", available)
        self.assertNotIn("gemini", available)
        self.assertNotIn("local", available)

    def test_get_supported_models(self):
        """Test getting supported models for providers."""
        # Test valid provider
        openai_models = self.service.get_supported_models("openai")
        self.assertIsInstance(openai_models, list)
        self.assertGreater(len(openai_models), 0)

        # Test invalid provider
        invalid_models = self.service.get_supported_models("invalid")
        self.assertEqual(invalid_models, [])

    def test_get_default_model(self):
        """Test getting default model for providers."""
        # Test valid providers
        for provider in ProviderConfiguration.AI_PROVIDERS.keys():
            default_model = self.service.get_default_model(provider)
            self.assertIsInstance(default_model, str)
            self.assertIn(default_model, ProviderConfiguration.AI_PROVIDERS[provider])

        # Test invalid provider
        with self.assertRaises(ValueError):
            self.service.get_default_model("invalid_provider")

    @patch.object(ProviderCapabilities, "detect_available_providers")
    def test_create_provider_unavailable(self, mock_detect):
        """Test creating provider when not available."""
        mock_detect.return_value = {"openai": False}

        # Clear cache
        self.service._capabilities_cache = None

        with self.assertRaises(RuntimeError) as cm:
            self.service.create_provider("openai", "gpt-4o", "test-key")

        self.assertIn("not available", str(cm.exception))

    def test_create_provider_invalid_combination(self):
        """Test creating provider with invalid model."""
        with self.assertRaises(ValueError) as cm:
            self.service.create_provider("openai", "invalid_model", "test-key")

        self.assertIn("Invalid provider/model combination", str(cm.exception))

    def test_get_provider_info(self):
        """Test getting comprehensive provider information."""
        # Test valid provider
        info = self.service.get_provider_info("openai")

        self.assertIsInstance(info, dict)
        self.assertEqual(info["name"], "openai")
        self.assertIn("available", info)
        self.assertIn("models", info)
        self.assertIn("default_model", info)
        self.assertIn("requirements", info)
        self.assertIn("capabilities", info)

        # Test invalid provider
        with self.assertRaises(ValueError):
            self.service.get_provider_info("invalid_provider")

    def test_provider_capabilities(self):
        """Test provider capability detection."""
        # Test OpenAI capabilities
        capabilities = self.service._get_provider_capabilities("openai")

        self.assertIsInstance(capabilities, dict)
        self.assertIn("text_generation", capabilities)
        self.assertIn("vision", capabilities)
        self.assertIn("function_calling", capabilities)
        self.assertTrue(capabilities["text_generation"])
        self.assertTrue(capabilities["vision"])  # OpenAI supports vision

    def test_clear_cache(self):
        """Test cache clearing."""
        # Set some cache data
        self.service._provider_cache["test"] = Mock()
        self.service._capabilities_cache = {"test": True}

        # Clear cache
        self.service.clear_cache()

        self.assertEqual(len(self.service._provider_cache), 0)
        self.assertIsNone(self.service._capabilities_cache)

    def test_provider_statistics(self):
        """Test getting provider statistics."""
        stats = self.service.get_provider_statistics()

        self.assertIsInstance(stats, dict)
        self.assertIn("total_providers", stats)
        self.assertIn("available_providers", stats)
        self.assertIn("availability_rate", stats)
        self.assertIn("cached_instances", stats)
        self.assertIn("provider_status", stats)


if __name__ == "__main__":
    unittest.main()
