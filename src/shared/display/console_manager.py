"""
Console Manager - Singleton Pattern for Rich Console Management

Provides a centralized, thread-safe Console instance management system
following Rich best practices for single Console instance usage.

This eliminates multiple Console() creations that conflict with pytest
and ensures consistent Rich configuration across the application.
"""

import io
import sys
import threading
from typing import Any, Dict, Optional, TextIO

from rich.console import Console


class ConsoleManager:
    """
    Singleton manager for Rich Console instances.

    Provides thread-safe access to a single Console instance throughout
    the application lifecycle, preventing Rich I/O conflicts and ensuring
    consistent configuration.
    """

    _instance: Optional[Console] = None
    _lock = threading.Lock()
    _test_mode = False

    @classmethod
    def get_console(cls, **console_options) -> Console:
        """
        Get the singleton Console instance.

        Creates the Console instance on first call with provided options.
        Subsequent calls return the same instance regardless of options.

        Args:
            **console_options: Configuration options for Console creation

        Returns:
            Console: The singleton Rich Console instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = cls._create_console(**console_options)

        return cls._instance

    @classmethod
    def set_console_for_testing(cls, console: Console) -> None:
        """
        Set a custom Console instance for testing.

        Used to inject StringIO-based Console instances during testing
        to capture output without I/O conflicts.

        Args:
            console: Custom Console instance for testing
        """
        with cls._lock:
            cls._instance = console
            cls._test_mode = True

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance.

        Used for testing and development to force Console recreation.
        Should not be used in production code.
        """
        with cls._lock:
            cls._instance = None
            cls._test_mode = False

    @classmethod
    def is_test_mode(cls) -> bool:
        """
        Check if Console is in test mode.

        Returns:
            bool: True if using test Console instance
        """
        return cls._test_mode

    @classmethod
    def _create_console(cls, **options) -> Console:
        """
        Create a Rich Console with optimal configuration.

        Applies Windows compatibility, UTF-8 encoding, and safe defaults
        based on application requirements.

        Args:
            **options: Console configuration options

        Returns:
            Console: Configured Rich Console instance
        """
        # Default configuration optimized for content-tamer-ai
        default_options = {
            "force_terminal": None,  # Let Rich auto-detect terminal capabilities
            "safe_box": True,  # Windows terminal compatibility
            "legacy_windows": False,  # Use modern Windows terminal features
            "no_color": options.get("no_color", False),
            "width": options.get("width", None),
        }

        # Handle file output with UTF-8 encoding for Windows
        output_file = options.get("file", sys.stdout)
        if (
            output_file == sys.stdout
            and hasattr(output_file, "buffer")
            and not hasattr(output_file, "_pytest_capture_wrapped")
        ):  # Avoid pytest conflicts
            try:
                # Wrap stdout with UTF-8 encoder for Windows compatibility
                output_file = io.TextIOWrapper(
                    output_file.buffer,
                    encoding="utf-8",
                    errors="replace",  # Replace non-encodable characters
                    newline="",
                    line_buffering=True,
                )
            except (ValueError, OSError):
                # If wrapping fails (e.g., in tests), use original stdout
                output_file = sys.stdout

        # Apply user-provided options, overriding defaults
        final_options = {**default_options, **options}
        final_options["file"] = output_file

        return Console(**final_options)

    @classmethod
    def get_console_config(cls) -> Dict[str, Any]:
        """
        Get current Console configuration.

        Returns:
            Dict[str, Any]: Console configuration parameters
        """
        if cls._instance is None:
            return {}

        return {
            "size": cls._instance.size,
            "is_terminal": cls._instance.is_terminal,
            "legacy_windows": cls._instance.legacy_windows,
            "no_color": getattr(cls._instance, "no_color", False),
            "force_terminal": getattr(cls._instance, "_force_terminal", False),
        }


def get_application_console(**options) -> Console:
    """
    Convenience function to get the application Console.

    Wrapper around ConsoleManager.get_console() for easier usage
    in application code.

    Args:
        **options: Console configuration options (only used on first call)

    Returns:
        Console: The singleton Console instance
    """
    return ConsoleManager.get_console(**options)


def create_test_console(output_file: Optional[TextIO] = None) -> Console:
    """
    Create a Console instance optimized for testing.

    Creates a Console with StringIO output and test-friendly configuration
    to avoid I/O conflicts with pytest.

    Args:
        output_file: Custom output file (defaults to StringIO)

    Returns:
        Console: Test-optimized Console instance
    """
    if output_file is None:
        output_file = io.StringIO()

    return Console(
        file=output_file,
        force_terminal=False,  # Disable terminal detection
        no_color=True,  # Consistent output for assertions
        width=80,  # Fixed width for predictable output
        safe_box=True,  # Maintain compatibility
        legacy_windows=False,  # Modern terminal features
    )
