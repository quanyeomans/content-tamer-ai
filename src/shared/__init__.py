"""
Shared Services Layer

Consolidated utilities and infrastructure services used across all domains.
Eliminates code duplication and provides consistent behavior.

Categories:
- File Operations: Safe file management, path validation, atomic operations
- Display Services: Unified Rich UI components and progress tracking
- Infrastructure: Configuration, dependency management, feature flags
"""

from .file_operations import SafeFileManager
from .display import UnifiedDisplayManager

# Infrastructure services to be implemented as needed
try:
    from .infrastructure import DependencyManager
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False

if INFRASTRUCTURE_AVAILABLE:
    __all__ = ['SafeFileManager', 'UnifiedDisplayManager', 'DependencyManager']
else:
    __all__ = ['SafeFileManager', 'UnifiedDisplayManager']
