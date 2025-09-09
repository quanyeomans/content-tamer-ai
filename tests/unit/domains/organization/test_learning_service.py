#!/usr/bin/env python3
"""
Tests for Learning Service in Organization Domain

Tests the learning service that handles state management and continuous
improvement for document organization.
"""

import unittest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch

# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

# Import from organization domain
from domains.organization.learning_service import (
    LearningService,
    StateManager,
    OrganizationSession,
    LearningMetrics
)
from domains.organization.clustering_service import ClassificationResult, ClusteringMethod
from domains.organization.folder_service import FolderStructure, FolderStructureType, FiscalYearType
from datetime import datetime

class TestStateManagerDefaults(unittest.TestCase):
    """Test StateManager default behavior and initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = StateManager(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_state_manager_initialization(self):
        """Test state manager initializes correctly."""
        self.assertIsInstance(self.state_manager, StateManager)
        self.assertEqual(self.state_manager.target_folder, self.temp_dir)
        self.assertTrue(self.state_manager.state_dir.exists())

    def test_default_preferences_loading(self):
        """Test loading default preferences."""
        preferences = self.state_manager.load_organization_preferences()

        self.assertIsInstance(preferences, dict)
        self.assertIn("structure_type", preferences)
        self.assertIn("ml_threshold", preferences)
        self.assertIn("learning_enabled", preferences)
        self.assertEqual(preferences["structure_type"], "category_first")
        self.assertEqual(preferences["ml_threshold"], 0.7)
        self.assertTrue(preferences["learning_enabled"])

    def test_preferences_persistence(self):
        """Test saving and loading preferences."""
        test_preferences = {
            "structure_type": "time_first",
            "ml_threshold": 0.8,
            "max_categories": 15
        }

        # Save preferences
        success = self.state_manager.save_organization_preferences(test_preferences)
        self.assertTrue(success)

        # Load preferences
        loaded_preferences = self.state_manager.load_organization_preferences()

        self.assertEqual(loaded_preferences["structure_type"], "time_first")
        self.assertEqual(loaded_preferences["ml_threshold"], 0.8)
        self.assertEqual(loaded_preferences["max_categories"], 15)
        self.assertIn("last_updated", loaded_preferences)

    def test_learned_patterns_persistence(self):
        """Test saving and loading learned patterns."""
        test_patterns = {
            "rule_patterns": {"financial": ["invoice", "bill"]},
            "ml_patterns": {"legal": ["contract", "agreement"]},
            "user_corrections": []
        }

        # Save patterns
        success = self.state_manager.save_learned_patterns(test_patterns)
        self.assertTrue(success)

        # Load patterns
        loaded_patterns = self.state_manager.load_learned_patterns()

        self.assertEqual(loaded_patterns["rule_patterns"], test_patterns["rule_patterns"])
        self.assertEqual(loaded_patterns["ml_patterns"], test_patterns["ml_patterns"])
        self.assertIn("last_updated", loaded_patterns)

class TestOrganizationSessionData(unittest.TestCase):
    """Test OrganizationSession data class."""

    def test_organization_session_creation(self):
        """Test creating organization session."""
        session = OrganizationSession(
            session_id="test_session_123",
            timestamp=datetime.now(),
            documents_processed=10,
            success_rate=0.85,
            structure_type="category_first",
            categories_created=["financial", "legal"],
            quality_score=0.78,
            metadata={"test": "data"}
        )

        self.assertEqual(session.session_id, "test_session_123")
        self.assertEqual(session.documents_processed, 10)
        self.assertEqual(session.success_rate, 0.85)
        self.assertEqual(session.structure_type, "category_first")
        self.assertEqual(len(session.categories_created), 2)
        self.assertEqual(session.quality_score, 0.78)

    def test_session_metadata_defaults(self):
        """Test session metadata initialization."""
        session = OrganizationSession(
            session_id="test",
            timestamp=datetime.now(),
            documents_processed=5,
            success_rate=0.9,
            structure_type="time_first",
            categories_created=[],
            quality_score=0.8,
            metadata=None  # Should be initialized to empty dict
        )

        self.assertIsInstance(session.metadata, dict)
        self.assertEqual(len(session.metadata), 0)

class TestLearningMetrics(unittest.TestCase):
    """Test LearningMetrics data class."""

    def test_learning_metrics_creation(self):
        """Test creating learning metrics."""
        metrics = LearningMetrics(
            total_sessions=15,
            average_quality_score=0.72,
            improvement_trend=0.05,
            user_corrections=3,
            successful_patterns={"rule_based": 120, "ml_enhanced": 45},
            failed_patterns={"fallback": 8}
        )

        self.assertEqual(metrics.total_sessions, 15)
        self.assertEqual(metrics.average_quality_score, 0.72)
        self.assertEqual(metrics.improvement_trend, 0.05)
        self.assertEqual(metrics.user_corrections, 3)
        self.assertEqual(metrics.successful_patterns["rule_based"], 120)
        self.assertEqual(metrics.failed_patterns["fallback"], 8)

    def test_metrics_defaults(self):
        """Test metrics with default values."""
        metrics = LearningMetrics(
            total_sessions=0,
            average_quality_score=0.0,
            improvement_trend=0.0,
            user_corrections=0,
            successful_patterns=None,  # Should be initialized to empty dict
            failed_patterns=None       # Should be initialized to empty dict
        )

        self.assertIsInstance(metrics.successful_patterns, dict)
        self.assertIsInstance(metrics.failed_patterns, dict)

class TestLearningServiceDefaults(unittest.TestCase):
    """Test LearningService default behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_service = LearningService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_learning_service_initialization(self):
        """Test learning service initializes correctly."""
        self.assertIsInstance(self.learning_service, LearningService)
        self.assertEqual(self.learning_service.target_folder, self.temp_dir)
        self.assertIsNotNone(self.learning_service.state_manager)
        self.assertIsNotNone(self.learning_service.preferences)
        self.assertIsNotNone(self.learning_service.learned_patterns)

    def test_default_preferences_loaded(self):
        """Test default preferences are loaded."""
        preferences = self.learning_service.preferences

        self.assertIn("structure_type", preferences)
        self.assertIn("learning_enabled", preferences)
        self.assertEqual(preferences["structure_type"], "category_first")
        self.assertTrue(preferences["learning_enabled"])

    def test_empty_learned_patterns_initially(self):
        """Test learned patterns start empty."""
        patterns = self.learning_service.learned_patterns

        self.assertIsInstance(patterns, dict)
        # Should have basic structure even if empty
        expected_keys = ["rule_patterns", "ml_patterns", "user_corrections"]
        for key in expected_keys:
            self.assertIn(key, patterns)

class TestSessionLearning(unittest.TestCase):
    """Test learning from organization sessions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_service = LearningService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_learn_from_session_success(self):
        """Test learning from successful session."""
        # Create mock session results
        session_results = {
            "doc1": ClassificationResult(
                category="financial",
                confidence=0.9,
                method=ClusteringMethod.RULE_BASED,
                reasoning="High confidence rule match",
                alternative_categories=[],
                metadata={"rule_patterns_matched": ["invoice", "payment"]}
            ),
            "doc2": ClassificationResult(
                category="legal",
                confidence=0.85,
                method=ClusteringMethod.ML_ENHANCED,
                reasoning="ML enhanced classification",
                alternative_categories=[("business", 0.3)],
                metadata={}
            )
        }

        folder_structure = FolderStructure(
            structure_type=FolderStructureType.CATEGORY_FIRST,
            fiscal_year_type=FiscalYearType.CALENDAR,
            time_granularity="year",
            base_path=self.temp_dir,
            categories=["financial", "legal"],
            metadata={}
        )

        quality_metrics = {
            "overall_quality": 85.0,
            "success_rate": 1.0,
            "method_distribution": {"rule_based": 1, "ml_enhanced": 1}
        }

        # Learn from session
        learning_results = self.learning_service.learn_from_session(
            session_results, folder_structure, quality_metrics
        )

        self.assertIsInstance(learning_results, dict)
        self.assertTrue(learning_results.get("session_recorded", False))
        self.assertIn("learning_summary", learning_results)

    def test_learn_from_empty_session(self):
        """Test learning from empty session."""
        session_results = {}
        folder_structure = FolderStructure(
            structure_type=FolderStructureType.CATEGORY_FIRST,
            fiscal_year_type=FiscalYearType.CALENDAR,
            time_granularity="year",
            base_path=self.temp_dir,
            categories=[],
            metadata={}
        )
        quality_metrics = {"overall_quality": 0.0, "success_rate": 0.0}

        learning_results = self.learning_service.learn_from_session(
            session_results, folder_structure, quality_metrics
        )

        self.assertIsInstance(learning_results, dict)
        # Should handle empty session gracefully

class TestUserCorrections(unittest.TestCase):
    """Test user correction learning."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_service = LearningService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_user_correction(self):
        """Test recording user correction."""
        success = self.learning_service.record_user_correction(
            file_name="invoice_2024.pd",
            from_category="legal",
            to_category="financial",
            session_id="test_session"
        )

        self.assertTrue(success)

    def test_correction_pattern_learning(self):
        """Test that corrections update learned patterns."""
        initial_patterns = dict(self.learning_service.learned_patterns)

        # Record correction
        self.learning_service.record_user_correction(
            file_name="contract_invoice.pd",
            from_category="legal",
            to_category="financial"
        )

        # Patterns should be updated
        updated_patterns = self.learning_service.learned_patterns
        self.assertIn("user_corrections", updated_patterns)

    def test_multiple_corrections(self):
        """Test handling multiple user corrections."""
        corrections = [
            ("invoice1.pd", "legal", "financial"),
            ("bill2.pd", "personal", "financial"),
            ("contract3.pd", "financial", "legal")
        ]

        for filename, from_cat, to_cat in corrections:
            success = self.learning_service.record_user_correction(
                filename, from_cat, to_cat
            )
            self.assertTrue(success)

class TestLearningMetricsCalculation(unittest.TestCase):
    """Test learning metrics calculation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_service = LearningService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_learning_metrics(self):
        """Test getting learning metrics."""
        metrics = self.learning_service.get_learning_metrics()

        self.assertIsInstance(metrics, LearningMetrics)
        self.assertGreaterEqual(metrics.total_sessions, 0)
        self.assertIsInstance(metrics.average_quality_score, float)
        self.assertIsInstance(metrics.improvement_trend, float)
        self.assertGreaterEqual(metrics.user_corrections, 0)
        self.assertIsInstance(metrics.successful_patterns, dict)
        self.assertIsInstance(metrics.failed_patterns, dict)

    def test_metrics_after_sessions(self):
        """Test metrics calculation after recording sessions."""
        # Create and record a session
        session_results = {
            "doc1": ClassificationResult(
                category="test", confidence=0.8, method=ClusteringMethod.RULE_BASED,
                reasoning="test", alternative_categories=[], metadata={}
            )
        }

        folder_structure = FolderStructure(
            structure_type=FolderStructureType.CATEGORY_FIRST,
            fiscal_year_type=FiscalYearType.CALENDAR,
            time_granularity="year",
            base_path=self.temp_dir,
            categories=["test"],
            metadata={}
        )

        quality_metrics = {"overall_quality": 80.0, "success_rate": 1.0}

        # Record session
        self.learning_service.learn_from_session(
            session_results, folder_structure, quality_metrics
        )

        # Get updated metrics
        metrics = self.learning_service.get_learning_metrics()
        self.assertGreaterEqual(metrics.total_sessions, 1)

class TestReorganizationRecommendations(unittest.TestCase):
    """Test reorganization recommendations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_service = LearningService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_should_reorganize_with_improvement(self):
        """Test reorganization recommendation with significant improvement."""
        recommendation = self.learning_service.should_reorganize_existing(
            current_quality=0.6,
            proposed_quality=0.8
        )

        self.assertIsInstance(recommendation, dict)
        self.assertIn("should_reorganize", recommendation)
        self.assertIn("improvement", recommendation)
        self.assertIn("recommendation", recommendation)
        self.assertTrue(recommendation["should_reorganize"])  # 33% improvement should trigger

    def test_should_not_reorganize_minimal_improvement(self):
        """Test no reorganization with minimal improvement."""
        recommendation = self.learning_service.should_reorganize_existing(
            current_quality=0.7,
            proposed_quality=0.72
        )

        self.assertFalse(recommendation["should_reorganize"])  # <15% improvement

    def test_reorganization_with_zero_current_quality(self):
        """Test reorganization recommendation with zero current quality."""
        recommendation = self.learning_service.should_reorganize_existing(
            current_quality=0.0,
            proposed_quality=0.6
        )

        # Should handle zero division gracefully
        self.assertIsInstance(recommendation, dict)
        self.assertIn("should_reorganize", recommendation)

class TestServiceStatistics(unittest.TestCase):
    """Test learning service statistics."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_service = LearningService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_service_statistics(self):
        """Test getting service statistics."""
        stats = self.learning_service.get_service_statistics()

        self.assertIsInstance(stats, dict)
        self.assertIn("target_folder", stats)
        self.assertIn("state_directory", stats)
        self.assertIn("preferences_loaded", stats)
        self.assertIn("patterns_loaded", stats)
        self.assertIn("learning_metrics", stats)
        self.assertIn("current_preferences", stats)

        # Verify data types
        self.assertEqual(stats["target_folder"], self.temp_dir)
        self.assertTrue(stats["preferences_loaded"])
        self.assertTrue(stats["patterns_loaded"])
        self.assertIsInstance(stats["learning_metrics"], dict)
        self.assertIsInstance(stats["current_preferences"], dict)

if __name__ == "__main__":
    unittest.main()
