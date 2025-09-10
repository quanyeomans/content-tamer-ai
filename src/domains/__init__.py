"""
Domain Services Layer

Provides clean domain service boundaries following the persona-driven architecture:
- Content Domain: Document processing, extraction, and enhancement
- AI Integration Domain: Provider management, model selection, and API handling
- Organization Domain: Document clustering, folder management, and learning

Each domain contains:
- Service interfaces and implementations
- Domain-specific models and data structures
- Business logic isolated from interface concerns
"""

# Import main domain services
try:
    from .content.content_service import ContentService
except ImportError:
    ContentService = None

try:
    from .ai_integration.ai_integration_service import AIIntegrationService
except ImportError:
    AIIntegrationService = None

try:
    from .organization.organization_service import OrganizationService
except ImportError:
    OrganizationService = None

__all__ = ["ContentService", "AIIntegrationService", "OrganizationService"]
