"""
Display Manager - Orchestrates CLI display components.

Provides a unified interface for progress tracking, message handling,
and user interaction with configurable verbosity levels.
"""

import sys
from typing import Optional, TextIO, Any, Dict
from contextlib import contextmanager
from dataclasses import dataclass

from .cli_display import ColorFormatter, MessageLevel
from .progress_display import ProgressDisplay, SimpleProgressDisplay
from .message_handler import MessageHandler, MessageConfig, SimpleMessageHandler, DisplayLocation


@dataclass
class DisplayOptions:
    """Configuration options for display behavior."""
    verbose: bool = False
    quiet: bool = False
    no_color: bool = False
    show_stats: bool = True
    file: Optional[TextIO] = None


class ProcessingContext:
    """Context manager for file processing with integrated display."""
    
    def __init__(self, display_manager: 'DisplayManager'):
        self.display = display_manager
        self.current_file = ""
        self.file_count = 0
        
    def start_file(self, filename: str) -> None:
        """Start processing a new file."""
        self.current_file = filename
        self.display.progress.update(filename=filename, status="processing", increment=False)
        
    def set_status(self, status: str) -> None:
        """Update current file processing status."""
        self.display.progress.update(status=status, increment=False)
        
    def skip_file(self, filename: str) -> None:
        """Mark file as skipped."""
        self.display.progress.update(filename=filename, status="skipped", increment=True)
        if not self.display.options.quiet:
            self.display.messages.debug(f"Skipping {filename} (already processed)")
        
    def complete_file(self, filename: str, new_filename: str = "") -> None:
        """Mark file as successfully completed."""
        self.display.progress.update(status="completed", increment=True)
        if new_filename and not self.display.options.quiet:
            self.show_success(f"→ {new_filename}")
        
    def fail_file(self, filename: str, error_details: str = "") -> None:
        """Mark file as failed."""
        self.display.progress.add_error()
        self.display.progress.update(status="failed", increment=True)
        if error_details:
            self.show_error(f"Failed to process {filename}: {error_details}")
        
    def show_success(self, message: str) -> None:
        """Show success message."""
        self.display.messages.success(message, location=DisplayLocation.BELOW_PROGRESS)
        
    def show_warning(self, message: str) -> None:
        """Show warning message."""
        self.display.progress.add_warning()
        self.display.messages.warning(message, location=DisplayLocation.BELOW_PROGRESS)
        
    def show_error(self, message: str) -> None:
        """Show error message."""
        self.display.messages.error(message, location=DisplayLocation.BELOW_PROGRESS)
        
    def show_info(self, message: str) -> None:
        """Show informational message."""
        self.display.messages.info(message, location=DisplayLocation.BELOW_PROGRESS)
        
    def show_debug(self, message: str) -> None:
        """Show debug message."""
        self.display.messages.debug(message, location=DisplayLocation.BELOW_PROGRESS)


class DisplayManager:
    """Central coordinator for all CLI display components."""
    
    def __init__(self, options: Optional[DisplayOptions] = None):
        self.options = options or DisplayOptions()
        
        # Apply no_color override if output is redirected
        if not self.options.file and not sys.stdout.isatty():
            self.options.no_color = True
            
        # Initialize components
        self._init_components()
        
    def _init_components(self) -> None:
        """Initialize display components based on options."""
        # Choose progress display implementation
        if self.options.quiet or not sys.stdout.isatty():
            self.progress = SimpleProgressDisplay(file=self.options.file)
        else:
            self.progress = ProgressDisplay(
                no_color=self.options.no_color,
                show_stats=self.options.show_stats,
                file=self.options.file
            )
        
        # Choose message handler implementation  
        if self.options.quiet or not sys.stdout.isatty():
            self.messages = SimpleMessageHandler(file=self.options.file)
        else:
            message_config = MessageConfig(
                show_debug=self.options.verbose,
                show_info=not self.options.quiet,
                quiet_mode=self.options.quiet,
                verbose_mode=self.options.verbose
            )
            self.messages = MessageHandler(
                config=message_config,
                no_color=self.options.no_color,
                file=self.options.file
            )
    
    def configure(self, **kwargs) -> None:
        """Update configuration at runtime."""
        for key, value in kwargs.items():
            if hasattr(self.options, key):
                setattr(self.options, key, value)
        
        # Reconfigure components
        self.messages.configure(
            quiet=self.options.quiet,
            verbose=self.options.verbose,
            no_color=self.options.no_color
        )
    
    @contextmanager
    def processing_context(self, total_files: int, description: str = "Processing Files"):
        """Create a processing context for batch file operations."""
        self.messages.set_progress_active(True)
        
        try:
            with self.progress as progress:
                progress.start(total_files, description)
                ctx = ProcessingContext(self)
                yield ctx
                
        except KeyboardInterrupt:
            self.messages.critical("Process interrupted by user", 
                                 location=DisplayLocation.REPLACE_PROGRESS)
            raise
        except Exception as e:
            self.messages.critical(f"Unexpected error: {e}", 
                                 location=DisplayLocation.REPLACE_PROGRESS)
            raise
        finally:
            self.messages.set_progress_active(False)
            self.progress.finish("Processing complete")
            if not self.options.quiet:
                self.messages.show_summary()
    
    def show_startup_info(self, info: Dict[str, Any]) -> None:
        """Display startup information."""
        if self.options.quiet:
            return
            
        # Show capability information
        if "ocr_capabilities" in info:
            self.messages.info(f"OCR capabilities: {info['ocr_capabilities']}")
            
        # Show directory information
        if "directories" in info:
            dirs = info["directories"]
            self.messages.info(f"Input: {dirs.get('input', 'N/A')}")
            self.messages.info(f"Processed: {dirs.get('processed', 'N/A')}")
            self.messages.info(f"Unprocessed: {dirs.get('unprocessed', 'N/A')}")
    
    def show_completion_stats(self, stats: Dict[str, Any]) -> None:
        """Display final completion statistics."""
        if self.options.quiet:
            return
            
        if "total_files" in stats and stats["total_files"] > 0:
            success_rate = (stats.get("successful", 0) / stats["total_files"]) * 100
            self.messages.success(f"Processing complete: {success_rate:.1f}% success rate")
            
        # Show enhanced retry/recovery statistics
        if stats.get("successful_retries", 0) > 0:
            self.messages.info(f"✅ {stats['successful_retries']} files recovered after temporary issues")
            
        if stats.get("recoverable_errors", 0) > 0:
            self.messages.info(
                f"ℹ️  {stats['recoverable_errors']} files encountered temporary permission/access issues "
                f"(typically antivirus scans or cloud sync) but processing continued"
            )
            
        if stats.get("errors", 0) > 0:
            self.messages.error(f"{stats['errors']} files could not be processed")
    
    def prompt_user(self, message: str, default: Optional[str] = None) -> str:
        """Prompt user for input with proper formatting."""
        if self.options.quiet:
            return default or ""
            
        # Ensure progress is not interfering
        self.messages.set_progress_active(False)
        
        formatter = ColorFormatter(no_color=self.options.no_color)
        prompt = formatter.colorize(message, "bright_blue", bold=True)
        
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        
        try:
            response = input(prompt).strip()
            return response if response else (default or "")
        except KeyboardInterrupt:
            self.messages.warning("\nOperation cancelled by user")
            return ""
        except EOFError:
            return default or ""
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Ask user for yes/no confirmation."""
        if self.options.quiet:
            return default
            
        default_text = "Y/n" if default else "y/N"
        response = self.prompt_user(f"{message} ({default_text})", 
                                  "y" if default else "n").lower()
        
        if response in ["y", "yes", "true", "1"]:
            return True
        elif response in ["n", "no", "false", "0"]:
            return False
        else:
            return default
    
    def debug(self, message: str) -> None:
        """Show debug message."""
        self.messages.debug(message)
    
    def info(self, message: str) -> None:
        """Show info message.""" 
        self.messages.info(message)
    
    def success(self, message: str) -> None:
        """Show success message."""
        self.messages.success(message)
    
    def warning(self, message: str) -> None:
        """Show warning message."""
        self.messages.warning(message)
    
    def error(self, message: str) -> None:
        """Show error message."""
        self.messages.error(message)
    
    def critical(self, message: str) -> None:
        """Show critical error message."""
        self.messages.critical(message)


def create_display_manager(
    verbose: bool = False,
    quiet: bool = False, 
    no_color: bool = False,
    show_stats: bool = True,
    file: Optional[TextIO] = None
) -> DisplayManager:
    """Create display manager with specified options."""
    options = DisplayOptions(
        verbose=verbose,
        quiet=quiet,
        no_color=no_color,
        show_stats=show_stats,
        file=file
    )
    return DisplayManager(options)


# Convenience functions for backward compatibility
def create_simple_display() -> DisplayManager:
    """Create simple display manager for basic usage."""
    return DisplayManager(DisplayOptions(quiet=True, no_color=True))


def create_rich_display(verbose: bool = False) -> DisplayManager:
    """Create rich display manager with full features."""
    return DisplayManager(DisplayOptions(verbose=verbose, show_stats=True))