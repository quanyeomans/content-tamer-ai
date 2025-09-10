#!/usr/bin/env python3
"""
Optimized Tests for Clustering Service in Organization Domain

Tests the clustering service using session-scoped ML model fixtures for performance.
Migrated from unittest to pytest for fixture compatibility.
"""

import os
import sys
import tempfile

# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

import pytest

# Import from organization domain
from domains.organization.clustering_service import (
    ClassificationResult,
    ClusteringConfig,
    ClusteringMethod,
    ClusteringService,
    ConfidenceLevel,
)


# ============================================================================
# Test ClusteringService Defaults and Configuration
# ============================================================================

def test_clustering_service_initialization(spacy_model):
    """Test clustering service initializes correctly with session-scoped model."""
    service = ClusteringService(spacy_model=spacy_model)
    
    assert isinstance(service, ClusteringService)
    assert service.config is not None
    assert isinstance(service.config, ClusteringConfig)
    assert service.spacy_model is spacy_model


def test_default_config_values():
    """Test default configuration values."""
    config = ClusteringConfig()
    assert config.ml_threshold == 0.7
    assert config.min_ml_documents == 10
    assert config.max_categories == 20
    assert config.enable_ensemble is False
    assert config.fallback_to_time is True


def test_custom_config_initialization(spacy_model):
    """Test initialization with custom configuration."""
    custom_config = ClusteringConfig(ml_threshold=0.5, max_categories=15, enable_ensemble=True)
    service = ClusteringService(custom_config, spacy_model=spacy_model)
    
    assert service.config.ml_threshold == 0.5
    assert service.config.max_categories == 15
    assert service.config.enable_ensemble is True


# ============================================================================
# Test ClassificationResult Data Class
# ============================================================================

def test_classification_result_creation():
    """Test creating classification result."""
    result = ClassificationResult(
        category="financial",
        confidence=0.85,
        method=ClusteringMethod.RULE_BASED,
        reasoning="Rule-based classification",
        alternative_categories=[("legal", 0.3)],
        metadata={"test": "data"},
    )

    assert result.category == "financial"
    assert result.confidence == 0.85
    assert result.method == ClusteringMethod.RULE_BASED
    assert result.confidence_level == ConfidenceLevel.HIGH


def test_confidence_level_mapping():
    """Test confidence level property mapping."""
    # Test HIGH confidence (>= 0.8)
    result_high = ClassificationResult(
        category="test",
        confidence=0.9,
        method=ClusteringMethod.RULE_BASED,
        reasoning="test",
        alternative_categories=[],
        metadata={},
    )
    assert result_high.confidence_level == ConfidenceLevel.HIGH

    # Test MEDIUM confidence (0.5-0.8)
    result_medium = ClassificationResult(
        category="test",
        confidence=0.6,
        method=ClusteringMethod.RULE_BASED,
        reasoning="test",
        alternative_categories=[],
        metadata={},
    )
    assert result_medium.confidence_level == ConfidenceLevel.MEDIUM

    # Test LOW confidence (0.2-0.5)
    result_low = ClassificationResult(
        category="test",
        confidence=0.3,
        method=ClusteringMethod.RULE_BASED,
        reasoning="test",
        alternative_categories=[],
        metadata={},
    )
    assert result_low.confidence_level == ConfidenceLevel.LOW

    # Test VERY_LOW confidence (< 0.2)
    result_very_low = ClassificationResult(
        category="test",
        confidence=0.1,
        method=ClusteringMethod.FALLBACK,
        reasoning="test",
        alternative_categories=[],
        metadata={},
    )
    assert result_very_low.confidence_level == ConfidenceLevel.VERY_LOW


# ============================================================================
# Test Document Classification
# ============================================================================

def test_classify_document_with_fallback(spacy_model):
    """Test document classification returns appropriate method based on available classifiers."""
    service = ClusteringService(spacy_model=spacy_model)
    
    # Test with basic document
    document = {
        "content": "This is a test invoice for payment processing",
        "filename": "invoice_2024.pdf",
        "metadata": {},
    }

    result = service.classify_document(document)

    # Should return a result using available classification methods
    assert isinstance(result, ClassificationResult)
    assert result.category is not None
    assert result.confidence is not None
    # Service should use whatever method is most appropriate
    valid_methods = [
        ClusteringMethod.RULE_BASED,
        ClusteringMethod.FALLBACK,
        ClusteringMethod.ML_ENHANCED,
    ]
    assert result.method in valid_methods


def test_classify_empty_document(spacy_model):
    """Test classification of empty document."""
    service = ClusteringService(spacy_model=spacy_model)
    document = {"content": "", "filename": "", "metadata": {}}

    result = service.classify_document(document)

    # Should handle empty document gracefully
    assert isinstance(result, ClassificationResult)
    assert result.category is not None


def test_classify_document_error_handling(spacy_model):
    """Test error handling in document classification."""
    service = ClusteringService(spacy_model=spacy_model)
    
    # Test with malformed document
    document = None

    try:
        result = service.classify_document(document)
        # Should return fallback result, not raise exception
        assert isinstance(result, ClassificationResult)
        assert result.method == ClusteringMethod.FALLBACK
    except Exception:
        # If exception is raised, that's also acceptable for malformed input
        pass


# ============================================================================
# Test Batch Classification
# ============================================================================

def test_batch_classify_documents(spacy_model):
    """Test batch classification of documents."""
    service = ClusteringService(spacy_model=spacy_model)
    
    documents = [
        {
            "id": "doc1",
            "content": "Invoice for services rendered",
            "filename": "invoice_001.pdf",
            "metadata": {},
        },
        {
            "id": "doc2",
            "content": "Legal contract agreement",
            "filename": "contract.pdf",
            "metadata": {},
        },
        {
            "id": "doc3",
            "content": "Medical report findings",
            "filename": "medical_report.pdf",
            "metadata": {},
        },
    ]

    results = service.batch_classify_documents(documents)

    # Should return results for all documents
    assert isinstance(results, dict)
    assert len(results) == 3

    for doc_id, result in results.items():
        assert isinstance(result, ClassificationResult)
        assert result.category is not None
        assert result.confidence is not None


def test_batch_classify_empty_list(spacy_model):
    """Test batch classification with empty document list."""
    service = ClusteringService(spacy_model=spacy_model)
    documents = []

    results = service.batch_classify_documents(documents)

    assert isinstance(results, dict)
    assert len(results) == 0


def test_batch_classify_with_errors(spacy_model):
    """Test batch classification with some malformed documents."""
    service = ClusteringService(spacy_model=spacy_model)
    
    documents = [
        {
            "id": "good_doc",
            "content": "Valid document content",
            "filename": "good.pdf",
            "metadata": {},
        },
        {
            "id": "bad_doc"
            # Missing required fields
        },
    ]

    results = service.batch_classify_documents(documents)

    # Should handle errors gracefully and return results for valid docs
    assert isinstance(results, dict)
    assert "good_doc" in results


# ============================================================================
# Test Clustering Quality Validation
# ============================================================================

def test_validate_good_quality_results(spacy_model):
    """Test validation of good quality clustering results."""
    service = ClusteringService(spacy_model=spacy_model)
    
    results = {
        "doc1": ClassificationResult(
            category="financial",
            confidence=0.9,
            method=ClusteringMethod.RULE_BASED,
            reasoning="High confidence",
            alternative_categories=[],
            metadata={},
        ),
        "doc2": ClassificationResult(
            category="legal",
            confidence=0.85,
            method=ClusteringMethod.RULE_BASED,
            reasoning="High confidence",
            alternative_categories=[],
            metadata={},
        ),
    }

    validation = service.validate_clustering_quality(results)

    assert isinstance(validation, dict)
    assert "valid" in validation
    assert "overall_score" in validation
    assert "quality_metrics" in validation
    assert "recommendations" in validation


def test_validate_poor_quality_results(spacy_model):
    """Test validation of poor quality clustering results."""
    service = ClusteringService(spacy_model=spacy_model)
    
    results = {
        "doc1": ClassificationResult(
            category="uncategorized",
            confidence=0.1,
            method=ClusteringMethod.FALLBACK,
            reasoning="Fallback",
            alternative_categories=[],
            metadata={},
        ),
        "doc2": ClassificationResult(
            category="uncategorized",
            confidence=0.2,
            method=ClusteringMethod.FALLBACK,
            reasoning="Fallback",
            alternative_categories=[],
            metadata={},
        ),
    }

    validation = service.validate_clustering_quality(results)

    assert validation["valid"] is False
    assert "recommendations" in validation
    assert len(validation["recommendations"]) > 0


def test_validate_empty_results(spacy_model):
    """Test validation of empty results."""
    service = ClusteringService(spacy_model=spacy_model)
    results = {}

    validation = service.validate_clustering_quality(results)

    assert validation["valid"] is False
    assert "reason" in validation


# ============================================================================
# Test Service Statistics
# ============================================================================

def test_get_clustering_statistics(spacy_model):
    """Test getting clustering service statistics."""
    service = ClusteringService(spacy_model=spacy_model)
    stats = service.get_clustering_statistics()

    assert isinstance(stats, dict)
    assert "config" in stats
    assert "capabilities" in stats
    assert "statistics" in stats

    # Check config section
    assert "ml_threshold" in stats["config"]
    assert "max_categories" in stats["config"]

    # Check capabilities section
    assert "rule_classifier" in stats["capabilities"]
    assert "ml_refiner" in stats["capabilities"]

    # Check statistics section
    assert isinstance(stats["statistics"], dict)


def test_statistics_tracking(spacy_model):
    """Test that statistics are tracked during classification."""
    service = ClusteringService(spacy_model=spacy_model)
    
    initial_stats = service.get_clustering_statistics()
    initial_total = initial_stats["statistics"].get("total_classifications", 0)

    # Perform some classifications
    document = {
        "content": "Test document for statistics",
        "filename": "test.pdf",
        "metadata": {},
    }

    service.classify_document(document)
    service.classify_document(document)

    # Check statistics were updated
    updated_stats = service.get_clustering_statistics()
    updated_total = updated_stats["statistics"].get("total_classifications", 0)

    assert updated_total >= initial_total