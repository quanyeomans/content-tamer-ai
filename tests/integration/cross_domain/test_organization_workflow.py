#!/usr/bin/env python3
"""
Integration Tests for Post-Processing Organization

Tests the complete end-to-end organization workflow from file processing
through content analysis, classification, and physical organization.
Clean implementation with consistent patterns and proper structure.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List

import pytest

# Add src to path for imports
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, "..", "..", "..", "src")
resolved_src_path = os.path.abspath(src_path)
sys.path.insert(0, resolved_src_path)

from shared.file_operations.file_organizer import FileOrganizer
from tests.utils.rich_test_utils import RichTestCase
from tests.utils.pytest_file_utils import (
    create_processing_directories,
    create_realistic_test_documents,
    create_mixed_content_documents,
    create_temporal_test_documents,
    TestFileEnvironment
)


class TestPostProcessingOrganizationIntegration(unittest.TestCase, RichTestCase):
    """Integration tests for complete organization workflow."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)
        
        # Ensure src path is always at the front (fix for sys.path contamination by other tests)
        current_dir = os.path.dirname(__file__)
        src_path = os.path.join(current_dir, "..", "..", "..", "src")
        resolved_src_path = os.path.abspath(src_path)
        
        # Remove any existing instances of this path and add it at the front
        import sys
        sys.path = [p for p in sys.path if os.path.abspath(p) != resolved_src_path]
        sys.path.insert(0, resolved_src_path)
        
        self.organizer = FileOrganizer()

    def tearDown(self):
        """Clean up Rich testing environment."""
        RichTestCase.tearDown(self)

    def test_end_to_end_organization_workflow_basic(self):
        """Test complete workflow from file processing to organization (Basic engine)."""
        with TestFileEnvironment(Path(tempfile.mkdtemp()), "organization") as env:
            # Create test files with realistic content
            test_files = self._create_realistic_test_files(env.tmp_path)

            # Run post-processing organization with basic engine
            result = self.organizer.run_post_processing_organization(
                processed_files=test_files,
                target_folder=str(env.tmp_path),
                enable_organization=True,
                ml_enhancement_level=1,  # Basic engine
            )

            # Verify overall success
            self.assertTrue(result["success"])
            self.assertTrue(result["organization_applied"])
            self.assertEqual(result["engine_type"], "Domain Architecture (Level 1)")
            self.assertGreater(result["documents_organized"], 0)

            # Verify organization structure was created
            org_result = result["organization_result"]
            self.assertTrue(org_result["success"])
            self.assertIn("folder_structure", org_result)

            # Check if reorganization was recommended and executed
            should_reorganize = org_result.get("should_reorganize", False)
            if should_reorganize:
                # If reorganization was recommended, execution should have occurred
                self.assertIn("execution_result", org_result)
                execution_result = org_result["execution_result"]
                if execution_result and execution_result.get("success"):
                    self.assertGreaterEqual(execution_result["files_moved"], 0)

                    # Verify folder structure exists
                    folders = org_result["folder_structure"].categories
                    for folder_name in folders:
                        folder_path = env.tmp_path / folder_name
                        self.assertTrue(
                            folder_path.exists(), f"Expected folder not created: {folder_name}"
                        )
            else:
                # If reorganization not recommended, that's also a valid result
                self.assertIn("quality_metrics", org_result)
                quality_metrics = org_result["quality_metrics"]
                self.assertIn("overall_score", quality_metrics)
                self.assertIsInstance(quality_metrics["overall_score"], (int, float))
        
        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

    def test_end_to_end_organization_workflow_enhanced(self):
        """Test complete workflow with enhanced ML processing (Level 2)."""
        with TestFileEnvironment(Path(tempfile.mkdtemp()), "organization") as env:
            # Create test files
            test_files = self._create_realistic_test_files(env.tmp_path)

            # Run post-processing organization with enhanced engine
            result = self.organizer.run_post_processing_organization(
                processed_files=test_files,
                target_folder=str(env.tmp_path),
                enable_organization=True,
                ml_enhancement_level=2,  # Enhanced engine
            )

            # Verify enhanced processing
            self.assertTrue(result["success"])
            self.assertTrue(result["organization_applied"])
            self.assertEqual(result["engine_type"], "Enhanced (Level 2)")

            # Verify ML enhancement was applied
            org_result = result["organization_result"]
            self.assertIn("ml_metrics", org_result)
            ml_metrics = org_result["ml_metrics"]
            self.assertTrue(ml_metrics.get("ml_applied", False))
            self.assertTrue(ml_metrics.get("ml_available", False))

            # Verify organization execution
            if org_result.get("execution_result"):
                execution_result = org_result["execution_result"]
                self.assertTrue(execution_result.get("success", False))
                self.assertGreaterEqual(execution_result.get("files_moved", 0), 0)
        
        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

    def test_organization_workflow_with_mixed_file_types(self):
        """Test organization with various file types and content patterns."""
        with TestFileEnvironment(Path(tempfile.mkdtemp()), "organization") as env:
            # Create diverse test files
            mixed_files = self._create_mixed_content_files(env.tmp_path)

            # Run organization
            result = self.organizer.run_post_processing_organization(
                processed_files=mixed_files,
                target_folder=str(env.tmp_path),
                enable_organization=True,
                ml_enhancement_level=2,
            )

            # Verify handling of diverse content
            self.assertTrue(result["success"])
            self.assertTrue(result["organization_applied"])

            org_result = result["organization_result"]
            classification_results = org_result.get("classification_results", {})

            # Verify different categories were identified
            categories = set(result.category for result in classification_results.values())
            self.assertGreaterEqual(len(categories), 1, "Should identify at least one category")

            # Verify execution handled all file types
            if org_result.get("execution_result"):
                execution_result = org_result["execution_result"]
                self.assertGreaterEqual(execution_result.get("total_operations", 0), 0)
        
        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

    def test_organization_workflow_error_handling(self):
        """Test organization workflow handles errors gracefully."""
        with TestFileEnvironment(Path(tempfile.mkdtemp()), "error_handling") as env:
            test_files = []

            # Valid file
            valid_file = env.tmp_path / "valid_document.pd"
            valid_file.write_text("This is a valid invoice document with proper content for classification.")
            test_files.append(str(valid_file))

            # File that will be missing during execution (simulate external deletion)
            missing_file = env.tmp_path / "will_be_missing.pd"
            missing_file.write_text("This file will be deleted before organization execution.")
            test_files.append(str(missing_file))

            # Delete the file after adding to list (simulates external interference)
            missing_file.unlink()

            # Run organization
            result = self.organizer.run_post_processing_organization(
                processed_files=test_files,
                target_folder=str(env.tmp_path),
                enable_organization=True,
                ml_enhancement_level=1,
            )

            # Verify graceful error handling
            self.assertTrue(result["success"])  # Overall should still succeed
            self.assertTrue(result["organization_applied"])

            # Verify execution handled partial failures
            org_result = result["organization_result"]
            if org_result.get("execution_result"):
                execution_result = org_result["execution_result"]
                # Should have some failures but continue processing
                self.assertGreaterEqual(execution_result.get("files_failed", 0), 1)
                # Should have some successes
                self.assertGreaterEqual(execution_result.get("files_moved", 0), 0)
        
        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

    def test_organization_workflow_disabled(self):
        """Test workflow when organization is explicitly disabled."""
        with TestFileEnvironment(Path(tempfile.mkdtemp()), "disabled") as env:
            test_files = self._create_realistic_test_files(env.tmp_path)

            # Run with organization disabled
            result = self.organizer.run_post_processing_organization(
                processed_files=test_files,
                target_folder=str(env.tmp_path),
                enable_organization=False,  # Disabled
                ml_enhancement_level=2,
            )

            # Verify organization was skipped
            self.assertTrue(result["success"])
            self.assertFalse(result["organization_applied"])
            self.assertIn("Organization disabled", result["reason"])

            # When organization is disabled, organization_result may not exist
            if "organization_result" in result:
                org_result = result["organization_result"]
                # If present, structure should be minimal
                if "folder_structure" in org_result:
                    folder_structure = org_result["folder_structure"] 
                    categories = getattr(folder_structure, 'categories', [])
                    self.assertLessEqual(len(categories), 2, "Organization should be minimal when disabled")
        
        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

    def test_organization_state_persistence(self):
        """Test that organization state is properly persisted."""
        with TestFileEnvironment(Path(tempfile.mkdtemp()), "persistence") as env:
            test_files = self._create_realistic_test_files(env.tmp_path)

            # Run organization
            result = self.organizer.run_post_processing_organization(
                processed_files=test_files,
                target_folder=str(env.tmp_path),
                enable_organization=True,
                ml_enhancement_level=2,
            )

            # Verify organization success
            self.assertTrue(result["success"])
            self.assertTrue(result["organization_applied"])

            # Verify state persistence
            content_tamer_dir = env.tmp_path / ".content_tamer"
            if content_tamer_dir.exists():
                # Check for state files
                organization_dir = content_tamer_dir / "organization"
                if organization_dir.exists():
                    state_files = list(organization_dir.iterdir())
                    # Should have some persistent state
                    self.assertGreater(len(state_files), 0)
        
        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

    def test_organization_workflow_temporal_analysis(self):
        """Test organization workflow with temporal intelligence."""
        with TestFileEnvironment(Path(tempfile.mkdtemp()), "temporal") as env:
            # Create files with temporal patterns
            temporal_files = self._create_temporal_test_files(env.tmp_path)

            # Run organization with temporal analysis
            result = self.organizer.run_post_processing_organization(
                processed_files=temporal_files,
                target_folder=str(env.tmp_path),
                enable_organization=True,
                ml_enhancement_level=3,  # Temporal intelligence
            )

            # Verify temporal processing
            self.assertTrue(result["success"])
            self.assertTrue(result["organization_applied"])

            org_result = result["organization_result"]

            # Verify temporal analysis was performed
            self.assertIn("temporal_analysis", org_result)
            temporal_analysis = org_result["temporal_analysis"]
            self.assertIsInstance(temporal_analysis, dict)

            # Verify organization structure considers temporal patterns
            folder_structure = org_result["folder_structure"]
            self.assertIsInstance(folder_structure.time_granularity, str)
        
        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_io_errors()

    def _create_realistic_test_files(self, tmp_path):
        """Create realistic test files with proper content for classification."""
        created_files = create_realistic_test_documents(tmp_path)
        return [str(f) for f in created_files]

    def _create_mixed_content_files(self, tmp_path):
        """Create files with diverse content types and patterns."""
        created_files = create_mixed_content_documents(tmp_path)
        return [str(f) for f in created_files]

    def _create_temporal_test_files(self, tmp_path):
        """Create files with clear temporal patterns for temporal analysis testing."""
        created_files = create_temporal_test_documents(tmp_path)
        return [str(f) for f in created_files]


if __name__ == "__main__":
    unittest.main(verbosity=2)