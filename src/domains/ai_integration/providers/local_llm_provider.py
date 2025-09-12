"""
Local LLM Provider Implementation

Extracted for domain architecture.
"""

import requests

# Import from shared infrastructure (correct layer)
from shared.infrastructure.filename_config import (
    get_secure_filename_prompt_template,
    validate_generated_filename,
)
from ..base_provider import AIProvider


def get_system_prompt(provider: str) -> str:
    """Get system prompt for provider."""
    from shared.infrastructure.filename_config import DEFAULT_SYSTEM_PROMPTS

    return DEFAULT_SYSTEM_PROMPTS.get(provider, DEFAULT_SYSTEM_PROMPTS["default"])


class LocalLLMProvider(AIProvider):
    """Local LLM provider using Ollama."""

    def __init__(self, model: str) -> None:
        """Initialize local LLM provider with model."""
        super().__init__(None, model)  # No API key needed for local

        # Check if Ollama is available
        try:
            from shared.infrastructure.dependency_manager import get_dependency_manager

            dep_manager = get_dependency_manager()
            ollama_path = dep_manager.find_dependency("ollama")
            if not ollama_path:
                raise RuntimeError("Ollama not found. Please install Ollama first.")
        except ImportError as exc:
            # Fallback check
            import shutil

            if not shutil.which("ollama"):
                raise RuntimeError("Ollama not found in PATH") from exc

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "local"

    def validate_api_key(self) -> bool:
        """Validate API key (always true for local)."""
        return True  # Local doesn't need API key

    def generate_filename(self, content: str, original_filename: str = "") -> str:
        """Generate intelligent filename using local LLM."""
        # First check if Ollama is running
        from shared.infrastructure.model_manager import ModelManager
        from shared.infrastructure.model_name_mapper import ModelNameMapper
        
        model_manager = ModelManager()
        
        if not model_manager.is_ollama_running():
            self.logger.error("Ollama service is not running")
            raise RuntimeError(
                "Ollama is not running. Please start it with: ollama serve"
            )
        
        # Convert model name to Ollama format
        ollama_model = ModelNameMapper.to_ollama_format(self.model)
        self.logger.debug(f"Using Ollama model: {ollama_model} (from internal: {self.model})")
        
        # Check if the model is available
        models = model_manager.list_available_models()
        # Models list has internal names, we need to check against our internal name
        model_available = any(m.name == self.model and m.status.value == "available" for m in models)
        
        if not model_available:
            self.logger.error(f"Model {ollama_model} is not available in Ollama")
            raise RuntimeError(
                f"Model '{ollama_model}' is not available. "
                f"Download it with: ollama pull {ollama_model}"
            )
        
        try:
            prompt = get_secure_filename_prompt_template()
            full_prompt = f"{prompt}\n\nDocument Content:\n{content}"

            # Call Ollama API with mapped model name
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                },
                timeout=600,  # 10 minute timeout for model loading
            )
            response.raise_for_status()

            result = response.json()
            raw_filename = result.get("response", "").strip()

            return validate_generated_filename(raw_filename)

        except requests.exceptions.ConnectionError as e:
            self.logger.error("Cannot connect to Ollama: %s", e)
            raise RuntimeError(
                "Cannot connect to Ollama. Please ensure it's running with: ollama serve"
            ) from e
        except requests.exceptions.Timeout as e:
            self.logger.error("Ollama request timed out: %s", e)
            raise RuntimeError(
                "Ollama request timed out. The model may be loading. Please try again."
            ) from e
        except Exception as e:
            self.logger.error("Local LLM filename generation failed: %s", e)
            raise RuntimeError(f"Local LLM error: {str(e)}") from e
