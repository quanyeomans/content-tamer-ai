"""
AI Provider implementations for PDF filename generation.

This module contains all AI client implementations and provides a clean
interface for adding new providers, including local LLM support.
"""

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import requests

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
    "gemini": ["gemini-pro"],
    "claude": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
    "deepseek": ["deepseek-chat"],
}

# Provider-specific system prompts for filename generation
DEFAULT_SYSTEM_PROMPTS = {
    "openai": (
        "Generate a descriptive, detailed filename based on the document content. "
        "Return ONLY the filename text, no quotes or code blocks. "
        "Use English letters, numbers, underscores, and hyphens only. "
        "Make it specific and informative, up to 160 characters. "
        "Include key topics, dates, document type when relevant."
    ),
    "gemini": "Generate a detailed, descriptive filename based on the document content. Use only English letters, numbers, underscores, and hyphens. Be specific and informative, up to 160 characters maximum.",
    "claude": "Generate a comprehensive, descriptive filename based on the document content. Use only English letters, numbers, underscores, and hyphens. Include key details and context, up to 160 characters maximum.",
    "deepseek": "Generate a detailed, informative filename based on the document content. Use only English letters, numbers, underscores, and hyphens. Make it comprehensive yet concise, up to 160 characters maximum.",
}

# Runtime prompt configuration (can be overridden)
SYSTEM_PROMPTS = DEFAULT_SYSTEM_PROMPTS

# Recommended default model for each provider
DEFAULT_MODELS = {
    "openai": "gpt-5-mini",
    "gemini": "gemini-pro",
    "claude": "claude-3-haiku",
    "deepseek": "deepseek-chat",
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
        pass

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
        """Build content parts for API request."""
        parts = []
        if content:
            parts.append(
                {
                    "type": "input_text",
                    "text": (
                        "You are a document analyst. Create a concise, human-readable filename "
                        "for this PDF based on its visible content. Use underscores between words. "
                        "Return ONLY the filename. 4-8 words, 60 chars max.\n\n"
                        f"---\nEXTRACTED_TEXT_START\n{content[:8000]}\nEXTRACTED_TEXT_END\n"
                    ),
                }
            )
        if image_b64:
            parts.append({"type": "input_image", "image_url": image_b64})
        return parts

    def _build_base_payload(self, parts: list) -> dict:
        """Build base API payload."""
        base = {
            "model": self.model,
            "instructions": get_system_prompt("openai"),
            "input": [{"role": "user", "content": parts}],
            "max_output_tokens": 50,
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
                # Handle APIError if available, otherwise any exception
                if (
                    HAVE_OPENAI
                    and hasattr(e, "__class__")
                    and "APIError" in str(type(e))
                ):
                    msg = str(e).lower()
                    if "image" in msg:  # Model doesn't support images, retry without
                        raw = self._handle_image_error(base, parts, client)
                    else:
                        raise
                else:
                    raise

            # Fallback to vision-capable model if no response and image available
            if not raw and image_b64:
                raw = self._try_fallback_model(base, client, image_b64)

            return raw
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class GeminiProvider(AIProvider):
    """Google Gemini API provider (text-only support)."""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        if not HAVE_GEMINI or genai is None:
            raise ImportError(
                "Please install Google Generative AI: pip install google-genai"
            )
        genai.configure(api_key=api_key)  # type: ignore
        self.client = genai.GenerativeModel(model)  # type: ignore

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generate filename using Gemini API (image parameter ignored)."""
        try:
            if genai is None:
                raise RuntimeError("Gemini not available")
            response = self.client.generate_content(
                [get_system_prompt("gemini"), content or ""],
                generation_config=genai.types.GenerationConfig(  # type: ignore
                    max_output_tokens=50,
                    temperature=0.2,
                ),
            )
            if not hasattr(response, "text"):
                raise AttributeError("Unexpected response format from Gemini API")
            return response.text
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
            message = self.client.messages.create(
                model=self.model,
                system=get_system_prompt("claude"),
                max_tokens=50,
                messages=[{"role": "user", "content": content or ""}],
            )
            # Handle new Anthropic API response format
            if hasattr(message, "content") and isinstance(message.content, list):
                for block in message.content:
                    if hasattr(block, "text"):
                        return block.text  # type: ignore
                    elif (
                        hasattr(block, "type")
                        and getattr(block, "type", None) == "text"
                        and hasattr(block, "text")
                    ):
                        return block.text  # type: ignore
            # Fallback for older response formats
            if hasattr(message, "content"):
                if isinstance(message.content, str):
                    return message.content
                elif isinstance(message.content, dict) and "text" in message.content:
                    return message.content["text"]  # type: ignore
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
            "max_tokens": 50,
            "temperature": 0.2,
        }
        try:
            response = requests.post(
                self.base_url, headers=headers, json=data, timeout=30
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise RuntimeError(f"Deepseek API request error: {str(e)}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Deepseek API response parsing error: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Deepseek API error: {str(e)}") from e


class AIProviderFactory:
    """Factory for creating and managing AI provider instances."""

    @staticmethod
    def create(provider: str, model: str, api_key: str) -> AIProvider:
        """Create AI provider instance for specified provider and model."""
        if provider == "openai":
            return OpenAIProvider(api_key, model)
        elif provider == "gemini":
            return GeminiProvider(api_key, model)
        elif provider == "claude":
            return ClaudeProvider(api_key, model)
        elif provider == "deepseek":
            return DeepseekProvider(api_key, model)
        else:
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
