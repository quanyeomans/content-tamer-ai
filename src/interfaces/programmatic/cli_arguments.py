"""
Pure CLI Argument Parsing - No UI Dependencies

Provides clean argument parsing for automation and programmatic use.
Separated from human interaction patterns for headless operation.
"""

import argparse
import os
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# Import paths utility for defaults with fallback
try:
    from shared.infrastructure.path_utilities import get_default_directories
except ImportError:
    # Add src directory to path for absolute imports
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from shared.infrastructure.path_utilities import get_default_directories


@dataclass
class ParsedArguments:
    """Structured argument data without UI coupling."""
    # File paths
    input_dir: Optional[str] = None
    output_dir: Optional[str] = None
    unprocessed_dir: Optional[str] = None

    # AI provider settings
    provider: str = "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None

    # Processing options
    ocr_language: str = "eng"
    reset_progress: bool = False

    # Local LLM options
    setup_local_llm: bool = False
    list_local_models: bool = False
    check_local_requirements: bool = False
    download_model: Optional[str] = None
    remove_model: Optional[str] = None
    local_model_info: Optional[str] = None

    # Dependency management
    check_dependencies: bool = False
    refresh_dependencies: bool = False
    configure_dependency: Optional[List[str]] = None

    # Organization options
    organize: bool = False
    no_organize: bool = False
    ml_level: int = 2

    # Feature management
    show_feature_flags: bool = False
    enable_organization_features: bool = False
    disable_organization_features: bool = False

    # Display options
    quiet_mode: bool = False
    verbose_mode: bool = False

    # Information commands
    list_models: bool = False

    # Additional metadata
    command_type: str = "process"  # process, info, setup, manage
    exit_after_command: bool = False


class PureCLIParser:
    """Argument parser without UI dependencies."""

    def __init__(self):
        self.default_dirs = get_default_directories()
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create parser with all arguments but no UI logic."""
        parser = argparse.ArgumentParser(
            description="Content Tamer AI - Organize documents with intelligent AI-powered filename generation",
            epilog="""
Examples:
  # Process documents using defaults (data/input -> data/processed)
  content-tamer-ai

  # Use specific AI provider and model
  content-tamer-ai -p openai -m gpt-4o

  # Use custom folders for organization
  content-tamer-ai -i ./my-documents -r ./organized -u ./needs-review

  # List all available AI models
  content-tamer-ai --list-models

  # Headless processing (automation-friendly)
  content-tamer-ai --quiet -i input/ -r output/ -k $API_KEY
""",
            add_help=True,
            allow_abbrev=True
        )

        # File path arguments
        self._add_file_path_arguments(parser)

        # AI provider arguments
        self._add_ai_provider_arguments(parser)

        # Processing arguments
        self._add_processing_arguments(parser)

        # Local LLM arguments
        self._add_local_llm_arguments(parser)

        # Dependency management arguments
        self._add_dependency_arguments(parser)

        # Organization arguments
        self._add_organization_arguments(parser)

        # Feature management arguments
        self._add_feature_arguments(parser)

        # Display arguments
        self._add_display_arguments(parser)

        return parser

    def _add_file_path_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add file path related arguments."""
        DEFAULT_DATA_DIR, DEFAULT_INPUT_DIR, DEFAULT_PROCESSED_DIR, _, _ = self.default_dirs

        parser.add_argument(
            "--input", "-i",
            help=f"Input folder containing documents to organize (PDFs, images, screenshots) (default: {DEFAULT_INPUT_DIR})",
        )
        parser.add_argument(
            "--unprocessed", "-u",
            help="[ADVANCED] Custom location for unprocessed files (default: auto-created within processed folder)",
        )
        parser.add_argument(
            "--renamed", "-r",
            help=f"Folder for organized documents with AI-generated names (default: {DEFAULT_PROCESSED_DIR})",
        )

    def _add_ai_provider_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add AI provider related arguments."""
        # Import AI providers here to avoid circular imports
        try:
            from domains.ai_integration.provider_service import ProviderConfiguration
            AI_PROVIDERS = ProviderConfiguration.AI_PROVIDERS
        except ImportError:
            # Fallback for testing or when ai_providers not available
            AI_PROVIDERS = {
                "openai": ["gpt-4o", "gpt-4o-mini"],
                "claude": ["claude-3.5-sonnet", "claude-3.5-haiku"],
                "gemini": ["gemini-2.0-flash", "gemini-1.5-pro"],
                "deepseek": ["deepseek-chat"],
                "local": ["llama3.2-3b", "gemma2:2b"]
            }

        parser.add_argument(
            "--provider", "-p",
            help=f"AI provider (options: {', '.join(AI_PROVIDERS.keys())})",
            default="openai",
            choices=AI_PROVIDERS.keys(),
        )
        parser.add_argument(
            "--model", "-m",
            help="Model to use for the selected provider (run with --list-models to see options)",
        )
        parser.add_argument(
            "--api-key", "-k",
            help="API key for the selected provider"
        )
        parser.add_argument(
            "--list-models", "-l",
            action="store_true",
            help="List all available models by provider and exit",
        )

    def _add_processing_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add processing related arguments."""
        parser.add_argument(
            "--ocr-lang",
            default="eng",
            help="Tesseract OCR language hint (e.g., 'eng', 'eng+ind')",
        )
        parser.add_argument(
            "--reset-progress",
            action="store_true",
            help="Ignore and delete existing .progress file before run",
        )

    def _add_local_llm_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add Local LLM related arguments."""
        llm_group = parser.add_argument_group(
            "Local LLM Options",
            "Setup and management of local LLM processing"
        )
        llm_group.add_argument(
            "--setup-local-llm",
            action="store_true",
            help="Set up local LLM with automatic hardware detection and model recommendation",
        )
        llm_group.add_argument(
            "--list-local-models",
            action="store_true",
            help="List available local models with memory requirements and system compatibility",
        )
        llm_group.add_argument(
            "--check-local-requirements",
            action="store_true",
            help="Check system compatibility for local LLM processing",
        )
        llm_group.add_argument(
            "--download-model",
            help="Download a specific local model (e.g., --download-model gemma2:2b)",
        )
        llm_group.add_argument(
            "--remove-model",
            help="Remove a specific local model (e.g., --remove-model gemma2:2b)",
        )
        llm_group.add_argument(
            "--local-model-info",
            help="Show detailed information about a specific local model",
        )

    def _add_dependency_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add dependency management arguments."""
        dependency_group = parser.add_argument_group(
            "Dependency Management",
            "Commands for managing external dependencies"
        )
        dependency_group.add_argument(
            "--check-dependencies",
            action="store_true",
            help="Check status of all external dependencies (Ollama, Tesseract, etc.)"
        )
        dependency_group.add_argument(
            "--refresh-dependencies",
            action="store_true",
            help="Refresh dependency detection and update configuration"
        )
        dependency_group.add_argument(
            "--configure-dependency",
            nargs=2,
            metavar=("NAME", "PATH"),
            help="Manually configure dependency path (e.g., --configure-dependency tesseract 'C:\\\\path\\\\to\\\\tesseract.exe')"
        )

    def _add_organization_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add organization related arguments."""
        organization_group = parser.add_argument_group(
            "Organization Options",
            "Post-processing document organization with AI-powered categorization",
        )
        organization_group.add_argument(
            "--organize",
            action="store_true",
            help="Enable post-processing document organization with intelligent categorization",
        )
        organization_group.add_argument(
            "--no-organize",
            action="store_true",
            help="Disable post-processing document organization (default behavior)",
        )
        organization_group.add_argument(
            "--ml-level",
            type=int,
            choices=[1, 2, 3],
            default=2,
            help="ML enhancement level: 1=Basic rules, 2=Selective ML, 3=Temporal intelligence (default: 2)",
        )

    def _add_feature_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add feature management arguments."""
        feature_group = parser.add_argument_group(
            "Feature Management",
            "Control experimental and rollout features"
        )
        feature_group.add_argument(
            "--show-feature-flags",
            action="store_true",
            help="Display current feature flag configuration and exit",
        )
        feature_group.add_argument(
            "--enable-organization-features",
            action="store_true",
            help="Enable organization features via feature flags (persists to config)",
        )
        feature_group.add_argument(
            "--disable-organization-features",
            action="store_true",
            help="Disable organization features via feature flags (persists to config)",
        )

    def _add_display_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add display related arguments."""
        display_group = parser.add_argument_group(
            "Display Options",
            "Control output formatting and verbosity"
        )
        display_group.add_argument(
            "--quiet", "-q",
            action="store_true",
            help="Self-contained mode: one-line stats output, no user prompts. Requires API key and folders as parameters.",
        )
        display_group.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Default mode with guided menus, auto-detecting unicode support for rich or basic UI",
        )

    def parse_args(self, args: Optional[List[str]] = None) -> ParsedArguments:
        """Parse arguments returning structured data."""
        parsed = self.parser.parse_args(args)

        # Convert to structured dataclass
        parsed_args = ParsedArguments(
            # File paths
            input_dir=parsed.input,
            output_dir=parsed.renamed,  # Note: --renamed maps to output_dir
            unprocessed_dir=parsed.unprocessed,

            # AI provider settings
            provider=parsed.provider,
            model=parsed.model,
            api_key=parsed.api_key,

            # Processing options
            ocr_language=parsed.ocr_lang,
            reset_progress=parsed.reset_progress,

            # Local LLM options
            setup_local_llm=parsed.setup_local_llm,
            list_local_models=parsed.list_local_models,
            check_local_requirements=parsed.check_local_requirements,
            download_model=parsed.download_model,
            remove_model=parsed.remove_model,
            local_model_info=parsed.local_model_info,

            # Dependency management
            check_dependencies=parsed.check_dependencies,
            refresh_dependencies=parsed.refresh_dependencies,
            configure_dependency=parsed.configure_dependency,

            # Organization options
            organize=parsed.organize,
            no_organize=parsed.no_organize,
            ml_level=parsed.ml_level,

            # Feature management
            show_feature_flags=parsed.show_feature_flags,
            enable_organization_features=parsed.enable_organization_features,
            disable_organization_features=parsed.disable_organization_features,

            # Display options
            quiet_mode=parsed.quiet,
            verbose_mode=parsed.verbose,

            # Information commands
            list_models=parsed.list_models,
        )

        # Determine command type and exit behavior
        self._determine_command_type(parsed_args)

        return parsed_args

    def _determine_command_type(self, args: ParsedArguments) -> None:
        """Determine command type and whether to exit after command."""
        # Information commands
        if (args.list_models or args.show_feature_flags or
            args.list_local_models or args.local_model_info):
            args.command_type = "info"
            args.exit_after_command = True

        # Setup commands
        elif (args.setup_local_llm or args.check_local_requirements or
              args.download_model or args.remove_model):
            args.command_type = "setup"
            args.exit_after_command = True

        # Management commands
        elif (args.check_dependencies or args.refresh_dependencies or
              args.configure_dependency or args.enable_organization_features or
              args.disable_organization_features):
            args.command_type = "manage"
            args.exit_after_command = True

        # Processing commands (default)
        else:
            args.command_type = "process"
            args.exit_after_command = False

    def validate_args(self, args: ParsedArguments) -> List[str]:
        """Validate arguments returning error list."""
        errors = []

        # Conflicting organization arguments
        if args.organize and args.no_organize:
            errors.append("Cannot specify both --organize and --no-organize")

        # Conflicting display modes
        if args.quiet_mode and args.verbose_mode:
            errors.append("Cannot specify both --quiet and --verbose modes")

        # Quiet mode requires certain parameters for headless operation
        if args.quiet_mode and args.command_type == "process":
            if not args.api_key:
                errors.append("Quiet mode requires --api-key for headless operation")

        # Conflicting feature flag commands
        if args.enable_organization_features and args.disable_organization_features:
            errors.append("Cannot both enable and disable organization features")

        # Dependency configuration validation
        if args.configure_dependency:
            if len(args.configure_dependency) != 2:
                errors.append("--configure-dependency requires exactly 2 arguments: NAME PATH")

        return errors

    def get_help_text(self) -> str:
        """Get formatted help text."""
        return self.parser.format_help()

    def get_usage_text(self) -> str:
        """Get formatted usage text."""
        return self.parser.format_usage()