"""
Local LLM Provider Implementation

Extracted for domain architecture.
"""

from typing import Optional
import requests

from ..base_provider import AIProvider

# Import from shared infrastructure (correct layer)
from ....shared.infrastructure.filename_config import (
    get_secure_filename_prompt_template,
    validate_generated_filename,
)


def get_system_prompt(provider: str) -> str:
    """Get system prompt for provider."""
    from ....shared.infrastructure.filename_config import DEFAULT_SYSTEM_PROMPTS

    return DEFAULT_SYSTEM_PROMPTS.get(provider, DEFAULT_SYSTEM_PROMPTS["default"])


class LocalLLMProvider(AIProvider):
    """Local LLM provider using Ollama."""

    def __init__(self, model: str) -> None:
        """Initialize local LLM provider with model."""
        super().__init__(None, model)  # No API key needed for local

        # Check if Ollama is available
        try:
            from ....shared.infrastructure.dependency_manager import get_dependency_manager

            dep_manager = get_dependency_manager()
            ollama_path = dep_manager.find_dependency("ollama")
            if not ollama_path:
                raise RuntimeError("Ollama not found. Please install Ollama first.")
        except ImportError:
            # Fallback check
            import shutil

            if not shutil.which("ollama"):
                raise RuntimeError("Ollama not found in PATH")

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "local"

    def validate_api_key(self) -> bool:
        """Validate API key (always true for local)."""
        return True  # Local doesn't need API key

    def generate_filename(self, content: str, original_filename: str = "") -> str:
        """Generate intelligent filename using local LLM."""
        try:
            prompt = get_secure_filename_prompt_template("local")
            full_prompt = f"{prompt}\n\nDocument Content:\n{content}"

            # Call Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                },
                timeout=600,  # 10 minute timeout for model loading
            )
            response.raise_for_status()

            result = response.json()
            raw_filename = result.get("response", "").strip()

            return validate_generated_filename(raw_filename)

        except Exception as e:
            self.logger.error(f"Local LLM filename generation failed: {e}")
            raise RuntimeError(f"Local LLM error: {str(e)}") from e
