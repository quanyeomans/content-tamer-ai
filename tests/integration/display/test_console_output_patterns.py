"""
Tests to document and preserve console output patterns.
These ensure refactoring doesn't change user-visible output.
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from interfaces.human.rich_console_manager import RichConsoleManager
from shared.display.unified_display_manager import UnifiedDisplayManager
from rich.console import Console


class TestConsoleOutputPatterns(unittest.TestCase):
    """Document and test console output patterns."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.console_output = StringIO()
        self.test_console = Console(
            file=self.console_output, 
            force_terminal=True, 
            width=80,
            legacy_windows=False,  # Force consistent output
            color_system="standard"
        )
    
    def get_output(self):
        """Get console output as string."""
        return self.console_output.getvalue()
    
    def clear_output(self):
        """Clear console output buffer."""
        self.console_output.truncate(0)
        self.console_output.seek(0)


class TestRichConsoleManagerOutput(TestConsoleOutputPatterns):
    """Test RichConsoleManager output patterns."""
    
    def setUp(self):
        super().setUp()
        # Patch the console creation to use our test console
        self.patcher = patch.object(RichConsoleManager, '_create_console', return_value=self.test_console)
        self.patcher.start()
        self.manager = RichConsoleManager()
    
    def tearDown(self):
        self.patcher.stop()
        super().tearDown()
    
    def test_show_status_output(self):
        """Document show_status output format."""
        test_cases = [
            ("info", "Information message", "ℹ️"),
            ("success", "Success message", "✅"),
            ("warning", "Warning message", "⚠️"),
            ("error", "Error message", "❌"),
        ]
        
        for status, message, expected_emoji in test_cases:
            self.clear_output()
            self.manager.show_status(message, status)
            output = self.get_output()
            
            # Document the output pattern
            self.assertIn(message, output)
            # Note: emoji might be ASCII fallback on Windows
    
    def test_show_section_header_output(self):
        """Document section header output format."""
        self.manager.show_section_header("Test Section", "This is a description")
        output = self.get_output()
        
        # Should contain both title and description
        self.assertIn("Test Section", output)
        self.assertIn("This is a description", output)
    
    def test_show_error_panel_output(self):
        """Document error panel output format."""
        self.manager.show_error_panel(
            title="Test Error",
            error="Something went wrong",
            suggestions=["Try this", "Or try that"]
        )
        output = self.get_output()
        
        # Should contain title, error, and suggestions
        self.assertIn("Test Error", output)
        self.assertIn("Something went wrong", output)
        self.assertIn("Try this", output)
        self.assertIn("Or try that", output)
    
    def test_show_configuration_table_output(self):
        """Document configuration table output format."""
        config = {
            "Input": "/path/to/input",
            "Output": "/path/to/output",
            "Provider": "local"
        }
        
        self.manager.show_configuration_table(config, "Test Configuration")
        output = self.get_output()
        
        # Should contain title and all config items
        self.assertIn("Test Configuration", output)
        self.assertIn("Input", output)
        self.assertIn("/path/to/input", output)
        self.assertIn("Provider", output)
        self.assertIn("local", output)


class TestUnifiedDisplayManagerOutput(TestConsoleOutputPatterns):
    """Test UnifiedDisplayManager output patterns."""
    
    def setUp(self):
        super().setUp()
        self.manager = UnifiedDisplayManager(console=self.test_console, quiet_mode=False)
    
    def test_message_output_patterns(self):
        """Document message output patterns."""
        test_cases = [
            ("info", "Info message", "ℹ️"),
            ("success", "Success message", "✅"),
            ("warning", "Warning message", "⚠️"),
            ("error", "Error message", "❌"),
        ]
        
        for method_name, message, expected_emoji in test_cases:
            self.clear_output()
            method = getattr(self.manager, method_name)
            
            if method_name == "error":
                method(message)
            else:
                method(message)
            
            output = self.get_output()
            self.assertIn(message, output)
    
    def test_show_panel_output(self):
        """Document panel output format."""
        self.manager.show_panel("Test Panel", "Panel content here", "blue")
        output = self.get_output()
        
        # Should contain title and content
        self.assertIn("Test Panel", output)
        self.assertIn("Panel content here", output)
    
    def test_show_table_output(self):
        """Document table output format."""
        self.manager.show_table(
            title="Test Table",
            headers=["Column 1", "Column 2"],
            rows=[["Value 1", "Value 2"], ["Value 3", "Value 4"]],
            style="blue"
        )
        output = self.get_output()
        
        # Should contain title, headers, and values
        self.assertIn("Test Table", output)
        self.assertIn("Column 1", output)
        self.assertIn("Column 2", output)
        self.assertIn("Value 1", output)
        self.assertIn("Value 4", output)


class TestOutputCompatibility(TestConsoleOutputPatterns):
    """Test that similar methods produce compatible output."""
    
    def test_status_message_compatibility(self):
        """Test that status messages are similar between managers."""
        # Create both managers with same console
        rich_manager = RichConsoleManager()
        with patch.object(rich_manager, '_console', self.test_console):
            unified_manager = UnifiedDisplayManager(console=self.test_console)
            
            # Test info messages
            self.clear_output()
            rich_manager.show_status("Test message", "info")
            rich_output = self.get_output()
            
            self.clear_output()
            unified_manager.info("Test message")
            unified_output = self.get_output()
            
            # Both should contain the message
            self.assertIn("Test message", rich_output)
            self.assertIn("Test message", unified_output)
            
            # Both should have similar structure (both use emoji/icons)
            # Exact format may differ, but both should be readable
    
    def test_panel_compatibility(self):
        """Test that panel methods produce similar output."""
        rich_manager = RichConsoleManager()
        with patch.object(rich_manager, '_console', self.test_console):
            unified_manager = UnifiedDisplayManager(console=self.test_console)
            
            # Test panel output
            self.clear_output()
            rich_manager.show_info_panel("Test Panel", "Content here", "info")
            rich_output = self.get_output()
            
            self.clear_output()
            unified_manager.show_panel("Test Panel", "Content here", "blue")
            unified_output = self.get_output()
            
            # Both should show panel with title and content
            for output in [rich_output, unified_output]:
                self.assertIn("Test Panel", output)
                self.assertIn("Content here", output)


class TestProgressOutputPatterns(TestConsoleOutputPatterns):
    """Test progress display output patterns."""
    
    @patch('interfaces.human.rich_console_manager.Progress')
    def test_rich_console_progress_pattern(self, mock_progress_class):
        """Document RichConsoleManager progress creation."""
        mock_progress = Mock()
        mock_progress_class.return_value = mock_progress
        
        manager = RichConsoleManager()
        progress = manager.create_progress_display("Processing")
        
        # Should create Progress with specific components
        mock_progress_class.assert_called_once()
        args, kwargs = mock_progress_class.call_args
        
        # Should have console parameter
        self.assertIn('console', kwargs)
        
        # Should store as current progress
        self.assertEqual(manager._current_progress, mock_progress)
    
    def test_unified_progress_pattern(self):
        """Document UnifiedDisplayManager progress pattern."""
        manager = UnifiedDisplayManager(console=self.test_console)
        
        # Start progress
        progress_id = manager.start_progress("Processing files")
        
        # Should return a progress ID
        self.assertIsNotNone(progress_id)
        self.assertTrue(progress_id.startswith("task_"))
        
        # Progress should be tracked
        self.assertIn(progress_id, manager._progress_tasks)


if __name__ == '__main__':
    unittest.main()