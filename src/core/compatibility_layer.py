"""
Compatibility Layer for Rich Architecture Migration

Provides backward compatibility wrappers to maintain existing APIs
while migrating to the new dependency injection architecture.

This allows gradual migration without breaking existing code.
"""

import warnings
from typing import Any, Dict, Optional

from core.application_container import ApplicationContainer
from utils.console_manager import ConsoleManager
from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions


class LegacyDisplayManagerAdapter:
    """
    Adapter that provides the old RichDisplayManager interface
    while using the new dependency injection architecture internally.
    """

    def __init__(self, options: Optional[RichDisplayOptions] = None):
        """
        Initialize with legacy interface for backward compatibility.

        Args:
            options: Display configuration options (legacy format)
        """
        # Issue deprecation warning
        warnings.warn(
            "Direct RichDisplayManager instantiation is deprecated. "
            "Use ApplicationContainer.create_display_manager() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Use new architecture internally
        self._container = ApplicationContainer()
        self._manager = self._container.create_display_manager(options)

    def __getattr__(self, name):
        """Proxy all attribute access to the new display manager."""
        return getattr(self._manager, name)


def _setup_display_manager_legacy(
    display_options: Optional[Dict[str, Any]] = None,
) -> RichDisplayManager:
    """
    Legacy display manager setup function for backward compatibility.

    Args:
        display_options: Display configuration options (legacy dict format)

    Returns:
        RichDisplayManager: Display manager instance
    """
    display_opts = display_options or {}

    # Check if we're using the new architecture pattern
    if hasattr(_setup_display_manager_legacy, "_use_new_architecture"):
        # New architecture path
        container = ApplicationContainer()
        options = RichDisplayOptions(
            verbose=display_opts.get("verbose", False),
            quiet=display_opts.get("quiet", False),
            no_color=display_opts.get("no_color", False),
            show_stats=display_opts.get("show_stats", True),
        )
        return container.create_display_manager(options)
    else:
        # Legacy compatibility path
        options = RichDisplayOptions(
            verbose=display_opts.get("verbose", False),
            quiet=display_opts.get("quiet", False),
            no_color=display_opts.get("no_color", False),
            show_stats=display_opts.get("show_stats", True),
        )
        return LegacyDisplayManagerAdapter(options)


def enable_new_architecture():
    """
    Enable the new dependency injection architecture globally.

    This switches all legacy compatibility functions to use the
    new architecture internally.
    """
    _setup_display_manager_legacy._use_new_architecture = True


def disable_new_architecture():
    """
    Disable the new architecture and use legacy compatibility mode.

    Used for rollback scenarios or gradual migration.
    """
    if hasattr(_setup_display_manager_legacy, "_use_new_architecture"):
        delattr(_setup_display_manager_legacy, "_use_new_architecture")


# Backward compatibility aliases
def create_rich_display_manager(
    options: Optional[Dict[str, Any]] = None,
) -> RichDisplayManager:
    """
    Legacy function for creating display manager.

    Args:
        options: Display configuration options

    Returns:
        RichDisplayManager: Display manager instance
    """
    return _setup_display_manager_legacy(options)


class DisplayManagerFactory:
    """
    Factory for creating display managers with different patterns.

    Supports both legacy and new architecture patterns.
    """

    @staticmethod
    def create_legacy(options: Optional[Dict[str, Any]] = None) -> RichDisplayManager:
        """Create display manager using legacy pattern."""
        return _setup_display_manager_legacy(options)

    @staticmethod
    def create_with_container(
        container: ApplicationContainer, options: Optional[RichDisplayOptions] = None
    ) -> RichDisplayManager:
        """Create display manager using dependency injection."""
        return container.create_display_manager(options)

    @staticmethod
    def create_default(options: Optional[Dict[str, Any]] = None) -> RichDisplayManager:
        """Create display manager using current default pattern."""
        return _setup_display_manager_legacy(options)
