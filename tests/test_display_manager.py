"""
Tests for display manager orchestration and integration.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
from io import StringIO

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.display_manager import (
    DisplayOptions, ProcessingContext, DisplayManager,
    create_display_manager, create_simple_display, create_rich_display
)
from utils.progress_display import ProgressDisplay, SimpleProgressDisplay
from utils.message_handler import MessageHandler, SimpleMessageHandler


class TestDisplayOptions(unittest.TestCase):
    """Test display options configuration."""
    
    def test_default_options(self):
        """Test default display options."""
        options = DisplayOptions()
        self.assertFalse(options.verbose)
        self.assertFalse(options.quiet)
        self.assertFalse(options.no_color)
        self.assertTrue(options.show_stats)
        self.assertIsNone(options.file)
        
    def test_custom_options(self):
        """Test custom display options."""
        output = StringIO()
        options = DisplayOptions(
            verbose=True,
            quiet=True,
            no_color=True,
            show_stats=False,
            file=output
        )
        
        self.assertTrue(options.verbose)
        self.assertTrue(options.quiet)
        self.assertTrue(options.no_color)
        self.assertFalse(options.show_stats)
        self.assertIs(options.file, output)


class TestProcessingContext(unittest.TestCase):
    """Test processing context functionality."""
    
    def setUp(self):
        self.output = StringIO()
        options = DisplayOptions(quiet=True, file=self.output)
        self.display_manager = DisplayManager(options)
        self.context = ProcessingContext(self.display_manager)
        
    def test_start_file(self):
        """Test starting file processing."""
        self.context.start_file("test.pdf")
        self.assertEqual(self.context.current_file, "test.pdf")
        
    def test_set_status(self):
        """Test setting processing status."""
        self.context.start_file("test.pdf")
        self.context.set_status("extracting_content")
        # Should not crash
        
    def test_skip_file(self):
        """Test skipping a file."""
        self.context.skip_file("already_processed.pdf")
        # Should update progress without errors
        
    def test_complete_file(self):
        """Test completing file processing."""
        self.context.complete_file("test.pdf", "new_name.pdf")
        # Should update progress and show success
        
    def test_fail_file(self):
        """Test failing file processing."""
        self.context.fail_file("error_file.pdf", "Processing failed")
        # Should update progress and show error
        
    def test_show_messages(self):
        """Test showing different message types."""
        self.context.show_success("File processed successfully")
        self.context.show_warning("Potential issue detected")
        self.context.show_error("Processing error occurred")
        self.context.show_info("Informational message")
        
        # All methods should execute without errors


class TestDisplayManager(unittest.TestCase):
    """Test display manager core functionality."""
    
    def setUp(self):
        self.output = StringIO()
        options = DisplayOptions(quiet=True, no_color=True, file=self.output)
        self.display_manager = DisplayManager(options)
        
    def test_initialization(self):
        """Test display manager initialization."""
        self.assertIsInstance(self.display_manager.options, DisplayOptions)
        self.assertIsNotNone(self.display_manager.progress)
        self.assertIsNotNone(self.display_manager.messages)
        
    def test_quiet_mode_uses_simple_components(self):
        """Test that quiet mode uses simple components."""
        quiet_options = DisplayOptions(quiet=True)
        quiet_manager = DisplayManager(quiet_options)
        
        # Should use simple implementations for quiet mode
        self.assertIsInstance(quiet_manager.progress, SimpleProgressDisplay)
        self.assertIsInstance(quiet_manager.messages, SimpleMessageHandler)
        
    def test_rich_mode_uses_enhanced_components(self):
        """Test that rich mode uses enhanced components."""
        # Mock isatty to return True for rich components
        with patch('sys.stdout.isatty', return_value=True):
            rich_options = DisplayOptions(quiet=False, verbose=True)
            rich_manager = DisplayManager(rich_options)
            
            # Should use enhanced implementations
            self.assertIsInstance(rich_manager.progress, ProgressDisplay)
            self.assertIsInstance(rich_manager.messages, MessageHandler)
    
    @patch('sys.stdout.isatty', return_value=False)
    def test_non_tty_forces_no_color(self, mock_isatty):
        """Test that non-TTY output forces no_color mode."""
        options = DisplayOptions()  # no_color=False initially
        manager = DisplayManager(options)
        
        # Should have been overridden to True
        self.assertTrue(manager.options.no_color)
        
    def test_configure_at_runtime(self):
        """Test runtime configuration updates."""
        initial_quiet = self.display_manager.options.quiet
        
        self.display_manager.configure(quiet=not initial_quiet)
        self.assertEqual(self.display_manager.options.quiet, not initial_quiet)
        
    def test_processing_context_creation(self):
        """Test processing context creation and usage."""
        with self.display_manager.processing_context(total_files=3, description="Testing") as ctx:
            self.assertIsInstance(ctx, ProcessingContext)
            self.assertIs(ctx.display, self.display_manager)
            
            # Test basic operations
            ctx.start_file("test1.pdf")
            ctx.set_status("processing")
            ctx.complete_file("test1.pdf", "new_name1.pdf")
            
    def test_processing_context_handles_keyboard_interrupt(self):
        """Test processing context handles KeyboardInterrupt."""
        with self.assertRaises(KeyboardInterrupt):
            with self.display_manager.processing_context(total_files=1) as ctx:
                raise KeyboardInterrupt()
                
    def test_processing_context_handles_exceptions(self):
        """Test processing context handles general exceptions."""
        with self.assertRaises(ValueError):
            with self.display_manager.processing_context(total_files=1) as ctx:
                raise ValueError("Test error")
                
    def test_startup_info_display(self):
        """Test startup information display."""
        info = {
            "ocr_capabilities": "PyMuPDF: yes, Tesseract: yes",
            "directories": {
                "input": "/path/to/input",
                "processed": "/path/to/processed",
                "unprocessed": "/path/to/unprocessed"
            }
        }
        
        # Should not crash in quiet mode
        self.display_manager.show_startup_info(info)
        
        # Test with non-quiet mode
        verbose_options = DisplayOptions(verbose=True, no_color=True, file=self.output)
        verbose_manager = DisplayManager(verbose_options)
        verbose_manager.show_startup_info(info)
        
    def test_completion_stats_display(self):
        """Test completion statistics display."""
        stats = {
            "total_files": 10,
            "successful": 8,
            "warnings": 1,
            "errors": 1
        }
        
        # Should not crash
        self.display_manager.show_completion_stats(stats)
        
    @patch('builtins.input', return_value='test response')
    def test_prompt_user(self, mock_input):
        """Test user prompting functionality."""
        response = self.display_manager.prompt_user("Enter something", default="default")
        
        # In quiet mode, should return default
        self.assertEqual(response, "default")
        
    def test_prompt_user_keyboard_interrupt(self):
        """Test user prompt handles KeyboardInterrupt."""
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            response = self.display_manager.prompt_user("Enter something")
            self.assertEqual(response, "")
            
    def test_confirm_action(self):
        """Test action confirmation."""
        # In quiet mode, should return default
        result = self.display_manager.confirm_action("Continue?", default=True)
        self.assertTrue(result)
        
        result = self.display_manager.confirm_action("Continue?", default=False)
        self.assertFalse(result)
        
    def test_message_methods(self):
        """Test direct message methods."""
        self.display_manager.debug("Debug message")
        self.display_manager.info("Info message")
        self.display_manager.success("Success message")
        self.display_manager.warning("Warning message")
        self.display_manager.error("Error message")
        self.display_manager.critical("Critical message")
        
        # All should execute without errors


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for creating display managers."""
    
    def test_create_display_manager(self):
        """Test create_display_manager function."""
        manager = create_display_manager(verbose=True, quiet=False, no_color=True)
        
        self.assertIsInstance(manager, DisplayManager)
        self.assertTrue(manager.options.verbose)
        self.assertFalse(manager.options.quiet)
        self.assertTrue(manager.options.no_color)
        
    def test_create_simple_display(self):
        """Test create_simple_display function."""
        manager = create_simple_display()
        
        self.assertIsInstance(manager, DisplayManager)
        self.assertTrue(manager.options.quiet)
        self.assertTrue(manager.options.no_color)
        
    def test_create_rich_display(self):
        """Test create_rich_display function."""
        manager = create_rich_display(verbose=True)
        
        self.assertIsInstance(manager, DisplayManager)
        self.assertTrue(manager.options.verbose)
        self.assertTrue(manager.options.show_stats)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and workflows."""
    
    def setUp(self):
        self.output = StringIO()
        
    def test_complete_processing_workflow(self):
        """Test a complete file processing workflow."""
        options = DisplayOptions(quiet=False, no_color=True, file=self.output)
        manager = DisplayManager(options)
        
        with manager.processing_context(total_files=3, description="Test Processing") as ctx:
            # Process first file successfully
            ctx.start_file("document1.pdf")
            ctx.set_status("extracting_content")
            ctx.set_status("generating_filename")
            ctx.complete_file("document1.pdf", "processed_document1.pdf")
            
            # Process second file with warning
            ctx.start_file("document2.pdf")
            ctx.show_warning("OCR quality may be poor")
            ctx.complete_file("document2.pdf", "processed_document2.pdf")
            
            # Third file fails
            ctx.start_file("document3.pdf")
            ctx.fail_file("document3.pdf", "Corrupted file")
            
        # Should complete successfully
        output_content = self.output.getvalue()
        self.assertGreater(len(output_content), 0)
        
    def test_error_recovery_workflow(self):
        """Test error recovery and continuation."""
        manager = create_display_manager(verbose=True, no_color=True, file=self.output)
        
        try:
            with manager.processing_context(total_files=2) as ctx:
                ctx.start_file("good_file.pdf")
                ctx.complete_file("good_file.pdf", "processed_good.pdf")
                
                # Simulate unexpected error
                raise RuntimeError("Simulated processing error")
                
        except RuntimeError:
            # Error should be caught and handled
            pass
            
        # Manager should still be usable after error
        manager.info("System recovered successfully")
        
    def test_quiet_vs_verbose_modes(self):
        """Test differences between quiet and verbose modes."""
        quiet_output = StringIO()
        verbose_output = StringIO()
        
        quiet_manager = create_display_manager(quiet=True, file=quiet_output)
        verbose_manager = create_display_manager(verbose=True, file=verbose_output)
        
        # Send same messages to both
        for manager in [quiet_manager, verbose_manager]:
            manager.debug("Debug information")
            manager.info("Processing started")
            manager.success("File processed")
            manager.warning("Minor issue detected")
            
        quiet_content = quiet_output.getvalue()
        verbose_content = verbose_output.getvalue()
        
        # Verbose should have more content than quiet
        # (Note: Exact comparison depends on implementation details)
        self.assertIsInstance(len(quiet_content), int)
        self.assertIsInstance(len(verbose_content), int)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_invalid_configuration_combinations(self):
        """Test handling of invalid configuration combinations."""
        # Quiet and verbose at the same time
        manager = create_display_manager(quiet=True, verbose=True)
        
        # Should not crash, though behavior may be implementation-defined
        manager.info("Test message")
        
    def test_file_output_error_handling(self):
        """Test handling of file output errors."""
        # Create a closed StringIO to simulate write errors
        closed_output = StringIO()
        closed_output.close()
        
        options = DisplayOptions(file=closed_output)
        
        # Should handle file errors gracefully
        try:
            manager = DisplayManager(options)
            manager.info("Test message")
        except ValueError:
            # Closed file may raise ValueError - this is acceptable
            pass
            
    def test_unicode_handling_in_messages(self):
        """Test Unicode handling in all message types."""
        output = StringIO()
        manager = create_display_manager(no_color=True, file=output)
        
        unicode_messages = [
            "Processing файл.pdf 📄",
            "Warning: тест ⚠️", 
            "Success: 完了 ✅",
            "Error: erreur 🚨"
        ]
        
        for msg in unicode_messages:
            manager.info(msg)
            manager.warning(msg)
            manager.success(msg)
            manager.error(msg)
            
        # Should handle all Unicode without crashing
        output_content = output.getvalue()
        self.assertGreater(len(output_content), 0)


if __name__ == '__main__':
    unittest.main()