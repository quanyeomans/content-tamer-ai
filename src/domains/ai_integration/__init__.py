"""
AI Integration Domain

Unified AI provider management, model selection, and request handling.
Consolidates scattered AI provider logic into clean domain services.

Services:
- ProviderService: Unified provider management and factory
- ModelService: Hardware detection and model selection
- RequestService: API calls, retry logic, and error handling
"""

from .provider_service import ProviderService
from .model_service import ModelService
from .request_service import RequestService
from .ai_integration_service import AIIntegrationService

__all__ = ["ProviderService", "ModelService", "RequestService", "AIIntegrationService"]
