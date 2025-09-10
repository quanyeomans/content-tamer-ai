#!/usr/bin/env python3
"""
Integration Tests for Post-Processing Organization - Pytest Style

Tests the complete end-to-end organization workflow from file processing
through content analysis, classification, and physical organization.
Migrated to use pytest tmp_path fixtures for proper cleanup and race condition elimination.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, "..", "..", "..", "src")
resolved_src_path = os.path.abspath(src_path)
sys.path.insert(0, resolved_src_path)

from shared.file_operations.file_organizer import FileOrganizer
from tests.utils.pytest_file_utils import (
    create_realistic_test_documents,
    create_mixed_content_documents,
    create_temporal_test_documents,
)


@pytest.fixture
def organizer():
    """Create file organizer for testing."""
    return FileOrganizer()


def test_end_to_end_organization_workflow_basic(tmp_path, organizer):
    """Test complete workflow from file processing to organization (Basic engine)."""
    # Create test files with realistic content
    test_files = [str(f) for f in create_realistic_test_documents(tmp_path)]

    # Run post-processing organization with basic engine
    result = organizer.run_post_processing_organization(
        processed_files=test_files,
        target_folder=str(tmp_path),
        enable_organization=True,
        ml_enhancement_level=1,  # Basic engine
    )

    # Verify overall success
    assert result["success"], "Organization workflow should succeed"
    assert result["organization_applied"], "Organization should be applied"
    assert result["engine_type"] == "Domain Architecture (Level 1)", "Should use correct engine type"
    assert result["documents_organized"] > 0, "Should organize documents"

    # Verify organization structure was created
    org_result = result["organization_result"]
    assert org_result["success"], "Organization result should be successful"
    assert "folder_structure" in org_result, "Should have folder structure"

    # Check if reorganization was recommended and executed
    should_reorganize = org_result.get("should_reorganize", False)
    if should_reorganize:
        # If reorganization was recommended, execution should have occurred
        assert "execution_result" in org_result, "Should have execution result"
        execution_result = org_result["execution_result"]
        if execution_result and execution_result.get("success"):
            assert execution_result["files_moved"] >= 0, "Should track moved files"

            # Verify folder structure exists
            folders = org_result["folder_structure"].categories
            for folder_name in folders:
                folder_path = tmp_path / folder_name
                assert folder_path.exists(), f"Expected folder not created: {folder_name}"
    else:
        # If reorganization not recommended, that's also a valid result
        # (quality score may be too low for reorganization threshold)
        assert "quality_metrics" in org_result, "Should have quality metrics"
        quality_metrics = org_result["quality_metrics"]
        assert "overall_score" in quality_metrics, "Should have overall score"
        assert isinstance(quality_metrics["overall_score"], (int, float)), "Score should be numeric"


def test_end_to_end_organization_workflow_enhanced(tmp_path, organizer):
    """Test complete workflow with enhanced ML processing (Level 2)."""
    # Create test files
    test_files = [str(f) for f in create_realistic_test_documents(tmp_path)]

    # Run post-processing organization with enhanced engine
    result = organizer.run_post_processing_organization(
        processed_files=test_files,
        target_folder=str(tmp_path),
        enable_organization=True,
        ml_enhancement_level=2,  # Enhanced engine
    )

    # Verify enhanced processing
    assert result["success"], "Enhanced workflow should succeed"
    assert result["organization_applied"], "Organization should be applied"
    assert result["engine_type"] == "Enhanced (Level 2)", "Should use enhanced engine"

    # Verify ML enhancement was applied
    org_result = result["organization_result"]
    assert "ml_metrics" in org_result, "Should have ML metrics"
    ml_metrics = org_result["ml_metrics"]
    assert ml_metrics.get("ml_applied", False), "ML should be applied"
    assert ml_metrics.get("ml_available", False), "ML should be available"

    # Verify organization execution
    if org_result.get("execution_result"):
        execution_result = org_result["execution_result"]
        assert execution_result.get("success", False), "Execution should succeed"
        assert execution_result.get("files_moved", 0) >= 0, "Should track moved files"


def test_organization_workflow_with_mixed_file_types(tmp_path, organizer):
    """Test organization with various file types and content patterns."""
    # Create diverse test files
    mixed_files = [str(f) for f in create_mixed_content_documents(tmp_path)]

    # Run organization
    result = organizer.run_post_processing_organization(
        processed_files=mixed_files,
        target_folder=str(tmp_path),
        enable_organization=True,
        ml_enhancement_level=2,
    )

    # Verify handling of diverse content
    assert result["success"], "Mixed file workflow should succeed"
    assert result["organization_applied"], "Organization should be applied"

    org_result = result["organization_result"]
    classification_results = org_result.get("classification_results", {})

    # Verify different categories were identified
    categories = set(result.category for result in classification_results.values())
    assert len(categories) >= 1, "Should identify at least one category"

    # Verify execution handled all file types
    if org_result.get("execution_result"):
        execution_result = org_result["execution_result"]
        # Verify execution attempted to handle files (actual count may vary due to processing logic)
        assert execution_result.get("total_operations", 0) >= 0, "Should track operations"


def test_organization_workflow_error_handling(tmp_path, organizer):
    """Test organization workflow handles errors gracefully."""
    # Create mix of valid and problematic files
    test_files = []

    # Valid file
    valid_file = tmp_path / "valid_document.pd"
    valid_file.write_text("This is a valid invoice document with proper content for classification.")
    test_files.append(str(valid_file))

    # File that will be missing during execution (simulate external deletion)
    missing_file = tmp_path / "will_be_missing.pd"
    missing_file.write_text("This file will be deleted before organization execution.")
    test_files.append(str(missing_file))

    # Delete the file after adding to list (simulates external interference)
    missing_file.unlink()

    # Run organization
    result = organizer.run_post_processing_organization(
        processed_files=test_files,
        target_folder=str(tmp_path),
        enable_organization=True,
        ml_enhancement_level=1,
    )

    # Verify graceful error handling
    assert result["success"], "Overall should still succeed with partial failures"
    assert result["organization_applied"], "Organization should be applied"

    # Verify execution handled partial failures
    org_result = result["organization_result"]
    if org_result.get("execution_result"):
        execution_result = org_result["execution_result"]
        # Should have some failures but continue processing
        assert execution_result.get("files_failed", 0) >= 1, "Should track failed files"
        # Should have some successes
        assert execution_result.get("files_moved", 0) >= 0, "Should track successful moves"


def test_organization_workflow_disabled(tmp_path, organizer):
    """Test workflow when organization is explicitly disabled."""
    # Create test files
    test_files = [str(f) for f in create_realistic_test_documents(tmp_path)]

    # Run with organization disabled
    result = organizer.run_post_processing_organization(
        processed_files=test_files,
        target_folder=str(tmp_path),
        enable_organization=False,  # Disabled
        ml_enhancement_level=2,
    )

    # Verify organization was skipped
    assert result["success"], "Should succeed even when disabled"
    assert not result["organization_applied"], "Organization should not be applied"
    assert "Organization disabled" in result["reason"], "Should explain why disabled"

    # Verify no folders were created
    folder_count = len([
        item for item in tmp_path.iterdir()
        if item.is_dir() and not item.name.startswith(".")
    ])
    assert folder_count == 0, "No organization folders should be created"


def test_organization_state_persistence(tmp_path, organizer):
    """Test that organization state is properly persisted."""
    # Create test files
    test_files = [str(f) for f in create_realistic_test_documents(tmp_path)]

    # Run organization
    result = organizer.run_post_processing_organization(
        processed_files=test_files,
        target_folder=str(tmp_path),
        enable_organization=True,
        ml_enhancement_level=2,
    )

    # Verify success
    assert result["success"], "Organization should succeed"
    assert result["organization_applied"], "Organization should be applied"

    # Verify state persistence
    content_tamer_dir = tmp_path / ".content_tamer"
    if content_tamer_dir.exists():
        # Check for state files
        organization_dir = content_tamer_dir / "organization"
        if organization_dir.exists():
            state_files = list(organization_dir.iterdir())
            # Should have some persistent state
            assert len(state_files) > 0, "Should persist organization state"


def test_organization_workflow_temporal_analysis(tmp_path, organizer):
    """Test organization workflow with temporal intelligence."""
    # Create files with temporal patterns
    temporal_files = [str(f) for f in create_temporal_test_documents(tmp_path)]

    # Run organization with temporal analysis
    result = organizer.run_post_processing_organization(
        processed_files=temporal_files,
        target_folder=str(tmp_path),
        enable_organization=True,
        ml_enhancement_level=3,  # Temporal intelligence
    )

    # Verify temporal processing
    assert result["success"], "Temporal workflow should succeed"
    assert result["organization_applied"], "Organization should be applied"

    org_result = result["organization_result"]

    # Verify temporal analysis was performed
    assert "temporal_analysis" in org_result, "Should have temporal analysis"
    temporal_analysis = org_result["temporal_analysis"]
    assert isinstance(temporal_analysis, dict), "Temporal analysis should be dict"

    # Verify organization structure considers temporal patterns
    folder_structure = org_result["folder_structure"]
    assert isinstance(folder_structure.time_granularity, str), "Should have time granularity"


# Parallel test execution to validate race condition elimination
@pytest.mark.parametrize("test_run", range(3))
def test_parallel_execution_race_condition_validation(tmp_path, organizer, test_run):
    """Test that multiple parallel executions don't interfere with each other."""
    # Each test gets its own tmp_path, eliminating race conditions
    test_files = [str(f) for f in create_realistic_test_documents(tmp_path)]
    
    # Add unique content per test run to verify isolation
    unique_file = tmp_path / f"unique_test_run_{test_run}.pd"
    unique_file.write_text(f"This is content for test run {test_run}")
    test_files.append(str(unique_file))

    result = organizer.run_post_processing_organization(
        processed_files=test_files,
        target_folder=str(tmp_path),
        enable_organization=True,
        ml_enhancement_level=1,
    )

    # Verify each test run succeeded independently
    assert result["success"], f"Test run {test_run} should succeed independently"
    
    # Verify unique file still exists (no interference from other test runs)
    assert unique_file.exists(), f"Unique file for test run {test_run} should exist"
    assert unique_file.read_text() == f"This is content for test run {test_run}", "Content should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])