"""
Regression tests to ensure singleton behavior is preserved during refactoring.
These tests are critical for maintaining backward compatibility.
"""

import os
import sys
import threading
import unittest
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from interfaces.human.rich_console_manager import RichConsoleManager


class TestSingletonRegression(unittest.TestCase):
    """Ensure singleton pattern is maintained through refactoring."""
    
    def setUp(self):
        """Reset singleton state for each test."""
        # Store original state
        self.original_instance = RichConsoleManager._instance
        self.original_console = RichConsoleManager._console
        
        # Reset for clean test
        RichConsoleManager._instance = None
        RichConsoleManager._console = None
    
    def tearDown(self):
        """Restore original state."""
        RichConsoleManager._instance = self.original_instance
        RichConsoleManager._console = self.original_console
    
    def test_singleton_instance_reuse(self):
        """Test that same instance is returned on multiple calls."""
        manager1 = RichConsoleManager()
        manager2 = RichConsoleManager()
        manager3 = RichConsoleManager()
        
        # All should be the same instance
        self.assertIs(manager1, manager2)
        self.assertIs(manager2, manager3)
        
        # Console should also be the same
        self.assertIs(manager1.console, manager2.console)
        self.assertIs(manager2.console, manager3.console)
    
    def test_singleton_thread_safety(self):
        """Test that singleton is thread-safe."""
        managers = []
        barrier = threading.Barrier(10)
        
        def create_manager():
            barrier.wait()  # Ensure all threads start at same time
            managers.append(RichConsoleManager())
        
        threads = [threading.Thread(target=create_manager) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should be the same instance despite concurrent creation
        first = managers[0]
        for manager in managers[1:]:
            self.assertIs(manager, first)
    
    def test_singleton_console_persistence(self):
        """Test that console is created once and persisted."""
        manager1 = RichConsoleManager()
        console1 = manager1.console
        
        # Create new manager instance reference
        manager2 = RichConsoleManager()
        console2 = manager2.console
        
        # Console should be the exact same object
        self.assertIs(console1, console2)
        
        # Verify it's not recreated on access
        console3 = manager1.console
        self.assertIs(console1, console3)
    
    def test_singleton_initialization_once(self):
        """Test that __init__ only runs initialization once."""
        with patch.object(RichConsoleManager, '_create_console') as mock_create:
            mock_console = MagicMock()
            mock_create.return_value = mock_console
            
            # Create multiple instances
            manager1 = RichConsoleManager()
            manager2 = RichConsoleManager()
            manager3 = RichConsoleManager()
            
            # Access console to trigger creation
            _ = manager1.console
            
            # _create_console should only be called once even with multiple accesses
            _ = manager2.console
            _ = manager3.console
            
            mock_create.assert_called_once()
    
    def test_singleton_attributes_shared(self):
        """Test that attributes are shared across instances."""
        manager1 = RichConsoleManager()
        manager2 = RichConsoleManager()
        
        # Set an attribute on one instance
        manager1._test_attribute = "test_value"
        
        # Should be accessible from other instance
        self.assertEqual(manager2._test_attribute, "test_value")
    
    def test_singleton_methods_consistent(self):
        """Test that methods operate on same underlying data."""
        manager1 = RichConsoleManager()
        manager2 = RichConsoleManager()
        
        # Trigger console creation to initialize emoji handler
        _ = manager1.console
        
        # Both should have the same emoji handler
        self.assertIs(manager1._emoji_handler, manager2._emoji_handler)
        
        # Both should have the same current progress
        manager1._current_progress = "test_progress"
        self.assertEqual(manager2._current_progress, "test_progress")


class TestSingletonEdgeCases(unittest.TestCase):
    """Test edge cases for singleton pattern."""
    
    def setUp(self):
        """Reset singleton state."""
        self.original_instance = RichConsoleManager._instance
        self.original_console = RichConsoleManager._console
        RichConsoleManager._instance = None
        RichConsoleManager._console = None
    
    def tearDown(self):
        """Restore original state."""
        RichConsoleManager._instance = self.original_instance
        RichConsoleManager._console = self.original_console
    
    def test_singleton_with_console_error(self):
        """Test singleton behavior when console creation fails."""
        with patch.object(RichConsoleManager, '_create_console') as mock_create:
            mock_create.side_effect = Exception("Console creation failed")
            
            # First instance should raise
            with self.assertRaises(Exception):
                manager1 = RichConsoleManager()
                _ = manager1.console
            
            # Reset and try again
            RichConsoleManager._instance = None
            RichConsoleManager._console = None
            mock_create.side_effect = None
            mock_create.return_value = MagicMock()
            
            # Should work after error is fixed
            manager2 = RichConsoleManager()
            console = manager2.console
            self.assertIsNotNone(console)
    
    def test_singleton_import_consistency(self):
        """Test that singleton is consistent across imports."""
        # Import in different ways
        from interfaces.human.rich_console_manager import RichConsoleManager as RCM1
        from interfaces.human import rich_console_manager
        RCM2 = rich_console_manager.RichConsoleManager
        
        # Create instances
        manager1 = RCM1()
        manager2 = RCM2()
        
        # Should be the same instance
        self.assertIs(manager1, manager2)


class TestFutureCompatibility(unittest.TestCase):
    """Tests to ensure future refactoring maintains compatibility."""
    
    def test_required_methods_exist(self):
        """Test that all required methods exist for compatibility."""
        manager = RichConsoleManager()
        
        # Display methods
        required_methods = [
            'show_welcome_panel',
            'show_section_header',
            'show_info_panel',
            'show_error_panel',
            'show_success_panel',
            'show_configuration_table',
            'show_status',
            'show_loading',
            'create_progress_display',
            'prompt_choice',
            'prompt_confirm',
            'prompt_text',
            'clear_screen',
            'print_separator',
            'get_terminal_size',
            'is_terminal_capable',
            'handle_error'
        ]
        
        for method_name in required_methods:
            self.assertTrue(
                hasattr(manager, method_name),
                f"Required method {method_name} is missing"
            )
            self.assertTrue(
                callable(getattr(manager, method_name)),
                f"Required method {method_name} is not callable"
            )
    
    def test_console_property_exists(self):
        """Test that console property is accessible."""
        manager = RichConsoleManager()
        
        # Should have console property
        self.assertTrue(hasattr(manager, 'console'))
        
        # Should be accessible without error
        console = manager.console
        self.assertIsNotNone(console)
    
    def test_emoji_handler_exists(self):
        """Test that emoji handler is available."""
        manager = RichConsoleManager()
        _ = manager.console  # Trigger initialization
        
        # Should have emoji handler
        self.assertTrue(hasattr(manager, '_emoji_handler'))
        self.assertIsNotNone(manager._emoji_handler)


if __name__ == '__main__':
    unittest.main()