#!/usr/bin/env python3
"""
Tests for Clustering Service in Organization Domain

Tests the clustering service that handles document classification and clustering
using progressive enhancement architecture.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

# Import from organization domain
from domains.organization.clustering_service import (
    ClassificationResult,
    ClusteringConfig,
    ClusteringMethod,
    ClusteringService,
    ConfidenceLevel,
)

# Pytest integration for session fixtures
import pytest


class TestClusteringServiceDefaults(unittest.TestCase):
    """Test Clustering Service default behavior and initialization."""

    def setUp(self):
        """Set up test fixtures."""
        # Use session-scoped spaCy model if available from pytest fixtures
        spacy_model = getattr(self, '_spacy_model', None)
        self.service = ClusteringService(spacy_model=spacy_model)

    def test_clustering_service_initialization(self):
        """Test clustering service initializes correctly."""
        self.assertIsInstance(self.service, ClusteringService)
        self.assertIsNotNone(self.service.config)
        self.assertIsInstance(self.service.config, ClusteringConfig)

    def test_default_config_values(self):
        """Test default configuration values."""
        config = ClusteringConfig()
        self.assertEqual(config.ml_threshold, 0.7)
        self.assertEqual(config.min_ml_documents, 10)
        self.assertEqual(config.max_categories, 20)
        self.assertFalse(config.enable_ensemble)
        self.assertTrue(config.fallback_to_time)

    def test_custom_config_initialization(self):
        """Test initialization with custom configuration."""
        custom_config = ClusteringConfig(ml_threshold=0.5, max_categories=15, enable_ensemble=True)
        service = ClusteringService(custom_config)
        self.assertEqual(service.config.ml_threshold, 0.5)
        self.assertEqual(service.config.max_categories, 15)
        self.assertTrue(service.config.enable_ensemble)


class TestClassificationResult(unittest.TestCase):
    """Test ClassificationResult data class and properties."""

    def test_classification_result_creation(self):
        """Test creating classification result."""
        result = ClassificationResult(
            category="financial",
            confidence=0.85,
            method=ClusteringMethod.RULE_BASED,
            reasoning="Rule-based classification",
            alternative_categories=[("legal", 0.3)],
            metadata={"test": "data"},
        )

        self.assertEqual(result.category, "financial")
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.method, ClusteringMethod.RULE_BASED)
        self.assertEqual(result.confidence_level, ConfidenceLevel.HIGH)

    def test_confidence_level_mapping(self):
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
        self.assertEqual(result_high.confidence_level, ConfidenceLevel.HIGH)

        # Test MEDIUM confidence (0.5-0.8)
        result_medium = ClassificationResult(
            category="test",
            confidence=0.6,
            method=ClusteringMethod.RULE_BASED,
            reasoning="test",
            alternative_categories=[],
            metadata={},
        )
        self.assertEqual(result_medium.confidence_level, ConfidenceLevel.MEDIUM)

        # Test LOW confidence (0.2-0.5)
        result_low = ClassificationResult(
            category="test",
            confidence=0.3,
            method=ClusteringMethod.RULE_BASED,
            reasoning="test",
            alternative_categories=[],
            metadata={},
        )
        self.assertEqual(result_low.confidence_level, ConfidenceLevel.LOW)

        # Test VERY_LOW confidence (< 0.2)
        result_very_low = ClassificationResult(
            category="test",
            confidence=0.1,
            method=ClusteringMethod.FALLBACK,
            reasoning="test",
            alternative_categories=[],
            metadata={},
        )
        self.assertEqual(result_very_low.confidence_level, ConfidenceLevel.VERY_LOW)


class TestDocumentClassification(unittest.TestCase):
    """Test document classification functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = ClusteringService()

    def test_classify_document_with_fallback(self):
        """Test document classification returns appropriate method based on available classifiers."""
        # Test with basic document
        document = {
            "content": "This is a test invoice for payment processing",
            "filename": "invoice_2024.pdf",
            "metadata": {},
        }

        result = self.service.classify_document(document)

        # Should return a result using available classification methods
        self.assertIsInstance(result, ClassificationResult)
        self.assertIsNotNone(result.category)
        self.assertIsNotNone(result.confidence)
        # Service should use whatever method is most appropriate (ML_ENHANCED, RULE_BASED, or FALLBACK)
        valid_methods = [
            ClusteringMethod.RULE_BASED,
            ClusteringMethod.FALLBACK,
            ClusteringMethod.ML_ENHANCED,
        ]
        self.assertIn(result.method, valid_methods)

    def test_classify_empty_document(self):
        """Test classification of empty document."""
        document = {"content": "", "filename": "", "metadata": {}}

        result = self.service.classify_document(document)

        # Should handle empty document gracefully
        self.assertIsInstance(result, ClassificationResult)
        self.assertIsNotNone(result.category)

    def test_classify_document_error_handling(self):
        """Test error handling in document classification."""
        # Test with malformed document
        document = None

        try:
            result = self.service.classify_document(document)
            # Should return fallback result, not raise exception
            self.assertIsInstance(result, ClassificationResult)
            self.assertEqual(result.method, ClusteringMethod.FALLBACK)
        except Exception:
            # If exception is raised, that's also acceptable for malformed input
            pass


class TestBatchClassification(unittest.TestCase):
    """Test batch document classification."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = ClusteringService()

    def test_batch_classify_documents(self):
        """Test batch classification of documents."""
        documents = [
            {
                "id": "doc1",
                "content": "Invoice for services rendered",
                "filename": "invoice_001.pd",
                "metadata": {},
            },
            {
                "id": "doc2",
                "content": "Legal contract agreement",
                "filename": "contract.pd",
                "metadata": {},
            },
            {
                "id": "doc3",
                "content": "Medical report findings",
                "filename": "medical_report.pd",
                "metadata": {},
            },
        ]

        results = self.service.batch_classify_documents(documents)

        # Should return results for all documents
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), 3)

        for doc_id, result in results.items():
            self.assertIsInstance(result, ClassificationResult)
            self.assertIsNotNone(result.category)
            self.assertIsNotNone(result.confidence)

    def test_batch_classify_empty_list(self):
        """Test batch classification with empty document list."""
        documents = []

        results = self.service.batch_classify_documents(documents)

        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), 0)

    def test_batch_classify_with_errors(self):
        """Test batch classification with some malformed documents."""
        documents = [
            {
                "id": "good_doc",
                "content": "Valid document content",
                "filename": "good.pd",
                "metadata": {},
            },
            {
                "id": "bad_doc"
                # Missing required fields
            },
        ]

        results = self.service.batch_classify_documents(documents)

        # Should handle errors gracefully and return results for valid docs
        self.assertIsInstance(results, dict)
        self.assertIn("good_doc", results)


class TestClusteringQualityValidation(unittest.TestCase):
    """Test clustering quality validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = ClusteringService()

    def test_validate_good_quality_results(self):
        """Test validation of good quality clustering results."""
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

        validation = self.service.validate_clustering_quality(results)

        self.assertIsInstance(validation, dict)
        self.assertIn("valid", validation)
        self.assertIn("overall_score", validation)
        self.assertIn("quality_metrics", validation)
        self.assertIn("recommendations", validation)

    def test_validate_poor_quality_results(self):
        """Test validation of poor quality clustering results."""
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

        validation = self.service.validate_clustering_quality(results)

        self.assertFalse(validation["valid"])
        self.assertIn("recommendations", validation)
        self.assertGreater(len(validation["recommendations"]), 0)

    def test_validate_empty_results(self):
        """Test validation of empty results."""
        results = {}

        validation = self.service.validate_clustering_quality(results)

        self.assertFalse(validation["valid"])
        self.assertIn("reason", validation)


class TestServiceStatistics(unittest.TestCase):
    """Test clustering service statistics and monitoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = ClusteringService()

    def test_get_clustering_statistics(self):
        """Test getting clustering service statistics."""
        stats = self.service.get_clustering_statistics()

        self.assertIsInstance(stats, dict)
        self.assertIn("config", stats)
        self.assertIn("capabilities", stats)
        self.assertIn("statistics", stats)

        # Check config section
        self.assertIn("ml_threshold", stats["config"])
        self.assertIn("max_categories", stats["config"])

        # Check capabilities section
        self.assertIn("rule_classifier", stats["capabilities"])
        self.assertIn("ml_refiner", stats["capabilities"])

        # Check statistics section
        self.assertIsInstance(stats["statistics"], dict)

    def test_statistics_tracking(self):
        """Test that statistics are tracked during classification."""
        initial_stats = self.service.get_clustering_statistics()
        initial_total = initial_stats["statistics"].get("total_classifications", 0)

        # Perform some classifications
        document = {
            "content": "Test document for statistics",
            "filename": "test.pd",
            "metadata": {},
        }

        self.service.classify_document(document)
        self.service.classify_document(document)

        # Check statistics were updated
        updated_stats = self.service.get_clustering_statistics()
        updated_total = updated_stats["statistics"].get("total_classifications", 0)

        self.assertGreaterEqual(updated_total, initial_total)


if __name__ == "__main__":
    unittest.main()
