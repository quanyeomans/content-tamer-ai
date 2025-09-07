"""
Simple State Manager

Manages organization preferences and session state using JSON files
in the .content_tamer directory pattern established in the codebase.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging


class SimpleStateManager:
    """Manages organization state and preferences using JSON files."""

    def __init__(self, target_folder: str):
        """
        Initialize state manager for target folder.

        Args:
            target_folder: Target directory for organization state
        """
        self.target_folder = target_folder
        self.state_dir = os.path.join(target_folder, ".content_tamer")
        self.organization_dir = os.path.join(self.state_dir, "organization")

        # Ensure directories exist
        self._ensure_directories()

        # State file paths
        self.preferences_file = os.path.join(self.organization_dir, "preferences.json")
        self.session_history_file = os.path.join(self.organization_dir, "session_history.json")
        self.domain_model_file = os.path.join(self.organization_dir, "domain_model.json")

    def _ensure_directories(self) -> None:
        """Ensure state directories exist."""
        try:
            os.makedirs(self.organization_dir, exist_ok=True)
        except OSError as e:
            logging.error(f"Failed to create state directories: {e}")
            raise

    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Save organization preferences to JSON file.

        Args:
            preferences: Organization preferences dictionary

        Returns:
            Success status
        """
        try:
            # Add metadata
            preferences_with_meta = {
                "preferences": preferences,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
            }

            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump(preferences_with_meta, f, indent=2, ensure_ascii=False)

            return True

        except (IOError, OSError, json.JSONEncodeError) as e:
            logging.error(f"Failed to save preferences: {e}")
            return False

    def load_preferences(self) -> Dict[str, Any]:
        """
        Load organization preferences from JSON file.

        Returns:
            Preferences dictionary or default values
        """
        default_preferences = {
            "hierarchy_type": "category-first",  # or "time-first"
            "fiscal_year": "calendar",  # or "fy-july", "fy-october", etc.
            "time_granularity": "year",  # or "year-month"
            "quality_threshold": 0.15,  # 15% improvement threshold
            "auto_reorganize": False,  # Require explicit confirmation
            "preferred_categories": [
                "contracts",
                "invoices",
                "reports",
                "correspondence",
                "financial",
                "legal",
            ],
        }

        if not os.path.exists(self.preferences_file):
            return default_preferences

        try:
            with open(self.preferences_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract preferences from metadata structure
            if "preferences" in data:
                loaded_prefs = data["preferences"]
            else:
                # Handle legacy format
                loaded_prefs = data

            # Merge with defaults to ensure all keys exist
            for key, default_value in default_preferences.items():
                if key not in loaded_prefs:
                    loaded_prefs[key] = default_value

            return loaded_prefs

        except (IOError, OSError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load preferences, using defaults: {e}")
            return default_preferences

    def save_session_data(self, session_data: Dict[str, Any]) -> bool:
        """
        Save organization session data.

        Args:
            session_data: Session data including quality metrics, classifications, etc.

        Returns:
            Success status
        """
        try:
            # Load existing history
            history = self._load_session_history()

            # Add new session with timestamp
            session_entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_data.get(
                    "session_id", f"session_{int(datetime.now().timestamp())}"
                ),
                "data": session_data,
            }

            history.append(session_entry)

            # Keep only last 50 sessions to prevent file growth
            if len(history) > 50:
                history = history[-50:]

            # Save updated history
            with open(self.session_history_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": "1.0",
                        "last_updated": datetime.now().isoformat(),
                        "sessions": history,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            return True

        except (IOError, OSError, json.JSONEncodeError) as e:
            logging.error(f"Failed to save session data: {e}")
            return False

    def _load_session_history(self) -> list:
        """Load session history from JSON file."""
        if not os.path.exists(self.session_history_file):
            return []

        try:
            with open(self.session_history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("sessions", [])

        except (IOError, OSError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load session history: {e}")
            return []

    def get_last_session_quality(self) -> Optional[float]:
        """Get quality metrics from the last organization session."""
        history = self._load_session_history()
        if not history:
            return None

        last_session = history[-1]
        session_data = last_session.get("data", {})
        quality_metrics = session_data.get("quality_metrics", {})

        return quality_metrics.get("accuracy")

    def save_domain_model(self, domain_patterns: Dict[str, Any]) -> bool:
        """
        Save learned domain patterns for future classification improvement.

        Args:
            domain_patterns: Learned patterns and examples

        Returns:
            Success status
        """
        try:
            domain_data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "target_folder": self.target_folder,
                "patterns": domain_patterns,
            }

            with open(self.domain_model_file, "w", encoding="utf-8") as f:
                json.dump(domain_data, f, indent=2, ensure_ascii=False)

            return True

        except (IOError, OSError, json.JSONEncodeError) as e:
            logging.error(f"Failed to save domain model: {e}")
            return False

    def load_domain_model(self) -> Dict[str, Any]:
        """Load learned domain patterns."""
        if not os.path.exists(self.domain_model_file):
            return {}

        try:
            with open(self.domain_model_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("patterns", {})

        except (IOError, OSError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load domain model: {e}")
            return {}

    def get_organization_stats(self) -> Dict[str, Any]:
        """Get organization statistics for the current folder."""
        history = self._load_session_history()
        preferences = self.load_preferences()

        stats = {
            "total_sessions": len(history),
            "current_preferences": preferences,
            "state_directory": self.state_dir,
            "last_organization": None,
            "average_quality": None,
        }

        if history:
            stats["last_organization"] = history[-1]["timestamp"]

            # Calculate average quality from recent sessions
            quality_scores = []
            for session in history[-10:]:  # Last 10 sessions
                session_data = session.get("data", {})
                quality_metrics = session_data.get("quality_metrics", {})
                if "accuracy" in quality_metrics:
                    quality_scores.append(quality_metrics["accuracy"])

            if quality_scores:
                stats["average_quality"] = sum(quality_scores) / len(quality_scores)

        return stats

    def clear_state(self) -> bool:
        """Clear all organization state (useful for testing)."""
        try:
            files_to_remove = [
                self.preferences_file,
                self.session_history_file,
                self.domain_model_file,
            ]

            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)

            return True

        except OSError as e:
            logging.error(f"Failed to clear state: {e}")
            return False
