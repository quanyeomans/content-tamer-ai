"""
Learning Service

State management and continuous improvement for document organization.
Implements hybrid learning approach from PRD_04 specification.
"""

import json
import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .clustering_service import ClassificationResult, ClusteringMethod
from .folder_service import FolderStructure


@dataclass
class OrganizationSession:
    """Represents a document organization session."""

    session_id: str
    timestamp: datetime
    documents_processed: int
    success_rate: float
    structure_type: str
    categories_created: List[str]
    quality_score: float
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LearningMetrics:
    """Metrics for learning system performance."""

    total_sessions: int
    average_quality_score: float
    improvement_trend: float
    user_corrections: int
    successful_patterns: Dict[str, int]
    failed_patterns: Dict[str, int]

    def __post_init__(self):
        if self.successful_patterns is None:
            self.successful_patterns = {}
        if self.failed_patterns is None:
            self.failed_patterns = {}


class StateManager:
    """Manages persistent state for organization learning."""

    def __init__(self, target_folder: str):
        """Initialize state manager for a target folder.

        Args:
            target_folder: Target folder for organization
        """
        self.target_folder = target_folder
        self.state_dir = Path(target_folder) / ".content_tamer"
        self.logger = logging.getLogger(__name__)

        # Initialize state directory
        self._initialize_state_directory()

        # File paths
        self.config_file = self.state_dir / "organization_config.json"
        self.preferences_file = self.state_dir / "organization_preferences.json"
        self.history_db = self.state_dir / "history.db"
        self.patterns_file = self.state_dir / "learned_patterns.json"

    def _initialize_state_directory(self) -> None:
        """Create state directory with proper permissions."""
        try:
            self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

            # Verify permissions
            if not os.access(self.state_dir, os.W_OK):
                raise PermissionError(f"Cannot write to state directory: {self.state_dir}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize state directory: {e}")

    def load_organization_preferences(self) -> Dict[str, Any]:
        """Load organization preferences from persistent storage."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, "r", encoding="utf-8") as f:
                    preferences = json.load(f)
                self.logger.debug("Loaded organization preferences")
                return preferences
            else:
                return self._get_default_preferences()

        except Exception as e:
            self.logger.warning("Failed to load preferences: %s", e)
            return self._get_default_preferences()

    def save_organization_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Save organization preferences to persistent storage."""
        try:
            preferences["last_updated"] = datetime.now().isoformat()

            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)

            self.logger.debug("Saved organization preferences")
            return True

        except Exception as e:
            self.logger.error("Failed to save preferences: %s", e)
            return False

    def load_learned_patterns(self) -> Dict[str, Any]:
        """Load learned classification patterns."""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, "r", encoding="utf-8") as f:
                    patterns = json.load(f)
                return patterns
            else:
                return {"rule_patterns": {}, "ml_patterns": {}, "user_corrections": []}

        except Exception as e:
            self.logger.warning("Failed to load learned patterns: %s", e)
            return {"rule_patterns": {}, "ml_patterns": {}, "user_corrections": []}

    def save_learned_patterns(self, patterns: Dict[str, Any]) -> bool:
        """Save learned classification patterns."""
        try:
            patterns["last_updated"] = datetime.now().isoformat()

            with open(self.patterns_file, "w", encoding="utf-8") as f:
                json.dump(patterns, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            self.logger.error("Failed to save learned patterns: %s", e)
            return False

    def record_organization_session(self, session: OrganizationSession) -> bool:
        """Record organization session in history database."""
        try:
            self._initialize_history_db()

            with sqlite3.connect(self.history_db) as conn:
                conn.execute(
                    """
                    INSERT INTO organization_sessions 
                    (session_id, timestamp, documents_processed, success_rate, 
                     structure_type, quality_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session.session_id,
                        session.timestamp.isoformat(),
                        session.documents_processed,
                        session.success_rate,
                        session.structure_type,
                        session.quality_score,
                        json.dumps(session.metadata),
                    ),
                )

                # Record categories created
                for category in session.categories_created:
                    conn.execute(
                        """
                        INSERT INTO session_categories (session_id, category_name)
                        VALUES (?, ?)
                    """,
                        (session.session_id, category),
                    )

                conn.commit()

            self.logger.debug("Recorded organization session: %s", session.session_id)
            return True

        except Exception as e:
            self.logger.error("Failed to record session: %s", e)
            return False

    def _initialize_history_db(self) -> None:
        """Initialize history database schema."""
        try:
            with sqlite3.connect(self.history_db) as conn:
                # Organization sessions table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS organization_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        timestamp TEXT NOT NULL,
                        documents_processed INTEGER NOT NULL,
                        success_rate REAL NOT NULL,
                        structure_type TEXT NOT NULL,
                        quality_score REAL NOT NULL,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Session categories table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS session_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        category_name TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES organization_sessions (session_id)
                    )
                """
                )

                # User corrections table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_corrections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT NOT NULL,
                        from_category TEXT NOT NULL,
                        to_category TEXT NOT NULL,
                        correction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                """
                )

                conn.commit()

        except Exception as e:
            self.logger.error("Failed to initialize history database: %s", e)
            raise

    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default organization preferences."""
        return {
            "structure_type": "category_first",
            "fiscal_year_type": "calendar",
            "time_granularity": "year",
            "ml_threshold": 0.7,
            "max_categories": 20,
            "min_category_size": 2,
            "quality_threshold": 0.15,
            "auto_reorganization": False,
            "learning_enabled": True,
        }


class LearningService:
    """Service for continuous learning and improvement."""

    def __init__(self, target_folder: str, spacy_model=None):
        """Initialize learning service.

        Args:
            target_folder: Target folder for organization
            spacy_model: Pre-loaded spaCy model to use (for performance optimization)
        """
        self.target_folder = target_folder
        self.spacy_model = spacy_model
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager(target_folder)

        # Load existing patterns and preferences
        self.learned_patterns = self.state_manager.load_learned_patterns()
        self.preferences = self.state_manager.load_organization_preferences()

    def learn_from_session(
        self,
        session_results: Dict[str, ClassificationResult],
        folder_structure: FolderStructure,
        quality_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Learn from organization session results.

        Args:
            session_results: Classification results from session
            folder_structure: Folder structure used
            quality_metrics: Quality assessment of organization

        Returns:
            Dictionary with learning outcomes
        """
        try:
            # Create session record
            session = OrganizationSession(
                session_id=f"session_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                documents_processed=len(session_results),
                success_rate=quality_metrics.get("success_rate", 0.0),
                structure_type=folder_structure.structure_type.value if folder_structure.structure_type else "unknown",
                categories_created=folder_structure.categories,
                quality_score=quality_metrics.get("overall_quality", 0.0),
                metadata={
                    "fiscal_year": folder_structure.fiscal_year_type.value if folder_structure.fiscal_year_type else "unknown",
                    "time_granularity": folder_structure.time_granularity,
                    "quality_metrics": quality_metrics,
                },
            )

            # Record session
            self.state_manager.record_organization_session(session)

            # Learn from successful patterns
            learned_improvements = self._extract_successful_patterns(session_results)

            # Update learned patterns
            self._update_learned_patterns(learned_improvements)

            # Update preferences if significant improvement
            preference_updates = self._evaluate_preference_updates(session, quality_metrics)
            if preference_updates:
                self._update_preferences(preference_updates)

            return {
                "session_recorded": True,
                "patterns_learned": len(learned_improvements),
                "preferences_updated": bool(preference_updates),
                "learning_summary": {
                    "session_quality": session.quality_score,
                    "documents_processed": session.documents_processed,
                    "new_patterns": len(learned_improvements),
                },
            }

        except Exception as e:
            self.logger.error("Learning from session failed: %s", e)
            return {"session_recorded": False, "error": str(e)}

    def _extract_successful_patterns(
        self, results: Dict[str, ClassificationResult]
    ) -> Dict[str, Any]:
        """Extract successful patterns from classification results."""
        successful_patterns = {
            "high_confidence_rules": [],
            "effective_ml_patterns": [],
            "category_indicators": {},
        }

        for file_path, result in results.items():
            if result.confidence >= 0.8:  # High confidence results
                pattern = {
                    "category": result.category,
                    "method": result.method.value if result.method else "unknown",
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "file_indicators": self._extract_file_indicators(file_path, result),
                }

                if result.method == ClusteringMethod.RULE_BASED:
                    successful_patterns["high_confidence_rules"].append(pattern)
                elif result.method == ClusteringMethod.ML_ENHANCED:
                    successful_patterns["effective_ml_patterns"].append(pattern)

                # Track category indicators
                category = result.category
                if category not in successful_patterns["category_indicators"]:
                    successful_patterns["category_indicators"][category] = []

                successful_patterns["category_indicators"][category].append(
                    pattern["file_indicators"]
                )

        return successful_patterns

    def _extract_file_indicators(
        self, file_path: str, result: ClassificationResult
    ) -> Dict[str, Any]:
        """Extract indicators from file that led to successful classification."""
        filename = os.path.basename(file_path)

        return {
            "filename_pattern": filename,
            "file_extension": os.path.splitext(filename)[1].lower(),
            "confidence": result.confidence,
            "method": result.method.value if result.method else "unknown",
            "pattern_matched": result.metadata.get("rule_patterns_matched", []),
        }

    def _update_learned_patterns(self, improvements: Dict[str, Any]) -> None:
        """Update learned patterns with new successful patterns."""
        # Merge with existing patterns
        for pattern_type, patterns in improvements.items():
            if pattern_type not in self.learned_patterns:
                self.learned_patterns[pattern_type] = []

            self.learned_patterns[pattern_type].extend(patterns)

            # Limit pattern storage to prevent bloat
            if len(self.learned_patterns[pattern_type]) > 100:
                # Keep most recent and highest confidence patterns
                sorted_patterns = sorted(
                    self.learned_patterns[pattern_type],
                    key=lambda p: (p.get("confidence", 0), p.get("timestamp", "")),
                    reverse=True,
                )
                self.learned_patterns[pattern_type] = sorted_patterns[:100]

        # Save updated patterns
        self.state_manager.save_learned_patterns(self.learned_patterns)

    def _evaluate_preference_updates(
        self, session: OrganizationSession, quality_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate whether to update organization preferences."""
        updates = {}

        # Check if this session performed significantly better than previous
        historical_quality = self._get_historical_average_quality()
        if session.quality_score > historical_quality + 0.15:  # 15% improvement
            self.logger.info(
                "Session quality (%.2f) significantly better than average (%.2f)",
                session.quality_score,
                historical_quality,
            )

            # Consider updating structure preferences
            if session.structure_type != self.preferences.get("structure_type"):
                updates["structure_type"] = session.structure_type
                updates["structure_update_reason"] = (
                    f"Better quality: {session.quality_score:.2f} vs {historical_quality:.2f}"
                )

            # Consider updating ML threshold
            method_distribution = quality_metrics.get("method_distribution", {})
            ml_success_rate = (
                method_distribution.get("ml_enhanced", 0) / session.documents_processed
            )
            if ml_success_rate > 0.3:  # ML was used successfully for >30% of documents
                current_threshold = self.preferences.get("ml_threshold", 0.7)
                if current_threshold > 0.6:  # Lower threshold to use ML more
                    updates["ml_threshold"] = max(0.5, current_threshold - 0.1)
                    updates["ml_threshold_reason"] = f"ML success rate: {ml_success_rate:.1%}"

        return updates

    def _update_preferences(self, updates: Dict[str, Any]) -> None:
        """Update organization preferences with learning outcomes."""
        self.preferences.update(updates)
        self.preferences["last_learning_update"] = datetime.now().isoformat()

        # Save updated preferences
        if self.state_manager.save_organization_preferences(self.preferences):
            self.logger.info("Updated preferences: %s", list(updates.keys()))
        else:
            self.logger.error("Failed to save updated preferences")

    def _get_historical_average_quality(self) -> float:
        """Get average quality score from historical sessions."""
        try:
            with sqlite3.connect(self.state_manager.history_db) as conn:
                cursor = conn.execute(
                    """
                    SELECT AVG(quality_score) FROM organization_sessions 
                    WHERE timestamp > datetime('now', '-30 days')
                """
                )
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0.5

        except Exception as e:
            self.logger.warning("Failed to get historical quality: %s", e)
            return 0.5  # Default baseline

    def record_user_correction(
        self, file_name: str, from_category: str, to_category: str, session_id: Optional[str] = None
    ) -> bool:
        """Record user correction for learning.

        Args:
            file_name: Name of file that was moved
            from_category: Original category
            to_category: Corrected category
            session_id: Optional session ID

        Returns:
            True if correction was recorded successfully
        """
        try:
            self.state_manager._initialize_history_db()

            with sqlite3.connect(self.state_manager.history_db) as conn:
                conn.execute(
                    """
                    INSERT INTO user_corrections 
                    (file_name, from_category, to_category, session_id)
                    VALUES (?, ?, ?, ?)
                """,
                    (file_name, from_category, to_category, session_id),
                )

                conn.commit()

            self.logger.info(
                "Recorded user correction: %s %s → %s", file_name, from_category, to_category
            )

            # Update learning patterns based on correction
            self._learn_from_correction(file_name, from_category, to_category)

            return True

        except Exception as e:
            self.logger.error("Failed to record user correction: %s", e)
            return False

    def _learn_from_correction(self, file_name: str, from_category: str, to_category: str) -> None:
        """Update learning patterns based on user correction."""
        try:
            # Load current patterns
            patterns = self.state_manager.load_learned_patterns()

            # Record the correction pattern
            if "user_corrections" not in patterns:
                patterns["user_corrections"] = []

            correction = {
                "file_name": file_name,
                "from_category": from_category,
                "to_category": to_category,
                "timestamp": datetime.now().isoformat(),
                "file_indicators": self._analyze_corrected_file_patterns(file_name),
            }

            patterns["user_corrections"].append(correction)

            # Update rule patterns to prefer user's category choice
            self._strengthen_pattern_for_category(patterns, file_name, to_category)
            self._weaken_pattern_for_category(patterns, file_name, from_category)

            # Save updated patterns
            self.state_manager.save_learned_patterns(patterns)

        except Exception as e:
            self.logger.error("Failed to learn from correction: %s", e)

    def _analyze_corrected_file_patterns(self, file_name: str) -> Dict[str, Any]:
        """Analyze patterns in corrected file for learning."""
        indicators = {
            "keywords": [],
            "file_extension": os.path.splitext(file_name)[1].lower(),
            "length": len(file_name),
            "has_numbers": bool(re.search(r"\d", file_name)),
            "has_date": bool(re.search(r"\d{4}|\d{1,2}[/-]\d{1,2}", file_name)),
        }

        # Extract keywords from filename
        filename_words = re.findall(r"[a-zA-Z]+", file_name.lower())
        indicators["keywords"] = [word for word in filename_words if len(word) > 2]

        return indicators

    def _strengthen_pattern_for_category(
        self, patterns: Dict[str, Any], file_name: str, category: str
    ) -> None:
        """Strengthen patterns that should lead to this category."""
        if "category_strengthening" not in patterns:
            patterns["category_strengthening"] = {}

        if category not in patterns["category_strengthening"]:
            patterns["category_strengthening"][category] = []

        file_indicators = self._analyze_corrected_file_patterns(file_name)
        patterns["category_strengthening"][category].append(file_indicators)

    def _weaken_pattern_for_category(
        self, patterns: Dict[str, Any], file_name: str, category: str
    ) -> None:
        """Weaken patterns that incorrectly led to this category."""
        if "category_weakening" not in patterns:
            patterns["category_weakening"] = {}

        if category not in patterns["category_weakening"]:
            patterns["category_weakening"][category] = []

        file_indicators = self._analyze_corrected_file_patterns(file_name)
        patterns["category_weakening"][category].append(file_indicators)

    def get_learning_metrics(self) -> LearningMetrics:
        """Get comprehensive learning metrics."""
        try:
            with sqlite3.connect(self.state_manager.history_db) as conn:
                # Get session statistics
                cursor = conn.execute(
                    """
                    SELECT COUNT(*), AVG(quality_score) 
                    FROM organization_sessions
                """
                )
                session_stats = cursor.fetchone()

                total_sessions = session_stats[0] if session_stats else 0
                avg_quality = session_stats[1] if session_stats and session_stats[1] else 0.0

                # Get improvement trend (last 10 vs previous sessions)
                cursor = conn.execute(
                    """
                    SELECT AVG(quality_score) FROM (
                        SELECT quality_score FROM organization_sessions 
                        ORDER BY timestamp DESC LIMIT 10
                    )
                """
                )
                recent_quality = cursor.fetchone()[0] or 0.0

                cursor = conn.execute(
                    """
                    SELECT AVG(quality_score) FROM (
                        SELECT quality_score FROM organization_sessions 
                        ORDER BY timestamp DESC LIMIT 20 OFFSET 10
                    )
                """
                )
                older_quality = cursor.fetchone()[0] or 0.0

                improvement_trend = recent_quality - older_quality

                # Get user correction count
                cursor = conn.execute("SELECT COUNT(*) FROM user_corrections")
                correction_count = cursor.fetchone()[0] or 0

            # Analyze pattern success
            successful_patterns, failed_patterns = self._analyze_pattern_success()

            return LearningMetrics(
                total_sessions=total_sessions,
                average_quality_score=avg_quality,
                improvement_trend=improvement_trend,
                user_corrections=correction_count,
                successful_patterns=successful_patterns,
                failed_patterns=failed_patterns,
            )

        except Exception as e:
            self.logger.error("Failed to get learning metrics: %s", e)
            return LearningMetrics(
                total_sessions=0,
                average_quality_score=0.0,
                improvement_trend=0.0,
                user_corrections=0,
                successful_patterns={},
                failed_patterns={},
            )

    def _analyze_pattern_success(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Analyze which patterns are successful vs failed."""
        successful = {}
        failed = {}

        # Analyze learned patterns
        for pattern_type, patterns in self.learned_patterns.items():
            if pattern_type == "high_confidence_rules":
                successful[pattern_type] = len(patterns)
            elif pattern_type in ["category_weakening", "failed_classifications"]:
                failed[pattern_type] = len(patterns)

        return successful, failed

    def should_reorganize_existing(
        self, current_quality: float, proposed_quality: float
    ) -> Dict[str, Any]:
        """Determine if existing organization should be improved.

        Args:
            current_quality: Quality score of current organization
            proposed_quality: Quality score of proposed reorganization

        Returns:
            Dictionary with reorganization recommendation
        """
        quality_threshold = self.preferences.get(
            "quality_threshold", 0.15
        )  # 15% improvement required
        auto_reorganization = self.preferences.get("auto_reorganization", False)

        improvement = (
            (proposed_quality - current_quality) / current_quality if current_quality > 0 else 0
        )

        should_reorganize = improvement >= quality_threshold

        return {
            "should_reorganize": should_reorganize,
            "auto_approved": should_reorganize and auto_reorganization,
            "improvement": f"{improvement:.1%}",
            "quality_threshold": f"{quality_threshold:.1%}",
            "current_quality": current_quality,
            "proposed_quality": proposed_quality,
            "recommendation": (
                "Reorganization recommended - significant improvement detected"
                if should_reorganize
                else "Current organization is adequate - no reorganization needed"
            ),
        }

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get learning service statistics."""
        metrics = self.get_learning_metrics()

        return {
            "target_folder": self.target_folder,
            "state_directory": str(self.state_manager.state_dir),
            "preferences_loaded": bool(self.preferences),
            "patterns_loaded": bool(self.learned_patterns),
            "learning_metrics": {
                "sessions": metrics.total_sessions,
                "average_quality": f"{metrics.average_quality_score:.2f}",
                "improvement_trend": f"{metrics.improvement_trend:.2f}",
                "corrections": metrics.user_corrections,
            },
            "current_preferences": {
                k: v
                for k, v in self.preferences.items()
                if k in ["structure_type", "ml_threshold", "max_categories"]
            },
        }
