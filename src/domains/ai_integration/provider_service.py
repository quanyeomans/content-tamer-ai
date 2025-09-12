"""
AI Provider Service

Unified AI provider management and factory service.
Consolidates all AI provider logic into a clean domain service.
"""

import logging
from typing import Any, Dict, List, Optional

# Import from shared infrastructure (correct layer)
from shared.infrastructure.filename_config import DEFAULT_SYSTEM_PROMPTS

# Import base provider interface
from .base_provider import AIProvider


class ProviderConfiguration:
    """Configuration for AI providers and models."""

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
        "claude": [
            "claude-3.5-sonnet-20241022",
            "claude-3.5-haiku-20241022",
            "claude-3.5-sonnet",
            "claude-3.5-haiku",
            "claude-3-opus",  # For high-quality tasks
            "claude-3-sonnet",
            "claude-3-haiku",
        ],
        "gemini": [
            "gemini-2.0-flash-exp",  # Latest experimental model
            "gemini-2.0-flash",  # Fast and efficient
            "gemini-1.5-pro",  # Balanced capability
            "gemini-1.5-flash",  # Fast inference
            "gemini-1.5-pro-vision",  # Vision capabilities
        ],
        "deepseek": [
            "deepseek-chat",
            "deepseek-coder",
        ],
        "local": [
            "llama3.2-3b",  # Balanced for most systems
            "gemma2-2b",  # Very efficient (using internal format)
            "mistral-7b",  # Good quality
            "llama3.1-8b",  # High capability
        ],
    }

    DEFAULT_MODELS = {
        "openai": "gpt-5-mini",
        "gemini": "gemini-2.0-flash",
        "claude": "claude-3.5-haiku",
        "deepseek": "deepseek-chat",
        "local": "llama3.1-8b",  # Default to better model
    }


class ProviderCapabilities:
    """Provider capability detection and validation."""

    @staticmethod
    def detect_available_providers() -> Dict[str, bool]:
        """Detect which providers are available based on dependencies."""
        capabilities = {}

        # OpenAI
        try:
            import openai  # pylint: disable=unused-import

            capabilities["openai"] = True
        except ImportError:
            capabilities["openai"] = False

        # Claude
        try:
            import anthropic  # pylint: disable=unused-import

            capabilities["claude"] = True
        except ImportError:
            capabilities["claude"] = False

        # Gemini
        try:
            import google.genai as genai  # pylint: disable=unused-import

            capabilities["gemini"] = True
        except ImportError:
            capabilities["gemini"] = False

        # Deepseek (uses OpenAI-compatible API)
        capabilities["deepseek"] = capabilities["openai"]

        # Local (requires ollama)
        try:
            from shared.infrastructure.dependency_manager import DependencyManager

            dep_manager = DependencyManager()
            ollama_path = dep_manager.find_dependency("ollama")
            capabilities["local"] = ollama_path is not None
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to detect local provider: {e}")
            capabilities["local"] = False

        return capabilities

    @staticmethod
    def validate_provider_model_combination(provider: str, model: str) -> bool:
        """Validate that a model is supported by a provider."""
        if provider not in ProviderConfiguration.AI_PROVIDERS:
            return False

        # For local provider, normalize model names for comparison
        if provider == "local":
            from shared.infrastructure.model_name_mapper import ModelNameMapper
            # Check both original and internal format
            internal_model = ModelNameMapper.to_internal_format(ModelNameMapper.to_ollama_format(model))
            return (
                model in ProviderConfiguration.AI_PROVIDERS[provider] or
                internal_model in ProviderConfiguration.AI_PROVIDERS[provider]
            )
        
        return model in ProviderConfiguration.AI_PROVIDERS[provider]

    @staticmethod
    def get_provider_requirements(provider: str) -> Dict[str, Any]:
        """Get requirements for a specific provider."""
        requirements = {
            "openai": {
                "api_key_required": True,
                "environment_var": "OPENAI_API_KEY",
                "dependencies": ["openai"],
                "key_format": "sk-proj-* or sk-*",
            },
            "claude": {
                "api_key_required": True,
                "environment_var": "ANTHROPIC_API_KEY",
                "dependencies": ["anthropic"],
                "key_format": "sk-ant-*",
            },
            "gemini": {
                "api_key_required": True,
                "environment_var": "GEMINI_API_KEY",
                "dependencies": ["google-genai"],
                "key_format": "AIza*",
            },
            "deepseek": {
                "api_key_required": True,
                "environment_var": "DEEPSEEK_API_KEY",
                "dependencies": ["openai"],
                "key_format": "sk-*",
            },
            "local": {
                "api_key_required": False,
                "environment_var": None,
                "dependencies": ["ollama"],
                "key_format": None,
            },
        }

        return requirements.get(provider, {})


class ProviderService:
    """Unified AI provider management service."""

    def __init__(self):
        """Initialize provider service."""
        self.logger = logging.getLogger(__name__)
        self._provider_cache: Dict[str, AIProvider] = {}
        self._capabilities_cache: Optional[Dict[str, bool]] = None

    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        if self._capabilities_cache is None:
            self._capabilities_cache = ProviderCapabilities.detect_available_providers()

        return [provider for provider, available in self._capabilities_cache.items() if available]

    def get_supported_models(self, provider: str) -> List[str]:
        """Get supported models for a provider."""
        return ProviderConfiguration.AI_PROVIDERS.get(provider, [])

    def get_default_model(self, provider: str) -> str:
        """Get default model for a provider."""
        if provider not in ProviderConfiguration.AI_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        return ProviderConfiguration.DEFAULT_MODELS.get(
            provider, ProviderConfiguration.AI_PROVIDERS[provider][0]
        )

    def create_provider(
        self, provider: str, model: str, api_key: Optional[str] = None
    ) -> AIProvider:
        """Create AI provider instance."""
        # Validate provider and model
        if not ProviderCapabilities.validate_provider_model_combination(provider, model):
            raise ValueError(f"Invalid provider/model combination: {provider}/{model}")

        # Check if provider is available
        available_providers = self.get_available_providers()
        if provider not in available_providers:
            requirements = ProviderCapabilities.get_provider_requirements(provider)
            missing_deps = requirements.get("dependencies", [])
            raise RuntimeError(
                f"Provider '{provider}' not available. Missing dependencies: {missing_deps}"
            )

        # Create provider instance
        cache_key = f"{provider}:{model}:{api_key or 'none'}"
        if cache_key not in self._provider_cache:
            self._provider_cache[cache_key] = self._create_provider_instance(
                provider, model, api_key
            )

        return self._provider_cache[cache_key]

    def _create_provider_instance(
        self, provider: str, model: str, api_key: Optional[str]
    ) -> AIProvider:
        """Create specific provider instance using domain architecture."""
        # Validate API key requirements
        requirements = ProviderCapabilities.get_provider_requirements(provider)
        if requirements.get("api_key_required", False) and not api_key:
            raise ValueError(f"API key required for provider '{provider}'")

        try:
            if provider == "openai":
                from .providers.openai_provider import OpenAIProvider

                if api_key is None:
                    raise ValueError("API key required for OpenAI provider")
                return OpenAIProvider(api_key, model)
            if provider == "claude":
                from .providers.claude_provider import ClaudeProvider

                if api_key is None:
                    raise ValueError("API key required for Claude provider")
                return ClaudeProvider(api_key, model)
            if provider == "gemini":
                from .providers.gemini_provider import GeminiProvider

                if api_key is None:
                    raise ValueError("API key required for Gemini provider")
                return GeminiProvider(api_key, model)
            if provider == "deepseek":
                from .providers.deepseek_provider import DeepseekProvider

                if api_key is None:
                    raise ValueError("API key required for Deepseek provider")
                return DeepseekProvider(api_key, model)
            if provider == "local":
                from .providers.local_llm_provider import LocalLLMProvider

                return LocalLLMProvider(model)
            raise ValueError(f"Unsupported provider: {provider}")

        except ImportError as e:
            raise RuntimeError(f"Failed to import {provider} provider: {e}") from e

    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Validate API key for a provider."""
        try:
            # Get default model for testing
            model = self.get_default_model(provider)
            test_provider = self.create_provider(provider, model, api_key)
            return test_provider.validate_api_key()
        except Exception as e:
            self.logger.warning("API key validation failed for %s: %s", provider, e)
            return False

    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get comprehensive information about a provider."""
        if provider not in ProviderConfiguration.AI_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")

        capabilities = ProviderCapabilities.detect_available_providers()
        requirements = ProviderCapabilities.get_provider_requirements(provider)

        return {
            "name": provider,
            "available": capabilities.get(provider, False),
            "models": self.get_supported_models(provider),
            "default_model": self.get_default_model(provider),
            "requirements": requirements,
            "capabilities": self._get_provider_capabilities(provider),
        }

    def _get_provider_capabilities(self, provider: str) -> Dict[str, bool]:
        """Get specific capabilities for a provider."""
        # This could be expanded based on provider features
        capabilities = {
            "text_generation": True,
            "vision": False,
            "function_calling": False,
            "streaming": False,
        }

        # Provider-specific capabilities
        if provider == "openai":
            capabilities.update({"vision": True, "function_calling": True, "streaming": True})
        elif provider == "claude":
            capabilities.update({"vision": True, "function_calling": True, "streaming": True})
        elif provider == "gemini":
            capabilities.update({"vision": True, "function_calling": True, "streaming": True})
        elif provider == "local":
            capabilities.update({"streaming": True})

        return capabilities

    def get_system_prompt(self, provider: str) -> str:
        """Get system prompt for provider with fallback to default."""
        return DEFAULT_SYSTEM_PROMPTS.get(provider, DEFAULT_SYSTEM_PROMPTS["default"])

    def clear_cache(self) -> None:
        """Clear provider cache."""
        self._provider_cache.clear()
        self._capabilities_cache = None

    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get statistics about provider usage and availability."""
        available_providers = self.get_available_providers()
        all_providers = list(ProviderConfiguration.AI_PROVIDERS.keys())

        return {
            "total_providers": len(all_providers),
            "available_providers": len(available_providers),
            "availability_rate": len(available_providers) / len(all_providers),
            "cached_instances": len(self._provider_cache),
            "provider_status": {
                provider: provider in available_providers for provider in all_providers
            },
        }
