#!/usr/bin/env python3
"""
Tests for Organization Service in Organization Domain

Tests the main orchestrating service for document organization domain
that implements the progressive enhancement architecture from PRD_04.
"""

import unittest
import os
import sys
import tempfile
# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

# Import from organization domain
from domains.organization.organization_service import OrganizationService
from domains.organization.clustering_service import ClusteringConfig, ClassificationResult, ClusteringMethod
from domains.organization.folder_service import FolderStructure, FolderStructureType, FiscalYearType
from datetime import datetime

class TestOrganizationServiceDefaults(unittest.TestCase):
    """Test Organization Service default behavior and initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = OrganizationService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_organization_service_initialization(self):
        """Test organization service initializes correctly."""
        self.assertIsInstance(self.service, OrganizationService)
        self.assertEqual(self.service.target_folder, self.temp_dir)
        self.assertIsNotNone(self.service.clustering_service)
        self.assertIsNotNone(self.service.folder_service)
        self.assertIsNotNone(self.service.learning_service)
        self.assertIsNotNone(self.service.preferences)

    def test_initialization_with_custom_config(self):
        """Test initialization with custom clustering configuration."""
        custom_config = ClusteringConfig(
            ml_threshold=0.6,
            max_categories=15,
            enable_ensemble=True
        )

        service = OrganizationService(self.temp_dir, custom_config)

        self.assertEqual(service.clustering_service.config.ml_threshold, 0.6)
        self.assertEqual(service.clustering_service.config.max_categories, 15)
        self.assertTrue(service.clustering_service.config.enable_ensemble)

    def test_preferences_loaded_from_learning_service(self):
        """Test that preferences are loaded from learning service."""
        preferences = self.service.preferences

        self.assertIsInstance(preferences, dict)
        self.assertIn("structure_type", preferences)
        self.assertIn("learning_enabled", preferences)

class TestDocumentOrganization(unittest.TestCase):
    """Test document organization functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = OrganizationService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_organize_processed_documents_success(self):
        """Test successful document organization."""
        # Create test documents
        documents = [
            {
                "file_path": os.path.join(self.temp_dir, "invoice1.pd"),
                "content": "Invoice for services rendered amount due $1000",
                "filename": "invoice1.pd",
                "metadata": {}
            },
            {
                "file_path": os.path.join(self.temp_dir, "contract1.pd"),
                "content": "Legal contract agreement between parties",
                "filename": "contract1.pd",
                "metadata": {}
            }
        ]

        # Create the actual files for organization
        for doc in documents:
            with open(doc["file_path"], 'w') as f:
                f.write("test content")

        # Mock the services to avoid complex dependencies
        with patch.object(self.service.clustering_service, 'batch_classify_documents') as mock_classify, \
             patch.object(self.service.clustering_service, 'validate_clustering_quality') as mock_validate, \
             patch.object(self.service.folder_service, 'create_folder_structure') as mock_create, \
             patch.object(self.service.folder_service, 'validate_folder_structure') as mock_validate_folder, \
             patch.object(self.service.folder_service, 'execute_file_operations') as mock_execute:

            # Setup mocks
            mock_classify.return_value = {
                documents[0]["file_path"]: ClassificationResult(
                    category="financial", confidence=0.9, method=ClusteringMethod.RULE_BASED,
                    reasoning="Invoice detected", alternative_categories=[], metadata={}
                ),
                documents[1]["file_path"]: ClassificationResult(
                    category="legal", confidence=0.85, method=ClusteringMethod.RULE_BASED,
                    reasoning="Contract detected", alternative_categories=[], metadata={}
                )
            }

            mock_validate.return_value = {
                "valid": True,
                "overall_score": 85.0,
                "recommendations": []
            }

            mock_folder_structure = FolderStructure(
                structure_type=FolderStructureType.CATEGORY_FIRST,
                fiscal_year_type=FiscalYearType.CALENDAR,
                time_granularity="year",
                base_path=self.temp_dir,
                categories=["financial", "legal"],
                metadata={}
            )

            mock_create.return_value = (mock_folder_structure, [])
            mock_validate_folder.return_value = {"valid": True, "issues": []}
            mock_execute.return_value = {
                "total_operations": 2,
                "successful_operations": 2,
                "moved_files": 2,
                "created_directories": 2,
                "errors": []
            }

            # Test organization
            results = self.service.organize_processed_documents(documents)

            # Verify results
            self.assertIsInstance(results, dict)
            self.assertTrue(results["success"])
            self.assertEqual(results["documents_processed"], 2)
            self.assertEqual(results["files_organized"], 2)
            self.assertIn("session_id", results)
            self.assertIn("classification_results", results)

    def test_organize_with_poor_clustering_quality(self):
        """Test organization with poor clustering quality fallback."""
        documents = [
            {
                "file_path": os.path.join(self.temp_dir, "unclear1.pd"),
                "content": "Unclear document content",
                "filename": "unclear1.pd",
                "metadata": {}
            }
        ]

        # Create test file
        with open(documents[0]["file_path"], 'w') as f:
            f.write("test content")

        with patch.object(self.service.clustering_service, 'batch_classify_documents') as mock_classify, \
             patch.object(self.service.clustering_service, 'validate_clustering_quality') as mock_validate:

            # Setup poor quality classification
            mock_classify.return_value = {
                documents[0]["file_path"]: ClassificationResult(
                    category="uncategorized", confidence=0.1, method=ClusteringMethod.FALLBACK,
                    reasoning="Poor quality", alternative_categories=[], metadata={}
                )
            }

            mock_validate.return_value = {
                "valid": False,
                "overall_score": 35.0,  # Below 40 threshold
                "recommendations": ["Use manual organization"]
            }

            # Test organization - should fall back to time-based
            results = self.service.organize_processed_documents(documents)

            # Should still succeed with fallback
            self.assertIn("fallback_method", results)
            self.assertEqual(results["fallback_method"], "time_based")

    def test_organize_empty_document_list(self):
        """Test organization with empty document list."""
        documents = []

        results = self.service.organize_processed_documents(documents)

        self.assertIsInstance(results, dict)
        self.assertEqual(results["documents_processed"], 0)

    def test_organize_with_learning_disabled(self):
        """Test organization with learning disabled."""
        documents = [
            {
                "file_path": os.path.join(self.temp_dir, "test.pd"),
                "content": "Test document",
                "filename": "test.pd",
                "metadata": {}
            }
        ]

        # Create test file
        with open(documents[0]["file_path"], 'w') as f:
            f.write("test content")

        with patch.object(self.service.clustering_service, 'batch_classify_documents') as mock_classify, \
             patch.object(self.service.clustering_service, 'validate_clustering_quality') as mock_validate, \
             patch.object(self.service.folder_service, 'create_folder_structure') as mock_create, \
             patch.object(self.service.folder_service, 'validate_folder_structure') as mock_validate_folder, \
             patch.object(self.service.folder_service, 'execute_file_operations') as mock_execute:

            # Setup basic mocks
            mock_classify.return_value = {
                documents[0]["file_path"]: ClassificationResult(
                    category="test", confidence=0.8, method=ClusteringMethod.RULE_BASED,
                    reasoning="Test", alternative_categories=[], metadata={}
                )
            }
            mock_validate.return_value = {"valid": True, "overall_score": 80.0}
            mock_create.return_value = (Mock(), [])
            mock_validate_folder.return_value = {"valid": True}
            mock_execute.return_value = {"total_operations": 1, "successful_operations": 1, "moved_files": 1}

            # Test with learning disabled
            results = self.service.organize_processed_documents(documents, enable_learning=False)

            # Should succeed without learning results
            self.assertIsInstance(results, dict)
            self.assertEqual(results.get("learning_results", {}), {})

class TestOrganizationPreview(unittest.TestCase):
    """Test organization preview functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = OrganizationService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_preview_organization(self):
        """Test preview organization without file movement."""
        documents = [
            {
                "content": "Invoice document",
                "filename": "invoice.pd",
                "metadata": {}
            },
            {
                "content": "Contract document",
                "filename": "contract.pd",
                "metadata": {}
            }
        ]

        with patch.object(self.service.clustering_service, 'batch_classify_documents') as mock_classify, \
             patch.object(self.service.clustering_service, 'validate_clustering_quality') as mock_validate, \
             patch.object(self.service.folder_service, 'create_folder_structure') as mock_create:

            # Setup mocks
            mock_classify.return_value = {
                "doc1": ClassificationResult(
                    category="financial", confidence=0.9, method=ClusteringMethod.RULE_BASED,
                    reasoning="Invoice", alternative_categories=[], metadata={}
                ),
                "doc2": ClassificationResult(
                    category="legal", confidence=0.85, method=ClusteringMethod.RULE_BASED,
                    reasoning="Contract", alternative_categories=[], metadata={}
                )
            }

            mock_validate.return_value = {
                "valid": True,
                "overall_score": 87.0,
                "recommendations": ["Good quality clustering"]
            }

            # Create mock file operations
            mock_file_ops = [
                Mock(operation_type="move", category="financial", source_path="/test/invoice.pd"),
                Mock(operation_type="move", category="legal", source_path="/test/contract.pd")
            ]

            mock_folder_structure = FolderStructure(
                structure_type=FolderStructureType.CATEGORY_FIRST,
                fiscal_year_type=FiscalYearType.CALENDAR,
                time_granularity="year",
                base_path=self.temp_dir,
                categories=["financial", "legal"],
                metadata={}
            )

            mock_create.return_value = (mock_folder_structure, mock_file_ops)

            # Test preview
            preview = self.service.preview_organization(documents)

            # Verify preview results
            self.assertIsInstance(preview, dict)
            self.assertTrue(preview["preview"])
            self.assertIn("folder_structure", preview)
            self.assertIn("operations_by_category", preview)
            self.assertIn("quality_metrics", preview)
            self.assertEqual(preview["total_operations"], 2)

    def test_preview_organization_error(self):
        """Test preview organization with error handling."""
        documents = [{"malformed": "document"}]

        # Test with error condition
        preview = self.service.preview_organization(documents)

        self.assertTrue(preview["preview"])
        self.assertIn("error", preview)
        self.assertFalse(preview["success"])

class TestOrganizationStatus(unittest.TestCase):
    """Test organization status functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = OrganizationService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_organization_status(self):
        """Test getting organization status."""
        with patch.object(self.service.folder_service, 'get_folder_statistics') as mock_folder_stats, \
             patch.object(self.service.clustering_service, 'get_clustering_statistics') as mock_clustering_stats, \
             patch.object(self.service.learning_service, 'get_learning_metrics') as mock_learning_metrics:

            # Setup mocks
            mock_folder_stats.return_value = {
                "exists": True,
                "total_files": 10,
                "total_directories": 3
            }

            mock_clustering_stats.return_value = {
                "capabilities": {"rule_classifier": True, "ml_refiner": False},
                "config": {"ml_threshold": 0.7}
            }

            mock_learning_metrics.return_value = Mock(
                total_sessions=5,
                average_quality_score=0.78,
                improvement_trend=0.05,
                user_corrections=2
            )

            # Test status
            status = self.service.get_organization_status()

            # Verify status
            self.assertIsInstance(status, dict)
            self.assertEqual(status["target_folder"], self.temp_dir)
            self.assertIn("folder_statistics", status)
            self.assertIn("clustering_capabilities", status)
            self.assertIn("learning_status", status)
            self.assertIn("current_preferences", status)
            self.assertIn("ready_for_organization", status)

    def test_get_organization_status_error(self):
        """Test status retrieval with error."""
        with patch.object(self.service.folder_service, 'get_folder_statistics') as mock_stats:
            # Simulate error
            mock_stats.side_effect = Exception("Test error")

            status = self.service.get_organization_status()

            self.assertIn("error", status)
            self.assertFalse(status["ready_for_organization"])

class TestPreferencesManagement(unittest.TestCase):
    """Test organization preferences management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = OrganizationService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_configure_valid_preferences(self):
        """Test configuring valid organization preferences."""
        valid_preferences = {
            "structure_type": "time_first",
            "ml_threshold": 0.8,
            "max_categories": 15,
            "quality_threshold": 0.6
        }

        success = self.service.configure_organization_preferences(valid_preferences)

        self.assertTrue(success)

        # Verify preferences were updated
        self.assertEqual(self.service.preferences["structure_type"], "time_first")
        self.assertEqual(self.service.preferences["ml_threshold"], 0.8)
        self.assertEqual(self.service.preferences["max_categories"], 15)

    def test_configure_invalid_preferences(self):
        """Test configuring invalid preferences."""
        invalid_preferences = {
            "ml_threshold": 1.5,  # Invalid: > 1.0
            "max_categories": -5,  # Invalid: < 1
            "structure_type": "invalid_type"  # Invalid type
        }

        success = self.service.configure_organization_preferences(invalid_preferences)

        self.assertFalse(success)

    def test_preference_validation(self):
        """Test preference validation logic."""
        # Test ML threshold validation
        result = self.service._validate_preferences({"ml_threshold": 1.5})
        self.assertFalse(result["valid"])
        self.assertIn("ML threshold must be between 0.0 and 1.0", result["errors"])

        # Test max categories validation
        result = self.service._validate_preferences({"max_categories": 100})
        self.assertFalse(result["valid"])
        self.assertIn("Max categories must be integer between 1 and 50", result["errors"])

        # Test structure type validation
        result = self.service._validate_preferences({"structure_type": "invalid"})
        self.assertFalse(result["valid"])
        self.assertIn("Structure type must be one of:", result["errors"][0])

        # Test valid preferences
        result = self.service._validate_preferences({
            "ml_threshold": 0.7,
            "max_categories": 20,
            "structure_type": "category_first"
        })
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

class TestMethodDistribution(unittest.TestCase):
    """Test method distribution calculation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = OrganizationService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_method_distribution(self):
        """Test calculation of classification method distribution."""
        classifications = {
            "doc1": ClassificationResult(
                category="test1", confidence=0.9, method=ClusteringMethod.RULE_BASED,
                reasoning="Rule", alternative_categories=[], metadata={}
            ),
            "doc2": ClassificationResult(
                category="test2", confidence=0.8, method=ClusteringMethod.RULE_BASED,
                reasoning="Rule", alternative_categories=[], metadata={}
            ),
            "doc3": ClassificationResult(
                category="test3", confidence=0.7, method=ClusteringMethod.ML_ENHANCED,
                reasoning="ML", alternative_categories=[], metadata={}
            ),
            "doc4": ClassificationResult(
                category="test4", confidence=0.2, method=ClusteringMethod.FALLBACK,
                reasoning="Fallback", alternative_categories=[], metadata={}
            )
        }

        distribution = self.service._get_method_distribution(classifications)

        self.assertIsInstance(distribution, dict)
        self.assertEqual(distribution["rule_based"], 2)
        self.assertEqual(distribution["ml_enhanced"], 1)
        self.assertEqual(distribution["fallback"], 1)

    def test_empty_classification_distribution(self):
        """Test method distribution with empty classifications."""
        classifications = {}

        distribution = self.service._get_method_distribution(classifications)

        self.assertIsInstance(distribution, dict)
        self.assertEqual(len(distribution), 0)

if __name__ == "__main__":
    unittest.main()
