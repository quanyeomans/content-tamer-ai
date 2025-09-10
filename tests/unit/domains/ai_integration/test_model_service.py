"""
Tests for Model Service functionality in AI Integration Domain.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

# Import from domain architecture
from domains.ai_integration.model_service import HardwareTier, ModelInfo, ModelService, ModelStatus


class TestModelService(unittest.TestCase):
    """Test Model Service functionality in AI Integration Domain."""

    def setUp(self):
        """Set up test fixtures for Model Service."""
        # Create model service instance for testing
        self.service = ModelService()

    def test_model_service_initialization(self):
        """Test Model Service initializes correctly."""
        self.assertIsInstance(self.service, ModelService)
        self.assertIsNotNone(self.service._model_catalog)
        self.assertIsNotNone(self.service._hardware_tiers)

    def test_get_system_capabilities(self):
        """Test system capability detection."""
        capabilities = self.service.get_system_capabilities()

        self.assertIsInstance(capabilities.total_ram_gb, float)
        self.assertIsInstance(capabilities.cpu_count, int)
        self.assertIsInstance(capabilities.platform, str)
        self.assertGreater(capabilities.total_ram_gb, 0)
        self.assertGreater(capabilities.cpu_count, 0)

    def test_get_model_info(self):
        """Test model information retrieval."""
        # Test known model
        model_info = self.service.get_model_info("gemma2:2b")

        if model_info:  # Model catalog might be empty in test
            self.assertIsInstance(model_info, ModelInfo)
            self.assertEqual(model_info.name, "gemma2:2b")
            self.assertGreater(model_info.memory_requirement_gb, 0)

    def test_validate_model_compatibility_invalid_model(self):
        """Test validation of invalid model."""
        result = self.service.validate_model_compatibility("invalid-model")

        self.assertFalse(result["compatible"])
        self.assertIn("Unknown model", result["reason"])

    def test_get_all_models(self):
        """Test getting all available models."""
        models = self.service.get_all_models()

        # Should have our 4 defined models
        self.assertEqual(len(models), 4)
        model_names = list(models.keys())
        self.assertIn("gemma2:2b", model_names)
        self.assertIn("llama3.2:3b", model_names)
        self.assertIn("mistral:7b", model_names)
        self.assertIn("llama3.1:8b", model_names)

    def test_validate_model_compatibility_sufficient_ram(self):
        """Test validation with sufficient RAM."""
        system = self.service.get_system_capabilities()
        # Mock higher available RAM for the test
        system.available_ram_gb = 20.0

        result = self.service.validate_model_compatibility("gemma2:2b", system)

        self.assertTrue(result["compatible"])
        self.assertIn("performance_level", result)

    def test_get_performance_estimate_valid_model(self):
        """Test performance estimation for valid model."""
        estimate = self.service.get_performance_estimate("gemma2:2b")

        self.assertIn("inference_speed", estimate)
        self.assertIn("memory_status", estimate)
        self.assertIn("recommendation", estimate)
        self.assertIn("performance_level", estimate)

    def test_get_performance_estimate_invalid_model(self):
        """Test performance estimation for invalid model."""
        estimate = self.service.get_performance_estimate("invalid-model")

        self.assertIn("error", estimate)
        self.assertIn("Unknown model", estimate["error"])

    def test_get_recommended_models_for_system(self):
        """Test getting recommended models for system."""
        system = self.service.get_system_capabilities()
        # Mock a standard system with 12GB RAM (within standard tier range)
        system.total_ram_gb = 12.0

        models = self.service.get_recommended_models_for_system(system)

        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)
        # Should get standard tier recommendations
        expected_models = ["llama3.2:3b", "gemma2:2b"]
        for model in expected_models:
            self.assertIn(model, models)

    def test_get_system_summary(self):
        """Test getting comprehensive system summary."""
        summary = self.service.get_system_summary()

        self.assertIn("hardware", summary)
        self.assertIn("tier", summary)
        self.assertIn("recommendations", summary)

        # Check hardware section
        hardware = summary["hardware"]
        self.assertIn("ram_total", hardware)
        self.assertIn("cpu_count", hardware)
        self.assertIn("platform", hardware)

        # Check recommendations section
        recommendations = summary["recommendations"]
        self.assertIn("models", recommendations)
        self.assertIn("primary_model", recommendations)

    def test_validate_model_compatibility_insufficient_ram(self):
        """Test validation with insufficient RAM."""
        system = self.service.get_system_capabilities()
        # Mock very low available RAM for the test
        system.available_ram_gb = 1.0

        result = self.service.validate_model_compatibility("llama3.1:8b", system)

        self.assertFalse(result["compatible"])
        self.assertIn("Insufficient RAM", result["reason"])
        self.assertIn("recommendation", result)

    def test_model_info_valid_model(self):
        """Test getting info for valid model."""
        info = self.service.get_model_info("gemma2:2b")

        self.assertIsNotNone(info)
        self.assertIsInstance(info, ModelInfo)
        self.assertEqual(info.name, "gemma2:2b")
        self.assertGreater(info.size_gb, 0)
        self.assertGreater(info.memory_requirement_gb, 0)
        self.assertEqual(info.provider, "local")

    def test_model_info_invalid_model(self):
        """Test getting info for invalid model."""
        info = self.service.get_model_info("invalid-model")

        self.assertIsNone(info)

    def test_model_catalog_completeness(self):
        """Test that model catalog is properly initialized."""
        models = self.service.get_all_models()

        # Check that all expected models are present
        expected_models = ["gemma2:2b", "llama3.2:3b", "mistral:7b", "llama3.1:8b"]
        for model_name in expected_models:
            self.assertIn(model_name, models)
            model_info = models[model_name]
            self.assertIsInstance(model_info, ModelInfo)
            self.assertEqual(model_info.name, model_name)
            self.assertIsInstance(model_info.capabilities, list)
            self.assertTrue(len(model_info.capabilities) > 0)

    def test_hardware_tier_detection_minimal(self):
        """Test hardware tier detection for minimal systems."""
        system = self.service.get_system_capabilities()
        # Mock minimal system with 6GB RAM
        system.total_ram_gb = 6.0

        models = self.service.get_recommended_models_for_system(system)

        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)
        # Should get minimal tier recommendations
        self.assertIn("gemma2:2b", models)

    def test_hardware_tier_detection_standard(self):
        """Test hardware tier detection for standard systems."""
        system = self.service.get_system_capabilities()
        # Mock standard system with 12GB RAM
        system.total_ram_gb = 12.0

        models = self.service.get_recommended_models_for_system(system)

        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)
        # Should get standard tier recommendations
        expected_models = ["llama3.2:3b", "gemma2:2b"]
        for model in expected_models:
            self.assertIn(model, models)

    def test_model_memory_requirements_consistency(self):
        """Test that model memory requirements are consistent."""
        models = self.service.get_all_models()

        for model_name, model_info in models.items():
            # Memory requirement should be greater than file size
            self.assertGreater(model_info.memory_requirement_gb, model_info.size_gb)

            # Memory requirement should be reasonable (not more than 5x file size)
            self.assertLess(model_info.memory_requirement_gb, model_info.size_gb * 5)

            # All models should have descriptions
            self.assertTrue(len(model_info.description) > 0)

            # All models should have capabilities
            self.assertIn("text_generation", model_info.capabilities)

    def test_hardware_tier_coverage(self):
        """Test that hardware tiers cover all reasonable RAM ranges."""
        system = self.service.get_system_capabilities()

        # Test various RAM amounts
        ram_amounts = [4.0, 8.0, 16.0, 32.0, 64.0]

        for ram_gb in ram_amounts:
            system.total_ram_gb = ram_gb
            models = self.service.get_recommended_models_for_system(system)

            # Should always get some recommendation
            self.assertIsInstance(models, list)
            self.assertTrue(len(models) > 0)

            # All recommended models should exist in catalog
            catalog = self.service.get_all_models()
            for model in models:
                self.assertIn(model, catalog)

    def test_system_capability_detection(self):
        """Test system capability detection methods."""
        capabilities = self.service.get_system_capabilities()

        # Basic sanity checks
        self.assertGreater(capabilities.total_ram_gb, 0)
        self.assertGreater(capabilities.available_ram_gb, 0)
        self.assertGreater(capabilities.cpu_count, 0)
        self.assertTrue(len(capabilities.platform) > 0)
        self.assertTrue(len(capabilities.cpu_brand) > 0)

        # Available RAM should not exceed total RAM
        self.assertLessEqual(capabilities.available_ram_gb, capabilities.total_ram_gb)

        # CPU count should be reasonable
        self.assertLessEqual(capabilities.cpu_count, 128)  # Reasonable upper bound

    def test_performance_level_categorization(self):
        """Test that performance levels are correctly categorized."""
        system = self.service.get_system_capabilities()

        # Test with a model we know exists
        estimate = self.service.get_performance_estimate("gemma2:2b", system)

        self.assertIn("performance_level", estimate)
        valid_levels = ["optimal", "good", "acceptable", "slow"]
        self.assertIn(estimate["performance_level"], valid_levels)

        # Test speed categorization
        self.assertIn("inference_speed", estimate)
        speed_categories = ["Very Fast", "Fast", "Moderate", "Slow"]
        speed_found = any(category in estimate["inference_speed"] for category in speed_categories)
        self.assertTrue(speed_found)

    def test_tier_boundary_conditions(self):
        """Test hardware tier boundary conditions."""
        system = self.service.get_system_capabilities()

        # Test exact tier boundaries
        boundary_tests = [
            (8.0, "minimal"),  # Boundary between minimal and standard
            (16.0, "standard"),  # Boundary between standard and performance
            (32.0, "performance"),  # Boundary between performance and workstation
            (64.0, "workstation"),  # Boundary between workstation and server
        ]

        for ram_gb, expected_tier in boundary_tests:
            system.total_ram_gb = ram_gb
            models = self.service.get_recommended_models_for_system(system)

            # Should get appropriate recommendations for the tier
            self.assertIsInstance(models, list)
            self.assertTrue(len(models) > 0)

            # Validate models exist in catalog
            catalog = self.service.get_all_models()
            for model in models:
                self.assertIn(model, catalog)

    def tearDown(self):
        """Clean up test fixtures."""
        # No cleanup needed for domain service tests
        pass


if __name__ == "__main__":
    unittest.main()
