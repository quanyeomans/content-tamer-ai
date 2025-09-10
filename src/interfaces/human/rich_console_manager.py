"""
Centralized Rich Console Management

Provides singleton Rich Console management specifically for human interfaces.
Ensures consistent UI experience across all human-facing components.
Integrates with shared display infrastructure for unified Rich UI patterns.
"""

import threading
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel

# TaskID imported but not used - keeping for future progress management
from rich.progress import (  # pylint: disable=unused-import
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Text imported but not used - keeping for future rich text formatting
from rich.text import Text  # pylint: disable=unused-import
from rich.theme import Theme

# Integration with shared display infrastructure
try:
    from src.shared.display.emoji_handler import SmartEmojiHandler
except ImportError:
    # Fallback for when running from src directory
    from shared.display.emoji_handler import SmartEmojiHandler


class RichConsoleManager:
    """Centralized Rich Console for human interfaces."""

    _instance: Optional["RichConsoleManager"] = None
    _console: Optional[Console] = None
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
            self._current_progress: Optional[Progress] = None

    @property
    def console(self) -> Console:
        """Get or create Rich Console instance."""
        if self._console is None:
            self._console = self._create_console()
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
        # Use Rich's auto-detection with Windows emoji handling
        import os
        import platform

        # sys imported but not used - keeping for future system utilities
        import sys  # pylint: disable=unused-import

        # Set environment for better Windows Terminal support
        if platform.system() == "Windows":
            # Enable UTF-8 support for Windows Terminal
            os.environ.setdefault("PYTHONIOENCODING", "utf-8")

        console = Console(
            theme=theme,
            force_terminal=None,  # Let Rich auto-detect terminal capabilities
            width=None,  # Auto-detect terminal width
            # Rich will handle emoji rendering based on actual terminal capabilities
            # In Windows Terminal: Full emoji support
            # In cmd.exe: Automatic text fallbacks
        )

        # Initialize smart emoji handler with console
        self._emoji_handler = SmartEmojiHandler(console)

        return console

    def create_progress_display(
        self, description: str = "Processing"
    ) -> Progress:  # pylint: disable=unused-argument
        """Create consistent progress display for human interface."""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="progress.complete", finished_style="progress.complete"),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
            transient=False,  # Keep progress visible after completion
        )
        self._current_progress = progress
        return progress

    def show_welcome_panel(self) -> None:
        """Standard welcome display using encoding-safe symbols (test framework pattern)."""
        # Use ASCII-safe symbols following established test framework approach
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
        panel = Panel(
            content, title=f"[{style}]{title}[/{style}]", border_style=style, padding=(0, 1)
        )
        self.console.print(panel)

    def show_error_panel(self, title: str, error: str, suggestions: Optional[list] = None) -> None:
        """Display error panel with optional suggestions."""
        content = f"[error]{error}[/error]"

        if suggestions:
            content += "\n\n[bold white]Suggestions:[/bold white]"
            for suggestion in suggestions:
                content += f"\n• {suggestion}"

        # Use smart emoji handler for error panel title
        title = self._emoji_handler.format_with_emoji("❌", "Error", "error")
        panel = Panel(content, title=title, border_style="error", padding=(0, 1))
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

        # Use smart emoji handler for success panel title
        title = self._emoji_handler.format_with_emoji("✅", "Success", "success")
        panel = Panel(content, title=title, border_style="success", padding=(0, 1))
        self.console.print(panel)

    def show_configuration_table(
        self, config: Dict[str, Any], title: str = "Configuration"
    ) -> None:
        """Display configuration in a formatted table."""
        table = Table(title=title, border_style="table.border")
        table.add_column("Setting", style="table.header", no_wrap=True)
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
        # Rich.Prompt.ask can return None if no default and user presses enter
        # But with choices and default, it should always return a string
        return result or (default if default else choices[0])

    def prompt_confirm(self, message: str, default: bool = True) -> bool:
        """Interactive confirmation prompt."""
        return Confirm.ask(message, default=default, console=self.console)

    def prompt_text(self, message: str, default: Optional[str] = None) -> str:
        """Interactive text input prompt."""
        result = Prompt.ask(message, default=default, console=self.console)
        # Rich.Prompt.ask can return None if no default and user presses enter
        # Return empty string in that case to maintain str return type
        return result or ""

    def show_status(self, message: str, status: str = "info") -> None:
        """Show status message with smart emoji usage using shared emoji handler."""
        # Use shared emoji handler for consistent cross-platform emoji support
        emoji_map = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "progress": "🔄"}

        emoji = emoji_map.get(status, "ℹ️")
        formatted = self._emoji_handler.format_with_emoji(emoji, message, status)
        self.console.print(formatted)

    def show_loading(self, message: str) -> None:
        """Show loading message with smart emoji usage."""
        formatted = self._emoji_handler.format_with_emoji("🔄", f"{message}...", "progress")
        self.console.print(formatted)

    def clear_screen(self) -> None:
        """Clear the console screen."""
        self.console.clear()

    def print_separator(self, char: str = "─", length: Optional[int] = None) -> None:
        """Print a separator line."""
        if length is None:
            length = self.console.size.width
        self.console.print(char * length, style="muted")

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
