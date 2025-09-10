"""
Rich CLI Display System

Provides beautiful, engaging command-line interface with colors, formatting,
and cross-platform compatibility using the Rich library.
"""

# Typing imports not used - keeping for future type hints

from rich.align import Align

# RenderableType imported but not used - keeping for future rich typing
from rich.console import Console, RenderableType  # pylint: disable=unused-import
from rich.panel import Panel
from rich.rule import Rule

# Style imported but not used - keeping for future styling enhancements
from rich.style import Style  # pylint: disable=unused-import
from rich.table import Table
from rich.text import Text


class MessageLevel:
    """Message level constants for consistent styling."""

    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RichCLIDisplay:
    """Rich-powered CLI display system for delightful user interactions."""

    def __init__(self, console: Console, no_color: bool = False):  # pylint: disable=unused-argument
        """
        Initialize RichCLIDisplay with injected Console.

        Args:
            console: Rich Console instance to use for all output
            no_color: Whether to disable colors (for legacy compatibility)
        """
        if console is None:
            raise ValueError("Console instance is required for RichCLIDisplay")

        self.console = console

        # Message styling configuration
        self.styles = {
            MessageLevel.DEBUG: ("🔍", "dim cyan", "DEBUG"),
            MessageLevel.INFO: ("ℹ️", "blue", "INFO"),
            MessageLevel.SUCCESS: ("✅", "bright_green", "SUCCESS"),
            MessageLevel.WARNING: ("⚠️", "yellow", "WARNING"),
            MessageLevel.ERROR: ("❌", "red", "ERROR"),
            MessageLevel.CRITICAL: ("🚨", "bold red", "CRITICAL"),
        }

    def debug(self, message: str, **kwargs) -> None:
        """Display debug message with subtle styling."""
        self._print_message(message, MessageLevel.DEBUG, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Display informational message with clear visibility."""
        self._print_message(message, MessageLevel.INFO, **kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Display success message with celebration."""
        self._print_message(message, MessageLevel.SUCCESS, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Display warning message with attention-getting style."""
        self._print_message(message, MessageLevel.WARNING, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Display error message with clear problem indication."""
        self._print_message(message, MessageLevel.ERROR, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Display critical error with urgent styling."""
        self._print_message(message, MessageLevel.CRITICAL, **kwargs)

    def _print_message(self, message: str, level: str, **kwargs) -> None:
        """Print formatted message with appropriate styling."""
        _, color, label = self.styles[level]

        # Create formatted message
        text = Text()
        text.append(f"[{label}] ", style=f"bold {color}")
        text.append(message, style=color if level == MessageLevel.CRITICAL else "")

        self.console.print(text, **kwargs)

    def print_header(self, title: str, subtitle: str = "") -> None:
        """Display application header with attractive styling."""
        header_text = Text()
        header_text.append("🎯 ", style="bold cyan")
        header_text.append(title.upper(), style="bold bright_cyan")

        if subtitle:
            header_text.append("\n")
            header_text.append(subtitle, style="dim cyan")

        panel = Panel(
            Align.center(header_text),
            border_style="bright_cyan",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def print_section(self, title: str, style: str = "cyan") -> None:
        """Display section header with visual separation."""
        self.console.print(Rule(f"[bold {style}]{title}[/bold {style}]", style=style))

    def print_capabilities(self, ocr_deps: dict, ocr_settings: dict) -> None:
        """Display system capabilities with beautiful formatting."""
        self.print_section("System Capabilities", "bright_blue")

        # Create capabilities table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Component", style="cyan", min_width=15)
        table.add_column("Status", min_width=10)
        table.add_column("Details", style="dim")

        # OCR dependencies
        for dep, available in ocr_deps.items():
            status_icon = "✅" if available else "❌"
            status_text = "Available" if available else "Missing"
            status_style = "green" if available else "red"

            table.add_row(
                f"{dep}:",
                f"[{status_style}]{status_icon} {status_text}[/{status_style}]",
                (
                    "Required for PDF text extraction"
                    if dep == "PyMuPDF"
                    else "Required for image OCR"
                ),
            )

        # OCR settings
        table.add_row("", "", "")  # Spacer
        for setting, value in ocr_settings.items():
            if setting == "OCR_LANG":
                table.add_row("Language:", f"[cyan]{value}[/cyan]", "Text recognition language")
            elif setting == "OCR_PAGES":
                table.add_row(
                    "Max Pages:",
                    f"[cyan]{value}[/cyan]",
                    "Pages processed per document",
                )
            elif setting == "OCR_ZOOM":
                table.add_row(
                    "Image Zoom:",
                    f"[cyan]{value}x[/cyan]",
                    "Resolution enhancement factor",
                )

        self.console.print(table)
        self.console.print()

    def print_api_key_prompt(self, provider: str) -> None:
        """Display beautiful API key input prompt."""
        self.print_section(f"{provider.title()} API Key", "magenta")

        # Create informative panel
        info_text = Text()
        info_text.append("🔐 ", style="yellow")
        info_text.append("Type or paste your API key (you'll see it as you type)\n", style="white")
        info_text.append("🔑 ", style="cyan")
        info_text.append(
            f"{provider.title()} keys start with 'sk-' and are typically 40-60 characters\n",
            style="dim",
        )
        info_text.append("💡 ", style="green")
        info_text.append(
            f"You can set {provider.upper()}_API_KEY environment variable to skip this step\n",
            style="dim",
        )
        info_text.append("🔒 ", style="blue")
        info_text.append(
            "Your key will be validated and cleared from display after entry",
            style="dim",
        )

        panel = Panel(
            info_text,
            title="API Key Input",
            title_align="left",
            border_style="magenta",
            padding=(1, 2),
        )

        self.console.print(panel)

    def print_api_key_validation(self, key: str, key_length: int) -> None:
        """Display API key validation results."""
        masked_key = f"{key[:8]}{'*' * (key_length - 16)}{key[-8:]}"

        validation_text = Text()
        validation_text.append("[OK] ", style="bold green")
        validation_text.append("Received API key: ", style="white")
        validation_text.append(f"{masked_key} ({key_length} characters)", style="cyan")

        self.console.print(validation_text)

        # Validation success
        success_text = Text()
        success_text.append("[OK] ", style="bold green")
        success_text.append("API key format validated successfully", style="green")
        self.console.print(success_text)

    def print_provider_setup(self, provider: str, model: str) -> None:
        """Display provider setup confirmation with style."""
        setup_text = Text()
        setup_text.append("[OK] ", style="bold green")
        setup_text.append(f"{provider.title()} API key accepted and secured.", style="green")

        self.console.print(setup_text)
        self.console.print()

        # Model info
        model_text = Text()
        model_text.append("[INFO] ", style="bold blue")
        model_text.append(f"Using {provider} provider with model ", style="blue")
        model_text.append(model, style="bold cyan")

        self.console.print(model_text)

    def print_directory_info(self, directories: dict) -> None:
        """Display directory configuration with clear paths."""
        self.console.print()

        # Create directory info table
        for label, path in directories.items():
            info_text = Text()
            info_text.append("[INFO] ", style="bold blue")
            info_text.append(f"{label}: ", style="blue")
            info_text.append(str(path), style="bright_white")
            self.console.print(info_text)

    def print_available_models(self, providers: dict) -> None:
        """Display available models in beautiful table format."""
        self.print_section("Available AI Models", "bright_magenta")

        # Create models table
        table = Table(show_header=True, header_style="bold bright_magenta")
        table.add_column("Provider", style="cyan", min_width=12)
        table.add_column("Available Models", style="white")
        table.add_column("Recommended", style="green")

        # Add provider rows
        for provider, models in providers.items():
            models_text = ", ".join(models)
            recommended = models[0] if models else "N/A"  # First model is usually default

            table.add_row(provider.title(), models_text, f"✨ {recommended}")

        self.console.print(table)
        self.console.print()

    def print_error_summary(self, error_details: list) -> None:
        """Display error summary with helpful formatting."""
        if not error_details:
            return

        self.print_section("Detailed Error Summary", "red")

        for error in error_details:
            filename = error.get("filename", "Unknown file")
            error_msg = error.get("error", "Unknown error")

            error_text = Text()
            error_text.append("[ERROR] ", style="bold red")
            error_text.append("❌ ", style="red")
            error_text.append(f"{filename}: ", style="bright_white")
            error_text.append(error_msg, style="red")

            self.console.print(error_text)

        self.console.print()

    def print_completion_message(
        self, success_rate: float, total_files: int  # pylint: disable=unused-argument
    ) -> None:
        """Display completion message with appropriate celebration level."""
        self.console.print()

        if success_rate >= 100:
            # Perfect success!
            completion_text = Text()
            completion_text.append("[OK] ", style="bold bright_green")
            completion_text.append("Processing complete: ", style="bright_green")
            completion_text.append("🎉 100% success rate! 🎉", style="bold bright_green")
        elif success_rate >= 80:
            # Good success rate
            completion_text = Text()
            completion_text.append("[OK] ", style="bold green")
            completion_text.append("Processing complete: ", style="green")
            completion_text.append(f"{success_rate:.1f}% success rate", style="bright_green")
        elif success_rate > 0:
            # Partial success
            completion_text = Text()
            completion_text.append("[OK] ", style="bold yellow")
            completion_text.append("Processing complete: ", style="yellow")
            completion_text.append(f"{success_rate:.1f}% success rate", style="bright_yellow")
        else:
            # No successes
            completion_text = Text()
            completion_text.append("[ERROR] ", style="bold red")
            completion_text.append("Processing complete: ", style="red")
            completion_text.append("0.0% success rate", style="bright_red")

        self.console.print(completion_text)

    def highlight_filename(self, filename: str) -> Text:
        """Create highlighted filename text for display."""
        text = Text()

        # Split filename and extension
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            text.append(name, style="bright_white")
            text.append(".", style="dim")
            text.append(ext, style="cyan")
        else:
            text.append(filename, style="bright_white")

        return text

    def format_time(self, seconds: float) -> str:
        """Format elapsed time in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            return f"{hours}h {remaining_minutes}m"

    def clear_screen(self) -> None:
        """Clear screen with Rich-compatible method."""
        self.console.clear()

    def print_rule(self, title: str = "", style: str = "white") -> None:
        """Print a horizontal rule with optional title."""
        if title:
            self.console.print(Rule(title, style=style))
        else:
            self.console.print(Rule(style=style))
