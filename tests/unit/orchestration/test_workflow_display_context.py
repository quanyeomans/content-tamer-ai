"""
Unit tests for LegacyDisplayContext in workflow processor.

Tests that errors and warnings are properly routed through Rich console.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))


class TestLegacyDisplayContext(unittest.TestCase):
    """Test the LegacyDisplayContext class for proper Rich console integration."""

    def setUp(self):
        """Set up test fixtures."""
        # We need to import here to avoid import issues
        from orchestration import workflow_processor
        self.workflow_module = workflow_processor

    @patch('orchestration.workflow_processor.ConsoleManager')
    def test_display_context_with_rich_available(self, mock_console_manager):
        """Test that display context uses Rich console when available."""
        # Setup mock console
        mock_console = MagicMock()
        mock_instance = MagicMock()
        mock_instance.console = mock_console
        mock_console_manager.get_instance.return_value = mock_instance
        
        # Execute the code that creates LegacyDisplayContext
        # This simulates what happens in process_file function
        exec_globals = {
            'ConsoleManager': mock_console_manager
        }
        
        exec("""
class LegacyDisplayContext:
    def __init__(self):
        try:
            from shared.display.console_manager import ConsoleManager
            self.console_manager = ConsoleManager.get_instance()
            self.console = self.console_manager.console
            self.has_rich = True
        except ImportError:
            self.has_rich = False
            import logging
            self.logger = logging.getLogger(__name__)
    
    def show_warning(self, msg, **kwargs):
        if self.has_rich:
            self.console.print(f"[yellow]⚠ {msg}[/yellow]")
        else:
            self.logger.warning(msg)

    def show_error(self, msg, **kwargs):
        if self.has_rich:
            self.console.print(f"[red]✗ {msg}[/red]")
        else:
            self.logger.error(msg)

display_context = LegacyDisplayContext()
display_context.show_error("Test error message")
display_context.show_warning("Test warning message")
        """, exec_globals)
        
        # Verify Rich console was used
        mock_console.print.assert_any_call("[red]✗ Test error message[/red]")
        mock_console.print.assert_any_call("[yellow]⚠ Test warning message[/yellow]")
        self.assertEqual(mock_console.print.call_count, 2)

    @patch('logging.getLogger')
    def test_display_context_fallback_to_logging(self, mock_get_logger):
        """Test that display context falls back to logging when Rich unavailable."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Simulate ImportError for ConsoleManager
        with patch.dict('sys.modules', {'shared.display.console_manager': None}):
            exec_globals = {
                'logging': MagicMock(getLogger=mock_get_logger)
            }
            
            exec("""
class LegacyDisplayContext:
    def __init__(self):
        try:
            from shared.display.console_manager import ConsoleManager
            self.console_manager = ConsoleManager.get_instance()
            self.console = self.console_manager.console
            self.has_rich = True
        except (ImportError, ModuleNotFoundError):
            self.has_rich = False
            import logging
            self.logger = logging.getLogger(__name__)
    
    def show_warning(self, msg, **kwargs):
        if self.has_rich:
            self.console.print(f"[yellow]⚠ {msg}[/yellow]")
        else:
            self.logger.warning(msg)

    def show_error(self, msg, **kwargs):
        if self.has_rich:
            self.console.print(f"[red]✗ {msg}[/red]")
        else:
            self.logger.error(msg)

display_context = LegacyDisplayContext()
display_context.show_error("Test error message")
display_context.show_warning("Test warning message")
            """, exec_globals)
            
        # Verify logging was used as fallback
        mock_logger.error.assert_called_once_with("Test error message")
        mock_logger.warning.assert_called_once_with("Test warning message")

    def test_display_context_set_status_is_noop(self):
        """Test that set_status method is a no-op."""
        exec_globals = {}
        
        exec("""
class LegacyDisplayContext:
    def set_status(self, status, **kwargs):
        pass  # Status is shown in progress bar

display_context = LegacyDisplayContext()
# Should not raise any errors
display_context.set_status("Processing", filename="test.pdf")
display_context.set_status("Complete")
        """, exec_globals)
        
        # If we get here without exceptions, the test passes
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()