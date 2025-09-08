"""
Application Container - Dependency Injection Container

Provides centralized dependency management using dependency injection
principles. Acts as the composition root where all application
components are wired together with their dependencies.

This eliminates hard-coded dependencies and enables clean testing
through dependency substitution.
"""

from typing import Any, Dict, Optional

from rich.console import Console

from utils.console_manager import ConsoleManager, create_test_console
from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions


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

    def create_cli_handler(self):
        """
        Create CLI command handlers with injected Console.

        Returns:
            CLIHandler: CLI handler with injected Console dependencies
        """
        # Import here to avoid circular dependencies
        from core.cli_handler import CLIHandler

        return CLIHandler(self._console)

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


class TestApplicationContainer(ApplicationContainer):
    """
    Application container optimized for testing.

    Pre-configured with StringIO Console and test-friendly settings
    to eliminate Rich I/O conflicts during test execution.
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


def create_test_container(capture_output: bool = True) -> TestApplicationContainer:
    """
    Create a test-optimized application container.

    Args:
        capture_output: Whether to capture Console output

    Returns:
        TestApplicationContainer: Test-configured container
    """
    return TestApplicationContainer(capture_output)


# Global container instance for application-wide access
_global_container: Optional[ApplicationContainer] = None


def get_global_container() -> ApplicationContainer:
    """
    Get the global application container instance.

    Creates the container on first access using lazy initialization.

    Returns:
        ApplicationContainer: Global container instance
    """
    global _global_container
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
    global _global_container
    _global_container = container


def reset_global_container() -> None:
    """
    Reset the global container instance.

    Forces recreation on next access. Used for testing
    and development scenarios.
    """
    global _global_container
    _global_container = None
    ConsoleManager.reset()
