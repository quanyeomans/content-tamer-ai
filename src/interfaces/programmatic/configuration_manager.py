"""
Headless Configuration Management

Provides configuration loading and management without UI dependencies.
Supports environment variables, config files, and programmatic configuration.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cli_arguments import ParsedArguments


@dataclass
class ProcessingConfiguration:
    """Complete processing configuration structure."""

    # File paths
    input_dir: str
    output_dir: str
    unprocessed_dir: Optional[str] = None

    # AI provider settings
    provider: str = "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None

    # Processing options
    ocr_language: str = "eng"
    reset_progress: bool = False

    # Organization options
    organization_enabled: bool = False
    ml_level: int = 2

    # Display options
    quiet_mode: bool = False
    verbose_mode: bool = False

    # Feature flags
    feature_flags: Dict[str, Any] = field(default_factory=dict)

    # Additional metadata
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    version: str = "1.0"


class ConfigurationManager:
    """Headless configuration management."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Override default config directory for testing
        """
        self.config_dir = config_dir or (Path.home() / ".content-tamer")
        self.config_file = self.config_dir / "config.json"
        self.logger = logging.getLogger(__name__)

    def load_configuration(self, args: Optional[ParsedArguments] = None) -> ProcessingConfiguration:
        """Load configuration from all sources with precedence.

        Precedence order (highest to lowest):
        1. Command line arguments (if provided)
        2. Environment variables
        3. Configuration file
        4. Default values
        """
        # Start with default configuration
        config = self._get_default_configuration()

        # Layer on configuration file
        if self.config_file.exists():
            config = self._merge_config_file(config)

        # Layer on environment variables
        config = self._merge_environment_variables(config)

        # Layer on command line arguments (highest precedence)
        if args:
            config = self._merge_command_line_arguments(config, args)

        return config

    def save_configuration(self, config: ProcessingConfiguration) -> bool:
        """Save configuration to persistent storage.

        Returns:
            bool: True if save was successful
        """
        try:
            self.config_dir.mkdir(exist_ok=True, parents=True)

            # Update modification timestamp
            import datetime

            config.modified_at = datetime.datetime.now().isoformat()
            if not config.created_at:
                config.created_at = config.modified_at

            config_dict = asdict(config)

            # SECURITY: Never store API keys in plain text configuration files
            if config_dict.get("api_key"):
                # Remove API key from saved configuration for security
                config_dict["api_key"] = None
                config_dict["api_key_source"] = "environment_variable_required"
                self.logger.info("API key excluded from configuration file for security")

            # Write configuration atomically
            temp_file = self.config_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            # Atomic move
            temp_file.replace(self.config_file)

            self.logger.info(f"Configuration saved to {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def validate_configuration(self, config: ProcessingConfiguration) -> List[str]:
        """Validate configuration returning list of errors."""
        errors = []

        # Validate required paths
        if not config.input_dir:
            errors.append("Input directory is required")
        elif not Path(config.input_dir).exists():
            errors.append(f"Input directory does not exist: {config.input_dir}")
        elif not os.access(config.input_dir, os.R_OK):
            errors.append(f"Input directory is not readable: {config.input_dir}")

        if not config.output_dir:
            errors.append("Output directory is required")
        else:
            # Try to create output directory if it doesn't exist
            try:
                Path(config.output_dir).mkdir(parents=True, exist_ok=True)
                if not os.access(config.output_dir, os.W_OK):
                    errors.append(f"Output directory is not writable: {config.output_dir}")
            except Exception as e:
                errors.append(f"Cannot create output directory: {config.output_dir} - {e}")

        # Validate AI provider settings
        if not config.provider:
            errors.append("AI provider is required")
        else:
            # Validate API key
            if not config.api_key:
                env_key = f"{config.provider.upper()}_API_KEY"
                if not os.getenv(env_key):
                    errors.append(
                        f"API key required for {config.provider} (set {env_key} environment variable or use --api-key)"
                    )

        # Validate ML level
        if config.ml_level not in [1, 2, 3]:
            errors.append("ML level must be 1, 2, or 3")

        # Validate OCR language format
        if not config.ocr_language or not config.ocr_language.strip():
            errors.append("OCR language cannot be empty")

        return errors

    def _get_default_configuration(self) -> ProcessingConfiguration:
        """Get default configuration values."""
        # Import defaults here to avoid circular imports
        try:
            from ...shared.infrastructure.path_utilities import get_default_directories

            _DEFAULT_DATA_DIR, DEFAULT_INPUT_DIR, DEFAULT_PROCESSED_DIR, _, _ = (
                get_default_directories()
            )
        except ImportError:
            # Fallback defaults for testing
            DEFAULT_INPUT_DIR = "./data/input"
            DEFAULT_PROCESSED_DIR = "./data/processed"

        return ProcessingConfiguration(
            input_dir=DEFAULT_INPUT_DIR,
            output_dir=DEFAULT_PROCESSED_DIR,
            provider="openai",
            ocr_language="eng",
            ml_level=2,
            feature_flags={},
        )

    def _merge_config_file(self, config: ProcessingConfiguration) -> ProcessingConfiguration:
        """Merge configuration file values."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                file_config = json.load(f)

            # Update config with file values (only if not None/empty)
            for key, value in file_config.items():
                if hasattr(config, key) and value is not None:
                    setattr(config, key, value)

            self.logger.debug(f"Loaded configuration from {self.config_file}")

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.warning(f"Could not load configuration file: {e}")

        return config

    def _merge_environment_variables(
        self, config: ProcessingConfiguration
    ) -> ProcessingConfiguration:
        """Merge environment variable values."""
        env_mappings = {
            "CONTENT_TAMER_INPUT_DIR": "input_dir",
            "CONTENT_TAMER_OUTPUT_DIR": "output_dir",
            "CONTENT_TAMER_PROVIDER": "provider",
            "CONTENT_TAMER_MODEL": "model",
            "CONTENT_TAMER_OCR_LANG": "ocr_language",
            "CONTENT_TAMER_ML_LEVEL": "ml_level",
            "CONTENT_TAMER_QUIET": "quiet_mode",
            "CONTENT_TAMER_VERBOSE": "verbose_mode",
        }

        # Also check for provider-specific API keys
        if config.provider:
            api_key_env = f"{config.provider.upper()}_API_KEY"
            if os.getenv(api_key_env) and not config.api_key:
                config.api_key = os.getenv(api_key_env)

        # Apply environment variable mappings
        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Convert string values to appropriate types
                if config_attr == "ml_level":
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        self.logger.warning(f"Invalid ML level in {env_var}: {env_value}")
                        continue
                elif config_attr in ["quiet_mode", "verbose_mode"]:
                    env_value = env_value.lower() in ("true", "1", "yes", "on")

                setattr(config, config_attr, env_value)
                self.logger.debug(f"Applied environment variable {env_var}={env_value}")

        return config

    def _merge_command_line_arguments(
        self, config: ProcessingConfiguration, args: ParsedArguments
    ) -> ProcessingConfiguration:
        """Merge command line argument values (highest precedence)."""
        # Only override config if argument was explicitly provided
        if args.input_dir:
            config.input_dir = args.input_dir
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.unprocessed_dir:
            config.unprocessed_dir = args.unprocessed_dir

        # AI provider settings
        if args.provider != "openai":  # Only if not default
            config.provider = args.provider
        if args.model:
            config.model = args.model
        if args.api_key:
            config.api_key = args.api_key

        # Processing options
        if args.ocr_language != "eng":  # Only if not default
            config.ocr_language = args.ocr_language
        if args.reset_progress:
            config.reset_progress = args.reset_progress

        # Organization options
        if args.organize:
            config.organization_enabled = True
        elif args.no_organize:
            config.organization_enabled = False
        if args.ml_level != 2:  # Only if not default
            config.ml_level = args.ml_level

        # Display options
        if args.quiet_mode:
            config.quiet_mode = True
            config.verbose_mode = False  # Quiet overrides verbose
        elif args.verbose_mode:
            config.verbose_mode = True

        return config

    def export_configuration(self, config: ProcessingConfiguration, format: str = "json") -> str:
        """Export configuration in specified format.

        Args:
            config: Configuration to export
            format: Export format ("json", "yaml", "env")

        Returns:
            str: Formatted configuration string
        """
        if format.lower() == "json":
            return json.dumps(asdict(config), indent=2, ensure_ascii=False)

        elif format.lower() == "yaml":
            try:
                import yaml

                return yaml.dump(asdict(config), default_flow_style=False, sort_keys=True)
            except ImportError:
                raise ValueError("PyYAML not installed - cannot export as YAML")

        elif format.lower() == "env":
            # Export as environment variable format
            env_lines = []
            config_dict = asdict(config)

            for key, value in config_dict.items():
                if value is not None and key not in [
                    "created_at",
                    "modified_at",
                    "version",
                    "feature_flags",
                ]:
                    env_key = f"CONTENT_TAMER_{key.upper()}"
                    env_lines.append(f"export {env_key}='{value}'")

            return "\n".join(env_lines)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def load_from_dict(self, config_dict: Dict[str, Any]) -> ProcessingConfiguration:
        """Load configuration from dictionary."""
        try:
            return ProcessingConfiguration(**config_dict)
        except TypeError as e:
            self.logger.error(f"Invalid configuration dictionary: {e}")
            raise ValueError(f"Invalid configuration: {e}")

    def get_configuration_summary(self, config: ProcessingConfiguration) -> Dict[str, Any]:
        """Get human-readable configuration summary."""
        return {
            "Input Directory": config.input_dir,
            "Output Directory": config.output_dir,
            "AI Provider": config.provider,
            "AI Model": config.model or "default",
            "OCR Language": config.ocr_language,
            "Organization": "Enabled" if config.organization_enabled else "Disabled",
            "ML Level": config.ml_level,
            "Display Mode": (
                "Quiet" if config.quiet_mode else ("Verbose" if config.verbose_mode else "Normal")
            ),
            "Configuration File": (
                str(self.config_file) if self.config_file.exists() else "Not found"
            ),
        }
