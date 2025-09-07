"""
Tests for AI provider implementations with mocked API calls.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ai_providers import (
    AIProviderFactory,
    ClaudeProvider,
    DeepseekProvider,
    GeminiProvider,
    OpenAIProvider,
    get_system_prompt,
)


class TestAIProviderFactory(unittest.TestCase):
    """Test AI provider factory functionality."""

    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        with patch("ai_providers.HAVE_OPENAI", True), patch("ai_providers.OpenAI"):
            provider = AIProviderFactory.create("openai", "gpt-4o", "test-key")
            self.assertIsInstance(provider, OpenAIProvider)

    def test_create_unsupported_provider(self):
        """Test creating unsupported provider raises error."""
        with self.assertRaises(ValueError) as context:
            AIProviderFactory.create("unsupported", "model", "key")
        self.assertIn("Unsupported AI provider", str(context.exception))

    def test_list_providers(self):
        """Test listing available providers."""
        providers = AIProviderFactory.list_providers()
        self.assertIn("openai", providers)
        self.assertIn("claude", providers)
        self.assertIn("gemini", providers)
        self.assertIn("deepseek", providers)

    def test_get_default_model(self):
        """Test getting default model for provider."""
        model = AIProviderFactory.get_default_model("openai")
        self.assertEqual(model, "gpt-5-mini")


class TestSystemPrompts(unittest.TestCase):
    """Test system prompt functionality."""

    def test_get_system_prompt_valid(self):
        """Test getting system prompt for valid provider."""
        prompt = get_system_prompt("openai")
        self.assertIn("filename", prompt.lower())
        self.assertIn("underscores", prompt.lower())

    def test_get_system_prompt_fallback(self):
        """Test system prompt fallback for invalid provider."""
        with patch("ai_providers.SYSTEM_PROMPTS", {}):
            prompt = get_system_prompt("openai")
            self.assertIsNotNone(prompt)


class TestOpenAIProvider(unittest.TestCase):
    """Test OpenAI provider implementation."""

    def setUp(self):
        """Set up test provider."""
        with patch("ai_providers.HAVE_OPENAI", True), patch("ai_providers.OpenAI") as mock_client:
            self.mock_client = mock_client.return_value
            self.provider = OpenAIProvider("test-key", "gpt-4o")

    def test_generate_filename_success(self):
        """Test successful filename generation."""
        # Mock the response chain
        mock_response = MagicMock()
        mock_response.output_text = "test_document_summary"

        mock_client_with_options = MagicMock()
        mock_client_with_options.responses.create.return_value = mock_response
        self.mock_client.with_options.return_value = mock_client_with_options

        result = self.provider.generate_filename("test content", None)
        self.assertEqual(result, "test_document_summary")

    def test_generate_filename_with_image(self):
        """Test filename generation with image data."""
        mock_response = MagicMock()
        mock_response.output_text = "image_based_filename"

        mock_client_with_options = MagicMock()
        mock_client_with_options.responses.create.return_value = mock_response
        self.mock_client.with_options.return_value = mock_client_with_options

        image_data = "data:image/png;base64,test"
        result = self.provider.generate_filename("test content", image_data)

        self.assertEqual(result, "image_based_filename")
        # Verify image was included in the call
        call_args = mock_client_with_options.responses.create.call_args
        self.assertTrue(
            any("input_image" in str(part) for part in call_args[1]["input"][0]["content"])
        )

    def test_generate_filename_image_fallback(self):
        """Test fallback when model doesn't support images."""
        # Mock APIError as a proper exception class
        with patch("ai_providers.APIError", Exception):
            mock_response = MagicMock()
            mock_response.output_text = "text_only_filename"

            mock_client_with_options = MagicMock()
            mock_client_with_options.responses.create.side_effect = [
                Exception("image not supported"),  # First call fails
                mock_response,  # Second call succeeds
            ]
            self.mock_client.with_options.return_value = mock_client_with_options

            result = self.provider.generate_filename("test content", "image_data")
            self.assertEqual(result, "text_only_filename")

    def test_generate_filename_api_error(self):
        """Test handling of API errors."""
        mock_client_with_options = MagicMock()
        mock_client_with_options.responses.create.side_effect = Exception("API Error")
        self.mock_client.with_options.return_value = mock_client_with_options

        with self.assertRaises(Exception) as context:
            self.provider.generate_filename("test content", None)
        self.assertIn("OpenAI API error", str(context.exception))


class TestClaudeProvider(unittest.TestCase):
    """Test Claude provider implementation."""

    def setUp(self):
        """Set up test provider."""
        with patch("ai_providers.HAVE_CLAUDE", True), patch(
            "ai_providers.anthropic.Anthropic"
        ) as mock_client:
            self.mock_client = mock_client.return_value
            self.provider = ClaudeProvider("test-key", "claude-3-sonnet")

    def test_generate_filename_success(self):
        """Test successful filename generation with Claude."""
        # Mock Claude response format
        mock_content = MagicMock()
        mock_content.text = "claude_generated_filename"

        mock_message = MagicMock()
        mock_message.content = [mock_content]

        self.mock_client.messages.create.return_value = mock_message

        result = self.provider.generate_filename("test content", None)
        self.assertEqual(result, "claude_generated_filename")

    def test_generate_filename_string_content(self):
        """Test handling of string content response."""
        mock_message = MagicMock()
        mock_message.content = "string_response_filename"

        self.mock_client.messages.create.return_value = mock_message

        result = self.provider.generate_filename("test content", None)
        self.assertEqual(result, "string_response_filename")

    def test_generate_filename_error(self):
        """Test handling of Claude API errors."""
        self.mock_client.messages.create.side_effect = Exception("Claude Error")

        with self.assertRaises(RuntimeError) as context:
            self.provider.generate_filename("test content", None)
        self.assertIn("Claude API error", str(context.exception))


class TestGeminiProvider(unittest.TestCase):
    """Test Gemini provider implementation."""

    def setUp(self):
        """Set up test provider."""
        with patch("ai_providers.HAVE_GEMINI", True), patch("ai_providers.genai") as mock_genai:
            self.mock_genai = mock_genai
            self.mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = self.mock_model
            self.provider = GeminiProvider("test-key", "gemini-pro")

    def test_generate_filename_success(self):
        """Test successful filename generation with Gemini."""
        mock_response = MagicMock()
        mock_response.text = "gemini_generated_filename"

        self.mock_model.generate_content.return_value = mock_response

        result = self.provider.generate_filename("test content", None)
        self.assertEqual(result, "gemini_generated_filename")

    def test_generate_filename_error(self):
        """Test handling of Gemini API errors."""
        self.mock_model.generate_content.side_effect = Exception("Gemini Error")

        with self.assertRaises(RuntimeError) as context:
            self.provider.generate_filename("test content", None)
        self.assertIn("Gemini API error", str(context.exception))


class TestDeepseekProvider(unittest.TestCase):
    """Test Deepseek provider implementation."""

    def setUp(self):
        """Set up test provider."""
        self.provider = DeepseekProvider("test-key", "deepseek-chat")

    @patch("ai_providers.requests.post")
    def test_generate_filename_success(self, mock_post):
        """Test successful filename generation with Deepseek."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "deepseek_generated_filename"}}]
        }
        mock_post.return_value = mock_response

        result = self.provider.generate_filename("test content", None)
        self.assertEqual(result, "deepseek_generated_filename")

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "https://api.deepseek.com/v1/chat/completions")

    @patch("ai_providers.requests.post")
    def test_generate_filename_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            self.provider.generate_filename("test content", None)
        self.assertIn("Status code: 500", str(context.exception))

    @patch("ai_providers.requests.post")
    def test_generate_filename_network_error(self, mock_post):
        """Test handling of network errors."""
        mock_post.side_effect = Exception("Network Error")

        with self.assertRaises(RuntimeError) as context:
            self.provider.generate_filename("test content", None)
        self.assertIn("Deepseek API error", str(context.exception))


class TestLocalLLMProvider(unittest.TestCase):
    """Test Local LLM provider functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the connection verification to avoid real network calls
        with patch("ai_providers.LocalLLMProvider._verify_ollama_connection"):
            try:
                from ai_providers import LocalLLMProvider
                self.provider = LocalLLMProvider("gemma-2-2b")
            except ImportError:
                self.skipTest("LocalLLMProvider not implemented yet")

    def test_local_provider_creation(self):
        """Test LocalLLMProvider can be created with model name."""
        self.assertEqual(self.provider.model_name, "gemma-2-2b")
        self.assertEqual(self.provider.host, "localhost:11434")

    def test_local_provider_custom_host(self):
        """Test LocalLLMProvider can be created with custom host."""
        with patch("ai_providers.LocalLLMProvider._verify_ollama_connection"):
            try:
                from ai_providers import LocalLLMProvider
                provider = LocalLLMProvider("mistral-7b", host="custom:8080")
                self.assertEqual(provider.host, "custom:8080")
            except ImportError:
                self.skipTest("LocalLLMProvider not implemented yet")

    @patch("ai_providers.requests.Session.post")
    def test_filename_generation_success(self, mock_post):
        """Test successful filename generation via mocked Ollama."""
        # Mock successful Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "technical_documentation_analysis_report"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.provider.generate_filename("This is a technical document about API testing", None)
        
        # Verify the result is a valid filename
        self.assertTrue(isinstance(result, str))
        self.assertTrue(len(result) > 0)
        self.assertNotIn("/", result)  # Should not contain path separators

    @patch("ai_providers.requests.Session.post")
    def test_filename_generation_with_image(self, mock_post):
        """Test filename generation with image content."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "image_analysis_document"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.provider.generate_filename("Document text", "base64_image_data")
        self.assertTrue(isinstance(result, str))
        self.assertTrue(len(result) > 0)

    @patch("ai_providers.requests.Session.post")
    def test_filename_generation_ollama_connection_failure(self, mock_post):
        """Test graceful failure when Ollama is unavailable."""
        # Mock connection error
        import requests
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        with self.assertRaises(RuntimeError) as context:
            self.provider.generate_filename("test content", None)
        
        error_message = str(context.exception).lower()
        self.assertTrue("ollama" in error_message or "connection" in error_message)

    @patch("ai_providers.requests.Session.post")
    def test_filename_generation_empty_response(self, mock_post):
        """Test handling of empty response from Ollama."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": ""}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            self.provider.generate_filename("test content", None)
        self.assertIn("empty response", str(context.exception).lower())

    @patch("ai_providers.requests.Session.post")
    def test_filename_generation_http_error(self, mock_post):
        """Test handling of HTTP errors from Ollama."""
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Model not found")
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            self.provider.generate_filename("test content", None)
        # Should contain either "ollama api error" or the specific 404 model not found error
        error_message = str(context.exception).lower()
        self.assertTrue("ollama" in error_message and ("api error" in error_message or "not found" in error_message))

    def test_provider_factory_supports_local(self):
        """Test that AIProviderFactory supports local provider."""
        providers = AIProviderFactory.list_providers()
        self.assertIn("local", providers)

    def test_provider_factory_creates_local_provider(self):
        """Test that AIProviderFactory can create local provider."""
        with patch("ai_providers.LocalLLMProvider._verify_ollama_connection"):
            try:
                provider = AIProviderFactory.create("local", "gemma-2-2b", None)
                from ai_providers import LocalLLMProvider
                self.assertIsInstance(provider, LocalLLMProvider)
            except (ImportError, ValueError):
                self.skipTest("LocalLLMProvider not fully implemented yet")

    def test_local_models_available(self):
        """Test that local models are defined."""
        from ai_providers import AI_PROVIDERS
        self.assertIn("local", AI_PROVIDERS)
        local_models = AI_PROVIDERS["local"]
        
        # Verify our 4 recommended models are available
        expected_models = ["gemma-2-2b", "llama3.2-3b", "mistral-7b", "llama3.1-8b"]
        for model in expected_models:
            self.assertIn(model, local_models)


if __name__ == "__main__":
    unittest.main()
