"""
Test that refactored RichConsoleManager maintains full backward compatibility.
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from interfaces.human.rich_console_manager_refactored import RichConsoleManager
from rich.console import Console


class TestRefactoredCompatibility(unittest.TestCase):
    """Test refactored manager maintains compatibility."""
    
    def setUp(self):
        """Reset singleton state for each test."""
        RichConsoleManager._instance = None
        RichConsoleManager._console = None
        RichConsoleManager._display_manager = None
    
    def test_singleton_preserved(self):
        """Test singleton pattern still works."""
        manager1 = RichConsoleManager()
        manager2 = RichConsoleManager()
        self.assertIs(manager1, manager2)
    
    def test_console_property_works(self):
        """Test console property is accessible."""
        manager = RichConsoleManager()
        console = manager.console
        self.assertIsNotNone(console)
        self.assertIsInstance(console, Console)
    
    def test_all_methods_exist(self):
        """Test all original methods still exist."""
        manager = RichConsoleManager()
        
        methods = [
            # Display methods
            'show_welcome_panel',
            'show_section_header',
            'show_info_panel',
            'show_error_panel',
            'show_success_panel',
            'show_configuration_table',
            'show_status',
            'show_loading',
            'create_progress_display',
            # Prompt methods
            'prompt_choice',
            'prompt_confirm',
            'prompt_text',
            # Utility methods
            'clear_screen',
            'print_separator',
            'get_terminal_size',
            'is_terminal_capable',
            'handle_error',
            # New delegated methods
            'info',
            'success',
            'warning',
            'error',
            'show_panel',
            'show_table',
            'start_progress',
            'update_progress',
            'finish_progress'
        ]
        
        for method_name in methods:
            self.assertTrue(
                hasattr(manager, method_name),
                f"Method {method_name} is missing"
            )
            self.assertTrue(
                callable(getattr(manager, method_name)),
                f"Method {method_name} is not callable"
            )
    
    def test_emoji_handler_accessible(self):
        """Test emoji handler is still accessible for backward compatibility."""
        manager = RichConsoleManager()
        _ = manager.console  # Initialize
        self.assertIsNotNone(manager._emoji_handler)
    
    def test_current_progress_attribute(self):
        """Test _current_progress attribute exists."""
        manager = RichConsoleManager()
        self.assertTrue(hasattr(manager, '_current_progress'))
    
    def test_display_manager_delegation(self):
        """Test that methods delegate to display manager."""
        manager = RichConsoleManager()
        
        # Create mock display manager
        mock_display = MagicMock()
        manager._display_manager = mock_display
        
        # Test delegation
        manager.info("test message")
        mock_display.info.assert_called_once_with("test message", None)
        
        manager.success("success")
        mock_display.success.assert_called_once_with("success", None)
        
        manager.warning("warning")
        mock_display.warning.assert_called_once_with("warning", None)
        
        manager.error("error")
        mock_display.error.assert_called_once_with("error", None, None)
    
    def test_progress_methods_work(self):
        """Test progress methods work correctly."""
        manager = RichConsoleManager()
        
        # Test create_progress_display (human-specific)
        progress = manager.create_progress_display("Testing")
        self.assertIsNotNone(progress)
        self.assertEqual(manager._current_progress, progress)
        
        # Test delegated progress methods
        mock_display = MagicMock()
        mock_display.start_progress.return_value = "task_0"
        manager._display_manager = mock_display
        
        progress_id = manager.start_progress("Processing")
        self.assertEqual(progress_id, "task_0")
        mock_display.start_progress.assert_called_once_with("Processing")
        
        manager.update_progress(progress_id, 50, 100)
        mock_display.update_progress.assert_called_once_with("task_0", 50, 100, None)
        
        manager.finish_progress(progress_id)
        mock_display.finish_progress.assert_called_once_with("task_0")
    
    def test_prompt_methods_work(self):
        """Test interactive prompt methods still work."""
        manager = RichConsoleManager()
        
        with patch('interfaces.human.rich_console_manager_refactored.Prompt') as mock_prompt:
            mock_prompt.ask.return_value = "choice1"
            result = manager.prompt_choice("Choose", ["choice1", "choice2"])
            self.assertEqual(result, "choice1")
        
        with patch('interfaces.human.rich_console_manager_refactored.Confirm') as mock_confirm:
            mock_confirm.ask.return_value = True
            result = manager.prompt_confirm("Confirm?")
            self.assertTrue(result)
    
    def test_configuration_table_formatting(self):
        """Test configuration table still formats correctly."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True, width=80)
        
        manager = RichConsoleManager()
        manager._console = test_console
        
        config = {
            "Input": "/path/to/input",
            "Output": "/path/to/output",
            "Enabled": True,
            "Disabled": False,
            "Not Set": None
        }
        
        manager.show_configuration_table(config, "Test Config")
        output_str = output.getvalue()
        
        # Check key elements are present
        self.assertIn("Test Config", output_str)
        self.assertIn("Input", output_str)
        self.assertIn("/path/to/input", output_str)
        # Boolean formatting
        self.assertIn("✓", output_str) or self.assertIn("Yes", output_str)
        self.assertIn("✗", output_str) or self.assertIn("No", output_str)
        self.assertIn("Not set", output_str)


class TestMethodSignatures(unittest.TestCase):
    """Test method signatures match original."""
    
    def test_show_status_signature(self):
        """Test show_status maintains signature."""
        manager = RichConsoleManager()
        mock_display = MagicMock()
        manager._display_manager = mock_display
        
        # Should accept message and status
        manager.show_status("message", "info")
        manager.show_status("message", "success")
        manager.show_status("message", "warning")
        manager.show_status("message", "error")
    
    def test_show_section_header_signature(self):
        """Test show_section_header maintains signature."""
        manager = RichConsoleManager()
        
        # Should accept title and optional description
        output = StringIO()
        manager._console = Console(file=output, force_terminal=True)
        
        manager.show_section_header("Title")
        manager.show_section_header("Title", "Description")
        
        output_str = output.getvalue()
        self.assertIn("Title", output_str)
    
    def test_handle_error_signature(self):
        """Test handle_error maintains signature."""
        manager = RichConsoleManager()
        mock_display = MagicMock()
        manager._display_manager = mock_display
        
        # Should accept exception and optional context
        error = ValueError("Test error")
        manager.handle_error(error)
        manager.handle_error(error, {"context": "configuration_wizard"})


if __name__ == '__main__':
    unittest.main()