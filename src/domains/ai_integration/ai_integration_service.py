"""
AI Integration Service

Unified service orchestrating all AI-related functionality.
Provides clean interface for AI operations across the application.
"""

import logging
import os
import time
from typing import Dict, Optional, Any, TYPE_CHECKING

# Import request types that are used at runtime
from .request_service import RequestResult, RequestStatus

if TYPE_CHECKING:
    # Type hints only - not runtime imports
    from .provider_service import ProviderService, AIProvider
    from .model_service import ModelService, ModelInfo, SystemCapabilities
    from .request_service import RequestService, RetryConfig


class AIIntegrationService:
    """Main service for all AI integration functionality."""

    def __init__(self, retry_config: Optional[Any] = None):
        """Initialize AI integration service with lazy loading."""
        self.retry_config = retry_config
        self.logger = logging.getLogger(__name__)

        # Lazy-loaded services
        self._provider_service = None
        self._model_service = None
        self._request_service = None

        # Cache for active providers
        self._active_providers: Dict[str, Any] = {}

    @property
    def provider_service(self):
        """Lazy-load provider service."""
        if self._provider_service is None:
            from .provider_service import ProviderService

            self._provider_service = ProviderService()
        return self._provider_service

    @property
    def model_service(self):
        """Lazy-load model service."""
        if self._model_service is None:
            from .model_service import ModelService

            self._model_service = ModelService()
        return self._model_service

    @property
    def request_service(self):
        """Lazy-load request service."""
        if self._request_service is None:
            from .request_service import RequestService

            self._request_service = RequestService(self.retry_config)
        return self._request_service

    def get_provider_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive provider capabilities."""
        return {
            "available_providers": self.provider_service.get_available_providers(),
            "system_capabilities": self.model_service.get_system_summary(),
            "provider_info": {
                provider: self.provider_service.get_provider_info(provider)
                for provider in self.provider_service.get_available_providers()
            },
        }

    def setup_provider(
        self, provider: str, model: Optional[str] = None, api_key: Optional[str] = None
    ) -> Any:
        """Setup and validate an AI provider for use.

        Args:
            provider: Provider name (openai, claude, gemini, etc.)
            model: Model name (optional, uses default if not specified)
            api_key: API key (optional, tries environment variables)

        Returns:
            Configured AIProvider instance

        Raises:
            ValueError: If provider/model combination is invalid
            RuntimeError: If provider is not available or setup fails
        """
        # Get default model if not specified
        if model is None:
            model = self.provider_service.get_default_model(provider)

        # Get API key from environment if not provided
        if api_key is None and provider != "local":
            api_key = self._get_api_key_from_environment(provider)
            if api_key is None:
                raise ValueError(
                    f"API key required for {provider}. Set environment variable or provide directly."
                )

        # Create provider instance
        provider_instance = self.provider_service.create_provider(provider, model, api_key)

        # Validate setup
        if not self._validate_provider_setup(provider_instance):
            raise RuntimeError(f"Provider {provider} setup validation failed")

        # Cache active provider
        cache_key = f"{provider}:{model}"
        self._active_providers[cache_key] = provider_instance

        self.logger.info("Successfully setup %s provider with model %s", provider, model)
        return provider_instance

    def generate_filename_with_ai(
        self,
        content: str,
        original_filename: str,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Any:
        """Generate filename using AI with proper error handling and retry logic.

        Args:
            content: Document content to analyze
            original_filename: Original filename for context
            provider: AI provider to use
            model: Model to use (optional)
            api_key: API key (optional)

        Returns:
            RequestResult with generated filename or error information
        """
        try:
            # Setup provider
            provider_instance = self.setup_provider(provider, model, api_key)

            # Create request function
            def make_request() -> str:
                return provider_instance.generate_filename(content, original_filename)

            # Execute request with retry logic
            request_id = f"filename_gen_{hash(original_filename)}_{int(time.time())}"
            result = self.request_service.make_ai_request(
                provider_func=make_request, request_id=request_id
            )

            return result

        except Exception as e:
            self.logger.error("Filename generation failed: %s", e)
            return RequestResult(
                status=RequestStatus.FAILED, error=str(e), attempts=1, total_time=0.0
            )

    def validate_provider_setup(
        self, provider: str, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate provider setup and return detailed status.

        Args:
            provider: Provider name to validate
            api_key: API key to validate (optional)

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "provider": provider,
            "available": False,
            "api_key_valid": False,
            "recommended_models": [],
            "system_compatibility": {},
            "errors": [],
            "warnings": [],
        }

        try:
            # Check provider availability
            available_providers = self.provider_service.get_available_providers()
            if provider not in available_providers:
                validation_result["errors"].append(f"Provider {provider} not available")
                return validation_result

            validation_result["available"] = True

            # Get provider information
            provider_info = self.provider_service.get_provider_info(provider)
            validation_result["recommended_models"] = provider_info["models"][:3]  # Top 3

            # Validate API key if provided and required
            if provider != "local":
                if api_key:
                    validation_result["api_key_valid"] = self.provider_service.validate_api_key(
                        provider, api_key
                    )
                else:
                    # Check environment variable
                    env_key = self._get_api_key_from_environment(provider)
                    if env_key:
                        validation_result["api_key_valid"] = self.provider_service.validate_api_key(
                            provider, env_key
                        )
                        validation_result["warnings"].append(
                            "Using API key from environment variable"
                        )
                    else:
                        validation_result["warnings"].append(f"No API key provided for {provider}")
            else:
                validation_result["api_key_valid"] = True  # Local doesn't need API key

            # Check system compatibility for local models
            if provider == "local":
                system_caps = self.model_service.get_system_capabilities()
                recommended_models = self.model_service.get_recommended_models_for_system(
                    system_caps
                )

                # Get hardware tier through public interface
                tier = None
                for model in recommended_models:
                    if hasattr(model, 'hardware_tier'):
                        tier = model.hardware_tier
                        break
                validation_result["system_compatibility"] = {
                    "recommended_models": recommended_models,
                    "system_tier": tier.name if tier else "unknown",
                    "ram_available": f"{system_caps.available_ram_gb:.1f}GB",
                }

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")

        return validation_result

    def get_optimal_provider_for_task(
        self, task_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get optimal provider recommendation for a task.

        Args:
            task_requirements: Optional requirements (speed, quality, cost, etc.)

        Returns:
            Dictionary with provider recommendation
        """
        requirements = task_requirements or {}
        available_providers = self.provider_service.get_available_providers()

        if not available_providers:
            return {
                "error": "No AI providers available",
                "recommendation": "Install required dependencies for at least one provider",
            }

        # Default preferences
        preferences = {
            "speed": requirements.get("speed", "balanced"),  # fast, balanced, quality
            "cost": requirements.get("cost", "balanced"),  # low, balanced, quality
            "offline": requirements.get("offline", False),  # prefer offline processing
            "quality": requirements.get("quality", "balanced"),  # good, balanced, best
        }

        # Provider scoring based on preferences
        provider_scores = {}

        for provider in available_providers:
            score = 0

            # Speed scoring
            if preferences["speed"] == "fast":
                speed_scores = {"local": 3, "claude": 2, "openai": 2, "gemini": 2, "deepseek": 1}
            elif preferences["speed"] == "quality":
                speed_scores = {"claude": 3, "openai": 3, "gemini": 2, "local": 1, "deepseek": 1}
            else:  # balanced
                speed_scores = {"openai": 3, "claude": 3, "gemini": 2, "local": 2, "deepseek": 1}

            score += speed_scores.get(provider, 1)

            # Cost scoring
            if preferences["cost"] == "low":
                cost_scores = {"local": 3, "deepseek": 2, "gemini": 1, "claude": 1, "openai": 1}
            else:
                cost_scores = {"openai": 2, "claude": 2, "gemini": 2, "local": 3, "deepseek": 2}

            score += cost_scores.get(provider, 1)

            # Offline preference
            if preferences["offline"]:
                offline_scores = {"local": 5, "openai": 0, "claude": 0, "gemini": 0, "deepseek": 0}
                score += offline_scores.get(provider, 0)

            provider_scores[provider] = score

        # Find best provider
        if not provider_scores:
            return {
                "error": "No providers scored",
                "recommendation": "Check provider availability"
            }
        best_provider = max(provider_scores, key=lambda x: provider_scores[x])
        best_model = self.provider_service.get_default_model(best_provider)

        return {
            "provider": best_provider,
            "model": best_model,
            "score": provider_scores[best_provider],
            "reasoning": self._explain_provider_choice(best_provider, preferences),
            "alternatives": [
                {"provider": p, "score": s}
                for p, s in sorted(provider_scores.items(), key=lambda x: x[1], reverse=True)[1:3]
            ],
        }

    def _explain_provider_choice(self, provider: str, preferences: Dict[str, Any]) -> str:
        """Explain why a provider was recommended."""
        explanations = {
            "openai": "Excellent balance of speed, quality, and reliability",
            "claude": "High quality output with good performance",
            "gemini": "Fast and efficient with good quality",
            "deepseek": "Cost-effective option with decent quality",
            "local": "Complete privacy and no API costs",
        }

        base_reason = explanations.get(provider, "Unknown reason")

        # Add preference-specific reasoning
        if preferences.get("offline"):
            if provider == "local":
                return f"{base_reason}. Chosen for offline processing requirement."

        if preferences.get("cost") == "low":
            if provider in ["local", "deepseek"]:
                return f"{base_reason}. Chosen for low-cost requirement."

        if preferences.get("quality") == "best":
            if provider in ["claude", "openai"]:
                return f"{base_reason}. Chosen for highest quality requirement."

        return base_reason

    def _get_api_key_from_environment(self, provider: str) -> Optional[str]:
        """Get API key from environment variable."""
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }

        env_var = env_vars.get(provider)
        if env_var:
            return os.getenv(env_var)
        return None

    def _validate_provider_setup(self, provider: Any) -> bool:
        """Validate that a provider is properly configured."""
        try:
            return provider.validate_api_key()
        except Exception as e:
            self.logger.warning("Provider validation failed: %s", e)
            return False

    def clear_provider_cache(self) -> None:
        """Clear all cached providers."""
        self._active_providers.clear()
        self.provider_service.clear_cache()

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about AI integration services."""
        return {
            "provider_service": self.provider_service.get_provider_statistics(),
            "model_service": self.model_service.get_system_summary(),
            "request_service": self.request_service.get_request_statistics(),
            "active_providers": len(self._active_providers),
            "cached_providers": list(self._active_providers.keys()),
        }
