"""
Enhanced Progress Display with Rich UI Library

Provides a delightful, engaging progress bar experience with automatic
cross-platform compatibility, beautiful colors, and rich formatting.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TextIO

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text


@dataclass
class RichProgressStats:
    """Statistics for progress tracking with enhanced metrics."""
    
    total: int = 0
    completed: int = 0
    succeeded: int = 0
    failed: int = 0
    warnings: int = 0
    start_time: float = field(default_factory=time.time)
    _files_with_warnings: set = field(default_factory=set)
    _processed_files: list = field(default_factory=list)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed processing time."""
        return time.time() - self.start_time

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.succeeded / self.total) * 100

    @property
    def completion_rate(self) -> float:
        """Get completion rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100


class RichProgressDisplay:
    """Enhanced progress display with Rich library providing delightful UI."""

    def __init__(
        self,
        no_color: bool = False,
        show_stats: bool = True,
        console: Optional[Console] = None,
        width: Optional[int] = None,
    ):
        # Initialize Rich console with cross-platform compatibility
        self.console = console or Console(
            force_terminal=True,
            safe_box=True,  # Windows legacy terminal compatibility
            width=width,
            no_color=no_color,
            legacy_windows=False,  # Disable legacy Windows mode to avoid encoding issues
            _environ={'TERM': 'xterm-256color'},  # Force modern terminal detection
        )
        
        self.show_stats = show_stats
        self.stats = RichProgressStats()
        self.current_filename = ""
        self.current_target_filename = ""
        
        # Rich Progress components
        self._progress = None
        self._task_id: Optional[TaskID] = None
        self._live = None
        self._status_text = ""

    def start(self, total: int, description: str = "Processing Files") -> None:
        """Initialize the delightful progress display."""
        self.stats.total = total
        self.stats.start_time = time.time()
        
        # Create Rich progress bar with beautiful styling
        self._progress = Progress(
            SpinnerColumn("dots12", style="cyan"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(
                style="green",
                complete_style="bright_green",
                finished_style="bright_green",
                pulse_style="yellow",
            ),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )
        
        self._task_id = self._progress.add_task(
            f"[cyan]{description}[/cyan]", total=total
        )
        
        # Start live display
        self._start_live_display()

    def update(
        self,
        filename: str = "",
        status: str = "",
        increment: bool = True,
        target_filename: str = "",
    ) -> None:
        """Update progress with rich status information."""
        if not self._progress or self._task_id is None:
            return

        if increment:
            self.stats.completed += 1

        if filename:
            self.current_filename = filename
        if target_filename:
            self.current_target_filename = target_filename
        if status:
            self._status_text = status

        # Update the task description with current file and status
        self._update_task_description()
        
        if increment:
            self._progress.advance(self._task_id, 1)

    def add_success(self, filename: str = "", target_filename: str = "") -> None:
        """Add a successful processing with celebration."""
        self.stats.succeeded += 1
        if filename:
            self.stats._processed_files.append({
                'source': filename,
                'target': target_filename or filename,
                'status': 'success',
                'timestamp': time.time()
            })
        
        # Update status to show success
        self._status_text = "completed"
        self._update_task_description()

    def add_warning(self, filename: str = None) -> None:
        """Add warning count with visual indication."""
        if filename and filename not in self.stats._files_with_warnings:
            self.stats.warnings += 1
            self.stats._files_with_warnings.add(filename)
        elif not filename:
            self.stats.warnings += 1

    def add_error(self, filename: str = "") -> None:
        """Add error count with visual feedback."""
        self.stats.failed += 1
        self._status_text = "failed"
        self._update_task_description()

    def _update_task_description(self) -> None:
        """Update the task description with current status and file."""
        if not self._progress or self._task_id is None:
            return

        # Create status indicator with appropriate styling
        status_styles = {
            "processing": ("⚙️", "blue", "Processing"),
            "extracting_content": ("📄", "cyan", "Extracting"),
            "generating_filename": ("🤖", "magenta", "AI Processing"),
            "moving_file": ("📁", "green", "Organizing"),
            "completed": ("✅", "bright_green", "Success"),
            "failed": ("❌", "bright_red", "Failed"),
            "warning": ("⚠️", "yellow", "Warning"),
        }

        icon, color, text = status_styles.get(self._status_text, ("•", "white", ""))
        
        # Format current filename for display
        display_name = self.current_target_filename or self.current_filename
        if display_name:
            # Truncate long filenames gracefully
            if len(display_name) > 40:
                display_name = f"{display_name[:37]}..."
            
            file_display = f"[dim cyan]→[/dim cyan] [bright_white]{display_name}[/bright_white]"
        else:
            file_display = ""
        
        # Create rich description
        if text and file_display:
            description = f"[cyan]Processing Files[/cyan] {file_display} [{color}]{icon} {text}[/{color}]"
        elif file_display:
            description = f"[cyan]Processing Files[/cyan] {file_display}"
        else:
            description = "[cyan]Processing Files[/cyan]"
        
        self._progress.update(self._task_id, description=description)

    def _start_live_display(self) -> None:
        """Start the live Rich display."""
        if not self.show_stats:
            self._live = Live(
                self._progress, 
                console=self.console, 
                refresh_per_second=10,
                transient=True
            )
        else:
            # Create combined display with stats
            self._live = Live(
                self._create_full_display(), 
                console=self.console, 
                refresh_per_second=10,
                transient=True
            )
        
        self._live.start()

    def _create_full_display(self) -> Table:
        """Create the full display with progress and stats."""
        table = Table.grid()
        table.add_row(self._progress)
        
        if self.show_stats and self.stats.total > 0:
            table.add_row(self._create_stats_display())
        
        return table

    def _create_stats_display(self) -> Panel:
        """Create a beautiful stats panel."""
        stats_text = Text()
        
        # Success stats
        if self.stats.succeeded > 0:
            stats_text.append("✅ ", style="bright_green")
            stats_text.append(f"{self.stats.succeeded} processed", style="bright_green")
            stats_text.append("  ")

        # Warning stats  
        if self.stats.warnings > 0:
            stats_text.append("⚠️ ", style="yellow")
            stats_text.append(f"{self.stats.warnings} warnings", style="yellow")
            stats_text.append("  ")

        # Error stats
        if self.stats.failed > 0:
            stats_text.append("❌ ", style="bright_red")
            stats_text.append(f"{self.stats.failed} errors", style="bright_red")
            stats_text.append("  ")

        # Time elapsed
        elapsed = self.stats.elapsed_time
        if elapsed < 60:
            time_str = f"{elapsed:.1f}s"
        elif elapsed < 3600:
            time_str = f"{elapsed/60:.1f}m"
        else:
            time_str = f"{elapsed/3600:.1f}h"
        
        stats_text.append("⏱️ ", style="dim cyan")
        stats_text.append(f"{time_str} elapsed", style="dim cyan")

        return Panel(
            stats_text,
            border_style="dim",
            padding=(0, 1),
            height=1,
        )

    def finish(self, final_message: str = "Processing complete") -> None:
        """Complete the progress display with celebration."""
        if self._live:
            self._live.stop()

        # Create final summary with rich styling
        self._display_final_summary(final_message)

    def _display_final_summary(self, message: str) -> None:
        """Display a beautiful final summary."""
        # Create summary table
        summary_table = Table.grid(padding=1)
        
        # Header
        if self.stats.succeeded == self.stats.total and self.stats.total > 0:
            # Perfect success - celebrate!
            header = Text(f"🎉 {message} 🎉", style="bold bright_green")
        elif self.stats.succeeded > 0:
            # Partial success
            header = Text(f"✅ {message}", style="bold green")
        else:
            # No successes
            header = Text(f"⚠️ {message}", style="bold yellow")
        
        summary_table.add_row(header)
        summary_table.add_row("")

        # Stats summary
        if self.stats.total > 0:
            success_rate = self.stats.success_rate
            
            stats_text = Text()
            stats_text.append("📊 Results: ", style="bold cyan")
            stats_text.append(f"Total: {self.stats.total}", style="white")
            stats_text.append(" • ", style="dim")
            stats_text.append(f"Successful: {self.stats.succeeded}", style="bright_green")
            stats_text.append(" • ", style="dim")
            stats_text.append(f"Success Rate: {success_rate:.1f}%", 
                             style="bright_green" if success_rate >= 80 else "yellow" if success_rate >= 50 else "red")
            
            if self.stats.warnings > 0:
                stats_text.append(" • ", style="dim")
                stats_text.append(f"Warnings: {self.stats.warnings}", style="yellow")
            
            if self.stats.failed > 0:
                stats_text.append(" • ", style="dim")
                stats_text.append(f"Errors: {self.stats.failed}", style="red")
            
            # Time summary
            elapsed = self.stats.elapsed_time
            if elapsed < 60:
                time_str = f"{elapsed:.1f}s"
            elif elapsed < 3600:
                time_str = f"{elapsed/60:.1f}m"
            else:
                time_str = f"{elapsed/3600:.1f}h"
            
            stats_text.append(" • ", style="dim")
            stats_text.append(f"Time: {time_str}", style="cyan")
            
            summary_table.add_row(stats_text)

        # Display in a nice panel
        panel = Panel(
            summary_table,
            border_style="bright_green" if self.stats.success_rate >= 80 else "yellow",
            padding=(1, 2),
        )
        
        self.console.print()
        self.console.print(panel)

    @contextmanager
    def processing_context(self, total_files: int, description: str = "Processing Files"):
        """Context manager for convenient progress tracking."""
        self.start(total_files, description)
        try:
            yield self
        finally:
            self.finish()

    def skip_file(self, filename: str) -> None:
        """Skip a file (already processed)."""
        self.update(filename=filename, status="skipped", increment=True)

    def start_file(self, filename: str) -> None:
        """Start processing a file."""
        self.update(filename=filename, status="processing", increment=False)

    def complete_file(self, filename: str, target_filename: str = "") -> None:
        """Complete file processing successfully."""
        self.add_success(filename, target_filename)
        self.update(filename=filename, target_filename=target_filename, status="completed", increment=False)

    def fail_file(self, filename: str, error: str = "") -> None:
        """Mark file processing as failed."""
        self.add_error(filename)
        self.update(filename=filename, status="failed", increment=False)

    def warn_file(self, filename: str, warning: str = "") -> None:
        """Add warning for file processing."""
        self.add_warning(filename)
        self.update(filename=filename, status="warning", increment=False)

    def set_status(self, status: str) -> None:
        """Set current processing status."""
        self._status_text = status
        self._update_task_description()