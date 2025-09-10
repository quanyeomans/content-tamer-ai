"""
Tests for Application Kernel

Tests the main application orchestration and domain service coordination.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from core.application_container import ApplicationContainer
from orchestration.application_kernel import ApplicationKernel


class TestApplicationKernel(unittest.TestCase):
    """Test application kernel functionality."""

    def setUp(self):
        """Set up test application kernel."""
        self.container = ApplicationContainer(test_mode=True)
        self.kernel = ApplicationKernel(self.container)

    def test_initialization(self):
        """Test kernel initializes correctly."""
        self.assertIsInstance(self.kernel, ApplicationKernel)
        self.assertEqual(self.kernel.container, self.container)
        self.assertIsNone(self.kernel._content_service)  # Lazy loaded
        self.assertIsNone(self.kernel._ai_service)  # Lazy loaded

    def test_lazy_service_creation(self):
        """Test services are created lazily."""
        # Mock the container methods to avoid import issues
        with patch.object(self.container, "create_content_service") as mock_create_content:
            mock_content_service = Mock()
            mock_create_content.return_value = mock_content_service

            # Access content service
            content_service = self.kernel.content_service

            # Should have called container method
            mock_create_content.assert_called_once()
            self.assertEqual(content_service, mock_content_service)

            # Second access should return cached service
            content_service2 = self.kernel.content_service
            self.assertEqual(content_service2, mock_content_service)
            # Container method should only be called once
            self.assertEqual(mock_create_content.call_count, 1)

    @patch("orchestration.application_kernel.os.walk")
    def test_discover_documents(self, mock_walk):
        """Test document discovery in input directory."""
        # Mock os.walk to return test files
        mock_walk.return_value = [
            ("/test/input", [], ["test.pdf", "image.png", "unsupported.txt", "doc.jpg"])
        ]

        documents = self.kernel._discover_documents("/test/input")

        # Should include supported file types only
        expected_files = [
            os.path.join("/test/input", "test.pdf"), 
            os.path.join("/test/input", "image.png"), 
            os.path.join("/test/input", "doc.jpg")
        ]

        self.assertEqual(len(documents), 3)
        for expected in expected_files:
            self.assertIn(expected, documents)

        # Should not include unsupported .txt file
        self.assertNotIn(os.path.join("/test/input", "unsupported.txt"), documents)

    def test_discover_documents_empty_directory(self):
        """Test document discovery in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            documents = self.kernel._discover_documents(temp_dir)
            self.assertEqual(len(documents), 0)

    def test_validate_processing_config_invalid_input(self):
        """Test validation rejects invalid input directory."""
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration

        config = ProcessingConfiguration(
            input_dir="/nonexistent/directory", output_dir="/tmp/test", provider="openai"
        )

        errors = self.kernel._validate_processing_config(config)

        self.assertGreater(len(errors), 0)
        self.assertTrue(any("does not exist" in error for error in errors))

    def test_validate_processing_config_valid(self):
        """Test validation passes for valid configuration."""
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration

        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:

            config = ProcessingConfiguration(
                input_dir=input_dir, output_dir=output_dir, provider="openai", api_key="test-key"
            )

            # Mock AI service validation
            mock_ai_service = Mock()
            mock_ai_service.validate_provider_setup.return_value = {
                "available": True,
                "api_key_valid": True,
            }
            self.kernel._ai_service = mock_ai_service

            errors = self.kernel._validate_processing_config(config)

            # Should have no errors for valid config
            self.assertEqual(len(errors), 0)

    def test_get_ai_providers_with_service(self):
        """Test getting AI providers when AI service is available."""
        mock_ai_service = Mock()
        mock_ai_service.provider_service.get_available_providers.return_value = ["openai", "claude"]

        self.kernel._ai_service = mock_ai_service
        providers = self.kernel.get_ai_providers()

        self.assertEqual(providers, ["openai", "claude"])
        mock_ai_service.provider_service.get_available_providers.assert_called_once()

    def test_get_ai_providers_fallback(self):
        """Test getting AI providers when AI service not available."""
        self.kernel._ai_service = None
        providers = self.kernel.get_ai_providers()

        # Should return fallback list
        self.assertIsInstance(providers, list)
        self.assertIn("openai", providers)
        self.assertIn("claude", providers)
        self.assertIn("gemini", providers)

    def test_get_provider_models_with_service(self):
        """Test getting provider models when AI service available."""
        mock_ai_service = Mock()
        mock_ai_service.provider_service.get_supported_models.return_value = [
            "gpt-4o",
            "gpt-4o-mini",
        ]

        self.kernel._ai_service = mock_ai_service
        models = self.kernel.get_provider_models("openai")

        self.assertEqual(models, ["gpt-4o", "gpt-4o-mini"])
        mock_ai_service.provider_service.get_supported_models.assert_called_once_with("openai")

    def test_get_provider_models_fallback(self):
        """Test getting provider models when AI service not available."""
        self.kernel._ai_service = None
        models = self.kernel.get_provider_models("openai")

        # Should return fallback list
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)

    def test_validate_provider_api_key_with_service(self):
        """Test API key validation when AI service available."""
        mock_ai_service = Mock()
        mock_ai_service.provider_service.validate_api_key.return_value = True

        self.kernel._ai_service = mock_ai_service
        valid = self.kernel.validate_provider_api_key("openai", "test-key")

        self.assertTrue(valid)
        mock_ai_service.provider_service.validate_api_key.assert_called_once_with(
            "openai", "test-key"
        )

    def test_validate_provider_api_key_fallback(self):
        """Test API key validation fallback when AI service not available."""
        # Mock the container to return None for ai service creation
        with patch.object(self.container, "create_ai_integration_service", return_value=None):
            self.kernel._ai_service = None
            
            # Valid key
            valid = self.kernel.validate_provider_api_key("openai", "test-key")
            self.assertTrue(valid)

            # Empty key
            valid = self.kernel.validate_provider_api_key("openai", "")
            self.assertFalse(valid)

            # None key
            valid = self.kernel.validate_provider_api_key("openai", None)
            self.assertFalse(valid)

    def test_get_system_capabilities(self):
        """Test getting system capabilities."""
        capabilities = self.kernel.get_system_capabilities()

        self.assertIsInstance(capabilities, dict)
        self.assertIn("domain_services", capabilities)

        domain_services = capabilities["domain_services"]
        self.assertIn("content", domain_services)
        self.assertIn("ai_integration", domain_services)
        self.assertIn("organization", domain_services)

    def test_health_check_basic(self):
        """Test basic health check functionality."""
        health = self.kernel.health_check()

        self.assertIsInstance(health, dict)
        self.assertIn("healthy", health)
        self.assertIn("timestamp", health)
        self.assertIn("issues", health)
        self.assertIn("warnings", health)
        self.assertIsInstance(health["healthy"], bool)
        self.assertIsInstance(health["issues"], list)
        self.assertIsInstance(health["warnings"], list)

    def test_get_progress_status(self):
        """Test getting progress status."""
        status = self.kernel.get_progress_status()

        self.assertIsInstance(status, dict)
        self.assertIn("status", status)
        self.assertIn("services_available", status)

        services_available = status["services_available"]
        self.assertIn("content", services_available)
        self.assertIn("ai_integration", services_available)
        self.assertIn("organization", services_available)


if __name__ == "__main__":
    unittest.main()
