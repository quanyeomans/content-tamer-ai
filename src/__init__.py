"""
Content Tamer AI - Intelligent Document Organization

Originally based on sort-rename-move-pdf by munir-abbasi
(https://github.com/munir-abbasi/sort-rename-move-pdf)
Substantially modified and extended for multi-format content processing
and AI-powered document intelligence.

Transform digital chaos into organized, searchable assets.
AI-powered content analysis and filename generation for any document type.

Licensed under MIT License - see LICENSE file for details.
"""

__version__ = "2.0.0"
__author__ = "Content Tamer AI Project"

# Main entry point for persona-driven architecture
from .main import main

# Domain services for library usage
try:
    from .domains.content import ContentService
    from .domains.ai_integration import AIIntegrationService
    from .domains.organization import OrganizationService
    DOMAIN_SERVICES_AVAILABLE = True
except ImportError:
    DOMAIN_SERVICES_AVAILABLE = False

# Interface layer for programmatic access
try:
    from .interfaces.programmatic.library_interface import ContentTamerAPI
    LIBRARY_API_AVAILABLE = True
except ImportError:
    LIBRARY_API_AVAILABLE = False

__all__ = ["main"]

if DOMAIN_SERVICES_AVAILABLE:
    __all__.extend(["ContentService", "AIIntegrationService", "OrganizationService"])

if LIBRARY_API_AVAILABLE:
    __all__.extend(["ContentTamerAPI"])
