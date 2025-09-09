"""
Gemini Provider Implementation

Extracted for domain architecture.
"""

import os
import sys
from typing import Optional

from ..base_provider import AIProvider

# Import from shared infrastructure (correct layer)
from ....shared.infrastructure.filename_config import (
    get_secure_filename_prompt_template,
    get_token_limit_for_provider,
    validate_generated_filename,
)

try:
    import google.genai as genai

    HAVE_GEMINI = True
except ImportError:
    genai = None
    HAVE_GEMINI = False


def get_system_prompt(provider: str) -> str:
    """Get system prompt for provider."""
    from shared.infrastructure.filename_config import DEFAULT_SYSTEM_PROMPTS

    return DEFAULT_SYSTEM_PROMPTS.get(provider, DEFAULT_SYSTEM_PROMPTS["default"])


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize Gemini provider with API key and model."""
        super().__init__(api_key, model)
        if not HAVE_GEMINI or genai is None:
            raise ImportError("Please install Google Gemini: pip install google-genai")

        genai.configure(api_key=api_key)  # type: ignore
        self.client = genai.GenerativeModel(model)  # type: ignore

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "gemini"

    def validate_api_key(self) -> bool:
        """Validate API key format."""
        try:
            return bool(self.api_key and self.api_key.startswith("AIza"))
        except Exception:
            return False

    def generate_filename(self, content: str, original_filename: str = "") -> str:
        """Generate intelligent filename using Gemini API."""
        try:
            prompt = get_secure_filename_prompt_template("gemini")
            full_prompt = f"{prompt}\n\nDocument Content:\n{content}"

            response = self.client.generate_content(full_prompt)
            raw_filename = response.text.strip()

            return validate_generated_filename(raw_filename)

        except Exception as e:
            self.logger.error(f"Gemini filename generation failed: {e}")
            raise RuntimeError(f"Gemini error: {str(e)}") from e
