"""
Feature Flag System for Content Tamer AI

Provides centralized feature flag management to control rollout of new features
like post-processing organization, with environment variable and config file support.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OrganizationFeatureFlags:
    """Feature flags specifically for organization features."""

    # Main feature flags
    enable_organization: bool = False
    enable_guided_navigation: bool = True
    enable_expert_mode_integration: bool = True
    enable_auto_enablement: bool = True

    # ML enhancement flags
    enable_ml_level_1: bool = True  # Basic rules
    enable_ml_level_2: bool = True  # Selective ML
    enable_ml_level_3: bool = True  # Temporal intelligence

    # UI/UX flags
    enable_progress_display: bool = True
    enable_unified_error_messaging: bool = True
    enable_consent_prompts: bool = False  # Not yet implemented

    # Safety flags
    max_files_for_auto_enable: int = 100
    require_confirmation_above: int = 50

    # Rollout control
    rollout_percentage: float = 100.0  # Percentage of users to show organization features

    def is_organization_available(self, file_count: int = 1) -> bool:
        """Check if organization features should be available for this context."""
        # Safety check for large file counts
        if file_count > self.max_files_for_auto_enable:
            return False

        # Check rollout percentage (placeholder for A/B testing)
        # In real implementation, this could use user ID hash
        return self.rollout_percentage >= 100.0

    def should_auto_enable(self, file_count: int = 1) -> bool:
        """Check if organization should be auto-enabled for guided navigation."""
        return (
            self.enable_auto_enablement
            and self.is_organization_available(file_count)
            and file_count > 1
        )


@dataclass
class FeatureFlags:
    """Main feature flag configuration."""

    # Organization features
    organization: OrganizationFeatureFlags

    # Future feature categories can be added here
    # ai_enhancement: AIFeatureFlags
    # ui_features: UIFeatureFlags

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlags":
        """Create FeatureFlags from dictionary."""
        org_data = data.get("organization", {})
        organization = OrganizationFeatureFlags(**org_data)
        return cls(organization=organization)

    def to_dict(self) -> Dict[str, Any]:
        """Convert FeatureFlags to dictionary."""
        return {"organization": asdict(self.organization)}


class FeatureFlagManager:
    """Manages feature flags from multiple sources with precedence."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize feature flag manager with optional config directory."""
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "data" / "config"
        self.config_file = self.config_dir / "feature_flags.json"
        self._flags = None

    def load_flags(self) -> FeatureFlags:
        """Load feature flags from all sources with precedence."""
        if self._flags is not None:
            return self._flags

        # Start with defaults
        flags = FeatureFlags(organization=OrganizationFeatureFlags())

        # Override with config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                flags = FeatureFlags.from_dict(config_data)
                logger.debug(f"Loaded feature flags from {self.config_file}")
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Error loading feature flags from {self.config_file}: {e}")
                # Continue with defaults

        # Override with environment variables
        flags = self._apply_environment_overrides(flags)

        self._flags = flags
        return flags

    def _apply_environment_overrides(self, flags: FeatureFlags) -> FeatureFlags:
        """Apply environment variable overrides to feature flags."""

        # Organization feature overrides
        org_flags = flags.organization

        # Main toggles
        org_flags.enable_organization = self._get_bool_env(
            "CONTENT_TAMER_ENABLE_ORGANIZATION", org_flags.enable_organization
        )

        org_flags.enable_guided_navigation = self._get_bool_env(
            "CONTENT_TAMER_ENABLE_GUIDED_NAV", org_flags.enable_guided_navigation
        )

        # ML level toggles
        org_flags.enable_ml_level_1 = self._get_bool_env(
            "CONTENT_TAMER_ENABLE_ML_LEVEL_1", org_flags.enable_ml_level_1
        )

        org_flags.enable_ml_level_2 = self._get_bool_env(
            "CONTENT_TAMER_ENABLE_ML_LEVEL_2", org_flags.enable_ml_level_2
        )

        org_flags.enable_ml_level_3 = self._get_bool_env(
            "CONTENT_TAMER_ENABLE_ML_LEVEL_3", org_flags.enable_ml_level_3
        )

        # Safety limits
        org_flags.max_files_for_auto_enable = self._get_int_env(
            "CONTENT_TAMER_MAX_FILES_AUTO_ENABLE", org_flags.max_files_for_auto_enable
        )

        # Rollout percentage
        org_flags.rollout_percentage = self._get_float_env(
            "CONTENT_TAMER_ORGANIZATION_ROLLOUT", org_flags.rollout_percentage
        )

        return flags

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}, using default {default}")
            return default

    def _get_float_env(self, key: str, default: float) -> float:
        """Get float environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Invalid float value for {key}: {value}, using default {default}")
            return default

    def save_flags(self, flags: FeatureFlags) -> bool:
        """Save current feature flags to config file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(flags.to_dict(), f, indent=2)

            logger.info(f"Feature flags saved to {self.config_file}")
            self._flags = flags  # Update cache
            return True

        except OSError as e:
            logger.error(f"Error saving feature flags to {self.config_file}: {e}")
            return False

    def get_organization_flags(self) -> OrganizationFeatureFlags:
        """Get organization-specific feature flags."""
        return self.load_flags().organization

    def is_organization_enabled(self, file_count: int = 1, force_check: bool = False) -> bool:
        """Check if organization features should be available."""
        if force_check:
            self._flags = None  # Force reload

        org_flags = self.get_organization_flags()
        return org_flags.is_organization_available(file_count)

    def should_show_guided_navigation(self, file_count: int = 1) -> bool:
        """Check if guided navigation should be shown."""
        org_flags = self.get_organization_flags()
        return org_flags.enable_guided_navigation and org_flags.should_auto_enable(file_count)

    def get_available_ml_levels(self) -> List[int]:
        """Get list of available ML enhancement levels."""
        org_flags = self.get_organization_flags()
        available_levels = []

        if org_flags.enable_ml_level_1:
            available_levels.append(1)
        if org_flags.enable_ml_level_2:
            available_levels.append(2)
        if org_flags.enable_ml_level_3:
            available_levels.append(3)

        return available_levels

    def validate_ml_level(self, requested_level: int) -> int:
        """Validate and return appropriate ML level based on feature flags."""
        available_levels = self.get_available_ml_levels()

        if not available_levels:
            # No ML levels enabled, return 1 as fallback
            return 1

        if requested_level in available_levels:
            return requested_level

        # Find closest available level
        return min(available_levels, key=lambda x: abs(x - requested_level))


# Global feature flag manager instance
_feature_manager = None


def get_feature_manager() -> FeatureFlagManager:
    """Get global feature flag manager instance."""
    global _feature_manager
    if _feature_manager is None:
        _feature_manager = FeatureFlagManager()
    return _feature_manager


def is_organization_enabled(file_count: int = 1) -> bool:
    """Quick helper to check if organization is enabled."""
    return get_feature_manager().is_organization_enabled(file_count)


def should_show_guided_navigation(file_count: int = 1) -> bool:
    """Quick helper to check if guided navigation should be shown."""
    return get_feature_manager().should_show_guided_navigation(file_count)


def get_available_ml_levels() -> List[int]:
    """Quick helper to get available ML levels."""
    return get_feature_manager().get_available_ml_levels()
