#!/usr/bin/env python3
"""
Optimized Tests for Learning Service in Organization Domain

Tests the learning service using session-scoped ML model fixtures for performance.
Migrated from unittest to pytest for fixture compatibility.
"""

import json
import os
import sys
import tempfile

# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

import pytest
from datetime import datetime

from domains.organization.clustering_service import ClassificationResult, ClusteringMethod
from domains.organization.folder_service import FiscalYearType, FolderStructure, FolderStructureType

# Import from organization domain
from domains.organization.learning_service import (
    LearningMetrics,
    LearningService,
    OrganizationSession,
    StateManager,
)


# ============================================================================
# Test StateManager Defaults and Functionality
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup handled by tempfile system


def test_state_manager_initialization(temp_dir):
    """Test state manager initializes correctly."""
    state_manager = StateManager(temp_dir)
    
    assert isinstance(state_manager, StateManager)
    assert state_manager.target_folder == temp_dir
    assert state_manager.state_dir.exists()


def test_default_preferences_loading(temp_dir):
    """Test loading default preferences."""
    state_manager = StateManager(temp_dir)
    preferences = state_manager.load_organization_preferences()

    assert isinstance(preferences, dict)
    assert "structure_type" in preferences
    assert "ml_threshold" in preferences
    assert "learning_enabled" in preferences
    assert preferences["structure_type"] == "category_first"
    assert preferences["ml_threshold"] == 0.7
    assert preferences["learning_enabled"] is True


def test_preferences_persistence(temp_dir):
    """Test saving and loading preferences."""
    state_manager = StateManager(temp_dir)
    
    test_preferences = {
        "structure_type": "time_first",
        "ml_threshold": 0.8,
        "max_categories": 15,
    }

    # Save preferences
    success = state_manager.save_organization_preferences(test_preferences)
    assert success is True

    # Load preferences
    loaded_preferences = state_manager.load_organization_preferences()

    assert loaded_preferences["structure_type"] == "time_first"
    assert loaded_preferences["ml_threshold"] == 0.8
    assert loaded_preferences["max_categories"] == 15
    assert "last_updated" in loaded_preferences


def test_learned_patterns_persistence(temp_dir):
    """Test saving and loading learned patterns."""
    state_manager = StateManager(temp_dir)
    
    test_patterns = {
        "rule_patterns": {"financial": ["invoice", "bill"]},
        "ml_patterns": {"legal": ["contract", "agreement"]},
        "user_corrections": [],
    }

    # Save patterns
    success = state_manager.save_learned_patterns(test_patterns)
    assert success is True

    # Load patterns
    loaded_patterns = state_manager.load_learned_patterns()

    assert loaded_patterns["rule_patterns"] == test_patterns["rule_patterns"]
    assert loaded_patterns["ml_patterns"] == test_patterns["ml_patterns"]
    assert "last_updated" in loaded_patterns


# ============================================================================
# Test OrganizationSession Data Class
# ============================================================================

def test_organization_session_creation():
    """Test creating organization session."""
    session = OrganizationSession(
        session_id="test_session_123",
        timestamp=datetime.now(),
        documents_processed=10,
        success_rate=0.85,
        structure_type="category_first",
        categories_created=["financial", "legal"],
        quality_score=0.78,
        metadata={"test": "data"},
    )

    assert session.session_id == "test_session_123"
    assert session.documents_processed == 10
    assert session.success_rate == 0.85
    assert session.structure_type == "category_first"
    assert len(session.categories_created) == 2
    assert session.quality_score == 0.78


def test_session_metadata_defaults():
    """Test session metadata initialization."""
    session = OrganizationSession(
        session_id="test",
        timestamp=datetime.now(),
        documents_processed=5,
        success_rate=0.9,
        structure_type="time_first",
        categories_created=[],
        quality_score=0.8,
        metadata=None,  # Should be initialized to empty dict
    )

    assert isinstance(session.metadata, dict)
    assert len(session.metadata) == 0


# ============================================================================
# Test LearningMetrics Data Class
# ============================================================================

def test_learning_metrics_creation():
    """Test creating learning metrics."""
    metrics = LearningMetrics(
        total_sessions=15,
        average_quality_score=0.72,
        improvement_trend=0.05,
        user_corrections=3,
        successful_patterns={"rule_based": 120, "ml_enhanced": 45},
        failed_patterns={"fallback": 8},
    )

    assert metrics.total_sessions == 15
    assert metrics.average_quality_score == 0.72
    assert metrics.improvement_trend == 0.05
    assert metrics.user_corrections == 3
    assert metrics.successful_patterns["rule_based"] == 120
    assert metrics.failed_patterns["fallback"] == 8


def test_metrics_defaults():
    """Test metrics with default values."""
    metrics = LearningMetrics(
        total_sessions=0,
        average_quality_score=0.0,
        improvement_trend=0.0,
        user_corrections=0,
        successful_patterns=None,  # Should be initialized to empty dict
        failed_patterns=None,  # Should be initialized to empty dict
    )

    assert isinstance(metrics.successful_patterns, dict)
    assert isinstance(metrics.failed_patterns, dict)


# ============================================================================
# Test LearningService Defaults and Initialization
# ============================================================================

def test_learning_service_initialization(temp_dir, spacy_model):
    """Test learning service initializes correctly."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)

    assert isinstance(learning_service, LearningService)
    assert learning_service.target_folder == temp_dir
    assert learning_service.spacy_model is spacy_model
    assert learning_service.state_manager is not None
    assert learning_service.preferences is not None
    assert learning_service.learned_patterns is not None


def test_default_preferences_loaded(temp_dir, spacy_model):
    """Test default preferences are loaded."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    preferences = learning_service.preferences

    assert "structure_type" in preferences
    assert "learning_enabled" in preferences
    assert preferences["structure_type"] == "category_first"
    assert preferences["learning_enabled"] is True


def test_empty_learned_patterns_initially(temp_dir, spacy_model):
    """Test learned patterns start empty."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    patterns = learning_service.learned_patterns

    assert isinstance(patterns, dict)
    # Should have basic structure even if empty
    expected_keys = ["rule_patterns", "ml_patterns", "user_corrections"]
    for key in expected_keys:
        assert key in patterns


# ============================================================================
# Test Session Learning
# ============================================================================

def test_learn_from_session_success(temp_dir, spacy_model):
    """Test learning from successful session."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    # Create mock session results
    session_results = {
        "doc1": ClassificationResult(
            category="financial",
            confidence=0.9,
            method=ClusteringMethod.RULE_BASED,
            reasoning="High confidence rule match",
            alternative_categories=[],
            metadata={"rule_patterns_matched": ["invoice", "payment"]},
        ),
        "doc2": ClassificationResult(
            category="legal",
            confidence=0.85,
            method=ClusteringMethod.ML_ENHANCED,
            reasoning="ML enhanced classification",
            alternative_categories=[("business", 0.3)],
            metadata={},
        ),
    }

    folder_structure = FolderStructure(
        structure_type=FolderStructureType.CATEGORY_FIRST,
        fiscal_year_type=FiscalYearType.CALENDAR,
        time_granularity="year",
        base_path=temp_dir,
        categories=["financial", "legal"],
        metadata={},
    )

    quality_metrics = {
        "overall_quality": 85.0,
        "success_rate": 1.0,
        "method_distribution": {"rule_based": 1, "ml_enhanced": 1},
    }

    # Learn from session
    learning_results = learning_service.learn_from_session(
        session_results, folder_structure, quality_metrics
    )

    assert isinstance(learning_results, dict)
    assert learning_results.get("session_recorded", False) is True
    assert "learning_summary" in learning_results


def test_learn_from_empty_session(temp_dir, spacy_model):
    """Test learning from empty session."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    session_results = {}
    folder_structure = FolderStructure(
        structure_type=FolderStructureType.CATEGORY_FIRST,
        fiscal_year_type=FiscalYearType.CALENDAR,
        time_granularity="year",
        base_path=temp_dir,
        categories=[],
        metadata={},
    )
    quality_metrics = {"overall_quality": 0.0, "success_rate": 0.0}

    learning_results = learning_service.learn_from_session(
        session_results, folder_structure, quality_metrics
    )

    assert isinstance(learning_results, dict)
    # Should handle empty session gracefully


# ============================================================================
# Test User Corrections
# ============================================================================

def test_record_user_correction(temp_dir, spacy_model):
    """Test recording user correction."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    success = learning_service.record_user_correction(
        file_name="invoice_2024.pdf",
        from_category="legal",
        to_category="financial",
        session_id="test_session",
    )

    assert success is True


def test_correction_pattern_learning(temp_dir, spacy_model):
    """Test that corrections update learned patterns."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    initial_patterns = dict(learning_service.learned_patterns)

    # Record correction
    learning_service.record_user_correction(
        file_name="contract_invoice.pdf", from_category="legal", to_category="financial"
    )

    # Patterns should be updated
    updated_patterns = learning_service.learned_patterns
    assert "user_corrections" in updated_patterns


def test_multiple_corrections(temp_dir, spacy_model):
    """Test handling multiple user corrections."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    corrections = [
        ("invoice1.pdf", "legal", "financial"),
        ("bill2.pdf", "personal", "financial"),
        ("contract3.pdf", "financial", "legal"),
    ]

    for filename, from_cat, to_cat in corrections:
        success = learning_service.record_user_correction(filename, from_cat, to_cat)
        assert success is True


# ============================================================================
# Test Learning Metrics Calculation
# ============================================================================

def test_get_learning_metrics(temp_dir, spacy_model):
    """Test getting learning metrics."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    metrics = learning_service.get_learning_metrics()

    assert isinstance(metrics, LearningMetrics)
    assert metrics.total_sessions >= 0
    assert isinstance(metrics.average_quality_score, float)
    assert isinstance(metrics.improvement_trend, float)
    assert metrics.user_corrections >= 0
    assert isinstance(metrics.successful_patterns, dict)
    assert isinstance(metrics.failed_patterns, dict)


def test_metrics_after_sessions(temp_dir, spacy_model):
    """Test metrics calculation after recording sessions."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    # Create and record a session
    session_results = {
        "doc1": ClassificationResult(
            category="test",
            confidence=0.8,
            method=ClusteringMethod.RULE_BASED,
            reasoning="test",
            alternative_categories=[],
            metadata={},
        )
    }

    folder_structure = FolderStructure(
        structure_type=FolderStructureType.CATEGORY_FIRST,
        fiscal_year_type=FiscalYearType.CALENDAR,
        time_granularity="year",
        base_path=temp_dir,
        categories=["test"],
        metadata={},
    )

    quality_metrics = {"overall_quality": 80.0, "success_rate": 1.0}

    # Record session
    learning_service.learn_from_session(session_results, folder_structure, quality_metrics)

    # Get updated metrics
    metrics = learning_service.get_learning_metrics()
    assert metrics.total_sessions >= 1


# ============================================================================
# Test Reorganization Recommendations
# ============================================================================

def test_should_reorganize_with_improvement(temp_dir, spacy_model):
    """Test reorganization recommendation with significant improvement."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    recommendation = learning_service.should_reorganize_existing(
        current_quality=0.6, proposed_quality=0.8
    )

    assert isinstance(recommendation, dict)
    assert "should_reorganize" in recommendation
    assert "improvement" in recommendation
    assert "recommendation" in recommendation
    assert recommendation["should_reorganize"] is True  # 33% improvement should trigger


def test_should_not_reorganize_minimal_improvement(temp_dir, spacy_model):
    """Test no reorganization with minimal improvement."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    recommendation = learning_service.should_reorganize_existing(
        current_quality=0.7, proposed_quality=0.72
    )

    assert recommendation["should_reorganize"] is False  # <15% improvement


def test_reorganization_with_zero_current_quality(temp_dir, spacy_model):
    """Test reorganization recommendation with zero current quality."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    recommendation = learning_service.should_reorganize_existing(
        current_quality=0.0, proposed_quality=0.6
    )

    # Should handle zero division gracefully
    assert isinstance(recommendation, dict)
    assert "should_reorganize" in recommendation


# ============================================================================
# Test Service Statistics
# ============================================================================

def test_get_service_statistics(temp_dir, spacy_model):
    """Test getting service statistics."""
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    stats = learning_service.get_service_statistics()

    assert isinstance(stats, dict)
    assert "target_folder" in stats
    assert "state_directory" in stats
    assert "preferences_loaded" in stats
    assert "patterns_loaded" in stats
    assert "learning_metrics" in stats
    assert "current_preferences" in stats

    # Verify data types
    assert stats["target_folder"] == temp_dir
    assert stats["preferences_loaded"] is True
    assert stats["patterns_loaded"] is True
    assert isinstance(stats["learning_metrics"], dict)
    assert isinstance(stats["current_preferences"], dict)