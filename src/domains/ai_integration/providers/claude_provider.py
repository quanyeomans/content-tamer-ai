"""
Claude Provider Implementation

Extracted from original ai_providers.py for domain architecture.
"""

import os
import sys
from typing import Optional

# Import the base provider interface
from ..base_provider import AIProvider

# Import centralized configuration
from ....shared.infrastructure.filename_config import (
    get_secure_filename_prompt_template,
    get_token_limit_for_provider,
    validate_generated_filename,
)

# Import Claude client with dependency check
try:
    import anthropic

    HAVE_ANTHROPIC = True
except ImportError:
    anthropic = None
    HAVE_ANTHROPIC = False


def get_system_prompt(provider: str) -> str:
    """Get system prompt for provider - temporary function until refactored."""
    from ....shared.infrastructure.filename_config import DEFAULT_SYSTEM_PROMPTS

    return DEFAULT_SYSTEM_PROMPTS.get(provider, DEFAULT_SYSTEM_PROMPTS["default"])


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider (text-only support)."""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        if not HAVE_ANTHROPIC or anthropic is None:
            raise ImportError("Please install Anthropic: pip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_filename(self, content: str, original_filename: str) -> str:
        """Generate filename using Claude API."""
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
                    elif (
                        hasattr(block, "type")
                        and getattr(block, "type", None) == "text"
                        and hasattr(block, "text")
                    ):
                        return validate_generated_filename(block.text)  # type: ignore
            # Fallback for older response formats
            if hasattr(message, "content"):
                if isinstance(message.content, str):
                    return validate_generated_filename(message.content)
                elif isinstance(message.content, dict) and "text" in message.content:
                    return validate_generated_filename(message.content["text"])  # type: ignore
            raise ValueError("Unable to extract text from Claude API response")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}") from e

    def validate_api_key(self) -> bool:
        """Validate Claude API key format and functionality."""
        if not self.api_key:
            return False
        
        # Check format
        if not self.api_key.startswith("sk-ant-"):
            return False
        
        try:
            # Test API key with minimal request
            self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "claude"
