"""
Unified Display Manager

Consolidates all Rich UI display functionality from scattered managers.
Eliminates conflicts between multiple display systems.
"""

import logging
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.text import Text

# Dynamic import to avoid circular dependency
# from interfaces.human.rich_console_manager import RichConsoleManager

from .emoji_handler import SmartEmojiHandler


class UnifiedDisplayManager:
    """Unified manager for all display operations across domains."""

    def __init__(self, console: Optional[Console] = None, quiet_mode: bool = False):
        """Initialize unified display manager.

        Args:
            console: Optional Rich Console instance (uses singleton if None)
            quiet_mode: Whether to suppress non-essential output
        """
        self.logger = logging.getLogger(__name__)
        self.quiet_mode = quiet_mode

        # Use provided console or get from singleton manager
        if console is not None:
            self.console = console
        else:
            # Use local console manager to avoid complex import paths
            from .console_manager import ConsoleManager
            self.console = ConsoleManager.get_console()

        # Smart emoji handler for cross-platform compatibility
        self.emoji = SmartEmojiHandler(self.console)

        # Progress tracking
        self._active_progress: Optional[Progress] = None
        self._progress_tasks: Dict[str, TaskID] = {}

    def info(self, message: str, context: Optional[str] = None) -> None:
        """Display info message with smart emoji handling."""
        if self.quiet_mode:
            return

        prefix = f"[{context}] " if context else ""
        formatted = self.emoji.format_with_emoji("ℹ️", f"{prefix}{message}", "blue")
        self.console.print(formatted)

    def success(self, message: str, context: Optional[str] = None) -> None:
        """Display success message with smart emoji handling."""
        prefix = f"[{context}] " if context else ""
        formatted = self.emoji.format_with_emoji("✅", f"{prefix}{message}", "green")
        self.console.print(formatted)

    def warning(self, message: str, context: Optional[str] = None) -> None:
        """Display warning message with smart emoji handling."""
        prefix = f"[{context}] " if context else ""
        formatted = self.emoji.format_with_emoji("⚠️", f"{prefix}{message}", "yellow")
        self.console.print(formatted)

    def error(
        self, message: str, context: Optional[str] = None, suggestions: Optional[List[str]] = None
    ) -> None:
        """Display error message with smart emoji handling and optional suggestions."""
        prefix = f"[{context}] " if context else ""
        formatted = self.emoji.format_with_emoji("❌", f"{prefix}{message}", "red")
        self.console.print(formatted)

        if suggestions and not self.quiet_mode:
            self.console.print("[yellow]Suggestions:[/yellow]")
            for suggestion in suggestions:
                self.console.print(f"  • {suggestion}")

    def show_panel(self, title: str, content: str, style: str = "blue") -> None:
        """Display content in a panel."""
        if self.quiet_mode:
            return

        panel = Panel(
            content, title=f"[{style}]{title}[/{style}]", border_style=style, padding=(0, 1)
        )
        self.console.print(panel)

    def show_table(
        self, title: str, headers: List[str], rows: List[List[str]], style: str = "blue"
    ) -> None:
        """Display data in a table."""
        if self.quiet_mode:
            return

        table = Table(title=title, border_style=style)

        # Add columns
        for header in headers:
            table.add_column(header, style="white")

        # Add rows
        for row in rows:
            table.add_row(*row)

        self.console.print(table)

    def start_progress(self, description: str = "Processing") -> str:
        """Start progress display.

        Args:
            description: Progress description

        Returns:
            Progress ID for updating
        """
        if self.quiet_mode:
            return "quiet_mode"

        if self._active_progress is None:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
            
            self._active_progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="progress.complete", finished_style="progress.complete"),
                MofNCompleteColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
                transient=False  # Keep progress visible after completion
            )
            self._active_progress.start()

        # Create or update task
        progress_id = f"task_{len(self._progress_tasks)}"
        task_id = self._active_progress.add_task(description, total=100)
        self._progress_tasks[progress_id] = task_id

        return progress_id

    def update_progress(
        self, progress_id: str, current: int, total: int, description: Optional[str] = None
    ) -> None:
        """Update progress display.

        Args:
            progress_id: Progress ID from start_progress
            current: Current progress value
            total: Total progress value
            description: Optional description update
        """
        if self.quiet_mode or progress_id == "quiet_mode":
            return

        if progress_id in self._progress_tasks and self._active_progress:
            task_id = self._progress_tasks[progress_id]

            # Calculate completion
            completed = (current / total) * 100 if total > 0 else 0

            # Update task
            update_kwargs: Dict[str, Any] = {"completed": completed}
            if description:
                update_kwargs["description"] = description

            self._active_progress.update(task_id, **update_kwargs)

    def finish_progress(self, progress_id: str) -> None:
        """Finish progress display.

        Args:
            progress_id: Progress ID to finish
        """
        if self.quiet_mode or progress_id == "quiet_mode":
            return

        if progress_id in self._progress_tasks:
            del self._progress_tasks[progress_id]

        # Stop progress if no more tasks
        if not self._progress_tasks and self._active_progress:
            self._active_progress.stop()
            self._active_progress = None

    def show_processing_summary(self, results: Dict[str, Any]) -> None:
        """Show processing summary in appropriate format."""
        if self.quiet_mode:
            # Minimal output for automation
            success = results.get("success", False)
            files_processed = results.get("files_processed", 0)
            output_dir = results.get("output_directory", "")

            if success:
                self.console.print(
                    f"SUCCESS: {files_processed} files processed, output: {output_dir}"
                )
            else:
                errors = results.get("errors", ["Unknown error"])
                self.console.print(f"FAILED: {errors[0]}")
            return

        # Rich display for human users
        if results.get("success"):
            self.success(f"Processed {results.get('files_processed', 0)} files successfully")

            if results.get("output_directory"):
                self.info(f"Output directory: {results['output_directory']}")

            # Show warnings if any
            warnings = results.get("warnings", [])
            for warning in warnings:
                self.warning(warning)

        else:
            errors = results.get("errors", [])
            self.error("Processing failed", suggestions=errors[:3])

    def clear_screen(self) -> None:
        """Clear the display screen."""
        if not self.quiet_mode:
            self.console.clear()

    def print_separator(self, char: str = "─") -> None:
        """Print separator line."""
        if not self.quiet_mode:
            width = self.console.size.width if hasattr(self.console, "size") else 80
            self.console.print(char * width, style="dim")

    def get_display_capabilities(self) -> Dict[str, Any]:
        """Get display system capabilities."""
        return {
            "console_available": self.console is not None,
            "rich_features": hasattr(self.console, "is_terminal") and self.console.is_terminal,
            "quiet_mode": self.quiet_mode,
            "progress_available": True,
            "color_support": (
                not getattr(self.console, "legacy_windows", False)
                if hasattr(self.console, "legacy_windows")
                else True
            ),
        }
