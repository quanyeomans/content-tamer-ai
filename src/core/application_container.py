"""
Application Container - Dependency Injection Container

Provides centralized dependency management using dependency injection
principles. Acts as the composition root where all application
components are wired together with their dependencies.

This eliminates hard-coded dependencies and enables clean testing
through dependency substitution.
"""

import os
import sys
from typing import TYPE_CHECKING, Any, Dict, Optional

from rich.console import Console

if TYPE_CHECKING:
    from interfaces.human.interactive_cli import InteractiveCLI

# Import display components with fallback for path issues
try:
    from shared.display.console_manager import ConsoleManager, create_test_console
    from shared.display.rich_display_manager import RichDisplayManager, RichDisplayOptions
except ImportError:
    # Add src directory to path for absolute imports
    src_dir = os.path.dirname(os.path.dirname(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from shared.display.console_manager import ConsoleManager, create_test_console
    from shared.display.rich_display_manager import RichDisplayManager, RichDisplayOptions


class ApplicationContainer:
    """
    Dependency injection container for the application.

    Manages the creation and wiring of application components,
    ensuring proper dependency injection and single Console
    instance usage throughout the application.
    """

    def __init__(self, console: Optional[Console] = None, test_mode: bool = False):
        """
        Initialize the application container.

        Args:
            console: Optional Console instance (for testing)
            test_mode: Whether to configure for testing environment
        """
        self._test_mode = test_mode

        if console is not None:
            # Inject custom console (typically for testing)
            ConsoleManager.set_console_for_testing(console)
            self._console = console
        else:
            # Use singleton console manager
            self._console = ConsoleManager.get_console()

    @property
    def console(self) -> Console:
        """
        Get the managed Console instance.

        Returns:
            Console: The application's Console instance
        """
        return self._console

    def create_display_manager(
        self, options: Optional[RichDisplayOptions] = None
    ) -> RichDisplayManager:
        """
        Create a RichDisplayManager with injected dependencies.

        Args:
            options: Display configuration options

        Returns:
            RichDisplayManager: Configured display manager with injected Console
        """
        if options is None:
            options = RichDisplayOptions()

        # Inject the managed Console instance
        return RichDisplayManager(self._console, options)

    def create_cli_interface(self) -> "InteractiveCLI":
        """
        Create CLI interface with injected Console.

        Returns:
            InteractiveCLI: CLI interface with injected Console dependencies
        """
        # Import here to avoid circular dependencies
        try:
            from interfaces.human.interactive_cli import InteractiveCLI
        except ImportError:
            # Add src directory to path if not already done
            current_src_dir = os.path.dirname(os.path.dirname(__file__))
            if current_src_dir not in sys.path:
                sys.path.insert(0, current_src_dir)
            from interfaces.human.interactive_cli import InteractiveCLI

        return InteractiveCLI()

    def is_test_mode(self) -> bool:
        """
        Check if container is in test mode.

        Returns:
            bool: True if configured for testing
        """
        return self._test_mode or ConsoleManager.is_test_mode()

    def get_console_config(self) -> Dict[str, Any]:
        """
        Get current Console configuration.

        Returns:
            Dict[str, Any]: Console configuration details
        """
        return ConsoleManager.get_console_config()

    def create_content_service(
        self, ocr_lang: str = "eng", max_content_length: int = 2000
    ) -> Optional[Any]:
        """
        Create Content Domain service with dependencies.

        Args:
            ocr_lang: OCR language for content extraction
            max_content_length: Maximum content length for AI processing

        Returns:
            ContentService: Configured content service
        """
        # Import here to avoid circular dependencies
        try:
            from domains.content.content_service import ContentService

            return ContentService(ocr_lang, max_content_length)
        except ImportError:
            # Fallback for when domain services not available
            self._warn_about_missing_domain_services("content")
            return None

    def create_ai_integration_service(self, retry_config: Optional[Any] = None) -> Optional[Any]:
        """
        Create AI Integration Domain service with dependencies.

        Args:
            retry_config: Optional retry configuration for AI requests

        Returns:
            AIIntegrationService: Configured AI integration service
        """
        try:
            from domains.ai_integration.ai_integration_service import AIIntegrationService

            return AIIntegrationService(retry_config)
        except ImportError:
            self._warn_about_missing_domain_services("ai_integration")
            return None

    def create_organization_service(
        self, target_folder: str, clustering_config: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Create Organization Domain service with dependencies.

        Args:
            target_folder: Target folder for document organization
            clustering_config: Optional clustering configuration

        Returns:
            OrganizationService: Configured organization service
        """
        try:
            from domains.organization.organization_service import OrganizationService

            return OrganizationService(target_folder, clustering_config)
        except ImportError:
            self._warn_about_missing_domain_services("organization")
            return None

    def create_application_kernel(self) -> Optional[Any]:
        """
        Create application kernel with all domain services wired.

        Returns:
            ApplicationKernel: Main application orchestration component
        """
        try:
            from orchestration.application_kernel import ApplicationKernel

            return ApplicationKernel(self)
        except ImportError:
            # Fallback to legacy application setup
            self._warn_about_missing_domain_services("application_kernel")
            return None

    def _warn_about_missing_domain_services(self, service_name: str) -> None:
        """Warn about missing domain services."""
        import warnings

        warnings.warn(
            f"Domain service '{service_name}' not available. "
            "Using legacy implementation or falling back to limited functionality.",
            RuntimeWarning,
        )


class TestApplicationContainer(ApplicationContainer):
    """
    Application container optimized for testing.

    Pre-configured with StringIO Console and test-friendly settings
    to eliminate Rich I/O conflicts during test execution. Provides
    state isolation mechanisms for reliable test execution.
    """

    def __init__(self, capture_output: bool = True):
        """
        Initialize test container.

        Args:
            capture_output: Whether to capture Console output to StringIO
        """
        if capture_output:
            # Create test console with StringIO output
            import io

            self._output_capture = io.StringIO()
            test_console = create_test_console(self._output_capture)
        else:
            self._output_capture = None
            test_console = create_test_console()

        super().__init__(console=test_console, test_mode=True)

        # State management for test isolation
        self._cached_services = {}
        self._original_sys_path = None
        self._service_overrides = {}

    def get_captured_output(self) -> str:
        """
        Get captured Console output.

        Returns:
            str: All Console output captured during testing
        """
        if self._output_capture is None:
            return ""
        return self._output_capture.getvalue()

    def clear_output(self) -> None:
        """Clear captured output buffer."""
        if self._output_capture is not None:
            self._output_capture.seek(0)
            self._output_capture.truncate(0)

    def reset_state(self) -> None:
        """
        Reset container state for clean test isolation.

        Clears cached services, resets sys.path modifications,
        and ensures fresh state for next test execution.
        """
        # Clear cached services
        self._cached_services.clear()
        self._service_overrides.clear()

        # Reset Console Manager state
        ConsoleManager.reset()

        # Reset sys.path modifications if any were made
        if self._original_sys_path is not None:
            sys.path[:] = self._original_sys_path
            self._original_sys_path = None

        # Clear console output buffer
        self.clear_output()

        # Reset global container state
        global _global_container  # pylint: disable=global-statement
        _global_container = None

    def preserve_sys_path(self) -> None:
        """
        Preserve current sys.path for restoration during reset.

        Call this before making sys.path modifications that need
        to be cleaned up during state reset.
        """
        if self._original_sys_path is None:
            self._original_sys_path = sys.path.copy()

    def override_services(self, **service_overrides):
        """
        Context manager for temporary service overrides.

        Allows injecting mock or test services during test execution,
        automatically restoring original services when context exits.

        Args:
            **service_overrides: Services to override (service_name=mock_service)

        Returns:
            Context manager that handles service override/restore
        """
        return ServiceOverrideContext(self, service_overrides)

    def _apply_service_override(self, service_name: str, override_service: Any) -> None:
        """Apply a service override internally."""
        if service_name not in self._service_overrides:
            # Store original service for restoration
            original_method = getattr(self, f"create_{service_name}", None)
            self._service_overrides[service_name] = original_method

        # Set the override
        setattr(self, f"create_{service_name}", lambda *args, **kwargs: override_service)

    def _restore_service_override(self, service_name: str) -> None:
        """Restore a service from override internally."""
        if service_name in self._service_overrides:
            original_method = self._service_overrides.pop(service_name)
            if original_method is not None:
                setattr(self, f"create_{service_name}", original_method)
            else:
                # Remove the override method if no original existed
                if hasattr(self, f"create_{service_name}"):
                    delattr(self, f"create_{service_name}")


class ServiceOverrideContext:
    """
    Context manager for temporary service overrides in TestApplicationContainer.

    Automatically applies service overrides on entry and restores
    original services on exit, ensuring clean test isolation.
    """

    def __init__(self, container: TestApplicationContainer, overrides: Dict[str, Any]):
        """
        Initialize service override context.

        Args:
            container: TestApplicationContainer to manage overrides for
            overrides: Dictionary of service_name -> override_service mappings
        """
        self._container = container
        self._overrides = overrides
        self._applied_overrides = []

    def __enter__(self):
        """Apply service overrides."""
        for service_name, override_service in self._overrides.items():
            self._container._apply_service_override(service_name, override_service)
            self._applied_overrides.append(service_name)
        return self._container

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original services."""
        for service_name in reversed(self._applied_overrides):
            self._container._restore_service_override(service_name)
        self._applied_overrides.clear()


# Convenience functions for common usage patterns


def create_application_container(
    console: Optional[Console] = None,
) -> ApplicationContainer:
    """
    Create the main application container.

    Args:
        console: Optional Console instance for dependency injection

    Returns:
        ApplicationContainer: Configured application container
    """
    return ApplicationContainer(console)


def create_test_container(capture_output: bool = True, fresh_state: bool = False) -> TestApplicationContainer:
    """
    Create a test-optimized application container.

    Args:
        capture_output: Whether to capture Console output
        fresh_state: Whether to ensure completely fresh state

    Returns:
        TestApplicationContainer: Test-configured container
    """
    if fresh_state:
        # Reset any global state before creating container
        ConsoleManager.reset()
        reset_global_container()

    return TestApplicationContainer(capture_output)


def create_function_scoped_container(capture_output: bool = True) -> TestApplicationContainer:
    """
    Create a function-scoped test container with guaranteed state isolation.

    This function creates a fresh TestApplicationContainer with reset state,
    ensuring no contamination from previous tests. Use this for tests that
    need guaranteed isolation.

    Args:
        capture_output: Whether to capture Console output

    Returns:
        TestApplicationContainer: Fresh test container with isolated state
    """
    container = create_test_container(capture_output=capture_output, fresh_state=True)

    # Preserve sys.path for automatic cleanup
    container.preserve_sys_path()

    return container


# Global container instance for application-wide access
_global_container: Optional[ApplicationContainer] = None


def get_global_container() -> ApplicationContainer:
    """
    Get the global application container instance.

    Creates the container on first access using lazy initialization.

    Returns:
        ApplicationContainer: Global container instance
    """
    global _global_container  # pylint: disable=global-statement
    if _global_container is None:
        _global_container = ApplicationContainer()
    return _global_container


def set_global_container(container: ApplicationContainer) -> None:
    """
    Set the global application container.

    Used primarily for testing to inject test containers.

    Args:
        container: Container instance to use globally
    """
    global _global_container  # pylint: disable=global-statement
    _global_container = container


def reset_global_container() -> None:
    """
    Reset the global container instance.

    Forces recreation on next access. Used for testing
    and development scenarios.
    """
    global _global_container  # pylint: disable=global-statement
    _global_container = None
    ConsoleManager.reset()
