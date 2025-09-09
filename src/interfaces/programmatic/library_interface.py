"""
Python Library Interface

Provides clean Python API for programmatic use cases.
Enables Content Tamer AI to be used as a library in other applications.
"""

from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
from pathlib import Path
import asyncio
import logging

from ..base_interfaces import ProgrammaticInterface, ProcessingResult
from .configuration_manager import ProcessingConfiguration, ConfigurationManager
from .cli_arguments import ParsedArguments


class ContentTamerAPI(ProgrammaticInterface):
    """Main Python API for Content Tamer AI."""

    def __init__(self, config: Optional[ProcessingConfiguration] = None):
        """Initialize API with optional configuration.

        Args:
            config: Processing configuration. If None, loads from defaults.
        """
        self.config_manager = ConfigurationManager()
        self.config = config or self.config_manager.load_configuration()
        self.logger = logging.getLogger(__name__)

        # Will be initialized when needed
        self._kernel = None

    @property
    def kernel(self):
        """Lazy-load application kernel to avoid circular imports."""
        if self._kernel is None:
            # Import here to avoid circular dependency
            try:
                from core.application_container import ApplicationContainer
                container = ApplicationContainer()
                self._kernel = container.create_application_kernel()
            except ImportError:
                # Fallback for when full kernel not available
                from .mock_kernel import MockApplicationKernel
                self._kernel = MockApplicationKernel()

        return self._kernel

    def process_documents(self, config: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """Process documents with specified configuration.

        Args:
            config: Optional configuration dictionary to override defaults

        Returns:
            ProcessingResult with processing outcome
        """
        try:
            # Merge configuration
            processing_config = self._prepare_configuration(config)

            # Validate configuration
            errors = self.validate_configuration(processing_config.__dict__)
            if errors:
                return ProcessingResult(
                    success=False,
                    files_processed=0,
                    files_failed=0,
                    output_directory="",
                    errors=errors,
                    warnings=[],
                    metadata={"validation_failed": True}
                )

            # Execute processing through kernel
            kernel = self.kernel
            if kernel is None:
                raise RuntimeError("Application kernel is not available")
            
            result = kernel.execute_processing(processing_config)
            # Ensure we return the correct ProcessingResult type
            if hasattr(result, 'success') and hasattr(result, 'files_processed'):
                return ProcessingResult(
                    success=result.success,
                    files_processed=result.files_processed,
                    files_failed=getattr(result, 'files_failed', 0),
                    output_directory=getattr(result, 'output_directory', ""),
                    errors=getattr(result, 'errors', []),
                    warnings=getattr(result, 'warnings', []),
                    metadata=getattr(result, 'metadata', {})
                )
            return result

        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return ProcessingResult(
                success=False,
                files_processed=0,
                files_failed=0,
                output_directory="",
                errors=[str(e)],
                warnings=[],
                metadata={"exception": str(e)}
            )

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration returning list of errors.

        Args:
            config: Configuration dictionary to validate

        Returns:
            List of error messages (empty if valid)
        """
        try:
            # Convert dict to ProcessingConfiguration for validation
            processing_config = self._dict_to_config(config)
            return self.config_manager.validate_configuration(processing_config)

        except Exception as e:
            return [f"Configuration validation error: {e}"]

    def get_progress_status(self) -> Dict[str, Any]:
        """Return machine-readable progress information.

        Returns:
            Dictionary with current processing status
        """
        kernel = self.kernel
        if kernel is None:
            return {"status": "unavailable", "error": "Application kernel is not available"}
        return kernel.get_progress_status()

    def get_supported_providers(self) -> List[str]:
        """Get list of supported AI providers.

        Returns:
            List of provider names
        """
        try:
            kernel = self.kernel
            if kernel is None:
                return ["openai", "claude", "gemini", "deepseek", "local"]
            return kernel.get_ai_providers()
        except Exception:
            # Fallback list
            return ["openai", "claude", "gemini", "deepseek", "local"]

    def get_supported_models(self, provider: str) -> List[str]:
        """Get supported models for a provider.

        Args:
            provider: AI provider name

        Returns:
            List of model names
        """
        try:
            kernel = self.kernel
            if kernel is None:
                # Use fallback model lists
                model_fallbacks = {
                    "openai": ["gpt-4o", "gpt-4o-mini"],
                    "claude": ["claude-3.5-sonnet", "claude-3.5-haiku"],
                    "gemini": ["gemini-2.0-flash", "gemini-1.5-pro"],
                    "deepseek": ["deepseek-chat"],
                    "local": ["llama3.2-3b", "gemma2:2b"]
                }
                return model_fallbacks.get(provider, [])
            return kernel.get_provider_models(provider)
        except Exception:
            # Fallback model lists
            model_fallbacks = {
                "openai": ["gpt-4o", "gpt-4o-mini"],
                "claude": ["claude-3.5-sonnet", "claude-3.5-haiku"],
                "gemini": ["gemini-2.0-flash", "gemini-1.5-pro"],
                "deepseek": ["deepseek-chat"],
                "local": ["llama3.2-3b", "gemma2:2b"]
            }
            return model_fallbacks.get(provider, [])

    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Validate API key for a provider.

        Args:
            provider: AI provider name
            api_key: API key to validate

        Returns:
            True if API key is valid
        """
        try:
            kernel = self.kernel
            if kernel is None:
                # Basic validation - just check it's not empty
                return bool(api_key and api_key.strip())
            return kernel.validate_provider_api_key(provider, api_key)
        except Exception:
            # Basic validation - just check it's not empty
            return bool(api_key and api_key.strip())

    async def process_documents_async(
        self,
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> ProcessingResult:
        """Async document processing with progress callbacks.

        Args:
            config: Optional configuration dictionary
            progress_callback: Optional callback for progress updates

        Returns:
            ProcessingResult with processing outcome
        """
        # Run synchronous processing in executor
        loop = asyncio.get_event_loop()

        def sync_process():
            return self.process_documents(config)

        return await loop.run_in_executor(None, sync_process)

    def _prepare_configuration(self, config_override: Optional[Dict[str, Any]]) -> ProcessingConfiguration:
        """Prepare configuration by merging defaults with overrides."""
        # Start with current configuration
        config = ProcessingConfiguration(
            input_dir=self.config.input_dir,
            output_dir=self.config.output_dir,
            unprocessed_dir=self.config.unprocessed_dir,
            provider=self.config.provider,
            model=self.config.model,
            api_key=self.config.api_key,
            ocr_language=self.config.ocr_language,
            reset_progress=self.config.reset_progress,
            organization_enabled=self.config.organization_enabled,
            ml_level=self.config.ml_level,
            quiet_mode=self.config.quiet_mode,
            verbose_mode=self.config.verbose_mode
        )

        # Apply overrides
        if config_override:
            for key, value in config_override.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        return config

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> ProcessingConfiguration:
        """Convert dictionary to ProcessingConfiguration."""
        # Start with defaults
        config = self.config_manager.load_configuration()

        # Apply dictionary values
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config


# Convenience functions for simple use cases

def process_documents_simple(
    input_dir: str,
    output_dir: str,
    api_key: str,
    provider: str = "openai",
    **kwargs
) -> ProcessingResult:
    """Simple function interface for basic processing.

    Args:
        input_dir: Directory containing documents to process
        output_dir: Directory where organized documents will be saved
        api_key: API key for the AI provider
        provider: AI provider to use (default: "openai")
        **kwargs: Additional configuration options

    Returns:
        ProcessingResult with processing outcome
    """
    api = ContentTamerAPI()

    config = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "provider": provider,
        "api_key": api_key,
        **kwargs
    }

    return api.process_documents(config)


def validate_setup(
    input_dir: str,
    output_dir: str,
    provider: str = "openai",
    api_key: Optional[str] = None
) -> List[str]:
    """Validate setup configuration.

    Args:
        input_dir: Input directory to validate
        output_dir: Output directory to validate
        provider: AI provider to validate
        api_key: Optional API key to validate

    Returns:
        List of validation errors (empty if valid)
    """
    api = ContentTamerAPI()

    config = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "provider": provider,
    }

    if api_key:
        config["api_key"] = api_key

    return api.validate_configuration(config)


def get_provider_info(provider: Optional[str] = None) -> Dict[str, Any]:
    """Get information about AI providers.

    Args:
        provider: Specific provider to get info for (optional)

    Returns:
        Dictionary with provider information
    """
    api = ContentTamerAPI()

    if provider:
        return {
            "provider": provider,
            "models": api.get_supported_models(provider),
            "supported": provider in api.get_supported_providers()
        }
    else:
        providers = api.get_supported_providers()
        return {
            "supported_providers": providers,
            "provider_models": {
                p: api.get_supported_models(p) for p in providers
            }
        }


# Context manager for configuration
class ContentTamerSession:
    """Context manager for Content Tamer API sessions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize session with configuration."""
        self.config = config
        self.api = None

    def __enter__(self) -> ContentTamerAPI:
        """Enter context and return API instance."""
        self.api = ContentTamerAPI()
        if self.config:
            self.api.config = self.api._prepare_configuration(self.config)
        return self.api

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup."""
        # Cleanup if needed
        self.api = None
        return False


# Example usage patterns:
"""
# Simple processing
result = process_documents_simple(
    input_dir="./documents",
    output_dir="./organized",
    api_key="your-api-key",
    provider="openai"
)

# Validation before processing
errors = validate_setup(
    input_dir="./documents",
    output_dir="./organized"
)

if not errors:
    # Process documents
    pass

# Using the full API
api = ContentTamerAPI()
config = {
    "input_dir": "./documents",
    "output_dir": "./organized",
    "organization_enabled": True,
    "ml_level": 2
}
result = api.process_documents(config)

# Using context manager
with ContentTamerSession(config) as session:
    result = session.process_documents()

# Async processing
async def process_async():
    api = ContentTamerAPI()
    result = await api.process_documents_async(
        config,
        progress_callback=lambda stage, current, total: print(f"{stage}: {current}/{total}")
    )
    return result
"""