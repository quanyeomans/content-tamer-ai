"""
Integration tests to capture current display manager behavior.
These tests ensure we don't break existing functionality during refactoring.
"""

import os
import sys
import threading
import unittest
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from interfaces.human.rich_console_manager import RichConsoleManager
from shared.display.unified_display_manager import UnifiedDisplayManager
from rich.console import Console


class TestCurrentDisplayBehavior(unittest.TestCase):
    """Capture current behavior of both display managers for regression testing."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create string buffer for console output
        self.console_output = StringIO()
        self.test_console = Console(file=self.console_output, force_terminal=True, width=80)
    
    def tearDown(self):
        """Clean up after tests."""
        self.console_output.close()
    
    def get_output(self):
        """Get console output as string."""
        return self.console_output.getvalue()
    
    def clear_output(self):
        """Clear console output buffer."""
        self.console_output.truncate(0)
        self.console_output.seek(0)


class TestRichConsoleManagerBehavior(TestCurrentDisplayBehavior):
    """Test current RichConsoleManager behavior."""
    
    def test_singleton_pattern(self):
        """Test that RichConsoleManager maintains singleton pattern."""
        manager1 = RichConsoleManager()
        manager2 = RichConsoleManager()
        
        # Should be the same instance
        self.assertIs(manager1, manager2)
        
        # Console should be the same
        self.assertIs(manager1.console, manager2.console)
    
    def test_thread_safety(self):
        """Test that singleton is thread-safe."""
        managers = []
        
        def create_manager():
            managers.append(RichConsoleManager())
        
        threads = [threading.Thread(target=create_manager) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should be the same instance
        first = managers[0]
        for manager in managers[1:]:
            self.assertIs(manager, first)
    
    def test_console_creation_with_theme(self):
        """Test that RichConsoleManager creates console with theme."""
        # Reset singleton for this test
        original_instance = RichConsoleManager._instance
        original_console = RichConsoleManager._console
        try:
            RichConsoleManager._instance = None
            RichConsoleManager._console = None
            
            manager = RichConsoleManager()
            console = manager.console
            
            # Console should exist and have emoji handler
            self.assertIsNotNone(console)
            self.assertTrue(hasattr(manager, '_emoji_handler'))
        finally:
            # Restore singleton state
            RichConsoleManager._instance = original_instance
            RichConsoleManager._console = original_console
    
    def test_show_methods_exist(self):
        """Test that all show methods exist and are callable."""
        manager = RichConsoleManager()
        
        # Test all display methods exist
        methods = [
            'show_welcome_panel',
            'show_section_header', 
            'show_info_panel',
            'show_error_panel',
            'show_success_panel',
            'show_configuration_table',
            'show_status',
            'show_loading'
        ]
        
        for method_name in methods:
            self.assertTrue(hasattr(manager, method_name))
            method = getattr(manager, method_name)
            self.assertTrue(callable(method))
    
    def test_prompt_methods_exist(self):
        """Test that all prompt methods exist."""
        manager = RichConsoleManager()
        
        methods = [
            'prompt_choice',
            'prompt_confirm',
            'prompt_text'
        ]
        
        for method_name in methods:
            self.assertTrue(hasattr(manager, method_name))
            method = getattr(manager, method_name)
            self.assertTrue(callable(method))
    
    def test_progress_creation(self):
        """Test progress display creation."""
        manager = RichConsoleManager()
        
        # Should have create_progress_display method
        self.assertTrue(hasattr(manager, 'create_progress_display'))
        
        # Create progress should return Progress object
        with patch('interfaces.human.rich_console_manager.Progress') as mock_progress_class:
            mock_progress = Mock()
            mock_progress_class.return_value = mock_progress
            
            progress = manager.create_progress_display("Test")
            
            # Should create Progress with correct parameters
            mock_progress_class.assert_called_once()
            
            # Should store as current progress
            self.assertIs(manager._current_progress, mock_progress)


class TestUnifiedDisplayManagerBehavior(TestCurrentDisplayBehavior):
    """Test current UnifiedDisplayManager behavior."""
    
    def test_not_singleton(self):
        """Test that UnifiedDisplayManager is NOT a singleton."""
        manager1 = UnifiedDisplayManager()
        manager2 = UnifiedDisplayManager()
        
        # Should be different instances
        self.assertIsNot(manager1, manager2)
    
    def test_console_optional(self):
        """Test that console parameter is optional."""
        # Should work without console parameter
        manager1 = UnifiedDisplayManager()
        self.assertIsNotNone(manager1.console)
        
        # Should accept console parameter
        custom_console = Console(file=StringIO())
        manager2 = UnifiedDisplayManager(console=custom_console)
        self.assertIs(manager2.console, custom_console)
    
    def test_quiet_mode(self):
        """Test quiet mode behavior."""
        manager = UnifiedDisplayManager(console=self.test_console, quiet_mode=True)
        
        # Test info, success, warning in quiet mode
        manager.info("Test message")
        manager.success("Success message")  
        manager.warning("Warning message")
        manager.error("Error message")
        
        output = self.get_output()
        # Document actual behavior: ALL messages still appear in quiet mode for these methods
        # This is important - quiet mode only affects certain display operations like panels/tables
        self.assertIn("Warning message", output)
        self.assertIn("Success message", output) 
        self.assertIn("Error message", output)
        
        # Info is actually suppressed in quiet mode
        self.assertNotIn("Test message", output)
    
    def test_message_methods_exist(self):
        """Test that all message methods exist."""
        manager = UnifiedDisplayManager()
        
        methods = [
            'info',
            'success',
            'warning',
            'error',
            'show_panel',
            'show_table'
        ]
        
        for method_name in methods:
            self.assertTrue(hasattr(manager, method_name))
            method = getattr(manager, method_name)
            self.assertTrue(callable(method))
    
    def test_progress_methods_exist(self):
        """Test that progress methods exist."""
        manager = UnifiedDisplayManager()
        
        methods = [
            'start_progress',
            'update_progress',
            'finish_progress'
        ]
        
        for method_name in methods:
            self.assertTrue(hasattr(manager, method_name))
            method = getattr(manager, method_name)
            self.assertTrue(callable(method))
    
    def test_progress_lifecycle(self):
        """Test progress creation and management."""
        manager = UnifiedDisplayManager(console=self.test_console)
        
        # Start progress
        progress_id = manager.start_progress("Test Progress")
        self.assertIsNotNone(progress_id)
        self.assertIsInstance(progress_id, str)
        
        # After starting, active progress should exist
        self.assertIsNotNone(manager._active_progress)
        
        # Update progress
        manager.update_progress(progress_id, 50, 100, "Half way")
        
        # Progress task should be tracked
        self.assertIn(progress_id, manager._progress_tasks)
        
        # Finish progress - this stops and clears the progress
        manager.finish_progress(progress_id)
        
        # After finishing, active progress is cleared
        # This is the actual behavior - document it
        self.assertIsNone(manager._active_progress)


class TestDisplayManagerInteraction(TestCurrentDisplayBehavior):
    """Test how the two managers interact when used together."""
    
    def test_interactive_cli_usage_pattern(self):
        """Test the pattern used in interactive_cli.py."""
        # This is how interactive_cli.py uses both managers
        console_manager = RichConsoleManager()
        display_manager = UnifiedDisplayManager(console=console_manager.console)
        
        # Both should share the same console
        self.assertIs(display_manager.console, console_manager.console)
    
    def test_console_consistency(self):
        """Test that console output is consistent between managers."""
        # Create managers with same console
        console_manager = RichConsoleManager()
        
        with patch.object(console_manager, '_console', self.test_console):
            display_manager = UnifiedDisplayManager(console=self.test_console)
            
            # Test similar operations produce similar output
            console_manager.show_status("Test message", "info")
            output1 = self.get_output()
            self.clear_output()
            
            display_manager.info("Test message")
            output2 = self.get_output()
            
            # Both should produce output (exact format may differ)
            self.assertTrue(len(output1) > 0)
            self.assertTrue(len(output2) > 0)


class TestMethodSignatures(unittest.TestCase):
    """Test and document method signatures for compatibility."""
    
    def test_rich_console_manager_signatures(self):
        """Document RichConsoleManager method signatures."""
        manager = RichConsoleManager()
        
        # Document signatures for critical methods
        signatures = {
            'show_section_header': ['title', 'description'],
            'show_error_panel': ['title', 'error', 'suggestions'],
            'show_success_panel': ['title', 'message', 'details'],
            'show_configuration_table': ['config_dict', 'title'],
            'prompt_choice': ['message', 'choices', 'default'],
            'prompt_confirm': ['message', 'default'],
            'show_status': ['message', 'status'],
        }
        
        for method_name, expected_params in signatures.items():
            method = getattr(manager, method_name)
            # This documents what parameters each method expects
            self.assertTrue(callable(method))
    
    def test_unified_display_manager_signatures(self):
        """Document UnifiedDisplayManager method signatures."""
        manager = UnifiedDisplayManager()
        
        signatures = {
            'info': ['message', 'context'],
            'success': ['message', 'context'],
            'warning': ['message', 'context'],
            'error': ['message', 'suggestions', 'context'],
            'start_progress': ['description'],
            'update_progress': ['progress_id', 'current', 'total', 'description'],
            'finish_progress': ['progress_id'],
        }
        
        for method_name, expected_params in signatures.items():
            method = getattr(manager, method_name)
            self.assertTrue(callable(method))


if __name__ == '__main__':
    unittest.main()