"""
Integration tests for Local LLM processing.

Tests the complete Local LLM pipeline including model availability,
name mapping, and filename generation.
"""

import unittest
from unittest.mock import patch, MagicMock
import requests
import json

from src.domains.ai_integration.providers.local_llm_provider import LocalLLMProvider
from src.shared.infrastructure.model_name_mapper import ModelNameMapper
from src.shared.infrastructure.model_manager import ModelManager, ModelStatus


class TestLocalLLMIntegration(unittest.TestCase):
    """Integration tests for Local LLM provider."""

    @patch('src.shared.infrastructure.dependency_manager.get_dependency_manager')
    @patch('requests.post')
    @patch('requests.Session.get')
    def test_local_llm_with_model_name_mapping(
        self, mock_session_get, mock_post, mock_get_dep_manager
    ):
        """Test that Local LLM correctly maps model names when calling Ollama."""
        # Setup dependency manager mock
        mock_dep_manager = MagicMock()
        mock_dep_manager.find_dependency.return_value = "/usr/local/bin/ollama"
        mock_get_dep_manager.return_value = mock_dep_manager
        
        # Setup Ollama API mocks
        # Mock the model list response
        mock_session_get.return_value.json.return_value = {
            "models": [
                {"name": "llama3.1:8b"},
                {"name": "gemma2:2b"}
            ]
        }
        mock_session_get.return_value.raise_for_status = MagicMock()
        
        # Mock the generate response
        mock_post.return_value.json.return_value = {
            "response": "Important_Business_Document_2024.pdf"
        }
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Create provider with internal name format
        provider = LocalLLMProvider("llama3.1-8b")
        
        # Generate filename
        result = provider.generate_filename(
            "This is a test document about business operations.",
            "test.pdf"
        )
        
        # Verify the model name was correctly mapped in the API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        json_data = call_args.kwargs['json']
        
        # Should use Ollama format in API call
        self.assertEqual(json_data['model'], "llama3.1:8b")
        self.assertEqual(result, "Important_Business_Document_2024.pdf")

    @patch('src.shared.infrastructure.dependency_manager.get_dependency_manager')
    @patch('requests.Session.get')
    def test_model_availability_check_with_mapping(self, mock_session_get, mock_get_dep_manager):
        """Test that model availability check works with name mapping."""
        # Setup dependency manager mock
        mock_dep_manager = MagicMock()
        mock_dep_manager.find_dependency.return_value = "/usr/local/bin/ollama"
        mock_get_dep_manager.return_value = mock_dep_manager
        
        # Mock Ollama API response with models in Ollama format
        mock_session_get.return_value.json.return_value = {
            "models": [
                {"name": "llama3.1:8b"},
                {"name": "gemma2:2b"},
                {"name": "mistral:7b"}
            ]
        }
        mock_session_get.return_value.raise_for_status = MagicMock()
        
        # Test with ModelManager
        manager = ModelManager()
        models = manager.list_available_models()
        
        # Find the llama model using internal name
        llama_model = next((m for m in models if m.name == "llama3.1-8b"), None)
        
        self.assertIsNotNone(llama_model)
        self.assertEqual(llama_model.status, ModelStatus.AVAILABLE)

    @patch('src.shared.infrastructure.dependency_manager.get_dependency_manager')
    @patch('requests.Session.get')
    def test_model_not_available_error(self, mock_session_get, mock_get_dep_manager):
        """Test error handling when model is not available."""
        # Setup dependency manager mock
        mock_dep_manager = MagicMock()
        mock_dep_manager.find_dependency.return_value = "/usr/local/bin/ollama"
        mock_get_dep_manager.return_value = mock_dep_manager
        
        # Mock empty model list
        mock_session_get.return_value.json.return_value = {
            "models": []
        }
        mock_session_get.return_value.raise_for_status = MagicMock()
        
        # Try to create provider with unavailable model
        with self.assertRaises(RuntimeError) as context:
            provider = LocalLLMProvider("llama3.1-8b")
            provider.generate_filename("test content", "test.pdf")
        
        self.assertIn("llama3.1:8b", str(context.exception))
        self.assertIn("ollama pull", str(context.exception))

    @patch('src.shared.infrastructure.dependency_manager.get_dependency_manager')
    @patch('requests.post')
    @patch('requests.Session.get')
    def test_ollama_connection_error_handling(
        self, mock_session_get, mock_post, mock_get_dep_manager
    ):
        """Test error handling when Ollama is not running."""
        # Setup dependency manager mock
        mock_dep_manager = MagicMock()
        mock_dep_manager.find_dependency.return_value = "/usr/local/bin/ollama"
        mock_get_dep_manager.return_value = mock_dep_manager
        
        # Mock Ollama not running
        mock_session_get.side_effect = requests.ConnectionError("Connection refused")
        
        # Try to create provider
        with self.assertRaises(RuntimeError) as context:
            provider = LocalLLMProvider("llama3.1-8b")
            provider.generate_filename("test content", "test.pdf")
        
        self.assertIn("Ollama", str(context.exception))

    @patch('src.shared.infrastructure.dependency_manager.get_dependency_manager')
    @patch('requests.post')
    @patch('requests.Session.get')
    def test_filename_validation(self, mock_session_get, mock_post, mock_get_dep_manager):
        """Test that generated filenames are properly validated."""
        # Setup dependency manager mock
        mock_dep_manager = MagicMock()
        mock_dep_manager.find_dependency.return_value = "/usr/local/bin/ollama"
        mock_get_dep_manager.return_value = mock_dep_manager
        
        # Mock model availability
        mock_session_get.return_value.json.return_value = {
            "models": [{"name": "llama3.1:8b"}]
        }
        mock_session_get.return_value.raise_for_status = MagicMock()
        
        # Mock response with invalid filename
        mock_post.return_value.json.return_value = {
            "response": "../../../etc/passwd"  # Path traversal attempt
        }
        mock_post.return_value.raise_for_status = MagicMock()
        
        provider = LocalLLMProvider("llama3.1-8b")
        result = provider.generate_filename("test content", "test.pdf")
        
        # Should sanitize the dangerous filename
        self.assertNotIn("..", result)
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)

    def test_model_name_mapper_consistency(self):
        """Test that model name mapper handles all known models correctly."""
        known_models = [
            ("llama3.1-8b", "llama3.1:8b"),
            ("llama3.2-3b", "llama3.2:3b"),
            ("mistral-7b", "mistral:7b"),
            ("gemma-2-2b", "gemma2:2b"),
        ]
        
        for internal, ollama in known_models:
            # Test forward mapping
            self.assertEqual(
                ModelNameMapper.to_ollama_format(internal),
                ollama,
                f"Failed to map {internal} to {ollama}"
            )
            
            # Test reverse mapping
            self.assertEqual(
                ModelNameMapper.to_internal_format(ollama),
                internal,
                f"Failed to map {ollama} back to {internal}"
            )


if __name__ == "__main__":
    unittest.main()