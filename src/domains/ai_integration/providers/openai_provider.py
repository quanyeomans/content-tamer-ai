"""
OpenAI Provider Implementation

Extracted from ai_providers.py for better maintainability and domain separation.
"""

from typing import Optional

# Import from shared infrastructure (correct layer)
from ....shared.infrastructure.filename_config import (
    get_secure_filename_prompt_template,
    get_token_limit_for_provider,
    validate_generated_filename,
)

# Import the base provider interface
from ..base_provider import AIProvider

# Import OpenAI client with dependency check
try:
    from openai import APIError, OpenAI

    HAVE_OPENAI = True
except ImportError:
    OpenAI = None
    APIError = None
    HAVE_OPENAI = False


def get_system_prompt(provider: str) -> str:
    """Get system prompt for provider - temporary function until refactored."""
    from shared.infrastructure.filename_config import DEFAULT_SYSTEM_PROMPTS

    return DEFAULT_SYSTEM_PROMPTS.get(provider, DEFAULT_SYSTEM_PROMPTS["default"])


class OpenAIProvider(AIProvider):
    """OpenAI API provider with support for text and vision models."""

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize OpenAI provider."""
        super().__init__(api_key, model)
        if not HAVE_OPENAI or OpenAI is None:
            raise ImportError("Please install OpenAI: pip install openai")
        self.client = OpenAI(api_key=api_key)
        self._current_image_data = None

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"

    def validate_api_key(self) -> bool:
        """Validate OpenAI API key."""
        try:
            # Make a minimal API call to test the key
            client = self.client.with_options(timeout=10)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheapest model for validation
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            self.logger.warning(f"OpenAI API key validation failed: {e}")
            return False

    def _build_content_parts(self, content: str, image_b64: Optional[str] = None) -> list:
        """Build content parts for API request with security sanitization."""
        # Simple content sanitization (domain-local implementation)
        def sanitize_content_for_ai(content):
            """Basic content sanitization for AI processing."""
            # Remove potential prompt injection attempts
            if any(pattern in content.lower() for pattern in ['ignore previous', 'forget all', 'system:', 'assistant:']):
                return "[Content contains potentially unsafe patterns - using safe fallback]"
            return content
        
        class SecurityError(Exception):
            pass

        parts = []
        if content:
            try:
                # Sanitize content to prevent prompt injection
                sanitized_content = sanitize_content_for_ai(content)

                # Use sanitized content with centralized prompt template
                secure_prompt = get_secure_filename_prompt_template("openai")
                parts.append(
                    {
                        "type": "text",
                        "text": f"{secure_prompt}\n\nDocument Content:\n{sanitized_content}\n",
                    }
                )
            except SecurityError:
                # If content is suspicious, use a safe fallback
                parts.append(
                    {
                        "type": "text",
                        "text": (
                            "Create a generic filename for a document that contained "
                            "potentially unsafe content. Use format: suspicious_document_YYYYMMDD"
                        ),
                    }
                )
                # Note: In production, this should also log the security event

        if image_b64:
            parts.append({"type": "image_url", "image_url": {"url": image_b64}})

        return parts

    def _build_chat_payload(self, parts: list) -> dict:
        """Build chat completion payload."""
        messages = [
            {"role": "system", "content": get_system_prompt("openai")},
            {"role": "user", "content": parts},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": get_token_limit_for_provider("openai"),
            "temperature": 0.1,
            "top_p": 0.9,
        }

        return payload

    def _handle_image_error(self, payload: dict, parts: list) -> str:
        """Handle image-related API errors by retrying without image."""
        # Remove image parts and retry
        text_only_parts = [part for part in parts if part.get("type") != "image_url"]

        retry_payload = dict(payload)
        retry_payload["messages"] = [
            {"role": "system", "content": get_system_prompt("openai")},
            {"role": "user", "content": text_only_parts},
        ]

        try:
            response = self.client.chat.completions.create(**retry_payload)
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Retry without image also failed: {e}")
            raise

    def _try_fallback_model(self, payload: dict, image_b64: Optional[str]) -> str:
        """Try fallback vision-capable model if original failed."""
        if not image_b64:
            return ""

        fallback_model = "gpt-4o"
        fallback_payload = dict(payload)
        fallback_payload["model"] = fallback_model

        try:
            response = self.client.chat.completions.create(**fallback_payload)
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.warning(f"Fallback model {fallback_model} also failed: {e}")
            return ""

    def generate_filename(self, content: str, original_filename: str = "") -> str:
        """Generate filename from content using OpenAI."""
        try:
            # Extract image data if this is a vision request
            image_b64 = None
            if hasattr(self, "_current_image_data"):
                image_b64 = self._current_image_data

            client = self.client.with_options(timeout=90)
            parts = self._build_content_parts(content, image_b64)
            payload = self._build_chat_payload(parts)

            try:
                response = client.chat.completions.create(**payload)
                content_text = response.choices[0].message.content
                if content_text is None:
                    raise ValueError("Empty response from OpenAI API")
                raw_filename = content_text.strip()
            except Exception as e:
                # Handle image-related errors
                error_msg = str(e).lower()
                if "image" in error_msg or "vision" in error_msg:
                    # Model doesn't support images, retry without
                    raw_filename = self._handle_image_error(payload, parts)
                elif HAVE_OPENAI and APIError is not None and isinstance(e, APIError):
                    # Handle other OpenAI API errors
                    raise RuntimeError(f"OpenAI API error: {e}")
                else:
                    raise

            # Fallback to vision-capable model if no response and image available
            if not raw_filename and image_b64:
                raw_filename = self._try_fallback_model(payload, image_b64)

            # Validate and sanitize the generated filename
            return validate_generated_filename(raw_filename)

        except Exception as e:
            self.logger.error("OpenAI filename generation failed: %s", e)
            raise RuntimeError(f"OpenAI error: {str(e)}") from e

    def set_image_data(self, image_data: Optional[str]) -> None:
        """Set image data for vision requests."""
        self._current_image_data = image_data
