"""
Rich Display Manager - Orchestrates Rich-powered CLI display components.

Provides a unified interface for progress tracking, message handling,
and user interaction with beautiful Rich-powered UI while maintaining
backward compatibility with existing code.
"""

import io
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional, TextIO

from rich.console import Console

from .rich_cli_display import RichCLIDisplay, MessageLevel
from .rich_progress_display import RichProgressDisplay


@dataclass
class RichDisplayOptions:
    """Configuration options for Rich display behavior."""

    verbose: bool = False
    quiet: bool = False
    no_color: bool = False
    show_stats: bool = True
    file: Optional[TextIO] = None
    width: Optional[int] = None


class RichProcessingContext:
    """Context manager for file processing with Rich integrated display."""

    def __init__(self, display_manager: "RichDisplayManager", total_files: int, description: str):
        self.display = display_manager
        self.total_files = total_files
        self.description = description
        self.current_file = ""
        self.files_processed = 0
        self._progress_started = False

    def __enter__(self):
        """Start the processing context with Rich progress display."""
        if not self._progress_started:
            self.display.progress.start(self.total_files, self.description)
            self._progress_started = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete the processing context."""
        if self._progress_started:
            self.display.progress.finish("Content organization completed successfully.")

    def start_file(self, filename: str, target_filename: str = "") -> None:
        """Start processing a new file."""
        self.current_file = filename
        self.display.progress.start_file(filename)

        if self.display.options.verbose:
            self.display.cli.debug(f"Starting file: {filename}")

    def complete_file(self, filename: str, target_filename: str = "") -> None:
        """Complete file processing successfully."""
        self.display.progress.complete_file(filename, target_filename)
        self.files_processed += 1

        if self.display.options.verbose:
            success_msg = f"Completed: {filename}"
            if target_filename and target_filename != filename:
                success_msg += f" → {target_filename}"
            self.display.cli.success(success_msg)

    def set_status(self, status: str) -> None:
        """Set current processing status."""
        self.display.progress.set_status(status)

        # Also show stage progress in verbose mode with simple descriptive messages
        if self.display.options.verbose and status:
            stage_messages = {
                "extracting_content": "Extracting text content from document",
                "generating_filename": "AI processing to generate intelligent filename",
                "moving_file": "Organizing file to processed directory",
                "completed": "File processing completed successfully",
            }
            if status in stage_messages:
                self.display.cli.info(stage_messages[status])

    def fail_file(self, filename: str, error: str = "") -> None:
        """Mark file processing as failed."""
        self.display.progress.fail_file(filename, error)
        self.files_processed += 1

        if not self.display.options.quiet:
            error_msg = f"Failed to process: {filename}"
            if error:
                error_msg += f" ({error})"
            self.display.cli.error(error_msg)

    def skip_file(self, filename: str) -> None:
        """Skip a file (already processed)."""
        self.display.progress.skip_file(filename)

        if self.display.options.verbose:
            self.display.cli.debug(f"Skipping (already processed): {filename}")

    def show_warning(self, message: str, filename: str = "") -> None:
        """Display a warning message."""
        if filename:
            self.display.progress.warn_file(filename, message)

        if not self.display.options.quiet:
            self.display.cli.warning(message)

    def set_status(self, status: str) -> None:
        """Set current processing status."""
        self.display.progress.set_status(status)


class RichDisplayManager:
    """Rich-powered display manager for delightful user experience."""

    def __init__(self, options: Optional[RichDisplayOptions] = None):
        self.options = options or RichDisplayOptions()

        # Create UTF-8 compatible output stream for Windows
        output_file = self.options.file or sys.stdout
        if hasattr(output_file, "buffer"):
            # Wrap stdout with UTF-8 encoder for Windows compatibility
            output_file = io.TextIOWrapper(
                output_file.buffer,
                encoding="utf-8",
                errors="replace",  # Replace non-encodable characters
                newline="",
                line_buffering=True,
            )

        # Initialize Rich console
        self.console = Console(
            force_terminal=True,
            safe_box=True,  # Windows compatibility
            no_color=self.options.no_color,
            width=self.options.width,
            file=output_file,
            legacy_windows=False,  # Disable legacy Windows mode
        )

        # Initialize Rich components
        self.cli = RichCLIDisplay(no_color=self.options.no_color, console=self.console)

        self.progress = RichProgressDisplay(
            no_color=self.options.no_color,
            show_stats=self.options.show_stats,
            console=self.console,
            width=self.options.width,
        )

    # Message methods with Rich styling
    def debug(self, message: str, **kwargs) -> None:
        """Display debug message (only in verbose mode)."""
        if self.options.verbose:
            self.cli.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Display informational message."""
        if not self.options.quiet:
            self.cli.info(message, **kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Display success message with celebration."""
        if not self.options.quiet:
            self.cli.success(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Display warning message."""
        if not self.options.quiet:
            self.cli.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Display error message."""
        self.cli.error(message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Display critical error message."""
        self.cli.critical(message, **kwargs)

    # UI Enhancement methods
    def print_header(self, title: str, subtitle: str = "") -> None:
        """Display application header with Rich styling."""
        if not self.options.quiet:
            self.cli.print_header(title, subtitle)

    def print_capabilities(self, ocr_deps: dict, ocr_settings: dict) -> None:
        """Display system capabilities."""
        if self.options.verbose and not self.options.quiet:
            self.cli.print_capabilities(ocr_deps, ocr_settings)

    def print_api_key_prompt(self, provider: str) -> None:
        """Display API key input prompt."""
        self.cli.print_api_key_prompt(provider)

    def print_api_key_validation(self, key: str, key_length: int) -> None:
        """Display API key validation results."""
        if not self.options.quiet:
            self.cli.print_api_key_validation(key, key_length)

    def print_provider_setup(self, provider: str, model: str) -> None:
        """Display provider setup confirmation."""
        if not self.options.quiet:
            self.cli.print_provider_setup(provider, model)

    def print_directory_info(self, directories: dict) -> None:
        """Display directory configuration."""
        if not self.options.quiet:
            self.cli.print_directory_info(directories)

    def print_available_models(self, providers: dict) -> None:
        """Display available models."""
        self.cli.print_available_models(providers)

    def print_error_summary(self, error_details: list) -> None:
        """Display error summary."""
        if error_details and not self.options.quiet:
            self.cli.print_error_summary(error_details)

    def print_completion_message(self, success_rate: float, total_files: int) -> None:
        """Display completion message."""
        if not self.options.quiet:
            self.cli.print_completion_message(success_rate, total_files)

    def clear_screen(self) -> None:
        """Clear screen with Rich-compatible method."""
        if not self.options.quiet:
            self.cli.clear_screen()

    @contextmanager
    def processing_context(self, total_files: int, description: str = "Processing Files"):
        """Create a Rich processing context for file operations."""
        context = RichProcessingContext(self, total_files, description)
        try:
            context.__enter__()
            yield context
        finally:
            context.__exit__(None, None, None)

    # Backward compatibility methods
    def show_message(self, message: str, level: str = MessageLevel.INFO, **kwargs) -> None:
        """Show message with specified level (backward compatibility)."""
        if level == MessageLevel.DEBUG:
            self.debug(message, **kwargs)
        elif level == MessageLevel.INFO:
            self.info(message, **kwargs)
        elif level == MessageLevel.WARNING:
            self.warning(message, **kwargs)
        elif level == MessageLevel.ERROR:
            self.error(message, **kwargs)
        elif level == MessageLevel.CRITICAL:
            self.critical(message, **kwargs)
        else:
            self.info(message, **kwargs)  # Default fallback

    def format_time(self, seconds: float) -> str:
        """Format elapsed time in human-readable format."""
        return self.cli.format_time(seconds)

    def highlight_filename(self, filename: str):
        """Create highlighted filename for display."""
        return self.cli.highlight_filename(filename)

    def show_startup_info(self, info: Dict[str, Any]) -> None:
        """Display startup information with Rich styling."""
        if self.options.quiet:
            return

        # Show capability information
        if "ocr_capabilities" in info:
            ocr_deps = info["ocr_capabilities"].get("dependencies", {})
            ocr_settings = info["ocr_capabilities"].get("settings", {})
            self.print_capabilities(ocr_deps, ocr_settings)

        # Show directory information
        if "directories" in info:
            self.print_directory_info(info["directories"])

    def show_completion_stats(self, stats: Dict[str, Any]) -> None:
        """Display final completion statistics with Rich styling."""
        if self.options.quiet:
            return

        # Calculate success rate from stats
        total_files = stats.get("total_files", 0)
        successful = stats.get("successful", 0)
        
        if total_files > 0:
            success_rate = (successful / total_files) * 100
        else:
            success_rate = stats.get("success_rate", 0.0)

        error_details = stats.get("error_details", [])

        # Only show completion message if we haven't already shown rich progress completion
        # The Rich progress display already shows a beautiful completion summary
        if not hasattr(self, 'progress') or not hasattr(self.progress, 'stats') or self.progress.stats.total == 0:
            self.print_completion_message(success_rate, total_files)
        
        self.print_error_summary(error_details)


# Backward compatibility: Create alias for existing import patterns
DisplayManager = RichDisplayManager
DisplayOptions = RichDisplayOptions
ProcessingContext = RichProcessingContext
