"""
Enhanced progress display with color support and filename highlighting.

Provides a rich progress bar experience with status indicators,
target filename display, and statistics tracking.
"""

import sys
import time
from typing import Dict, Optional, Any, TextIO
from dataclasses import dataclass, field

from .cli_display import ColorFormatter, MessageLevel, Colors


@dataclass
class ProgressStats:
    """Statistics for progress tracking."""
    total: int = 0
    completed: int = 0
    failed: int = 0
    warnings: int = 0
    start_time: float = field(default_factory=time.time)
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed processing time."""
        return time.time() - self.start_time
    
    @property
    def success_count(self) -> int:
        """Get successful processing count."""
        return self.completed - self.failed
    
    @property
    def progress_percentage(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100


class ProgressDisplay:
    """Enhanced progress display with colors and status tracking."""
    
    def __init__(
        self, 
        no_color: bool = False,
        show_stats: bool = True,
        file: Optional[TextIO] = None
    ):
        self.formatter = ColorFormatter(no_color=no_color)
        self.show_stats = show_stats
        self.file = file or sys.stdout
        self.stats = ProgressStats()
        self.current_filename = ""
        self.current_status = ""
        self.last_line_length = 0
        self._cursor_hidden = False
        
    def start(self, total: int, description: str = "Processing") -> None:
        """Initialize progress display."""
        self.stats.total = total
        self.stats.start_time = time.time()
        self._hide_cursor()
        self._render_progress(description)
        
    def update(
        self, 
        filename: str = "", 
        status: str = "", 
        increment: bool = True
    ) -> None:
        """Update progress with new filename and status."""
        if increment:
            self.stats.completed += 1
            
        if filename:
            self.current_filename = filename
        if status:
            self.current_status = status
            
        self._render_progress()
    
    def add_warning(self) -> None:
        """Increment warning count."""
        self.stats.warnings += 1
        
    def add_error(self) -> None:
        """Increment error count."""
        self.stats.failed += 1
        
    def finish(self, final_message: str = "Processing complete") -> None:
        """Complete progress display."""
        self._show_cursor()
        if self.show_stats:
            self._render_final_stats(final_message)
        else:
            self.file.write(f"\n{final_message}\n")
        self.file.flush()
    
    def _hide_cursor(self) -> None:
        """Hide terminal cursor for cleaner progress display."""
        if not self.formatter.no_color:
            self.file.write(Colors.HIDE_CURSOR)
            self._cursor_hidden = True
    
    def _show_cursor(self) -> None:
        """Show terminal cursor."""
        if self._cursor_hidden and not self.formatter.no_color:
            self.file.write(Colors.SHOW_CURSOR)
            self._cursor_hidden = False
    
    def _clear_current_line(self) -> None:
        """Clear the current terminal line."""
        if not self.formatter.no_color:
            self.file.write(f"\r{Colors.CLEAR_LINE}")
        else:
            # Fallback: overwrite with spaces
            self.file.write(f"\r{' ' * self.last_line_length}\r")
    
    def _render_progress(self, description: str = "Processing") -> None:
        """Render the complete progress display."""
        self._clear_current_line()
        
        # Calculate progress bar width (leave room for other info)
        terminal_width = self.formatter.capabilities.terminal_width
        available_width = max(terminal_width - 60, 20)  # Reserve space for stats
        
        # Create progress bar
        progress_bar = self.formatter.progress_bar(
            self.stats.completed,
            self.stats.total,
            width=min(available_width, 40)
        )
        
        # Format percentage
        percentage = self.formatter.colorize(
            f"{self.stats.progress_percentage:5.1f}%",
            "bright_white",
            bold=True
        )
        
        # Format current target filename
        target_display = ""
        if self.current_filename:
            # Truncate filename if too long
            max_filename_length = max(terminal_width - 80, 15)
            display_name = self.current_filename
            if len(display_name) > max_filename_length:
                display_name = display_name[:max_filename_length-3] + "..."
            
            target_display = f" → {self.formatter.highlight_filename(display_name)}"
        
        # Format status indicator
        status_display = ""
        if self.current_status:
            status_display = f" {self._format_status_indicator(self.current_status)}"
        
        # Main progress line
        progress_line = f"{progress_bar} {percentage}{target_display}{status_display}"
        
        # Write progress line
        self.file.write(progress_line)
        self.last_line_length = len(progress_line)
        
        # Add stats line if enabled
        if self.show_stats and self.stats.total > 0:
            stats_line = self._format_stats_line()
            self.file.write(f"\n{stats_line}")
            # Move cursor back up to progress line
            if not self.formatter.no_color:
                self.file.write(Colors.CURSOR_UP)
        
        self.file.flush()
    
    def _format_status_indicator(self, status: str) -> str:
        """Format status with appropriate color and icon."""
        status_config = {
            "processing": ("blue", "⚙️", "Processing"),
            "extracting_content": ("cyan", "📄", "Extracting"),
            "generating_filename": ("blue", "🤖", "AI Processing"),
            "moving_file": ("green", "📁", "Organizing"),
            "completed": ("bright_green", "✅", "Done"),
            "failed": ("bright_red", "❌", "Failed"),
            "warning": ("bright_yellow", "⚠️", "Warning"),
            "skipped": ("dim", "⏭️", "Skipped"),
            "retrying": ("yellow", "🔄", "Retrying"),
            "recovered": ("bright_green", "♻️", "Recovered"),
            "temp_issue": ("yellow", "⏳", "Waiting"),
        }
        
        color, icon, text = status_config.get(status, ("white", "•", status))
        
        # Use ASCII fallback if Unicode not supported
        if not self.formatter.capabilities.supports_unicode:
            icon_map = {
                "⚙️": "[PROC]",
                "📄": "[EXTR]",
                "🤖": "[AI]",
                "📁": "[ORG]",
                "✅": "[OK]",
                "❌": "[ERR]",
                "⚠️": "[WARN]",
                "⏭️": "[SKIP]",
                "🔄": "[RETRY]",
                "♻️": "[RECOV]",
                "⏳": "[WAIT]",
            }
            icon = icon_map.get(icon, icon)
        
        return self.formatter.colorize(f"{icon} {text}", color)
    
    def _format_stats_line(self) -> str:
        """Format statistics line."""
        stats_parts = []
        
        # Success count
        if self.stats.success_count > 0:
            success_text = f"✅ {self.stats.success_count} processed"
            if not self.formatter.capabilities.supports_unicode:
                success_text = f"[OK] {self.stats.success_count} processed"
            stats_parts.append(
                self.formatter.colorize(success_text, "bright_green")
            )
        
        # Warning count
        if self.stats.warnings > 0:
            warn_text = f"⚠️ {self.stats.warnings} warnings"
            if not self.formatter.capabilities.supports_unicode:
                warn_text = f"[WARN] {self.stats.warnings} warnings"
            stats_parts.append(
                self.formatter.colorize(warn_text, "bright_yellow")
            )
        
        # Error count
        if self.stats.failed > 0:
            error_text = f"❌ {self.stats.failed} errors"
            if not self.formatter.capabilities.supports_unicode:
                error_text = f"[ERR] {self.stats.failed} errors"
            stats_parts.append(
                self.formatter.colorize(error_text, "bright_red")
            )
        
        # Elapsed time
        elapsed_display = f"⏱️ {self.formatter.format_time(self.stats.elapsed_time)} elapsed"
        if not self.formatter.capabilities.supports_unicode:
            elapsed_display = f"[TIME] {self.formatter.format_time(self.stats.elapsed_time)} elapsed"
        
        stats_parts.append(elapsed_display)
        
        return " │ ".join(stats_parts) if stats_parts else ""
    
    def _render_final_stats(self, message: str) -> None:
        """Render final completion statistics."""
        self.file.write(f"\n\n{message}\n")
        
        if self.stats.total > 0:
            # Summary statistics
            success_rate = (self.stats.success_count / self.stats.total) * 100
            
            summary_parts = [
                f"Total: {self.stats.total}",
                self.formatter.colorize(f"Successful: {self.stats.success_count}", "bright_green"),
                f"Success rate: {success_rate:.1f}%"
            ]
            
            if self.stats.warnings > 0:
                summary_parts.append(
                    self.formatter.colorize(f"Warnings: {self.stats.warnings}", "bright_yellow")
                )
            
            if self.stats.failed > 0:
                summary_parts.append(
                    self.formatter.colorize(f"Errors: {self.stats.failed}", "bright_red")
                )
            
            summary_parts.append(f"Time: {self.formatter.format_time(self.stats.elapsed_time)}")
            
            self.file.write(" • ".join(summary_parts) + "\n")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cursor is restored."""
        self._show_cursor()


class SimpleProgressDisplay:
    """Simple fallback progress display for compatibility."""
    
    def __init__(self, file: Optional[TextIO] = None, **kwargs):
        self.completed = 0
        self.total = 0
        self.file = file or sys.stdout
    
    def start(self, total: int, description: str = "Processing") -> None:
        self.total = total
        self.file.write(f"{description} {total} files...\n")
        self.file.flush()
    
    def update(self, filename: str = "", status: str = "", increment: bool = True) -> None:
        if increment:
            self.completed += 1
        if filename:
            self.file.write(f"[{self.completed}/{self.total}] {filename}\n")
            self.file.flush()
    
    def add_warning(self) -> None:
        pass
    
    def add_error(self) -> None:
        pass
    
    def finish(self, final_message: str = "Processing complete") -> None:
        self.file.write(f"{final_message}\n")
        self.file.flush()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass