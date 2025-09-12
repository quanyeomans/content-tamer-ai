"""
Interactive CLI - Rich Human Interface

Provides guided navigation, expert mode, and Rich UI components
for human users. Depends on programmatic interface for business logic.
"""

# os imported but not used - keeping for future utilities
import os  # pylint: disable=unused-import
import sys
from typing import Any, Dict, List, Optional

from ..base_interfaces import HumanInterface, ProcessingResult
from ..programmatic.cli_arguments import ParsedArguments, PureCLIParser
from ..programmatic.configuration_manager import ConfigurationManager, ProcessingConfiguration
from .configuration_wizard import ExpertConfigurationWizard
from .rich_console_manager import RichConsoleManager

# Integration with shared display infrastructure
try:
    from src.shared.display.unified_display_manager import UnifiedDisplayManager
except ImportError:
    # Fallback for when running from src directory
    from shared.display.unified_display_manager import UnifiedDisplayManager


class InteractiveCLI(HumanInterface):
    """Main human interface for Content Tamer AI."""

    def __init__(self):
        """Initialize interactive CLI with all dependencies."""
        self.console_manager = RichConsoleManager()
        self.parser = PureCLIParser()
        self.config_manager = ConfigurationManager()
        self.wizard = ExpertConfigurationWizard(self.console_manager)

        # Store the console for interface contract compliance
        self._console = self.console_manager.console

        # Initialize unified display manager for additional display capabilities
        self.display_manager = UnifiedDisplayManager(console=self._console)

    def setup_console(self):
        """Initialize Rich Console for human interaction."""
        return self._console

    def show_progress(self, stage: str, current: int, total: int, detail: str = "") -> None:
        """Display human-friendly progress information."""
        if not hasattr(self, "_current_progress") or self._current_progress is None:
            self._current_progress = self.console_manager.create_progress_display()
            self._current_progress.start()

        # Update or create task
        if not hasattr(self, "_progress_task"):
            self._progress_task = self._current_progress.add_task(description=stage, total=total)

        # Update progress
        self._current_progress.update(
            self._progress_task, completed=current, description=f"{stage} {detail}".strip()
        )

        # Stop progress when complete
        if current >= total:
            self._current_progress.stop()
            self._current_progress = None

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Show user-friendly error message with guidance."""
        error_msg = str(error)
        suggestions = []

        # Provide context-specific suggestions
        if "API key" in error_msg.lower():
            suggestions.extend(
                [
                    "Check that your API key is set correctly",
                    f"Set environment variable: {context.get('provider', 'PROVIDER').upper()}_API_KEY",
                    "Use --api-key argument to provide key directly",
                ]
            )

        if "permission" in error_msg.lower():
            suggestions.extend(
                [
                    "Check file/directory permissions",
                    "Try running with appropriate permissions",
                    "Verify you have write access to output directory",
                ]
            )

        if "network" in error_msg.lower() or "connection" in error_msg.lower():
            suggestions.extend(
                [
                    "Check your internet connection",
                    "Verify firewall settings allow connections",
                    "Try again in a few moments",
                ]
            )

        if not suggestions:
            suggestions.append("Check the documentation or run with --verbose for more details")

        self.console_manager.show_error_panel(
            title="Error", error=error_msg, suggestions=suggestions
        )

    def prompt_user_choice(
        self, message: str, choices: List[str], default: Optional[str] = None
    ) -> str:
        """Interactive user prompting with validation."""
        return self.console_manager.prompt_choice(message, choices, default)

    def show_results(self, result: ProcessingResult) -> None:
        """Display processing results in human-friendly format."""
        if result.success:
            details = {
                "Files Processed": result.files_processed,
                "Output Directory": result.output_directory,
                "Total Time": result.metadata.get("processing_time", "N/A"),
            }

            if result.files_failed > 0:
                details["Files Failed"] = result.files_failed

            self.console_manager.show_success_panel(
                title="Processing Complete",
                message="Your documents have been successfully processed and organized!",
                details=details,
            )

            # Show any warnings
            if result.warnings:
                for warning in result.warnings:
                    self.console_manager.show_status(warning, "warning")

        else:
            self.console_manager.show_error_panel(
                title="Processing Failed",
                error="Document processing encountered errors",
                suggestions=[
                    f"Error: {error}" for error in result.errors[:3]
                ],  # Show first 3 errors
            )

    def run_interactive_setup(self) -> Optional[ParsedArguments]:
        """Main interactive setup flow."""
        # Welcome is already shown by main.py, don't duplicate it

        # Check if user provided command line arguments
        if len(sys.argv) > 1:
            # User is already using CLI arguments, just parse them
            try:
                args = self.parser.parse_args()
                errors = self.parser.validate_args(args)
                if errors:
                    self._show_validation_errors(errors)
                    return None
                return args
            except SystemExit:
                return None

        # Interactive setup flow
        return self._run_guided_setup()

    def _run_guided_setup(self) -> Optional[ParsedArguments]:
        """Run guided interactive setup."""
        self.console_manager.show_section_header(
            "Configuration", "Let's set up Content Tamer AI for your document processing needs"
        )

        # Ask about setup mode with clear options
        self.console_manager.console.print("[dim]Quick: Smart defaults for fast setup | Expert: Advanced configuration with full control[/dim]")
        mode_choice = self.console_manager.prompt_choice(
            "Choose your setup mode:", choices=["q", "e"], default="q"
        )

        if mode_choice == "e":
            return self._run_expert_mode()
        else:
            return self._run_quick_start()

    def _run_quick_start(self) -> Optional[ParsedArguments]:
        """Quick start with smart defaults."""
        self.console_manager.show_section_header(
            "Quick Start Setup", "Using smart defaults for fast setup"
        )

        # Load default configuration
        config = self.config_manager.load_configuration()

        # Only check for API key if not using local provider
        if config.provider != "local" and not config.api_key:
            self.console_manager.console.print()  # Add spacing before API key section
            self.console_manager.console.print(f"[yellow]Provider '{config.provider}' requires an API key[/yellow]")
            config.api_key = self.wizard._prompt_api_key_configuration(config.provider, config.api_key)
            if not config.api_key:
                return None
        elif config.provider == "local":
            # For local provider, verify Ollama is available
            from shared.infrastructure.dependency_manager import DependencyManager
            dep_manager = DependencyManager()
            ollama_path = dep_manager.find_dependency("ollama")
            if not ollama_path:
                self.console_manager.show_error(
                    "Local LLM provider requires Ollama to be installed",
                    ["Install Ollama from: https://ollama.ai", "Then run setup again"]
                )
                return None
            self.console_manager.console.print(f"[green]Using Local LLM with Ollama[/green]")

        self.console_manager.console.print()  # Add spacing before configuration summary
        # Show configuration summary
        summary = self.config_manager.get_configuration_summary(config)
        self.console_manager.show_configuration_table(summary, "Quick Start Configuration")

        # Confirm to proceed
        if self.console_manager.prompt_confirm("Proceed with this configuration?"):
            return self._config_to_args(config)
        else:
            self.console_manager.show_status("Setup cancelled", "info")
            return None

    def _run_expert_mode(self) -> Optional[ParsedArguments]:
        """Run expert configuration wizard."""
        self.console_manager.show_section_header(
            "Expert Mode", "Advanced configuration with full control"
        )

        try:
            config = self.wizard.run_configuration_wizard()
            if config:
                return self._config_to_args(config)
            else:
                self.console_manager.show_status("Configuration cancelled", "info")
                return None
        except KeyboardInterrupt:
            self.console_manager.show_status("Setup interrupted by user", "warning")
            return None

    # Removed duplicate _prompt_api_key method - quick start now uses expert mode wizard component

    def _config_to_args(self, config: ProcessingConfiguration) -> ParsedArguments:
        """Convert ProcessingConfiguration to ParsedArguments."""
        return ParsedArguments(
            input_dir=config.input_dir,
            output_dir=config.output_dir,
            unprocessed_dir=config.unprocessed_dir,
            provider=config.provider,
            model=config.model,
            api_key=config.api_key,
            ocr_language=config.ocr_language,
            reset_progress=config.reset_progress,
            organize=config.organization_enabled,
            ml_level=config.ml_level,
            quiet_mode=config.quiet_mode,
            verbose_mode=config.verbose_mode,
        )

    def _show_validation_errors(self, errors: List[str]) -> None:
        """Display validation errors to user."""
        self.console_manager.show_error_panel(
            title="Configuration Errors",
            error="Please fix the following issues:",
            suggestions=errors,
        )

    def show_help(self) -> None:
        """Show help information."""
        help_text = self.parser.get_help_text()

        self.console_manager.show_info_panel(
            title="Command Line Help", content=help_text, style="info"
        )

    def show_version_info(self) -> None:
        """Show version and system information."""
        try:
            # Import version info
            import platform

            # get_project_root imported but not used - keeping for future version info enhancements
            from ...shared.infrastructure.path_utilities import (  # pylint: disable=unused-import
                get_project_root,
            )

            version_info = {
                "Python Version": platform.python_version(),
                "Platform": platform.system(),
                "Architecture": platform.machine(),
            }

            self.console_manager.show_configuration_table(version_info, "System Information")

        except Exception as e:
            self.console_manager.show_error_panel(
                title="Version Info Error", error=f"Could not retrieve version information: {e}"
            )

    def confirm_exit(self) -> bool:
        """Ask user to confirm exit."""
        return self.console_manager.prompt_confirm("Are you sure you want to exit?", default=True)
