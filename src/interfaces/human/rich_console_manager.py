"""
Centralized Rich Console Management (Refactored)

Provides singleton Rich Console management specifically for human interfaces.
Now acts as a facade over UnifiedDisplayManager to eliminate code duplication.
Maintains backward compatibility while delegating to shared display infrastructure.
"""

import threading
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.theme import Theme

# Integration with shared display infrastructure
try:
    from src.shared.display.unified_display_manager import UnifiedDisplayManager
    from src.shared.display.display_interface import IDisplayManager
except ImportError:
    # Fallback for when running from src directory
    from shared.display.unified_display_manager import UnifiedDisplayManager
    from shared.display.display_interface import IDisplayManager


class RichConsoleManager(IDisplayManager):
    """Centralized Rich Console for human interfaces - facade over UnifiedDisplayManager."""

    _instance: Optional["RichConsoleManager"] = None
    _console: Optional[Console] = None
    _display_manager: Optional[UnifiedDisplayManager] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RichConsoleManager":
        """Ensure singleton pattern for consistent console management."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize console manager (only once due to singleton)."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._console = None
            self._display_manager = None
            self._current_progress: Optional[Progress] = None
            # Keep emoji handler reference for backward compatibility
            self._emoji_handler = None

    @property
    def console(self) -> Console:
        """Get or create Rich Console instance."""
        if self._console is None:
            self._console = self._create_console()
            # Create display manager with our console
            self._display_manager = UnifiedDisplayManager(console=self._console, quiet_mode=False)
            # Store emoji handler reference for backward compatibility
            self._emoji_handler = self._display_manager.emoji
        return self._console

    def _create_console(self) -> Console:
        """Create Rich Console with Content Tamer AI theme."""
        theme = Theme(
            {
                # Status colors
                "info": "blue",
                "warning": "yellow",
                "error": "red bold",
                "success": "green bold",
                "progress": "cyan",
                # UI elements
                "header": "bold blue",
                "subheader": "bold white",
                "highlight": "bold yellow",
                "muted": "dim white",
                "accent": "magenta",
                # Progress bars
                "progress.bar": "cyan",
                "progress.complete": "green",
                "progress.remaining": "dim cyan",
                # Tables
                "table.header": "bold blue",
                "table.border": "dim white",
            }
        )

        # Auto-detect terminal capabilities with proper encoding
        import os
        import platform

        # Set environment for better Windows Terminal support
        if platform.system() == "Windows":
            os.environ.setdefault("PYTHONIOENCODING", "utf-8")

        console = Console(
            theme=theme,
            force_terminal=None,  # Let Rich auto-detect terminal capabilities
            width=None,  # Auto-detect terminal width
        )

        return console

    # ========== Delegated Display Methods ==========
    # These methods delegate to UnifiedDisplayManager to eliminate duplication

    def info(self, message: str, context: Optional[str] = None) -> None:
        """Display info message."""
        self._ensure_display_manager()
        self._display_manager.info(message, context)

    def success(self, message: str, context: Optional[str] = None) -> None:
        """Display success message."""
        self._ensure_display_manager()
        self._display_manager.success(message, context)

    def warning(self, message: str, context: Optional[str] = None) -> None:
        """Display warning message."""
        self._ensure_display_manager()
        self._display_manager.warning(message, context)

    def error(
        self, message: str, context: Optional[str] = None, suggestions: Optional[List[str]] = None
    ) -> None:
        """Display error message with optional suggestions."""
        self._ensure_display_manager()
        self._display_manager.error(message, context, suggestions)

    def show_panel(self, title: str, content: str, style: str = "blue") -> None:
        """Display content in a panel."""
        self._ensure_display_manager()
        self._display_manager.show_panel(title, content, style)

    def show_table(
        self, title: str, headers: List[str], rows: List[List[str]], style: str = "blue"
    ) -> None:
        """Display data in a table."""
        self._ensure_display_manager()
        self._display_manager.show_table(title, headers, rows, style)

    def start_progress(self, description: str = "Processing") -> str:
        """Start progress display."""
        self._ensure_display_manager()
        return self._display_manager.start_progress(description)

    def update_progress(
        self, progress_id: str, current: int, total: int, description: Optional[str] = None
    ) -> None:
        """Update progress display."""
        self._ensure_display_manager()
        self._display_manager.update_progress(progress_id, current, total, description)

    def finish_progress(self, progress_id: str) -> None:
        """Finish progress display."""
        self._ensure_display_manager()
        self._display_manager.finish_progress(progress_id)

    def clear_screen(self) -> None:
        """Clear the console screen."""
        self._ensure_display_manager()
        self._display_manager.clear_screen()

    def print_separator(self, char: str = "─", length: Optional[int] = None) -> None:
        """Print a separator line."""
        self._ensure_display_manager()
        if length is not None:
            # For backward compatibility when length is specified
            self.console.print(char * length, style="muted")
        else:
            self._display_manager.print_separator(char)

    def show_processing_summary(self, results: Dict[str, Any]) -> None:
        """Show processing summary."""
        self._ensure_display_manager()
        self._display_manager.show_processing_summary(results)

    def get_display_capabilities(self) -> Dict[str, Any]:
        """Get display system capabilities."""
        self._ensure_display_manager()
        return self._display_manager.get_display_capabilities()

    # ========== Human Interface Specific Methods ==========
    # These remain in RichConsoleManager as they're specific to human interaction

    def create_progress_display(self, description: str = "Processing") -> Progress:
        """Create consistent progress display for human interface."""
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            SpinnerColumn,
            TextColumn,
        )

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
            transient=False,  # Keep progress visible after completion
        )
        self._current_progress = progress
        return progress

    def show_welcome_panel(self) -> None:
        """Standard welcome display using encoding-safe symbols."""
        self.console.print()
        self.console.print(">> [bold blue]CONTENT TAMER AI[/bold blue] <<")
        self.console.print(
            "[cyan]Intelligent document processing with AI-powered organization[/cyan]"
        )
        self.console.print()

    def show_section_header(self, title: str, description: Optional[str] = None) -> None:
        """Display section header with optional description."""
        self.console.print(f"\n[header]{title}[/header]")
        if description:
            self.console.print(f"[muted]{description}[/muted]")
        self.console.print()

    def show_info_panel(self, title: str, content: str, style: str = "info") -> None:
        """Display informational panel."""
        # Convert theme style to color
        color_style = "blue" if style == "info" else style
        self.show_panel(title, content, color_style)

    def show_error_panel(self, title: str, error: str, suggestions: Optional[list] = None) -> None:
        """Display error panel with optional suggestions."""
        content = f"[error]{error}[/error]"

        if suggestions:
            content += "\n\n[bold white]Suggestions:[/bold white]"
            for suggestion in suggestions:
                content += f"\n• {suggestion}"

        # Use emoji handler for error panel title
        self._ensure_display_manager()
        title_formatted = self._display_manager.emoji.format_with_emoji("❌", "Error", "error")
        from rich.panel import Panel
        panel = Panel(content, title=title_formatted, border_style="red", padding=(0, 1))
        self.console.print(panel)

    def show_success_panel(
        self, title: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Display success panel with optional details."""
        content = f"[success]{message}[/success]"

        if details:
            content += "\n\n[bold white]Details:[/bold white]"
            for key, value in details.items():
                content += f"\n• {key}: [highlight]{value}[/highlight]"

        # Use emoji handler for success panel title
        self._ensure_display_manager()
        title_formatted = self._display_manager.emoji.format_with_emoji("✅", "Success", "success")
        from rich.panel import Panel
        panel = Panel(content, title=title_formatted, border_style="green", padding=(0, 1))
        self.console.print(panel)

    def show_configuration_table(
        self, config: Dict[str, Any], title: str = "Configuration"
    ) -> None:
        """Display configuration in a formatted table."""
        from rich.table import Table
        
        table = Table(title=title, border_style="dim white")
        table.add_column("Setting", style="bold blue", no_wrap=True)
        table.add_column("Value", style="white")

        for key, value in config.items():
            # Format value for display
            if isinstance(value, bool):
                display_value = "[success]✓ Yes[/success]" if value else "[muted]✗ No[/muted]"
            elif value is None:
                display_value = "[muted]Not set[/muted]"
            else:
                display_value = str(value)

            table.add_row(key, display_value)

        self.console.print(table)

    def prompt_choice(self, message: str, choices: list, default: Optional[str] = None) -> str:
        """Interactive choice prompt with validation."""
        result = Prompt.ask(message, choices=choices, default=default, console=self.console)
        return result or (default if default else choices[0])

    def prompt_confirm(self, message: str, default: bool = True) -> bool:
        """Interactive confirmation prompt."""
        return Confirm.ask(message, default=default, console=self.console)

    def prompt_text(self, message: str, default: Optional[str] = None) -> str:
        """Interactive text input prompt."""
        result = Prompt.ask(message, default=default, console=self.console)
        return result or ""

    def show_status(self, message: str, status: str = "info") -> None:
        """Show status message with smart emoji usage."""
        self._ensure_display_manager()
        emoji_map = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "progress": "🔄"}
        emoji = emoji_map.get(status, "ℹ️")
        formatted = self._display_manager.emoji.format_with_emoji(emoji, message, status)
        self.console.print(formatted)

    def show_loading(self, message: str) -> None:
        """Show loading message with smart emoji usage."""
        self._ensure_display_manager()
        formatted = self._display_manager.emoji.format_with_emoji("🔄", f"{message}...", "progress")
        self.console.print(formatted)

    def get_terminal_size(self) -> tuple:
        """Get terminal dimensions (width, height)."""
        size = self.console.size
        return (size.width, size.height)

    def is_terminal_capable(self) -> bool:
        """Check if terminal supports Rich features."""
        return self.console.is_terminal and not self.console.legacy_windows

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle error display with user-friendly messaging and suggestions."""
        error_message = str(error)
        error_type = type(error).__name__

        # Prepare suggestions based on error type and context
        suggestions = []

        if context:
            if "configuration_wizard" in context.get("context", ""):
                suggestions.extend(
                    [
                        "Check your input values and try again",
                        "Ensure all required paths exist and are accessible",
                        "Verify your API key is correctly formatted",
                        "Use --help to see all available options",
                    ]
                )

            if "api_key" in str(error).lower():
                suggestions.extend(
                    [
                        "Verify your API key is correct and active",
                        "Set your API key as an environment variable",
                        "Check if the AI provider service is available",
                    ]
                )

            if "path" in str(error).lower() or "directory" in str(error).lower():
                suggestions.extend(
                    [
                        "Ensure the directory exists and is accessible",
                        "Check folder permissions",
                        "Use absolute paths to avoid confusion",
                    ]
                )

        # Generic suggestions if none specific
        if not suggestions:
            suggestions = [
                "Review the error details above",
                "Check the documentation for guidance",
                "Ensure all prerequisites are met",
            ]

        # Display error panel with suggestions
        self.show_error_panel(f"{error_type} Error", error_message, suggestions)

    # ========== Helper Methods ==========

    def _ensure_display_manager(self) -> None:
        """Ensure display manager is initialized."""
        if self._display_manager is None:
            _ = self.console  # This will initialize both console and display manager