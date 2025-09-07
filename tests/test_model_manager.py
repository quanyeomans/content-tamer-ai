"""
Tests for ModelManager functionality.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from utils.model_manager import ModelManager, ModelStatus, ModelInfo, HardwareTier


class TestModelManager(unittest.TestCase):
    """Test ModelManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a temporary directory for models
        self.temp_dir = tempfile.mkdtemp()
        
        with patch("utils.model_manager.ModelManager._get_models_directory") as mock_dir:
            mock_dir.return_value = self.temp_dir
            self.manager = ModelManager()

    @patch("utils.model_manager.requests.Session.get")
    def test_is_ollama_running_success(self, mock_get):
        """Test successful Ollama connection check."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.manager.is_ollama_running()
        self.assertTrue(result)

    @patch("utils.model_manager.requests.Session.get")
    def test_is_ollama_running_failure(self, mock_get):
        """Test failed Ollama connection check."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        
        result = self.manager.is_ollama_running()
        self.assertFalse(result)

    def test_list_available_models(self):
        """Test listing available models."""
        models = self.manager.list_available_models()
        
        # Should have our 4 defined models
        self.assertEqual(len(models), 4)
        model_names = [m.name for m in models]
        self.assertIn("gemma-2-2b", model_names)
        self.assertIn("llama3.2-3b", model_names)
        self.assertIn("mistral-7b", model_names)
        self.assertIn("llama3.1-8b", model_names)

    @patch("utils.model_manager.requests.Session.get")
    def test_get_model_status_not_downloaded(self, mock_get):
        """Test getting status of non-downloaded model."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        status = self.manager._get_model_status("gemma-2-2b")
        self.assertEqual(status, ModelStatus.NOT_DOWNLOADED)

    @patch("utils.model_manager.requests.Session.get")
    def test_get_model_status_available(self, mock_get):
        """Test getting status of available model."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "gemma-2-2b:latest", "size": 1000000}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        status = self.manager._get_model_status("gemma-2-2b")
        self.assertEqual(status, ModelStatus.AVAILABLE)

    @patch("utils.model_manager.requests.Session.get")
    def test_get_model_status_error(self, mock_get):
        """Test getting status when Ollama is not running."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        
        status = self.manager._get_model_status("gemma-2-2b")
        self.assertEqual(status, ModelStatus.ERROR)

    @patch("utils.model_manager.ModelManager.is_ollama_running")
    @patch("utils.model_manager.requests.Session.post")
    def test_download_model_success(self, mock_post, mock_running):
        """Test successful model download."""
        mock_running.return_value = True
        
        # Mock streaming response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_lines.return_value = [
            '{"status": "downloading", "total": 1000, "completed": 500}',
            '{"status": "success"}'
        ]
        mock_post.return_value = mock_response
        
        progress_calls = []
        def progress_callback(progress):
            progress_calls.append(progress)
        
        result = self.manager.download_model("gemma-2-2b", progress_callback)
        
        self.assertTrue(result)
        self.assertTrue(len(progress_calls) > 0)
        self.assertEqual(progress_calls[-1], 100.0)  # Final progress should be 100%

    @patch("utils.model_manager.ModelManager.is_ollama_running")
    def test_download_model_ollama_not_running(self, mock_running):
        """Test download when Ollama is not running."""
        mock_running.return_value = False
        
        with self.assertRaises(RuntimeError) as context:
            self.manager.download_model("gemma-2-2b")
        
        self.assertIn("Ollama is not running", str(context.exception))

    def test_download_model_unknown_model(self):
        """Test download of unknown model."""
        with self.assertRaises(ValueError) as context:
            self.manager.download_model("unknown-model")
        
        self.assertIn("Unknown model", str(context.exception))

    @patch("utils.model_manager.ModelManager.is_ollama_running")
    @patch("utils.model_manager.requests.Session.post")
    def test_verify_model_success(self, mock_post, mock_running):
        """Test successful model verification."""
        mock_running.return_value = True
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test response"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.manager.verify_model("gemma-2-2b")
        self.assertTrue(result)

    @patch("utils.model_manager.ModelManager.is_ollama_running")
    def test_verify_model_ollama_not_running(self, mock_running):
        """Test model verification when Ollama is not running."""
        mock_running.return_value = False
        
        result = self.manager.verify_model("gemma-2-2b")
        self.assertFalse(result)

    @patch("utils.model_manager.ModelManager.is_ollama_running")
    @patch("utils.model_manager.requests.Session.delete")
    def test_remove_model_success(self, mock_delete, mock_running):
        """Test successful model removal."""
        mock_running.return_value = True
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response
        
        result = self.manager.remove_model("gemma-2-2b")
        self.assertTrue(result)

    def test_get_model_info_valid(self):
        """Test getting info for valid model."""
        info = self.manager.get_model_info("gemma-2-2b")
        
        self.assertIsInstance(info, ModelInfo)
        self.assertEqual(info.name, "gemma-2-2b")
        self.assertEqual(info.size_gb, 1.7)
        self.assertEqual(info.memory_requirement_gb, 2.5)

    def test_get_model_info_invalid(self):
        """Test getting info for invalid model."""
        info = self.manager.get_model_info("invalid-model")
        self.assertIsNone(info)

    def test_get_recommended_model_for_system(self):
        """Test getting recommended model based on RAM."""
        # Test with 3GB RAM - should get gemma-2-2b (requires 2.5GB)
        model = self.manager.get_recommended_model_for_system(3.0)
        self.assertEqual(model, "gemma-2-2b")
        
        # Test with 5GB RAM - should get llama3.2-3b (requires 4.5GB)
        model = self.manager.get_recommended_model_for_system(5.0)
        self.assertEqual(model, "llama3.2-3b")
        
        # Test with 7GB RAM - should get mistral-7b (requires 6.5GB)
        model = self.manager.get_recommended_model_for_system(7.0)
        self.assertEqual(model, "mistral-7b")
        
        # Test with 8GB RAM - should get llama3.1-8b (requires 7.5GB)
        model = self.manager.get_recommended_model_for_system(8.0)
        self.assertEqual(model, "llama3.1-8b")
        
        # Test with insufficient RAM - should get None
        model = self.manager.get_recommended_model_for_system(2.0)
        self.assertIsNone(model)

    def test_get_hardware_tier_for_system(self):
        """Test getting hardware tier based on RAM."""
        # Test with 4GB RAM - should get ultra_lightweight
        tier = self.manager.get_hardware_tier_for_system(4.0)
        self.assertIsInstance(tier, HardwareTier)
        self.assertEqual(tier.name, "ultra_lightweight")
        
        # Test with 8GB RAM - should get enhanced
        tier = self.manager.get_hardware_tier_for_system(8.0)
        self.assertEqual(tier.name, "enhanced")
        
        # Test with 12GB RAM - should get premium
        tier = self.manager.get_hardware_tier_for_system(12.0)
        self.assertEqual(tier.name, "premium")
        
        # Test with insufficient RAM - should get None
        tier = self.manager.get_hardware_tier_for_system(2.0)
        self.assertIsNone(tier)

    def test_estimate_download_time(self):
        """Test download time estimation."""
        # gemma-2-2b is 1.7GB
        time_seconds = self.manager.estimate_download_time("gemma-2-2b", 10.0)  # 10 Mbps
        
        # Should be roughly (1.7 * 1024 * 8) / 10 seconds
        expected_time = (1.7 * 1024 * 8) / 10
        self.assertAlmostEqual(time_seconds, expected_time, delta=10)

    def test_estimate_download_time_unknown_model(self):
        """Test download time estimation for unknown model."""
        time_seconds = self.manager.estimate_download_time("unknown-model", 10.0)
        self.assertEqual(time_seconds, 0.0)

    @patch("utils.model_manager.ModelManager.is_ollama_running")
    @patch("utils.model_manager.ModelManager.list_available_models")
    def test_get_system_status(self, mock_list_models, mock_running):
        """Test getting system status."""
        mock_running.return_value = True
        
        # Mock some available models
        mock_models = [
            ModelInfo("gemma-2-2b", 1.7, 2.5, "test", ModelStatus.AVAILABLE),
            ModelInfo("llama3.2-3b", 2.2, 4.5, "test", ModelStatus.NOT_DOWNLOADED),
        ]
        mock_list_models.return_value = mock_models
        
        status = self.manager.get_system_status()
        
        self.assertTrue(status["ollama_running"])
        self.assertEqual(status["ollama_host"], "localhost:11434")
        self.assertEqual(status["available_models"], 1)  # Only one available
        self.assertEqual(status["total_models"], 4)  # Total in MODEL_SPECS

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    unittest.main()