"""
Test-specific display manager that avoids Rich I/O conflicts.

This display manager provides the same interface as the regular DisplayManager
but uses simple print statements instead of Rich UI components to avoid
I/O conflicts during test execution.
"""

import os
import sys
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Add src to path if not already added
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Create compatible DisplayOptions class
class TestDisplayOptions:
    def __init__(self, quiet: bool = False, no_color: bool = False, **_):
        self.quiet = quiet
        self.no_color = no_color


class TestDisplayManager:
    """Test-specific display manager that avoids Rich I/O conflicts."""

    def __init__(self, options: Optional[TestDisplayOptions] = None):
        """Initialize test display manager."""
        self.options = options or TestDisplayOptions(quiet=True, no_color=True)
        self.quiet = self.options.quiet

        # Track statistics for test validation
        class Stats:
            def __init__(self):
                self.processed: int = 0
                self.failed: int = 0
                self.warnings: int = 0
                self.total: int = 0
                self.success_rate: float = 0.0
                self.succeeded: int = 0  # Alternative naming
                self.errors: int = 0      # Alternative naming

        self.stats = Stats()

        # Capture output for test validation
        self.output_lines = []

        # Mock progress object
        class Progress:
            def __init__(self, stats):
                self.stats = stats

        self.progress = Progress(self.stats)

    def info(self, message: str, **_):
        """Display info message."""
        if not self.quiet:
            self.output_lines.append(f"INFO: {message}")

    def success(self, message: str, **_):
        """Display success message."""
        if not self.quiet:
            self.output_lines.append(f"SUCCESS: {message}")
        self.stats.processed += 1
        self.stats.succeeded += 1

    def error(self, message: str, **_):
        """Display error message."""
        if not self.quiet:
            self.output_lines.append(f"ERROR: {message}")
        self.stats.failed += 1
        self.stats.errors += 1

    def warning(self, message: str, **_):
        """Display warning message."""
        if not self.quiet:
            self.output_lines.append(f"WARNING: {message}")
        self.stats.warnings += 1

    def show_startup_info(self, _=None, **_kwargs):
        """Show startup information."""
        if not self.quiet:
            self.output_lines.append("STARTUP: Content Tamer AI starting")

    def show_completion_summary(self, stats=None, **_):
        """Show completion summary."""
        if not self.quiet and stats:
            successful = stats.get('successful', 0) if isinstance(stats, dict) else getattr(stats, 'successful', 0)
            self.output_lines.append(f"SUMMARY: Processed {successful} files successfully")

    def show_completion_stats(self, stats=None, **_):
        """Show completion statistics."""
        if not self.quiet and stats:
            self.output_lines.append("STATS: Completion stats displayed")

    def print(self, message: str, **_):
        """Print message (Rich console compatibility)."""
        if not self.quiet:
            self.output_lines.append(str(message))

    @contextmanager
    def processing_context(self, total_files: int = 0, description: str = "Processing"):
        """Create processing context for batch operations."""
        self.stats.total = total_files
        if not self.quiet:
            self.output_lines.append(f"PROCESSING: {description} ({total_files} files)")

        try:
            # Create a simple context object
            context = TestProcessingContext(self)
            yield context
        finally:
            # Calculate final statistics
            if self.stats.total > 0:
                self.stats.success_rate = (self.stats.processed / self.stats.total) * 100
            if not self.quiet:
                self.output_lines.append(f"COMPLETED: {self.stats.processed}/{self.stats.total} files processed")

    def get_output(self) -> str:
        """Get captured output for test validation."""
        return "\n".join(self.output_lines)


class TestProcessingContext:
    """Test-specific processing context."""

    def __init__(self, display_manager: TestDisplayManager):
        """Initialize processing context."""
        self.display_manager = display_manager
        self.current_file: Optional[str] = None

    def start_file(self, filename: str):
        """Start processing a file."""
        self.current_file = filename
        if not self.display_manager.quiet:
            self.display_manager.output_lines.append(f"PROCESSING: {filename}")

    def set_status(self, status: str):
        """Set current processing status."""
        if not self.display_manager.quiet and self.current_file:
            self.display_manager.output_lines.append(f"STATUS: {self.current_file} - {status}")

    def complete_file(self, original_name: str, new_name: str):
        """Complete file processing successfully."""
        self.display_manager.success(f"{original_name} -> {new_name}")
        self.current_file = None

    def fail_file(self, filename: str, error: str):
        """Mark file processing as failed."""
        self.display_manager.error(f"{filename}: {error}")
        self.current_file = None

    def show_warning(self, message: str, filename: Optional[str] = None):
        """Show warning message."""
        if filename:
            self.display_manager.warning(f"{filename}: {message}")
        else:
            self.display_manager.warning(message)

    def show_error(self, message: str):
        """Show error message."""
        self.display_manager.error(message)


def create_test_display_options(**kwargs) -> Dict[str, Any]:
    """Create display options optimized for testing."""
    return {
        'quiet': kwargs.get('quiet', True),
        'no_color': kwargs.get('no_color', True),
        'use_test_display': True,  # Signal to use test display manager
        **kwargs
    }
