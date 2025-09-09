"""
Mock Application Kernel for Library Interface

Provides fallback functionality when full kernel not available.
Used for testing and standalone library usage.
"""

from typing import Dict, Any, List
from ..base_interfaces import ProcessingResult


class MockApplicationKernel:
    """Mock kernel for testing and fallback scenarios."""

    def __init__(self):
        """Initialize mock kernel."""
        pass

    def execute_processing(self, config) -> ProcessingResult:
        """Mock processing execution."""
        return ProcessingResult(
            success=False,
            files_processed=0,
            files_failed=0,
            output_directory="",
            errors=["Mock kernel: Full application kernel not available"],
            warnings=["This is a mock implementation for testing only"],
            metadata={"mock": True, "kernel_type": "mock"}
        )

    def get_progress_status(self) -> Dict[str, Any]:
        """Return mock progress status."""
        return {
            "status": "mock",
            "current_task": "none",
            "progress": 0,
            "total": 0
        }

    def get_ai_providers(self) -> List[str]:
        """Get mock AI providers list."""
        return ["openai", "claude", "gemini", "deepseek", "local"]

    def get_provider_models(self, provider: str) -> List[str]:
        """Get mock models for provider."""
        model_map = {
            "openai": ["gpt-4o", "gpt-4o-mini"],
            "claude": ["claude-3.5-sonnet", "claude-3.5-haiku"],
            "gemini": ["gemini-2.0-flash", "gemini-1.5-pro"],
            "deepseek": ["deepseek-chat"],
            "local": ["llama3.2-3b", "gemma2:2b"]
        }
        return model_map.get(provider, [])

    def validate_provider_api_key(self, provider: str, api_key: str) -> bool:
        """Mock API key validation."""
        # Just check it's not empty for mock
        return bool(api_key and api_key.strip())