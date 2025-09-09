"""
Expert Configuration Wizard

Provides advanced configuration prompts for expert users who want
more control over Content Tamer AI settings and parameters.
Extracted from utils.expert_mode for clean interface separation.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from ..programmatic.configuration_manager import ProcessingConfiguration, ConfigurationManager
from .rich_console_manager import RichConsoleManager


class ExpertConfigurationWizard:
    """Handles expert mode configuration prompts with Rich UI."""

    def __init__(self, console_manager: RichConsoleManager):
        """Initialize wizard with Rich console manager."""
        self.console = console_manager
        self.config_manager = ConfigurationManager()

        # Available options
        self.providers = ["openai", "claude", "gemini", "deepseek", "local"]
        self.common_languages = {
            "eng": "English",
            "eng+fra": "English + French",
            "eng+spa": "English + Spanish",
            "eng+deu": "English + German",
            "eng+ita": "English + Italian",
            "eng+por": "English + Portuguese",
            "eng+rus": "English + Russian",
            "eng+chi_sim": "English + Chinese (Simplified)",
            "eng+jpn": "English + Japanese",
        }

    def run_configuration_wizard(self) -> Optional[ProcessingConfiguration]:
        """Run the complete configuration wizard."""
        try:
            self.console.show_section_header(
                "Expert Configuration Wizard",
                "Configure each setting with full control over all options"
            )

            # Start with default configuration
            config = self.config_manager.load_configuration()

            # Run configuration steps
            config = self._configure_file_paths(config)
            config = self._configure_ai_provider(config)
            config = self._configure_processing_options(config)
            config = self._configure_organization_options(config)
            config = self._configure_display_options(config)

            # Show final summary and confirm
            if self._confirm_configuration(config):
                # Save configuration if user wants
                if self.console.prompt_confirm("Save this configuration for future use?"):
                    if self.config_manager.save_configuration(config):
                        self.console.show_status("Configuration saved successfully", "success")
                    else:
                        self.console.show_status("Failed to save configuration", "warning")

                return config
            else:
                return None

        except KeyboardInterrupt:
            self.console.show_status("Configuration cancelled by user", "warning")
            return None
        except Exception as e:
            self.console.handle_error(e, {"context": "configuration_wizard"})
            return None

    def _configure_file_paths(self, config: ProcessingConfiguration) -> ProcessingConfiguration:
        """Configure input and output directories."""
        self.console.show_section_header(
            "📂 File Paths",
            "Configure where documents are read from and organized to"
        )

        # Input Directory
        config.input_dir = self._prompt_directory_path(
            "Input directory (where your documents are located)",
            current_value=config.input_dir,
            must_exist=True,
            must_be_readable=True
        )

        # Output Directory
        config.output_dir = self._prompt_directory_path(
            "Output directory (where organized documents will be saved)",
            current_value=config.output_dir,
            must_exist=False,
            must_be_writable=True
        )

        # Unprocessed Directory (optional)
        use_custom_unprocessed = self.console.prompt_confirm(
            "Use custom directory for unprocessed files?",
            default=False
        )

        if use_custom_unprocessed:
            config.unprocessed_dir = self._prompt_directory_path(
                "Unprocessed files directory",
                current_value=config.unprocessed_dir,
                must_exist=False,
                must_be_writable=True
            )

        return config

    def _configure_ai_provider(self, config: ProcessingConfiguration) -> ProcessingConfiguration:
        """Configure AI provider and model."""
        self.console.show_section_header(
            "🤖 AI Provider",
            "Choose your AI service for intelligent document analysis"
        )

        # Show available providers
        provider_table = {
            "openai": "OpenAI (GPT-4o, GPT-4o-mini)",
            "claude": "Anthropic Claude (Sonnet, Haiku)",
            "gemini": "Google Gemini (2.0 Flash, 1.5 Pro)",
            "deepseek": "Deepseek (Chat)",
            "local": "Local LLM (Ollama - offline processing)"
        }

        self.console.show_configuration_table(
            provider_table,
            "Available AI Providers"
        )

        # Select provider
        config.provider = self.console.prompt_choice(
            "Choose AI provider",
            choices=self.providers,
            default=config.provider
        )

        # Configure model for selected provider
        config.model = self._prompt_model_selection(config.provider, config.model)

        # Configure API key (if not local)
        if config.provider != "local":
            config.api_key = self._prompt_api_key_configuration(config.provider, config.api_key)

        return config

    def _configure_processing_options(self, config: ProcessingConfiguration) -> ProcessingConfiguration:
        """Configure processing-related options."""
        self.console.show_section_header(
            "⚙️ Processing Options",
            "Configure how documents are processed and analyzed"
        )

        # OCR Language
        self.console.show_configuration_table(
            self.common_languages,
            "Common OCR Languages"
        )

        config.ocr_language = self.console.prompt_text(
            "OCR language code (e.g., 'eng' or 'eng+fra')",
            default=config.ocr_language
        )

        # Reset progress
        config.reset_progress = self.console.prompt_confirm(
            "Reset processing progress (ignore previous runs)?",
            default=config.reset_progress
        )

        return config

    def _configure_organization_options(self, config: ProcessingConfiguration) -> ProcessingConfiguration:
        """Configure document organization options."""
        self.console.show_section_header(
            "🗂️ Document Organization",
            "Configure intelligent document categorization and folder organization"
        )

        # Organization enabled
        organization_info = """
Document organization uses AI to automatically:
• Analyze document content and context
• Create intelligent folder structures
• Group similar documents together
• Learn from your preferences over time

Choose your organization approach:
"""
        self.console.show_info_panel(
            "Organization Overview",
            organization_info,
            style="info"
        )

        org_choice = self.console.prompt_choice(
            "Enable document organization?",
            choices=["yes", "no"],
            default="yes" if config.organization_enabled else "no"
        )
        config.organization_enabled = (org_choice == "yes")

        # ML Level (if organization enabled)
        if config.organization_enabled:
            ml_info = {
                "Level 1": "Enhanced rule-based classification (fastest, 80% accuracy)",
                "Level 2": "Selective ML refinement for uncertain cases (balanced, 90% accuracy)",
                "Level 3": "Advanced temporal intelligence with business insights (comprehensive, 95% accuracy)"
            }

            self.console.show_configuration_table(
                ml_info,
                "ML Enhancement Levels"
            )

            level_choice = self.console.prompt_choice(
                "Choose ML enhancement level",
                choices=["1", "2", "3"],
                default=str(config.ml_level)
            )
            config.ml_level = int(level_choice)

        return config

    def _configure_display_options(self, config: ProcessingConfiguration) -> ProcessingConfiguration:
        """Configure display and output options."""
        self.console.show_section_header(
            "🎨 Display Options",
            "Configure how information is displayed during processing"
        )

        # Display mode
        display_mode = self.console.prompt_choice(
            "Choose display mode",
            choices=["normal", "verbose", "quiet"],
            default="verbose" if config.verbose_mode else ("quiet" if config.quiet_mode else "normal")
        )

        config.quiet_mode = (display_mode == "quiet")
        config.verbose_mode = (display_mode == "verbose")

        return config

    def _prompt_directory_path(
        self,
        prompt: str,
        current_value: Optional[str] = None,
        must_exist: bool = True,
        must_be_readable: bool = False,
        must_be_writable: bool = False
    ) -> str:
        """Prompt for directory path with validation."""
        while True:
            path_str = self.console.prompt_text(
                f"{prompt}",
                default=current_value
            )

            path = Path(path_str).expanduser().resolve()

            # Validation
            if must_exist and not path.exists():
                self.console.show_status(f"Directory does not exist: {path}", "error")
                continue

            if path.exists() and not path.is_dir():
                self.console.show_status(f"Path is not a directory: {path}", "error")
                continue

            if must_be_readable and path.exists() and not os.access(path, os.R_OK):
                self.console.show_status(f"Directory is not readable: {path}", "error")
                continue

            if must_be_writable:
                # Try to create directory if it doesn't exist
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    if not os.access(path, os.W_OK):
                        self.console.show_status(f"Directory is not writable: {path}", "error")
                        continue
                except Exception as e:
                    self.console.show_status(f"Cannot create/access directory: {e}", "error")
                    continue

            return str(path)

    def _prompt_model_selection(self, provider: str, current_model: Optional[str] = None) -> Optional[str]:
        """Prompt for model selection based on provider."""
        model_suggestions = {
            "openai": {
                "gpt-4o": "GPT-4o - Latest flagship model (best quality)",
                "gpt-4o-mini": "GPT-4o-mini - Faster and more affordable",
                "gpt-4-turbo": "GPT-4 Turbo - Previous generation flagship"
            },
            "claude": {
                "claude-3.5-sonnet": "Claude 3.5 Sonnet - Best balance of speed and capability",
                "claude-3.5-haiku": "Claude 3.5 Haiku - Fast and efficient",
                "claude-3-opus": "Claude 3 Opus - Highest capability"
            },
            "gemini": {
                "gemini-2.0-flash": "Gemini 2.0 Flash - Latest multimodal model",
                "gemini-1.5-pro": "Gemini 1.5 Pro - High-capability model",
                "gemini-1.5-flash": "Gemini 1.5 Flash - Fast processing"
            },
            "deepseek": {
                "deepseek-chat": "Deepseek Chat - General purpose model"
            },
            "local": {
                "llama3.2-3b": "Llama 3.2 3B - Lightweight local model",
                "gemma2:2b": "Gemma 2 2B - Very efficient local model",
                "mistral-7b": "Mistral 7B - Balanced local model",
                "llama3.1-8b": "Llama 3.1 8B - High-capability local model"
            }
        }

        suggestions = model_suggestions.get(provider, {})
        if suggestions:
            self.console.show_configuration_table(
                suggestions,
                f"Available {provider.capitalize()} Models"
            )

            default_model = current_model or list(suggestions.keys())[0]

            model = self.console.prompt_choice(
                f"Choose {provider} model",
                choices=list(suggestions.keys()) + ["custom"],
                default=default_model if default_model in suggestions else "custom"
            )

            if model == "custom":
                model = self.console.prompt_text(
                    f"Enter custom model name for {provider}"
                )

            return model
        else:
            return self.console.prompt_text(
                f"Enter model name for {provider}",
                default=current_model
            )

    def _prompt_api_key_configuration(self, provider: str, current_key: Optional[str] = None) -> Optional[str]:
        """Prompt for API key configuration."""
        env_var = f"{provider.upper()}_API_KEY"
        env_key = os.getenv(env_var)

        if env_key:
            self.console.show_status(f"Using API key from environment variable {env_var}", "success")
            return env_key

        if current_key:
            use_existing = self.console.prompt_confirm(
                f"Use existing saved API key for {provider}?",
                default=True
            )
            if use_existing:
                return current_key

        api_info = f"""
API Key for {provider.capitalize()}:

Get your API key from:
• OpenAI: https://platform.openai.com/api-keys
• Claude: https://console.anthropic.com/
• Gemini: https://aistudio.google.com/app/apikey
• Deepseek: https://platform.deepseek.com/api_keys

You can:
1. Enter it here (will be saved to config file)
2. Set environment variable: {env_var}
3. Skip and provide later with --api-key argument
        """

        self.console.show_info_panel(
            f"{provider.capitalize()} API Key",
            api_info,
            style="info"
        )

        api_key = self.console.prompt_text(
            f"Enter your {provider.capitalize()} API key (or press Enter to skip)"
        )

        return api_key if api_key else None

    def _confirm_configuration(self, config: ProcessingConfiguration) -> bool:
        """Show configuration summary and confirm."""
        self.console.show_section_header(
            "📋 Configuration Summary",
            "Review your configuration before proceeding"
        )

        summary = self.config_manager.get_configuration_summary(config)
        self.console.show_configuration_table(summary, "Expert Configuration")

        return self.console.prompt_confirm(
            "Proceed with this configuration?",
            default=True
        )
