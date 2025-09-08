"""
Console Singleton Runtime Validation Tests

Validates that the Console singleton pattern is properly implemented
and enforced at runtime. These tests detect multiple Console instances
and verify proper dependency injection.

Part of the architectural quality gates to ensure Rich I/O conflicts
are eliminated through proper singleton usage.
"""

import gc
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Add src to path for testing
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, src_path)

from rich.console import Console

from core.application_container import ApplicationContainer, TestApplicationContainer
from utils.console_manager import ConsoleManager, create_test_console


class TestConsoleSingletonValidation(unittest.TestCase):
    """Runtime validation of Console singleton pattern."""

    def setUp(self):
        """Reset Console state before each test."""
        ConsoleManager.reset()
        gc.collect()  # Force garbage collection to clear old instances

    def tearDown(self):
        """Clean up after each test."""
        ConsoleManager.reset()
        gc.collect()

    def test_single_console_instance_enforcement(self):
        """Verify only one Console instance exists in memory after component creation."""
        # Create application components that would previously create multiple Consoles
        container = ApplicationContainer()
        display_manager = container.create_display_manager()

        # Force garbage collection to ensure accurate count
        gc.collect()

        # Count Console instances in memory
        console_instances = [
            obj for obj in gc.get_objects() if isinstance(obj, Console)
        ]

        self.assertEqual(
            len(console_instances),
            1,
            f"Found {len(console_instances)} Console instances in memory, expected exactly 1. "
            f"Multiple instances indicate singleton pattern violation.",
        )

        # Verify it's the same instance used throughout
        self.assertIs(
            container.console,
            display_manager.console,
            "Container and display manager should share the same Console instance",
        )

    def test_console_reference_consistency(self):
        """Ensure all components share the same Console instance."""
        container = ApplicationContainer()
        display_manager = container.create_display_manager()

        # All Console references should be identical objects (same memory address)
        self.assertIs(
            container.console,
            ConsoleManager.get_console(),
            "Container console should be identical to ConsoleManager singleton",
        )

        self.assertIs(
            display_manager.console,
            container.console,
            "Display manager console should be identical to container console",
        )

        self.assertIs(
            display_manager.cli.console,
            display_manager.console,
            "CLI display console should be identical to display manager console",
        )

        self.assertIs(
            display_manager.progress.console,
            display_manager.console,
            "Progress display console should be identical to display manager console",
        )

    def test_singleton_persistence_across_calls(self):
        """Verify singleton persists across multiple ConsoleManager calls."""
        # First call creates instance
        console1 = ConsoleManager.get_console()

        # Subsequent calls return same instance
        console2 = ConsoleManager.get_console()
        console3 = ConsoleManager.get_console(
            no_color=True
        )  # Different options ignored

        # All should be the exact same object
        self.assertIs(console1, console2)
        self.assertIs(console2, console3)

        # Memory verification
        gc.collect()
        console_instances = [
            obj for obj in gc.get_objects() if isinstance(obj, Console)
        ]
        self.assertEqual(len(console_instances), 1)

    def test_test_mode_isolation(self):
        """Verify test mode properly isolates Console instances."""
        # Create test container with StringIO
        test_container = TestApplicationContainer(capture_output=True)
        test_display_manager = test_container.create_display_manager()

        # Test output capture works
        test_display_manager.info("Test message")
        captured_output = test_container.get_captured_output()

        self.assertIn("Test message", captured_output)
        self.assertTrue(test_container.is_test_mode())

        # Verify test console is isolated
        test_console = test_container.console
        self.assertIsInstance(test_console.file, StringIO)

    def test_console_manager_thread_safety(self):
        """Verify Console singleton is thread-safe."""
        import threading
        import time

        console_instances = []

        def create_console():
            # Small delay to increase chance of race condition
            time.sleep(0.001)
            console = ConsoleManager.get_console()
            console_instances.append(console)

        # Create multiple threads trying to get Console simultaneously
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_console)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All threads should have received the same Console instance
        first_console = console_instances[0]
        for console in console_instances:
            self.assertIs(
                console,
                first_console,
                "Thread safety violation: different Console instances returned",
            )

    def test_application_container_singleton_usage(self):
        """Verify ApplicationContainer properly uses Console singleton."""
        # Create multiple containers
        container1 = ApplicationContainer()
        container2 = ApplicationContainer()

        # Both should share the same Console
        self.assertIs(
            container1.console,
            container2.console,
            "Multiple ApplicationContainers should share the same Console singleton",
        )

        # Display managers from different containers should share Console
        display1 = container1.create_display_manager()
        display2 = container2.create_display_manager()

        self.assertIs(
            display1.console,
            display2.console,
            "Display managers from different containers should share Console",
        )

    def test_console_configuration_consistency(self):
        """Verify Console configuration is applied consistently."""
        # Reset to ensure clean state
        ConsoleManager.reset()

        # Create Console with specific configuration
        console = ConsoleManager.get_console(no_color=True, width=100, safe_box=True)

        # Verify configuration applied
        config = ConsoleManager.get_console_config()
        self.assertTrue(config.get("no_color", False))

        # Width may be adjusted by Rich, so verify it's set to a reasonable value
        width = config.get("size", (0, 0))[1]
        self.assertGreater(width, 0, "Console width should be greater than 0")

        # Subsequent calls should return same configured instance
        console2 = ConsoleManager.get_console(
            no_color=False, width=50
        )  # Different config ignored
        self.assertIs(console, console2)

        # Configuration should remain from first creation
        config2 = ConsoleManager.get_console_config()
        self.assertEqual(config, config2)


class TestConsoleArchitectureCompliance(unittest.TestCase):
    """Verify architectural compliance of Console usage."""

    def setUp(self):
        """Reset state before each test."""
        ConsoleManager.reset()
        gc.collect()

    def tearDown(self):
        """Clean up after each test."""
        ConsoleManager.reset()
        gc.collect()

    def test_no_direct_console_creation_in_display_manager(self):
        """Ensure RichDisplayManager receives Console via injection."""
        from utils.rich_display_manager import RichDisplayOptions

        # Create display manager through container (proper DI)
        container = ApplicationContainer()
        display_manager = container.create_display_manager(
            RichDisplayOptions(quiet=True)
        )

        # Verify the injected Console is the singleton
        self.assertIs(
            display_manager.console,
            ConsoleManager.get_console(),
            "Display manager should use injected singleton Console",
        )

        # Verify no additional Console instances were created
        gc.collect()
        console_instances = [
            obj for obj in gc.get_objects() if isinstance(obj, Console)
        ]
        self.assertEqual(
            len(console_instances),
            1,
            f"Display manager creation resulted in {len(console_instances)} Console instances, expected 1",
        )

    def test_test_console_isolation_compliance(self):
        """Verify test Console instances don't interfere with singleton."""
        # Create test console
        test_console = create_test_console()

        # Create regular singleton console
        app_console = ConsoleManager.get_console()

        # They should be different instances
        self.assertIsNot(test_console, app_console)

        # Test console should have StringIO file
        self.assertIsInstance(test_console.file, StringIO)

        # App console should have different file
        self.assertNotIsInstance(app_console.file, StringIO)


if __name__ == "__main__":
    # Run validation tests
    unittest.main(verbosity=2)
