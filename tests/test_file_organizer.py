"""
Tests for file organization and management utilities.
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from file_organizer import FileManager, FilenameHandler, FileOrganizer, ProgressTracker


class TestFilenameHandler(unittest.TestCase):
    """Test filename validation and handling."""

    def test_validate_and_trim_filename(self):
        """Test filename cleaning and validation logic."""
        handler = FilenameHandler()

        # Valid filename should remain unchanged
        self.assertEqual(
            handler.validate_and_trim_filename("Valid_Filename_123"),
            "Valid_Filename_123",
        )

        # Should remove invalid characters
        self.assertEqual(
            handler.validate_and_trim_filename("file-with-spaces!@#$"), "filewithspaces"
        )

        # Should handle unicode characters
        self.assertEqual(handler.validate_and_trim_filename("你好世界_document"), "_document")

        # Should truncate long filenames
        long_name = "a" * 200
        result = handler.validate_and_trim_filename(long_name)
        self.assertEqual(len(result), 160)

        # Should return placeholder for empty names
        result = handler.validate_and_trim_filename("")
        self.assertTrue(result.startswith("empty_file_"))

        # Should return placeholder for invalid names
        result = handler.validate_and_trim_filename("!@#$%^&*()")
        self.assertTrue(result.startswith("invalid_name_"))

    @patch("os.path.exists")
    def test_handle_duplicate_filename(self, mock_exists):
        """Test logic for appending numbers to duplicate filenames."""
        handler = FilenameHandler()

        # No duplicate exists
        mock_exists.return_value = False
        result = handler.handle_duplicate_filename("test_file", "/fake/dir", ".pdf")
        self.assertEqual(result, "test_file")

        # One duplicate exists
        mock_exists.side_effect = [True, False]
        result = handler.handle_duplicate_filename("test_file", "/fake/dir", ".pdf")
        self.assertEqual(result, "test_file_1")

        # Multiple duplicates exist
        mock_exists.side_effect = [True, True, True, False]
        result = handler.handle_duplicate_filename("test_file", "/fake/dir", ".pdf")
        self.assertEqual(result, "test_file_3")


class TestProgressTracker(unittest.TestCase):
    """Test progress tracking functionality."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.progress_file = os.path.join(self.temp_dir, ".progress")
        self.input_dir = os.path.join(self.temp_dir, "input")
        os.makedirs(self.input_dir, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_load_progress_empty(self):
        """Test loading progress when no progress file exists."""
        tracker = ProgressTracker()
        progress = tracker.load_progress(self.progress_file, self.input_dir)
        self.assertEqual(progress, set())

    def test_load_progress_with_data(self):
        """Test loading progress with existing data."""
        # Create progress file with some data
        with open(self.progress_file, "w") as f:
            f.write("file1.pdf\nfile2.pdf\n")

        tracker = ProgressTracker()
        progress = tracker.load_progress(self.progress_file, self.input_dir)
        self.assertEqual(progress, {"file1.pdf", "file2.pdf"})

    def test_record_progress(self):
        """Test recording progress with file locking."""
        tracker = ProgressTracker()
        file_manager = FileManager()

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            progress_f = mock_file()
            with patch.object(file_manager, "lock_file"), patch.object(file_manager, "unlock_file"):
                tracker.record_progress(progress_f, "test.pdf", file_manager)

        progress_f.write.assert_called_with("test.pdf\n")
        progress_f.flush.assert_called_once()


class TestFileOrganizer(unittest.TestCase):
    """Test file organization functionality."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_create_directories(self):
        """Test directory creation."""
        dir1 = os.path.join(self.temp_dir, "dir1")
        dir2 = os.path.join(self.temp_dir, "dir2")

        self.organizer.create_directories(dir1, dir2)

        self.assertTrue(os.path.exists(dir1))
        self.assertTrue(os.path.exists(dir2))

    def test_get_file_stats(self):
        """Test file statistics gathering."""
        # Create some test files
        test_files = [
            ("file1.pdf", "pdf content"),
            ("file2.txt", "text content"),
            ("file3.pdf", "more pdf content"),
        ]

        for filename, content in test_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)

        stats = self.organizer.get_file_stats(self.temp_dir)

        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_extension"][".pdf"], 2)
        self.assertEqual(stats["by_extension"][".txt"], 1)

    def test_get_file_stats_empty_dir(self):
        """Test file statistics for empty directory."""
        stats = self.organizer.get_file_stats(self.temp_dir)
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["by_extension"], {})

    def test_organize_by_content_type(self):
        """Test content type organization."""
        test_files = ["doc1.pdf", "image1.png", "sheet1.xlsx"]
        result = self.organizer.organize_by_content_type(test_files, self.temp_dir)

        self.assertEqual(result["documents"], ["doc1.pdf"])
        self.assertEqual(result["images"], ["image1.png"])
        self.assertEqual(result["other"], ["sheet1.xlsx"])

    def test_create_domain_folders(self):
        """Test domain folder creation."""
        domains = ["work", "personal", "finance"]
        result = self.organizer.create_domain_folders(self.temp_dir, domains)

        for domain in domains:
            domain_path = os.path.join(self.temp_dir, domain)
            self.assertTrue(os.path.exists(domain_path))
            self.assertEqual(result[domain], domain_path)


class TestFileManager(unittest.TestCase):
    """Test file management operations."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = FileManager()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_safe_move_success(self):
        """Test successful file move."""
        src_file = os.path.join(self.temp_dir, "source.txt")
        dst_file = os.path.join(self.temp_dir, "destination.txt")

        # Create source file
        with open(src_file, "w") as f:
            f.write("test content")

        # Move file
        self.manager.safe_move(src_file, dst_file)

        # Verify move
        self.assertFalse(os.path.exists(src_file))
        self.assertTrue(os.path.exists(dst_file))

        with open(dst_file, "r") as f:
            self.assertEqual(f.read(), "test content")

    @patch("time.sleep")  # Speed up test
    @patch("shutil.move")
    @patch("shutil.copy2")
    @patch("os.remove")
    def test_safe_move_fallback(self, mock_remove, mock_copy2, mock_move, mock_sleep):
        """Test file move with fallback to copy-then-delete."""
        # Simulate move failure, then successful copy/remove
        mock_move.side_effect = OSError("Move failed")

        self.manager.safe_move("src", "dst")

        # Verify fallback was used
        self.assertEqual(mock_move.call_count, 3)  # 3 attempts
        mock_copy2.assert_called_once_with("src", "dst")
        mock_remove.assert_called_once_with("src")


class TestPostProcessingOrganization(unittest.TestCase):
    """Test Phase 1 post-processing organization features."""

    def setUp(self):
        """Set up temporary directory and test documents for organization testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()
        
        # Create sample documents with different content types
        self.sample_docs = [
            {
                "filename": "contract_acme_corp_2024.pdf",
                "content": "This service agreement is entered into between Acme Corporation and the Client. Terms and conditions apply. Effective date: January 15, 2024.",
                "expected_category": "contracts"
            },
            {
                "filename": "invoice_inv_12345.pdf", 
                "content": "Invoice #12345 dated March 20, 2024. Amount due: $1,500.00. Payment terms: Net 30 days.",
                "expected_category": "invoices"
            },
            {
                "filename": "quarterly_report_q1_2024.pdf",
                "content": "Q1 2024 Financial Report: Revenue increased 15% year-over-year. Operating expenses remained stable.",
                "expected_category": "reports"
            },
            {
                "filename": "mixed_correspondence.pdf",
                "content": "Dear colleagues, this email contains various topics including meeting notes, project updates, and budget discussions.",
                "expected_category": "correspondence"  # This should be uncertain for ML refinement
            }
        ]

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_rule_based_classification_accuracy_target(self):
        """Test Phase 1: Rule-based classification achieves 80%+ accuracy."""
        # This test will fail initially - we need to implement the classifier
        from content_analysis.rule_classifier import EnhancedRuleBasedClassifier
        
        classifier = EnhancedRuleBasedClassifier()
        
        correct_classifications = 0
        total_documents = len(self.sample_docs)
        
        for doc in self.sample_docs:
            predicted_category = classifier.classify_document(doc["content"], doc["filename"])
            if predicted_category == doc["expected_category"]:
                correct_classifications += 1
        
        accuracy = correct_classifications / total_documents
        self.assertGreaterEqual(accuracy, 0.8, f"Rule-based accuracy {accuracy:.2f} below 80% target")

    def test_content_metadata_extraction(self):
        """Test content metadata extraction from processed documents."""
        # This test will fail initially - we need to implement the extractor
        from content_analysis.metadata_extractor import ContentMetadataExtractor
        
        extractor = ContentMetadataExtractor()
        
        for doc in self.sample_docs:
            metadata = extractor.extract_metadata(doc["content"], doc["filename"])
            
            # Validate required metadata fields
            self.assertIn("document_type", metadata)
            self.assertIn("confidence_score", metadata)
            self.assertIn("key_entities", metadata)
            self.assertIn("date_detected", metadata)
            self.assertIsInstance(metadata["confidence_score"], float)
            self.assertGreaterEqual(metadata["confidence_score"], 0.0)
            self.assertLessEqual(metadata["confidence_score"], 1.0)

    def test_simple_state_management(self):
        """Test simple JSON state management for organization preferences."""
        # This test will fail initially - we need to implement the state manager
        from organization.state_manager import SimpleStateManager
        
        state_dir = os.path.join(self.temp_dir, ".content_tamer")
        state_manager = SimpleStateManager(state_dir)
        
        # Test saving organization preferences
        preferences = {
            "hierarchy_type": "category-first",
            "fiscal_year": "calendar",
            "time_granularity": "year"
        }
        state_manager.save_preferences(preferences)
        
        # Test loading preferences
        loaded_preferences = state_manager.load_preferences()
        self.assertEqual(loaded_preferences["hierarchy_type"], "category-first")
        self.assertEqual(loaded_preferences["fiscal_year"], "calendar")
        
        # Test state directory creation
        self.assertTrue(os.path.exists(state_dir))

    def test_basic_organization_engine(self):
        """Test basic organization engine integrates classification and state management."""
        # This test will fail initially - we need to implement the organization engine
        from organization.organization_engine import BasicOrganizationEngine
        
        engine = BasicOrganizationEngine(self.temp_dir)
        
        # Test organization of sample documents
        processed_docs = []
        for doc in self.sample_docs:
            doc_info = {
                "filename": doc["filename"],
                "content": doc["content"],
                "path": os.path.join(self.temp_dir, doc["filename"])
            }
            processed_docs.append(doc_info)
        
        organization_result = engine.organize_documents(processed_docs)
        
        # Validate organization results
        self.assertIn("organization_structure", organization_result)
        self.assertIn("quality_metrics", organization_result)
        self.assertIn("classified_documents", organization_result)
        
        # Check quality metrics
        metrics = organization_result["quality_metrics"]
        self.assertIn("accuracy", metrics)
        self.assertIn("total_documents", metrics)
        self.assertEqual(metrics["total_documents"], len(self.sample_docs))

    def test_post_processing_integration_with_file_organizer(self):
        """Test post-processing organization integrates with existing FileOrganizer."""
        # Test that FileOrganizer has new post-processing method
        self.assertTrue(hasattr(self.organizer, "run_post_processing_organization"))
        
        # Create temporary processed files
        processed_files = []
        for doc in self.sample_docs:
            file_path = os.path.join(self.temp_dir, doc["filename"])
            with open(file_path, "w") as f:
                f.write(doc["content"])
            processed_files.append(file_path)
        
        # Test post-processing organization
        result = self.organizer.run_post_processing_organization(
            processed_files, 
            self.temp_dir,
            enable_organization=True
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("organization_applied", result)

    def test_graceful_degradation(self):
        """Test system gracefully handles component failures."""
        # Test that organization continues even if components fail
        with patch('content_analysis.rule_classifier.EnhancedRuleBasedClassifier') as mock_classifier:
            # Simulate classifier failure
            mock_classifier.side_effect = ImportError("spaCy not available")
            
            # Organization should still work with basic fallback
            result = self.organizer.run_post_processing_organization(
                [], self.temp_dir, enable_organization=True
            )
            
            # Should return success=False but not crash
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)
            
    def test_quality_improvement_threshold(self):
        """Test 15% quality improvement threshold for reorganization."""
        # This will be implemented as part of organization engine
        from organization.organization_engine import BasicOrganizationEngine
        
        engine = BasicOrganizationEngine(self.temp_dir)
        
        # Mock scenario: current organization has 70% quality, new has 80%
        current_quality = 0.70
        proposed_quality = 0.85
        
        should_reorganize = engine.should_apply_reorganization(current_quality, proposed_quality)
        self.assertTrue(should_reorganize)  # 15% improvement (0.70 -> 0.85)
        
        # Mock scenario: improvement is only 10%
        proposed_quality_low = 0.77
        should_not_reorganize = engine.should_apply_reorganization(current_quality, proposed_quality_low)
        self.assertFalse(should_not_reorganize)  # Only 10% improvement


if __name__ == "__main__":
    unittest.main()
