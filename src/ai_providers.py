"""
AI Provider implementations for PDF filename generation.

This module contains all AI client implementations and provides a clean
interface for adding new providers, including local LLM support.
"""

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import requests

# Import centralized filename configuration - handle both package and direct execution
try:
    from core.filename_config import (
        DEFAULT_SYSTEM_PROMPTS,
        get_secure_filename_prompt_template,
        validate_generated_filename,
        get_token_limit_for_provider,
    )
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from core.filename_config import (
        DEFAULT_SYSTEM_PROMPTS,
        get_secure_filename_prompt_template,
        validate_generated_filename,
        get_token_limit_for_provider,
    )

# Import API clients conditionally to avoid hard dependencies
# Use TYPE_CHECKING to prevent Pyright "possibly unbound" errors
if TYPE_CHECKING:
    import anthropic
    import google.genai as genai
    from openai import APIError, OpenAI

# Initialize flags and imports
try:
    import google.genai as genai

    HAVE_GEMINI = True
except ImportError:
    genai = None  # type: ignore
    HAVE_GEMINI = False

try:
    import anthropic

    HAVE_CLAUDE = True
except ImportError:
    anthropic = None  # type: ignore
    HAVE_CLAUDE = False

try:
    from openai import APIError, OpenAI

    HAVE_OPENAI = True
except ImportError:
    OpenAI = None  # type: ignore
    APIError = Exception  # Fallback for error handling
    HAVE_OPENAI = False

# No need for try/except for Deepseek since we're using requests
HAVE_DEEPSEEK = True

# Supported AI providers and their available models
AI_PROVIDERS = {
    "openai": [
        "gpt-5",
        "gpt-5-mini",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo",  # Legacy support
        "gpt-4-vision-preview",
        "gpt-4o-vision",  # Vision-capable models
    ],
    "gemini": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.0-pro-experimental",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",  # Legacy support
    ],
    "claude": [
        "claude-opus-4.1",
        "claude-sonnet-4",
        "claude-3.7-sonnet",
        "claude-3.5-opus",
        "claude-3.5-sonnet",
        "claude-3.5-haiku",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",  # Legacy support
    ],
    "deepseek": ["deepseek-chat"],
    "local": [
        "gemma-2-2b",  # Ultra-lightweight (4GB RAM)
        "llama3.2-3b",  # Standard (6GB RAM)
        "mistral-7b",  # Enhanced (8GB RAM)
        "llama3.1-8b",  # Premium (10GB+ RAM)
    ],
}

# Note: System prompts now imported from centralized configuration
# Runtime prompt configuration (can be overridden)
SYSTEM_PROMPTS = DEFAULT_SYSTEM_PROMPTS

# Recommended default model for each provider
DEFAULT_MODELS = {
    "openai": "gpt-5-mini",
    "gemini": "gemini-2.0-flash",  # Fast, cost-efficient, generally available
    "claude": "claude-3.5-haiku",  # Fastest, most cost-effective Claude 3.5 model
    "deepseek": "deepseek-chat",
    "local": "llama3.2-3b",  # Balanced performance for most systems
}


def get_system_prompt(provider: str) -> str:
    """Get system prompt for provider with fallback to default."""
    try:
        if isinstance(SYSTEM_PROMPTS, dict) and provider in SYSTEM_PROMPTS:
            return SYSTEM_PROMPTS[provider]
    except Exception:
        pass
    return DEFAULT_SYSTEM_PROMPTS[provider]


class AIProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generate filename from document content and optional image data."""

    def is_local(self) -> bool:
        """Return True if provider runs locally without API calls."""
        return False


class OpenAIProvider(AIProvider):
    """OpenAI API provider with support for text and vision models."""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        if not HAVE_OPENAI or OpenAI is None:
            raise ImportError("Please install OpenAI: pip install openai")
        self.client = OpenAI(api_key=api_key)

    def _build_content_parts(self, content: str, image_b64: Optional[str]) -> list:
        """Build content parts for API request with security sanitization."""
        # Import security utilities
        try:
            from utils.security import InputSanitizer, SecurityError
        except ImportError:
            sys.path.insert(0, os.path.dirname(__file__))
            from utils.security import InputSanitizer, SecurityError

        parts = []
        if content:
            try:
                # Sanitize content to prevent prompt injection
                sanitized_content = InputSanitizer.sanitize_content_for_ai(content)

                # Use sanitized content with centralized prompt template
                secure_prompt = get_secure_filename_prompt_template("openai")
                parts.append(
                    {
                        "type": "input_text",
                        "text": f"{secure_prompt}\n\nDocument Content:\n{sanitized_content}\n",
                    }
                )
            except SecurityError:
                # If content is suspicious, use a safe fallback
                parts.append(
                    {
                        "type": "input_text",
                        "text": (
                            "Create a generic filename for a document that contained "
                            "potentially unsafe content. Use format: suspicious_document_YYYYMMDD"
                        ),
                    }
                )
                # Note: In production, this should also log the security event
        if image_b64:
            parts.append({"type": "input_image", "image_url": image_b64})
        return parts

    def _build_base_payload(self, parts: list) -> dict:
        """Build base API payload."""
        base = {
            "model": self.model,
            "instructions": get_system_prompt("openai"),
            "input": [{"role": "user", "content": parts}],
            "max_output_tokens": get_token_limit_for_provider("openai"),
        }
        model_lc = (self.model or "").lower()
        if "gpt-5" in model_lc:
            base["reasoning"] = {"effort": "low"}
        else:
            base["temperature"] = 0.1
            base["top_p"] = 0.9
        return base

    def _handle_image_error(self, base: dict, parts: list, client) -> str:
        """Handle image-related API errors by retrying without image."""
        noimg = dict(base)
        noimg["input"] = [
            {
                "role": "user",
                "content": [c for c in parts if c.get("type") != "input_image"],
            }
        ]
        noimg.pop("reasoning", None)
        noimg["temperature"] = 0.1
        noimg["top_p"] = 0.9
        resp = client.responses.create(**noimg)
        return (resp.output_text or "").strip()

    def _try_fallback_model(self, base: dict, client, image_b64: Optional[str]) -> str:
        """Try fallback vision-capable model if original failed."""
        if not image_b64:
            return ""

        fallback_model = "gpt-4o"
        fb = dict(base)
        fb["model"] = fallback_model
        fb.pop("reasoning", None)
        fb["temperature"] = 0.1
        fb["top_p"] = 0.9
        try:
            resp = client.responses.create(**fb)
            return (resp.output_text or "").strip()
        except Exception:
            return ""

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        try:
            client = self.client.with_options(timeout=90)
            parts = self._build_content_parts(content, image_b64)
            base = self._build_base_payload(parts)

            try:
                resp = client.responses.create(**base)
                raw = (resp.output_text or "").strip()
            except Exception as e:
                # Handle image-related errors by checking message content
                msg = str(e).lower()
                if "image" in msg or "vision" in msg:  # Model doesn't support images, retry without
                    raw = self._handle_image_error(base, parts, client)
                elif HAVE_OPENAI and hasattr(e, "__class__") and "APIError" in str(type(e)):
                    # Handle other OpenAI API errors
                    raise
                else:
                    raise

            # Fallback to vision-capable model if no response and image available
            if not raw and image_b64:
                raw = self._try_fallback_model(base, client, image_b64)

            # Validate and sanitize the generated filename
            return validate_generated_filename(raw)
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e


class GeminiProvider(AIProvider):
    """Google Gemini API provider (text-only support)."""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        if not HAVE_GEMINI or genai is None:
            raise ImportError("Please install Google Generative AI: pip install google-genai")
        genai.configure(api_key=api_key)  # type: ignore
        self.client = genai.GenerativeModel(model)  # type: ignore

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generate filename using Gemini API (image parameter ignored)."""
        try:
            if genai is None:
                raise RuntimeError("Gemini not available")

            # Build generation config with latest API specification
            generation_config = genai.types.GenerationConfig(  # type: ignore
                max_output_tokens=get_token_limit_for_provider("gemini"),
                temperature=0.2,
                top_p=0.9,
                top_k=1,
                candidate_count=1,
            )

            # Disable thinking for 2.5 models to get faster responses for filename generation
            if "2.5" in self.model:
                try:
                    generation_config.thinking_config = genai.types.ThinkingConfig(  # type: ignore
                        thinking_budget=0  # Disable thinking for faster responses
                    )
                except (AttributeError, TypeError):
                    # Fallback if thinking_config not available in this version
                    pass

            response = self.client.generate_content(
                [get_system_prompt("gemini"), content or ""],
                generation_config=generation_config,
            )
            if not hasattr(response, "text"):
                raise AttributeError("Unexpected response format from Gemini API")

            # Validate and sanitize the generated filename
            return validate_generated_filename(response.text)
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}") from e


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider (text-only support)."""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        if not HAVE_CLAUDE or anthropic is None:
            raise ImportError("Please install Anthropic: pip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generate filename using Claude API (image parameter ignored)."""
        try:
            if anthropic is None:
                raise RuntimeError("Anthropic not available")

            # Build API parameters with temperature for consistency
            api_params = {
                "model": self.model,
                "system": get_system_prompt("claude"),
                "max_tokens": get_token_limit_for_provider("claude"),
                "messages": [{"role": "user", "content": content or ""}],
            }

            # Add temperature parameter, but avoid for Opus 4.1 models which have restrictions
            if "opus-4.1" not in self.model.lower():
                api_params["temperature"] = 0.2

            message = self.client.messages.create(**api_params)
            # Handle new Anthropic API response format
            if hasattr(message, "content") and isinstance(message.content, list):
                for block in message.content:
                    if hasattr(block, "text"):
                        return validate_generated_filename(block.text)  # type: ignore
                    if (
                        hasattr(block, "type")
                        and getattr(block, "type", None) == "text"
                        and hasattr(block, "text")
                    ):
                        return validate_generated_filename(block.text)  # type: ignore
            # Fallback for older response formats
            if hasattr(message, "content"):
                if isinstance(message.content, str):
                    return validate_generated_filename(message.content)
                if isinstance(message.content, dict) and "text" in message.content:
                    return validate_generated_filename(message.content["text"])  # type: ignore
            raise ValueError("Unable to extract text from Claude API response")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}") from e


class DeepseekProvider(AIProvider):
    """Deepseek API provider using direct HTTP requests."""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": get_system_prompt("deepseek")},
                {"role": "user", "content": content or ""},
            ],
            "max_tokens": get_token_limit_for_provider("deepseek"),
            "temperature": 0.2,
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
            result = response.json()
            return validate_generated_filename(result["choices"][0]["message"]["content"])
        except requests.RequestException as e:
            raise RuntimeError(f"Deepseek API request error: {str(e)}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Deepseek API response parsing error: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Deepseek API error: {str(e)}") from e


class LocalLLMProvider(AIProvider):
    """Local LLM provider using Ollama backend for offline processing."""

    def __init__(self, model: str, host: str = "localhost:11434") -> None:
        # Local providers don't need API keys
        super().__init__(api_key="", model=model)
        self.model_name = model
        self.host = host
        self.base_url = f"http://{host}/api/generate"

        # Create a session for HTTP requests
        self.session = requests.Session()

        # Verify Ollama is available
        self._verify_ollama_connection()

    def _verify_ollama_connection(self) -> None:
        """Verify that Ollama service is running and accessible."""
        try:
            health_url = f"http://{self.host}/api/tags"
            response = self.session.get(health_url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(
                f"Cannot connect to Ollama service at {self.host}. "
                f"Please ensure Ollama is running. Error: {str(e)}"
            ) from e

    def is_local(self) -> bool:
        """Return True since this is a local provider."""
        return True

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generate filename using local Ollama model."""
        try:
            # Get the system prompt for local provider
            system_prompt = get_secure_filename_prompt_template("local")

            # Prepare the prompt combining system instructions and content
            prompt = f"{system_prompt}\n\nDocument content:\n{content}"

            # Add image context if provided
            if image_b64:
                prompt += "\n\nNote: This document also contains visual elements that may be relevant to the filename."

            # Make request to Ollama
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent naming
                    "num_predict": 50,  # Limit response length for filenames
                    "stop": ["\n", ".", "!"],  # Stop at common filename endings
                },
            }

            response = self.session.post(self.base_url, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("response", "").strip()

            if not generated_text:
                raise RuntimeError("Ollama returned empty response")

            # Validate and clean the filename
            return validate_generated_filename(generated_text)

        except requests.ConnectionError as e:
            raise RuntimeError(
                f"Connection to Ollama failed. Is Ollama running on {self.host}? "
                f"Error: {str(e)}"
            ) from e
        except requests.HTTPError as e:
            if "404" in str(e):
                raise RuntimeError(
                    f"Model '{self.model_name}' not found in Ollama. "
                    f"Please download it first with: ollama pull {self.model_name}"
                ) from e
            raise RuntimeError(f"Ollama API error: {str(e)}") from e
        except requests.Timeout as e:
            raise RuntimeError(
                "Ollama request timed out. The model might be loading for the first time. "
                "Please try again in a few moments."
            ) from e
        except (KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Invalid response from Ollama: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Local LLM error: {str(e)}") from e


class AIProviderFactory:
    """Factory for creating and managing AI provider instances."""

    @staticmethod
    def create(provider: str, model: str, api_key: str = None) -> AIProvider:
        """Create AI provider instance for specified provider and model."""
        if provider == "openai":
            return OpenAIProvider(api_key, model)
        if provider == "gemini":
            return GeminiProvider(api_key, model)
        if provider == "claude":
            return ClaudeProvider(api_key, model)
        if provider == "deepseek":
            return DeepseekProvider(api_key, model)
        if provider == "local":
            # Local provider doesn't require API key
            return LocalLLMProvider(model)

        raise ValueError(f"Unsupported AI provider: {provider}")

    @staticmethod
    def list_providers():
        """Get dictionary of available providers and their models."""
        return AI_PROVIDERS

    @staticmethod
    def get_default_model(provider: str) -> str:
        """Get recommended default model for specified provider."""
        if provider not in AI_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        return DEFAULT_MODELS.get(provider, AI_PROVIDERS[provider][0])
