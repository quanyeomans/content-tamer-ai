"""
AI Integration Domain

Unified AI provider management, model selection, and request handling.
Consolidates scattered AI provider logic into clean domain services.

Services:
- ProviderService: Unified provider management and factory
- ModelService: Hardware detection and model selection
- RequestService: API calls, retry logic, and error handling
"""

from .ai_integration_service import AIIntegrationService
from .model_service import ModelService
from .provider_service import ProviderService
from .request_service import RequestService

__all__ = ["ProviderService", "ModelService", "RequestService", "AIIntegrationService"]
