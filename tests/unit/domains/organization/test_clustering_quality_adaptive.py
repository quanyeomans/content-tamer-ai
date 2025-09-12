"""
Unit tests for adaptive clustering quality thresholds.

Tests that clustering quality thresholds adapt appropriately to dataset size,
making organization more practical for small document sets.
"""

import unittest
from unittest.mock import MagicMock

from src.domains.organization.clustering_service import ClusteringService, ClassificationResult, ClusteringMethod


class TestAdaptiveClusteringQuality(unittest.TestCase):
    """Test adaptive clustering quality thresholds."""

    def setUp(self):
        """Set up test fixtures."""
        self.clustering_service = ClusteringService()

    def test_small_dataset_uses_lower_threshold(self):
        """Test that datasets with ≤5 documents use 40% threshold."""
        # Create 5 mock classification results with mixed confidence
        results = {}
        for i in range(5):
            result = MagicMock(spec=ClassificationResult)
            result.confidence = 0.6 if i < 2 else 0.9  # 2 low, 3 high confidence
            result.category = f"category_{i % 2}"  # 2 categories
            result.method = ClusteringMethod.ML_ENHANCED
            results[f"doc_{i}"] = result

        quality_result = self.clustering_service.validate_clustering_quality(results)
        
        self.assertEqual(quality_result["threshold_used"], 40)
        self.assertIn("threshold_used", quality_result)

    def test_medium_small_dataset_uses_moderate_threshold(self):
        """Test that datasets with 6-10 documents use 50% threshold."""
        # Create 9 mock classification results
        results = {}
        for i in range(9):
            result = MagicMock(spec=ClassificationResult)
            result.confidence = 0.7 if i < 4 else 0.9  # Mixed confidence
            result.category = f"category_{i % 3}"  # 3 categories
            result.method = ClusteringMethod.ML_ENHANCED
            results[f"doc_{i}"] = result

        quality_result = self.clustering_service.validate_clustering_quality(results)
        
        self.assertEqual(quality_result["threshold_used"], 50)

    def test_medium_dataset_uses_standard_threshold(self):
        """Test that datasets with 11-20 documents use 55% threshold."""
        # Create 15 mock classification results
        results = {}
        for i in range(15):
            result = MagicMock(spec=ClassificationResult)
            result.confidence = 0.8
            result.category = f"category_{i % 4}"  # 4 categories
            result.method = ClusteringMethod.ML_ENHANCED
            results[f"doc_{i}"] = result

        quality_result = self.clustering_service.validate_clustering_quality(results)
        
        self.assertEqual(quality_result["threshold_used"], 55)

    def test_large_dataset_uses_high_threshold(self):
        """Test that datasets with >20 documents use 60% threshold."""
        # Create 25 mock classification results
        results = {}
        for i in range(25):
            result = MagicMock(spec=ClassificationResult)
            result.confidence = 0.8
            result.category = f"category_{i % 5}"  # 5 categories
            result.method = ClusteringMethod.ML_ENHANCED
            results[f"doc_{i}"] = result

        quality_result = self.clustering_service.validate_clustering_quality(results)
        
        self.assertEqual(quality_result["threshold_used"], 60)

    def test_adaptive_min_category_size_for_small_datasets(self):
        """Test that small datasets allow single-document categories."""
        # Create 8 documents with 8 different categories (all single-doc categories)
        results = {}
        for i in range(8):
            result = MagicMock(spec=ClassificationResult)
            result.confidence = 0.9  # High confidence
            result.category = f"unique_category_{i}"  # Each doc gets its own category
            result.method = ClusteringMethod.RULE_BASED
            results[f"doc_{i}"] = result

        quality_result = self.clustering_service.validate_clustering_quality(results)
        
        # With adaptive min_category_size=1 for small datasets,
        # there should be no "small categories" penalty
        self.assertEqual(quality_result["category_metrics"]["small_categories"], 0)
        
        # Balance score should be 100% since no categories are below the adaptive threshold
        self.assertEqual(float(quality_result["category_metrics"]["balance_score"].rstrip('%')), 100.0)

    def test_quality_validation_passes_with_lower_threshold(self):
        """Test that previously failing datasets now pass with adaptive thresholds."""
        # Create a scenario that would fail with 60% threshold but pass with 50%
        # 9 documents with moderate quality
        results = {}
        for i in range(9):
            result = MagicMock(spec=ClassificationResult)
            # Mix of high and medium confidence to get ~55% overall score
            result.confidence = 0.9 if i < 5 else 0.4  # 5 high, 4 medium
            result.category = f"category_{i % 3}"  # 3 categories (3 docs each)
            result.method = ClusteringMethod.ML_ENHANCED
            results[f"doc_{i}"] = result

        quality_result = self.clustering_service.validate_clustering_quality(results)
        
        # Should use 50% threshold for 9 documents
        self.assertEqual(quality_result["threshold_used"], 50)
        
        # Should pass validation (overall score should be ≥50%)
        # With 5/9 high confidence = 55.6% quality score
        # With 3 balanced categories = 100% balance score
        # Overall = (55.6 + 100) / 2 = ~77.8% > 50% threshold
        self.assertTrue(quality_result["valid"])
        self.assertGreaterEqual(quality_result["overall_score"], 50)

    def test_empty_results_still_fail_validation(self):
        """Test that empty results still fail validation regardless of threshold."""
        results = {}
        quality_result = self.clustering_service.validate_clustering_quality(results)
        
        self.assertFalse(quality_result["valid"])
        self.assertEqual(quality_result["reason"], "No results to validate")


if __name__ == "__main__":
    unittest.main()