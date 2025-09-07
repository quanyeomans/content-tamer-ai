"""
Expert Mode Configuration System

Provides advanced configuration prompts for expert users who want
more control over Content Tamer AI settings and parameters.
"""

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ExpertConfig:
    """Configuration collected from expert mode prompts."""

    input_dir: Optional[str] = None
    output_dir: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    ocr_language: Optional[str] = None
    reset_progress: bool = False
    quiet_mode: bool = False
    verbose_mode: bool = False
    no_color: bool = False
    no_stats: bool = False
    enable_organization: Optional[bool] = None
    ml_level: int = 2


class ExpertModePrompter:
    """Handles expert mode configuration prompts."""

    def __init__(self):
        self.providers = ["openai", "claude", "gemini", "deepseek"]
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

    def should_use_expert_mode(self) -> bool:
        """Ask user if they want to use expert mode."""
        print("\n" + "=" * 60)
        print("🎯 CONTENT TAMER AI CONFIGURATION")
        print("=" * 60)
        print()
        print("Content Tamer AI can run in two modes:")
        print()
        print("🚀 QUICK START (Recommended for new users)")
        print("   • Uses smart defaults")
        print("   • Processes data/input/ -> data/processed/")
        print("   • Just needs your API key")
        print()
        print("⚙️  EXPERT MODE (For advanced users)")
        print("   • Customize all settings")
        print("   • Choose custom input/output folders")
        print("   • Configure AI provider, model, language settings")
        print("   • Set display and processing options")
        print()

        while True:
            choice = input("Choose mode [Q]uick start or [E]xpert mode (Q/E): ").strip().lower()
            if choice in ["q", "quick", ""]:
                return False
            elif choice in ["e", "expert"]:
                return True
            else:
                print("Please enter 'Q' for Quick start or 'E' for Expert mode.")

    def prompt_expert_configuration(self) -> ExpertConfig:
        """Collect expert configuration through interactive prompts."""
        config = ExpertConfig()

        print("\n" + "=" * 60)
        print("⚙️  EXPERT MODE CONFIGURATION")
        print("=" * 60)
        print()
        print("Configure each setting below. Press Enter to use defaults shown in [brackets].")
        print()

        # 1. Input Directory
        print("📂 INPUT DIRECTORY")
        print("   Where your documents are located for processing")
        default_input = os.path.join(os.getcwd(), "documents", "input")
        print(f"   Default: {default_input}")
        config.input_dir = self._prompt_with_validation(
            "   Input folder path",
            default=default_input,
            validator=self._validate_input_directory,
            help_text="Path must be accessible and contain supported files (PDFs, images)",
        )

        # 2. Output Directory
        print("\n📁 OUTPUT DIRECTORY")
        print("   Where organized documents will be saved")
        default_output = os.path.join(os.getcwd(), "documents", "processed")
        print(f"   Default: {default_output}")
        config.output_dir = self._prompt_with_validation(
            "   Output folder path",
            default=default_output,
            validator=self._validate_output_directory,
            help_text="Directory will be created if it doesn't exist",
        )

        # 3. AI Provider
        print("\n🤖 AI PROVIDER")
        print("   Choose your AI service for content analysis")
        print("   Available providers:")
        for i, provider in enumerate(self.providers, 1):
            print(f"     {i}. {provider}")
        print("   Default: openai")
        config.provider = self._prompt_provider()

        # 4. AI Model
        print(f"\n🧠 AI MODEL (for {config.provider})")
        print("   Specific model to use for analysis")
        config.model = self._prompt_model(config.provider)

        # 5. OCR Language
        print("\n🌍 OCR LANGUAGE")
        print("   Language detection for text extraction from images")
        print("   Common options:")
        for code, name in self.common_languages.items():
            print(f"     {code}: {name}")
        print("   Default: eng (English only)")
        config.ocr_language = self._prompt_with_default(
            "   Language code",
            default="eng",
            help_text="Use format like 'eng' or 'eng+fra' for multiple languages",
        )

        # 6. Processing Options
        print("\n⚙️  PROCESSING OPTIONS")
        config.reset_progress = self._prompt_yes_no(
            "   Reset progress (ignore previous processing)",
            default=False,
            help_text="Start fresh, reprocessing all files",
        )

        # 7. Display Options
        print("\n🎨 DISPLAY OPTIONS")
        config.quiet_mode = self._prompt_yes_no(
            "   Quiet mode (minimal output)",
            default=False,
            help_text="Show only progress bar, suppress info messages",
        )

        if not config.quiet_mode:
            config.verbose_mode = self._prompt_yes_no(
                "   Verbose mode (detailed output)",
                default=False,
                help_text="Show debug messages and detailed processing info",
            )

        config.no_color = self._prompt_yes_no(
            "   Disable colors (plain text)",
            default=False,
            help_text="Useful for logging or terminals without color support",
        )

        config.no_stats = self._prompt_yes_no(
            "   Disable statistics display",
            default=False,
            help_text="Hide processing statistics in progress display",
        )

        # 8. Document Organization Options
        print("\n🗂️  DOCUMENT ORGANIZATION")
        print("   Post-processing organization with AI-powered categorization")
        print("   Automatically organizes processed files into logical folder structures")
        print()
        print("   Organization Modes:")
        print("     • Level 1: Enhanced rule-based classification (fastest)")
        print("     • Level 2: Selective ML refinement for uncertain documents (balanced)")
        print("     • Level 3: Advanced temporal intelligence with business insights (most sophisticated)")
        print()
        
        config.enable_organization = self._prompt_organization_choice()
        
        if config.enable_organization:
            config.ml_level = self._prompt_ml_level()

        # Show configuration summary
        self._show_configuration_summary(config)

        return config

    def _prompt_with_default(self, prompt: str, default: str, help_text: str = "") -> str:
        """Prompt with a default value."""
        if help_text:
            print(f"     💡 {help_text}")

        while True:
            value = input(f"   {prompt} [{default}]: ").strip()
            return value if value else default

    def _prompt_with_validation(
        self, prompt: str, default: str, validator, help_text: str = ""
    ) -> str:
        """Prompt with validation function."""
        if help_text:
            print(f"     💡 {help_text}")

        while True:
            value = input(f"   {prompt} [{default}]: ").strip()
            value = value if value else default

            is_valid, error_msg = validator(value)
            if is_valid:
                return value
            else:
                print(f"   ❌ {error_msg}")

    def _prompt_yes_no(self, prompt: str, default: bool, help_text: str = "") -> bool:
        """Prompt for yes/no with default."""
        if help_text:
            print(f"     💡 {help_text}")

        default_str = "Y/n" if default else "y/N"
        while True:
            value = input(f"   {prompt} ({default_str}): ").strip().lower()
            if value in ["y", "yes"]:
                return True
            elif value in ["n", "no"]:
                return False
            elif value == "":
                return default
            else:
                print("   Please enter 'y' for yes or 'n' for no")

    def _prompt_provider(self) -> str:
        """Prompt for AI provider selection."""
        while True:
            choice = input("   Provider [openai]: ").strip().lower()
            if choice == "" or choice == "openai":
                return "openai"
            elif choice in self.providers:
                return choice
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.providers):
                    return self.providers[idx]

            print(f"   Please choose from: {', '.join(self.providers)}")

    def _prompt_model(self, provider: str) -> Optional[str]:
        """Prompt for model selection based on provider."""
        model_suggestions = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "claude": ["claude-3-sonnet", "claude-3-haiku"],
            "gemini": ["gemini-pro", "gemini-pro-vision"],
            "deepseek": ["deepseek-chat"],
        }

        suggestions = model_suggestions.get(provider, [])
        if suggestions:
            print(f"   Common {provider} models: {', '.join(suggestions)}")
            default = suggestions[0]
        else:
            default = "auto"

        return self._prompt_with_default(
            "   Model name",
            default=default,
            help_text=f"Use 'auto' to let {provider} choose the best model",
        )

    def _validate_input_directory(self, path: str) -> Tuple[bool, str]:
        """Validate input directory."""
        if not os.path.exists(path):
            return False, f"Directory does not exist: {path}"
        if not os.path.isdir(path):
            return False, f"Path is not a directory: {path}"
        if not os.access(path, os.R_OK):
            return False, f"Directory is not readable: {path}"
        return True, ""

    def _validate_output_directory(self, path: str) -> Tuple[bool, str]:
        """Validate output directory."""
        try:
            # Try to create the directory if it doesn't exist
            os.makedirs(path, exist_ok=True)
            if not os.access(path, os.W_OK):
                return False, f"Directory is not writable: {path}"
            return True, ""
        except Exception as e:
            return False, f"Cannot create directory: {str(e)}"

    def _prompt_organization_choice(self) -> bool:
        """Prompt user for organization workflow choice."""
        print("   Available Options:")
        print("     1. Skip organization (default) - Just rename files with AI-generated names")
        print("     2. Enable organization - Organize files into intelligent folder structures")
        print()
        
        while True:
            choice = input("   Choose organization option [1-2, default=1]: ").strip()
            
            if choice == "" or choice == "1":
                print("   ✅ Organization disabled - files will only be renamed")
                return False
            elif choice == "2":
                print("   ✅ Organization enabled - files will be organized into folders")
                return True
            else:
                print("   Please enter '1' to skip or '2' to enable organization")

    def _prompt_ml_level(self) -> int:
        """Prompt user for ML enhancement level choice."""
        print("\n   ML Enhancement Level:")
        print("     1. Basic Rules - Fast rule-based classification (80%+ accuracy)")
        print("     2. Selective ML - Applies ML only to uncertain documents (recommended)")
        print("     3. Temporal Intelligence - Advanced patterns + business insights")
        print()
        print("   💡 Level 2 provides the best balance of speed and accuracy")
        
        while True:
            choice = input("   Choose ML level [1-3, default=2]: ").strip()
            
            if choice == "" or choice == "2":
                print("   ✅ Using Level 2: Selective ML refinement")
                return 2
            elif choice == "1":
                print("   ✅ Using Level 1: Enhanced rule-based classification")
                return 1
            elif choice == "3":
                print("   ✅ Using Level 3: Advanced temporal intelligence")
                return 3
            else:
                print("   Please enter '1', '2', or '3' for ML enhancement level")

    def _show_configuration_summary(self, config: ExpertConfig) -> None:
        """Show a summary of the expert configuration."""
        print("\n" + "=" * 60)
        print("📋 CONFIGURATION SUMMARY")
        print("=" * 60)
        print(f"Input Directory:    {config.input_dir}")
        print(f"Output Directory:   {config.output_dir}")
        print(f"AI Provider:        {config.provider}")
        print(f"AI Model:           {config.model}")
        print(f"OCR Language:       {config.ocr_language}")
        print(f"Reset Progress:     {'Yes' if config.reset_progress else 'No'}")
        
        # Organization settings
        if config.enable_organization is not None:
            print(f"Organization:       {'Enabled' if config.enable_organization else 'Disabled'}")
            if config.enable_organization:
                level_names = {1: "Basic Rules", 2: "Selective ML", 3: "Temporal Intelligence"}
                print(f"ML Enhancement:     Level {config.ml_level} ({level_names[config.ml_level]})")
        
        print(f"Quiet Mode:         {'Yes' if config.quiet_mode else 'No'}")
        print(f"Verbose Mode:       {'Yes' if config.verbose_mode else 'No'}")
        print(f"Disable Colors:     {'Yes' if config.no_color else 'No'}")
        print(f"Disable Stats:      {'Yes' if config.no_stats else 'No'}")
        print()

        while True:
            confirm = input("Proceed with this configuration? (Y/n): ").strip().lower()
            if confirm in ["y", "yes", ""]:
                break
            elif confirm in ["n", "no"]:
                print("Configuration cancelled.")
                sys.exit(0)

    def convert_to_args(self, config: ExpertConfig) -> List[str]:
        """Convert expert configuration to command line arguments."""
        args = []

        if config.input_dir:
            args.extend(["--input", config.input_dir])
        if config.output_dir:
            args.extend(
                ["--renamed", config.output_dir]
            )  # Note: using --renamed for processed folder
        if config.provider:
            args.extend(["--provider", config.provider])
        if config.model:
            args.extend(["--model", config.model])
        if config.ocr_language and config.ocr_language != "eng":
            args.extend(["--ocr-lang", config.ocr_language])
        if config.reset_progress:
            args.append("--reset-progress")
        
        # Organization settings
        if config.enable_organization is True:
            args.append("--organize")
            if config.ml_level != 2:  # Only add if not default
                args.extend(["--ml-level", str(config.ml_level)])
        elif config.enable_organization is False:
            args.append("--no-organize")
            
        if config.quiet_mode:
            args.append("--quiet")
        if config.verbose_mode:
            args.append("--verbose")
        if config.no_color:
            args.append("--no-color")
        if config.no_stats:
            args.append("--no-stats")

        return args


def prompt_expert_mode_if_needed() -> List[str]:
    """
    Main function to handle expert mode prompting.
    Returns list of additional command line arguments to apply.
    """
    # Check if running with existing arguments (expert user already using CLI)
    if len(sys.argv) > 1:
        # User is already using command line arguments, don't prompt
        return []

    prompter = ExpertModePrompter()

    if prompter.should_use_expert_mode():
        config = prompter.prompt_expert_configuration()
        return prompter.convert_to_args(config)

    # Quick start mode - no additional args needed
    return []
