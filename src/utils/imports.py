"""
Content Tamer AI - Import Management Utilities

Centralized import handling to eliminate try/except ImportError boilerplate.
"""

import os
import sys
from typing import Any, Dict, List


def safe_import_with_fallback(
    modules: List[str], fallback_path: str = None
) -> Dict[str, Any]:
    """
    Safely import modules with automatic fallback to parent directory.

    Args:
        modules: List of module names to import (e.g., ['utils.display_manager', 'ai_providers'])
        fallback_path: Custom fallback path, defaults to parent directory of calling file

    Returns:
        Dictionary mapping module names to imported modules

    Raises:
        ImportError: If modules cannot be imported even after fallback
    """
    imported_modules = {}

    # First, try normal imports
    try:
        for module_name in modules:
            imported_modules[module_name] = __import__(module_name, fromlist=[""])
        return imported_modules
    except ImportError:
        pass

    # Fallback: Add parent directory to path
    if fallback_path is None:
        # Get the calling file's directory and go up one level
        frame = sys._getframe(1)
        calling_file = frame.f_globals["__file__"]
        fallback_path = os.path.dirname(os.path.dirname(calling_file))

    sys.path.insert(0, fallback_path)

    try:
        for module_name in modules:
            imported_modules[module_name] = __import__(module_name, fromlist=[""])
        return imported_modules
    except ImportError as e:
        raise ImportError(
            f"Failed to import modules {modules} even with fallback path {fallback_path}: {e}"
        ) from e


def import_display_components():
    """
    Import display management components with fallback.

    Returns:
        Tuple of (DisplayManager, DisplayOptions)
    """
    modules = safe_import_with_fallback(
        ["utils.display_manager", "utils.error_handling"]
    )

    display_manager = modules["utils.display_manager"]
    error_handling = modules["utils.error_handling"]

    return (
        display_manager.DisplayManager,
        display_manager.DisplayOptions,
        error_handling.create_retry_handler,
    )


def import_core_components():
    """
    Import core application components with fallback.

    Returns:
        Tuple of (AIProviderFactory, ContentProcessorFactory, FileOrganizer)
    """
    modules = safe_import_with_fallback(
        ["ai_providers", "content_processors", "file_organizer"]
    )

    return (
        modules["ai_providers"].AIProviderFactory,
        modules["content_processors"].ContentProcessorFactory,
        modules["file_organizer"].FileOrganizer,
    )


def import_with_error_context(module_name: str, context: str = ""):
    """
    Import a single module with better error context.

    Args:
        module_name: Name of module to import
        context: Additional context for error messages

    Returns:
        The imported module

    Raises:
        ImportError: With enhanced error message including context
    """
    try:
        return __import__(module_name, fromlist=[""])
    except ImportError as e:
        error_msg = f"Failed to import {module_name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {e}"

        # Add helpful suggestions
        if "utils." in module_name:
            error_msg += ". Try ensuring all utils modules are properly installed."
        elif module_name in ["ai_providers", "content_processors", "file_organizer"]:
            error_msg += ". Try running from the project root directory."

        raise ImportError(error_msg) from e
