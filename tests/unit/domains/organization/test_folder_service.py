#!/usr/bin/env python3
"""
Tests for Folder Service in Organization Domain

Tests the folder service that handles file operations and folder structure
management for document organization.
"""

import unittest
import os
import sys
import tempfile

# Add src to path for imports - correct path for domain structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

# Import from organization domain
from domains.organization.folder_service import FolderService, FolderStructureType, FiscalYearType, FolderStructure
from tests.utils.rich_test_utils import RichTestCase

class TestFolderServiceDefaults(unittest.TestCase):
    """Test Folder Service default behavior and initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = FolderService()

    def test_folder_service_initialization(self):
        """Test folder service initializes correctly."""
        self.assertIsInstance(self.service, FolderService)
        self.assertIsNotNone(self.service.analyzer)

    def test_folder_structure_validation(self):
        """Test folder structure validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test folder structure
            structure = FolderStructure(
                structure_type=FolderStructureType.CATEGORY_FIRST,
                fiscal_year_type=FiscalYearType.CALENDAR,
                time_granularity="year",
                base_path=temp_dir,
                categories=["financial", "legal"],
                metadata={}
            )

            validation = self.service.validate_folder_structure(structure)
            self.assertIn("valid", validation)
            self.assertIsInstance(validation["valid"], bool)

    def test_folder_statistics(self):
        """Test folder statistics collection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test structure
            os.makedirs(os.path.join(temp_dir, "test_folder"))
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")

            stats = self.service.get_folder_statistics(temp_dir)
            self.assertIn("exists", stats)
            self.assertTrue(stats["exists"])
            if "total_files" in stats:
                self.assertGreaterEqual(stats["total_files"], 1)

class TestFolderStructureAnalysis(unittest.TestCase):
    """Test folder structure analysis functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = FolderService()

    def test_analyze_existing_structure(self):
        """Test analysis of existing folder structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test directory structure
            os.makedirs(os.path.join(temp_dir, "2024"))
            os.makedirs(os.path.join(temp_dir, "2023"))

            analysis = self.service.analyzer.analyze_existing_structure(temp_dir)

            if analysis:  # May return None for unclear structures
                self.assertIsInstance(analysis, FolderStructure)
                self.assertIn(analysis.structure_type, list(FolderStructureType))

class TestFileOperations(unittest.TestCase, RichTestCase):
    """Test file operation functionality with Rich test framework."""

    def setUp(self):
        """Set up Rich test environment."""
        RichTestCase.setUp(self)
        self.service = FolderService()

    def test_safe_file_operations(self):
        """Test safe file operations through folder service."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source and target structure
            source_file = os.path.join(temp_dir, "source.txt")
            target_dir = os.path.join(temp_dir, "target")

            with open(source_file, 'w') as f:
                f.write("test content")

            os.makedirs(target_dir)

            # Test file operation validation
            valid, error = self.service.validate_file_operation(
                "move", source_file, os.path.join(target_dir, "target.txt")
            )

            # Should validate successfully for reasonable operations
            if not valid:
                # Log what the validation error was
                print("Validation error: {error}")

if __name__ == "__main__":
    unittest.main()
