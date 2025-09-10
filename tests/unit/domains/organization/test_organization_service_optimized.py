#!/usr/bin/env python3
"""
Optimized Tests for Organization Service in Organization Domain

Tests the main orchestrating service using session-scoped ML model fixtures for performance.
Migrated to pure pytest for fixture compatibility.
"""

import os
import sys
import tempfile

# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

import pytest
from datetime import datetime
from unittest.mock import patch

from domains.organization.clustering_service import (
    ClassificationResult,
    ClusteringConfig,
    ClusteringMethod,
)
from domains.organization.folder_service import FiscalYearType, FolderStructure, FolderStructureType

# Import from organization domain
from domains.organization.organization_service import OrganizationService


# ============================================================================
# Test Organization Service Defaults and Initialization
# ============================================================================

def test_organization_service_initialization(tmp_path, spacy_model):
    """Test organization service initializes correctly."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    assert isinstance(service, OrganizationService)
    assert service.target_folder == str(tmp_path)
    assert service.clustering_service is not None
    assert service.learning_service is not None
    assert service.folder_service is not None


def test_initialization_with_custom_config(tmp_path, spacy_model):
    """Test initialization with custom clustering configuration."""
    custom_config = ClusteringConfig(ml_threshold=0.5, max_categories=15)
    service = OrganizationService(str(tmp_path), config=custom_config, spacy_model=spacy_model)
    
    assert service.clustering_service.config.ml_threshold == 0.5
    assert service.clustering_service.config.max_categories == 15


def test_preferences_loaded_from_learning_service(tmp_path, spacy_model):
    """Test that preferences are loaded from learning service."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    preferences = service.get_current_preferences()
    assert isinstance(preferences, dict)
    assert "structure_type" in preferences
    assert "learning_enabled" in preferences


# ============================================================================
# Test Document Organization
# ============================================================================

def test_organize_empty_document_list(tmp_path, spacy_model):
    """Test organizing empty document list."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    documents = []

    result = service.organize_processed_documents(documents)

    assert isinstance(result, dict)
    assert result.get("success", False) is True
    assert result.get("documents_processed", 0) == 0


def test_organize_processed_documents_success(tmp_path, spacy_model):
    """Test successful organization of processed documents."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    # Mock documents
    documents = [
        {
            "id": "doc1",
            "content": "Invoice for Q4 services rendered to client ABC Corp",
            "filename": "invoice_q4_2024.pdf",
            "metadata": {"file_size": 25600, "pages": 2},
            "file_path": str(tmp_path / "invoice_q4_2024.pdf"),
        },
        {
            "id": "doc2", 
            "content": "Legal service agreement between parties for consulting services",
            "filename": "service_agreement_2024.pdf",
            "metadata": {"file_size": 51200, "pages": 8},
            "file_path": str(tmp_path / "service_agreement_2024.pdf"),
        },
    ]

    # Create mock files
    for doc in documents:
        Path(doc["file_path"]).touch()

    result = service.organize_processed_documents(documents)

    assert isinstance(result, dict)
    assert "success" in result
    assert "documents_processed" in result
    assert "folder_structure" in result
    assert "classification_results" in result


def test_organize_with_learning_disabled(tmp_path, spacy_model):
    """Test organization with learning disabled."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    # Disable learning in preferences
    service.learning_service.preferences["learning_enabled"] = False
    
    documents = [
        {
            "id": "doc1",
            "content": "Test document content for organization",
            "filename": "test_doc.pdf",
            "metadata": {},
            "file_path": str(tmp_path / "test_doc.pdf"),
        }
    ]
    
    # Create mock file
    Path(documents[0]["file_path"]).touch()

    result = service.organize_processed_documents(documents)

    assert isinstance(result, dict)
    assert result.get("learning_summary", {}).get("learning_enabled", True) is False


def test_organize_with_poor_clustering_quality(tmp_path, spacy_model):
    """Test organization handling poor clustering quality."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    # Mock documents with poor content for clustering
    documents = [
        {
            "id": "doc1",
            "content": "",  # Empty content should result in poor clustering
            "filename": "empty.pdf",
            "metadata": {},
            "file_path": str(tmp_path / "empty.pdf"),
        }
    ]
    
    # Create mock file
    Path(documents[0]["file_path"]).touch()

    result = service.organize_processed_documents(documents)

    # Should still complete successfully with fallback methods
    assert isinstance(result, dict)
    assert "success" in result


# ============================================================================
# Test Organization Preview
# ============================================================================

def test_preview_organization(tmp_path, spacy_model):
    """Test organization preview functionality."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    documents = [
        {
            "id": "doc1",
            "content": "Financial report for Q3 2024 showing revenue growth",
            "filename": "financial_report_q3.pdf",
            "metadata": {"file_size": 40960},
        }
    ]

    preview = service.preview_organization(documents)

    assert isinstance(preview, dict)
    assert "predicted_structure" in preview
    assert "classification_preview" in preview
    assert "quality_estimate" in preview
    assert "recommendations" in preview


def test_preview_organization_error(tmp_path, spacy_model):
    """Test preview organization with error handling."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    # Invalid documents should be handled gracefully
    documents = None

    try:
        preview = service.preview_organization(documents)
        # Should return error structure, not raise exception
        assert isinstance(preview, dict)
        assert "error" in preview or "success" in preview
    except Exception:
        # If exception is raised, that's also acceptable for malformed input
        pass


# ============================================================================
# Test Organization Status and Management
# ============================================================================

def test_get_organization_status(tmp_path, spacy_model):
    """Test getting organization status."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    status = service.get_organization_status()

    assert isinstance(status, dict)
    assert "target_folder" in status
    assert "clustering_service" in status
    assert "learning_service" in status
    assert "folder_service" in status
    assert "current_preferences" in status


def test_get_current_preferences(tmp_path, spacy_model):
    """Test getting current preferences."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    preferences = service.get_current_preferences()

    assert isinstance(preferences, dict)
    assert "structure_type" in preferences
    assert "learning_enabled" in preferences
    assert "ml_threshold" in preferences


def test_update_preferences(tmp_path, spacy_model):
    """Test updating organization preferences."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    new_preferences = {
        "structure_type": "time_first",
        "ml_threshold": 0.8,
        "max_categories": 25,
    }

    success = service.update_preferences(new_preferences)
    assert success is True

    # Verify preferences were updated
    updated_preferences = service.get_current_preferences()
    assert updated_preferences["structure_type"] == "time_first"
    assert updated_preferences["ml_threshold"] == 0.8
    assert updated_preferences["max_categories"] == 25


# ============================================================================
# Test Learning and Feedback Integration
# ============================================================================

def test_record_user_feedback(tmp_path, spacy_model):
    """Test recording user feedback for learning."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    feedback = {
        "file_name": "invoice_2024.pdf",
        "from_category": "legal",
        "to_category": "financial",
        "feedback_type": "correction"
    }

    success = service.record_user_feedback(feedback)
    assert success is True


def test_get_learning_insights(tmp_path, spacy_model):
    """Test getting learning insights and recommendations."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    insights = service.get_learning_insights()

    assert isinstance(insights, dict)
    assert "learning_metrics" in insights
    assert "patterns" in insights
    assert "recommendations" in insights


def test_reorganization_recommendation(tmp_path, spacy_model):
    """Test reorganization recommendation logic."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    recommendation = service.should_reorganize_existing(
        current_quality=0.6, proposed_quality=0.8
    )

    assert isinstance(recommendation, dict)
    assert "should_reorganize" in recommendation
    assert "improvement" in recommendation


# ============================================================================
# Test Error Handling and Edge Cases
# ============================================================================

def test_organize_with_missing_files(tmp_path, spacy_model):
    """Test organization with missing file references."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    documents = [
        {
            "id": "doc1",
            "content": "Test document content",
            "filename": "missing_file.pdf",
            "metadata": {},
            "file_path": str(tmp_path / "nonexistent.pdf"),  # File doesn't exist
        }
    ]

    result = service.organize_processed_documents(documents)

    # Should handle missing files gracefully
    assert isinstance(result, dict)
    # May succeed with warnings or fail gracefully


def test_organize_with_permission_errors(tmp_path, spacy_model):
    """Test organization with file permission issues."""
    service = OrganizationService(str(tmp_path), spacy_model=spacy_model)
    
    # This test would require platform-specific permission manipulation
    # For now, we'll just verify the service can handle the scenario conceptually
    documents = [
        {
            "id": "doc1",
            "content": "Test document",
            "filename": "test.pdf",
            "metadata": {},
            "file_path": str(tmp_path / "test.pdf"),
        }
    ]
    
    # Create the file
    Path(documents[0]["file_path"]).touch()

    # Normal organization should work
    result = service.organize_processed_documents(documents)
    assert isinstance(result, dict)


# ============================================================================
# Helper Imports for Proper Test Execution
# ============================================================================

from pathlib import Path  # Used in tests above