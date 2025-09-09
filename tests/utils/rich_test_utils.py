"""
Rich Testing Utilities - Test-friendly Rich Console patterns

Provides utilities for testing Rich-powered components without I/O conflicts.
Follows Rich testing best practices with StringIO capture and proper isolation.
"""

import os
import sys
from io import StringIO
from typing import Optional, TextIO, TYPE_CHECKING
from rich.console import Console

# Ensure src directory is in path for imports
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import with proper error handling
try:
    from core.application_container import ApplicationContainer
    from shared.display.console_manager import ConsoleManager
    from shared.display.rich_display_manager import RichDisplayManager, RichDisplayOptions
except ImportError as e:
    raise ImportError("Unable to import required modules from src/: {e}") from e

# Python 3.8 compatible typing
if TYPE_CHECKING:
    from typing import List
else:
    try:
        from typing import List
    except ImportError:
        List = list

def create_test_console() -> Console:
    """
    Create test-friendly Console with StringIO capture.

    Returns:
        Console: Rich Console configured for testing with output capture
    """
    test_output = StringIO()
    return Console(
        file=test_output,
        force_terminal=False,
        width=80,
        height=24,
        legacy_windows=False,
        safe_box=True,
        highlight=False,  # Disable highlighting for consistent test output
        log_time=False,   # Disable timestamps for predictable output
        log_path=False,   # Disable paths for cleaner output
    )

def create_test_container(console: Optional[Console] = None) -> ApplicationContainer:
    """
    Create ApplicationContainer with test console.

    Args:
        console: Optional Console instance. If None, creates test console

    Returns:
        ApplicationContainer: Container configured for testing
    """
    test_console = console or create_test_console()
    return ApplicationContainer(console=test_console, test_mode=True)

def capture_console_output(console: Console) -> str:
    """
    Extract captured output from test console.

    Args:
        console: Console instance with StringIO file

    Returns:
        str: Captured console output, empty string if not capturable
    """
    if hasattr(console.file, 'getvalue') and callable(getattr(console.file, 'getvalue')):
        file_io = console.file
        if isinstance(file_io, StringIO):
            return file_io.getvalue()
        # For other IO types with getvalue method
        return str(getattr(file_io, 'getvalue')())
    return ""

def reset_console_manager():
    """
    Reset ConsoleManager singleton for test isolation.

    Call this in test tearDown to prevent test interference.
    """
    ConsoleManager.reset()

class RichTestCase:
    """
    Mixin class with Rich testing utilities.

    Provides standardized Rich testing patterns and utilities.
    Use as a mixin with unittest.TestCase.

    Usage:
        class TestMyComponent(unittest.TestCase, RichTestCase):
            def setUp(self):
                super().setUp()  # Calls TestCase.setUp() first
                RichTestCase.setUp(self)  # Then initialize Rich testing
    """

    def setUp(self):
        """Set up test environment with Rich testing patterns."""
        # Reset any existing console manager state
        reset_console_manager()

        # Create test console and container
        self.test_console = create_test_console()
        self.test_container = create_test_container(self.test_console)

        # Create default display manager for testing
        from typing import cast
        self.display_options = RichDisplayOptions(
            verbose=False,
            quiet=False,
            no_color=True,  # Ensure consistent output for testing
            show_stats=False,  # Disable stats for cleaner test output
            file=cast(TextIO, self.test_console.file),
            width=80
        )
        self.display_manager = self.test_container.create_display_manager(self.display_options)

    def tearDown(self):
        """Clean up test environment."""
        # Ensure console file is properly closed to prevent pytest capture conflicts
        if hasattr(self, 'test_console') and hasattr(self.test_console, 'file'):
            try:
                if hasattr(self.test_console.file, 'close') and not self.test_console.file.closed:
                    self.test_console.file.close()
            except (AttributeError, ValueError):
                pass  # File already closed or doesn't support close

        # Reset console manager to prevent test interference
        reset_console_manager()

    def get_console_output(self) -> str:
        """
        Get captured console output.

        Returns:
            str: All console output captured during test
        """
        return capture_console_output(self.test_console)

    def clear_console_output(self):
        """Clear the console output buffer."""
        if hasattr(self.test_console.file, 'seek') and hasattr(self.test_console.file, 'truncate'):
            self.test_console.file.seek(0)
            self.test_console.file.truncate(0)

    def create_display_manager(self, options: Optional[RichDisplayOptions] = None) -> RichDisplayManager:
        """
        Create a display manager for testing.

        Args:
            options: Display options. If None, uses default test options

        Returns:
            RichDisplayManager: Display manager configured for testing
        """
        if options is None:
            options = self.display_options
        return self.test_container.create_display_manager(options)

    def assert_no_rich_rendering_errors(self):
        """Assert that no Rich rendering errors occurred during testing."""
        output = self.get_console_output()

        # Check for common Rich error patterns
        error_patterns = [
            "traceback",
            "exception",
            "error:",
            "failed to render",
            "rich rendering error",
            "markup error"
        ]

        for pattern in error_patterns:
            self.assertNotIn(
                pattern.lower(),
                output.lower(),
                f"Rich rendering error detected: '{pattern}' found in output"
            )

    def assert_console_contains(self, text: str, msg: Optional[str] = None):
        """
        Assert that console output contains specific text.

        Args:
            text: Text that should be in console output
            msg: Optional custom assertion message
        """
        output = self.get_console_output()
        if text not in output:
            error_msg = "Console output does not contain '{text}'"
            if msg:
                error_msg = "{msg}: {error_msg}"
            error_msg += "\nActual output: {repr(output)}"
            raise AssertionError(error_msg)

    def assert_console_not_contains(self, text: str, msg: Optional[str] = None):
        """
        Assert that console output does not contain specific text.

        Args:
            text: Text that should NOT be in console output
            msg: Optional custom assertion message
        """
        output = self.get_console_output()
        if text in output:
            error_msg = "Console output unexpectedly contains '{text}'"
            if msg:
                error_msg = "{msg}: {error_msg}"
            error_msg += "\nActual output: {repr(output)}"
            raise AssertionError(error_msg)

    def assert_console_empty(self, msg: Optional[str] = None):
        """
        Assert that console output is empty.

        Args:
            msg: Optional custom assertion message
        """
        output = self.get_console_output()
        if output.strip():
            error_msg = "Console output is not empty"
            if msg:
                error_msg = "{msg}: {error_msg}"
            error_msg += "\nActual output: {repr(output)}"
            raise AssertionError(error_msg)

    def get_console_lines(self) -> "List[str]":
        """
        Get console output as list of lines.

        Returns:
            List[str]: Console output split into lines, empty lines removed
        """
        output = self.get_console_output()
        return [line.strip() for line in output.split('\n') if line.strip()]

    def assert_no_rich_io_errors(self) -> None:
        """Assert that no Rich I/O errors occurred in console output."""
        output = self.get_console_output()
        error_patterns = [
            "I/O operation on closed file",
            "ValueError: I/O",
            "Rich console error",
            "AttributeError: 'NoneType'"
        ]

        for error_pattern in error_patterns:
            if error_pattern in output:
                raise AssertionError("Rich I/O error detected: {error_pattern}")

class MockApplicationContainer(ApplicationContainer):
    """
    Mock ApplicationContainer for advanced testing scenarios.

    Allows injection of mock components for isolated testing.
    """

    def __init__(self, console: Optional[Console] = None, **mock_components):
        """
        Initialize mock container.

        Args:
            console: Test console instance
            **mock_components: Mock components to inject
        """
        super().__init__(console=console or create_test_console(), test_mode=True)
        self._mock_components = mock_components

    def create_display_manager(self, options: Optional[RichDisplayOptions] = None) -> RichDisplayManager:
        """Create display manager, using mock if provided."""
        if 'display_manager' in self._mock_components:
            return self._mock_components['display_manager']
        return super().create_display_manager(options)

def with_test_console(test_func):
    """
    Decorator to inject test console into test function.

    Usage:
        @with_test_console
        def test_something(self, test_console):
            # test_console is pre-configured test Console
            pass
    """
    def wrapper(*args, **kwargs):
        test_console = create_test_console()
        return test_func(*args, test_console=test_console, **kwargs)
    return wrapper

def assert_rich_output_equals(expected: str, console: Console):
    """
    Assert Rich console output matches expected string exactly.

    Args:
        expected: Expected console output
        console: Console instance to check
    """
    actual = capture_console_output(console)
    if actual != expected:
        raise AssertionError(
            "Rich output mismatch:\n"
            "Expected: {repr(expected)}\n"
            "Actual:   {repr(actual)}"
        )

# Convenience aliases for common testing patterns
TestConsole = create_test_console
TestContainer = create_test_container
