"""
Infrastructure Services

Core infrastructure components used across all domains:
- Dependency detection and management
- Directory utilities and configuration
- Feature flag control
- System configuration loading
- Security and error handling
- Hardware detection and model management
- Text and path utilities
"""

# Import migrated infrastructure components
try:
    from .dependency_manager import DependencyManager, get_dependency_manager
    DEPENDENCY_MANAGER_AVAILABLE = True
except ImportError:
    DEPENDENCY_MANAGER_AVAILABLE = False

try:
    from .directory_manager import (
        ensure_default_directories,
        setup_directories,
        get_api_details
    )
    DIRECTORY_MANAGER_AVAILABLE = True
except ImportError:
    DIRECTORY_MANAGER_AVAILABLE = False

try:
    from .filename_config import *
    FILENAME_CONFIG_AVAILABLE = True
except ImportError:
    FILENAME_CONFIG_AVAILABLE = False

try:
    from .security import *
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

try:
    from .error_handling import *
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False

try:
    from .feature_flags import *
    FEATURE_FLAGS_AVAILABLE = True
except ImportError:
    FEATURE_FLAGS_AVAILABLE = False

try:
    from .import_utilities import *
    IMPORT_UTILITIES_AVAILABLE = True
except ImportError:
    IMPORT_UTILITIES_AVAILABLE = False

try:
    from .path_utilities import *
    PATH_UTILITIES_AVAILABLE = True
except ImportError:
    PATH_UTILITIES_AVAILABLE = False

try:
    from .hardware_detector import *
    HARDWARE_DETECTOR_AVAILABLE = True
except ImportError:
    HARDWARE_DETECTOR_AVAILABLE = False

try:
    from .model_manager import *
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    MODEL_MANAGER_AVAILABLE = False

try:
    from .text_utilities import *
    TEXT_UTILITIES_AVAILABLE = True
except ImportError:
    TEXT_UTILITIES_AVAILABLE = False

# Export available components
available_exports = []

if DEPENDENCY_MANAGER_AVAILABLE:
    available_exports.extend(['DependencyManager', 'get_dependency_manager'])

if DIRECTORY_MANAGER_AVAILABLE:
    available_exports.extend(['ensure_default_directories', 'setup_directories', 'get_api_details'])

__all__ = available_exports
