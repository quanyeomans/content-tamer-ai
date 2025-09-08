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

from .rich_cli_display import MessageLevel, RichCLIDisplay
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

    def __init__(
        self, display_manager: "RichDisplayManager", total_files: int, description: str
    ):
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

    def __init__(self, console: Console, options: Optional[RichDisplayOptions] = None):
        """
        Initialize RichDisplayManager with injected Console.

        Args:
            console: Rich Console instance to use for all output
            options: Display configuration options
        """
        self.console = console  # Use injected Console instead of creating new one
        self.options = options or RichDisplayOptions()

        # Initialize Rich components with shared console
        self.cli = RichCLIDisplay(console=self.console, no_color=self.options.no_color)

        self.progress = RichProgressDisplay(
            console=self.console,
            no_color=self.options.no_color,
            show_stats=self.options.show_stats,
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
    def processing_context(
        self, total_files: int, description: str = "Processing Files"
    ):
        """Create a Rich processing context for file operations."""
        context = RichProcessingContext(self, total_files, description)
        try:
            context.__enter__()
            yield context
        finally:
            context.__exit__(None, None, None)

    # Backward compatibility methods
    def show_message(
        self, message: str, level: str = MessageLevel.INFO, **kwargs
    ) -> None:
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
        if (
            not hasattr(self, "progress")
            or not hasattr(self.progress, "stats")
            or self.progress.stats.total == 0
        ):
            self.print_completion_message(success_rate, total_files)

        self.print_error_summary(error_details)

    def show_organization_progress(
        self, phase: str, current: int, total: int, details: str = ""
    ) -> None:
        """Display organization progress with Rich styling."""
        if self.options.quiet:
            return

        phase_emojis = {
            "analyzing": "🔍",
            "classifying": "📋",
            "ml_refinement": "🤖",
            "temporal_analysis": "🕒",
            "organizing": "🗂️",
            "complete": "✅",
        }

        emoji = phase_emojis.get(phase, "⚡")
        phase_name = phase.replace("_", " ").title()

        if total > 0:
            percentage = (current / total) * 100
            progress_msg = (
                f"{emoji} {phase_name}: {current}/{total} ({percentage:.1f}%)"
            )
        else:
            progress_msg = f"{emoji} {phase_name}"

        if details:
            progress_msg += f" - {details}"

        self.info(progress_msg)

    def show_organization_results(self, results: Dict[str, Any]) -> None:
        """Display organization results with Rich styling."""
        if self.options.quiet or not results:
            return

        docs_organized = results.get("documents_organized", 0)
        engine_type = results.get("engine_type", "Unknown")
        ml_level = results.get("ml_enhancement_level", 0)

        self.success(
            f"🗂️  Organization completed: {docs_organized} documents analyzed ({engine_type})"
        )

        # Show detailed quality metrics if available
        org_result = results.get("organization_result", {})
        quality_metrics = org_result.get("quality_metrics", {})

        if quality_metrics:
            accuracy = quality_metrics.get("accuracy", 0) * 100
            self.info(f"📊 Classification accuracy: {accuracy:.1f}%")

            # ML enhancement details
            if ml_level >= 2 and quality_metrics.get("ml_enhancement_applied"):
                ml_refined = quality_metrics.get("ml_refined_documents", 0)
                if ml_refined > 0:
                    self.info(
                        f"🤖 ML enhancement: {ml_refined} documents refined with advanced NLP"
                    )

            # Temporal intelligence details
            if ml_level >= 3 and quality_metrics.get("temporal_enhancement_applied"):
                temporal_confidence = quality_metrics.get("temporal_confidence", 0.0)
                organization_type = quality_metrics.get(
                    "temporal_organization_type", "chronological"
                )
                self.info(
                    f"🕒 Temporal intelligence: {temporal_confidence:.1f} confidence, {organization_type} structure"
                )

        # Show folder structure if available
        folder_structure = org_result.get("folder_structure", {})
        if folder_structure:
            self.info("📁 Folder structure created:")
            for folder, count in folder_structure.items():
                self.info(f"   • {folder}: {count} documents")

    def show_organization_error(
        self, error_msg: str, details: Dict[str, Any] = None
    ) -> None:
        """Display organization error with Rich styling and recovery suggestions."""
        if self.options.quiet:
            return

        # Determine severity and icon based on error type
        error_type = details.get("error_type", "unknown") if details else "unknown"
        is_recoverable = details.get("is_recoverable", False) if details else False
        retry_recommended = (
            details.get("retry_recommended", False) if details else False
        )
        context = details.get("context", "") if details else ""

        # Choose appropriate severity level and icon
        if is_recoverable:
            icon = "⚠️"
            self.warning(f"{icon} Organization issue: {error_msg}")

            # Show recovery suggestions for recoverable errors
            if retry_recommended:
                self.info("💡 This issue may resolve automatically on retry")

            if error_type == "org_ml_unavailable":
                self.info(
                    "💡 Consider installing ML dependencies: pip install spacy sentence-transformers"
                )
            elif error_type == "org_config_error":
                self.info("💡 Organization will continue with default settings")
            elif error_type == "org_folder_error":
                self.info("💡 Check folder permissions and disk space")
        else:
            icon = "❌"
            self.error(f"{icon} Organization failed: {error_msg}")

        # Show context and technical details in verbose mode
        if self.options.verbose and details:
            if context:
                self.debug(f"Context: {context}")
            if error_type != "unknown":
                self.debug(f"Error type: {error_type}")

            # Show specific guidance based on error type
            if error_type == "org_insufficient_data":
                self.debug(
                    "Suggestion: Try processing more files or use simpler organization"
                )
            elif error_type == "org_classifier_error":
                self.debug(
                    "Suggestion: Reducing ML level may help with classification issues"
                )

    @contextmanager
    def organization_context(self, total_docs: int, ml_level: int = 2):
        """Create organization progress context."""
        level_names = {1: "Basic Rules", 2: "Selective ML", 3: "Temporal Intelligence"}
        engine_name = level_names.get(ml_level, f"Level {ml_level}")

        self.info(f"🗂️  Starting document organization ({engine_name})...")

        try:
            yield self
        finally:
            pass  # Completion handled by show_organization_results


# Backward compatibility: Create alias for existing import patterns
DisplayManager = RichDisplayManager
DisplayOptions = RichDisplayOptions
ProcessingContext = RichProcessingContext
