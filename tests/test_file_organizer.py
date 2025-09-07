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


class TestPhase2MLEnhancement(unittest.TestCase):
    """Test Phase 2 ML enhancement features."""

    def setUp(self):
        """Set up temporary directory and test documents for ML testing."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create more diverse sample documents for ML testing
        self.sample_docs = [
            {
                "filename": "clear_contract_agreement_2024.pdf",
                "content": "This service agreement is entered into between Acme Corporation and the Client. Terms and conditions apply. The parties agree to be bound by these terms. Effective date: January 15, 2024.",
                "expected_category": "contracts",
                "expected_confidence": "high"  # Should be certain
            },
            {
                "filename": "mixed_business_document.pdf",
                "content": "Dear team, this document contains various business topics. There are some contract discussions, meeting notes, and project updates. Please review the attached materials.",
                "expected_category": "correspondence", 
                "expected_confidence": "low"  # Should be uncertain, good for ML
            },
            {
                "filename": "financial_summary_unclear.pdf",
                "content": "Summary of items: Revenue, expenses, costs. Analysis needed. Various data points. Further review required.",
                "expected_category": "reports",
                "expected_confidence": "low"  # Should be uncertain
            },
            {
                "filename": "invoice_123_clear.pdf",
                "content": "Invoice #12345 dated March 20, 2024. Amount due: $1,500.00. Payment terms: Net 30 days. Please remit payment to the address below.",
                "expected_category": "invoices",
                "expected_confidence": "high"  # Should be certain
            }
        ]

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_uncertainty_detector_basic_functionality(self):
        """Test uncertainty detector identifies low-confidence documents."""
        from content_analysis.uncertainty_detector import UncertaintyDetector
        
        detector = UncertaintyDetector(confidence_threshold=0.7)
        
        # Create mock classified documents with different confidence levels
        mock_classified = [
            {"filename": "high_conf.pdf", "confidence": 0.9, "category": "contracts"},
            {"filename": "low_conf.pdf", "confidence": 0.4, "category": "other"},
            {"filename": "medium_conf.pdf", "confidence": 0.6, "category": "reports"}
        ]
        
        certain_docs, uncertain_docs = detector.detect_uncertain_documents(mock_classified)
        
        # High confidence should be certain
        self.assertEqual(len(certain_docs), 1)
        self.assertEqual(certain_docs[0]["filename"], "high_conf.pdf")
        
        # Low and medium confidence should be uncertain  
        self.assertEqual(len(uncertain_docs), 2)
        uncertain_filenames = {doc["filename"] for doc in uncertain_docs}
        self.assertIn("low_conf.pdf", uncertain_filenames)
        self.assertIn("medium_conf.pdf", uncertain_filenames)

    def test_ml_refiner_availability_check(self):
        """Test ML refiner handles missing dependencies gracefully."""
        from content_analysis.ml_refiner import SelectiveMLRefinement
        
        refiner = SelectiveMLRefinement()
        
        # Should not crash even if dependencies are missing
        ml_stats = refiner.get_ml_stats()
        self.assertIsInstance(ml_stats, dict)
        self.assertIn("ml_available", ml_stats)

    def test_ml_refiner_with_small_document_set(self):
        """Test ML refiner skips processing for small document sets."""
        from content_analysis.ml_refiner import SelectiveMLRefinement
        
        refiner = SelectiveMLRefinement()
        
        # Small set should be skipped
        small_docs = [{"filename": "test.pdf", "content_preview": "test content"}]
        result = refiner.refine_uncertain_classifications(small_docs, small_docs)
        
        # Should return empty result for small sets
        self.assertEqual(len(result), 0)

    def test_hybrid_state_manager_initialization(self):
        """Test hybrid state manager initializes properly."""
        from organization.hybrid_state_manager import HybridStateManager
        
        # Should initialize without errors
        manager = HybridStateManager(self.temp_dir)
        
        # Should inherit all SimpleStateManager functionality
        self.assertTrue(hasattr(manager, 'save_preferences'))
        self.assertTrue(hasattr(manager, 'load_preferences'))
        
        # Should have additional hybrid functionality
        self.assertTrue(hasattr(manager, 'save_enhanced_session_data'))
        self.assertTrue(hasattr(manager, 'get_advanced_insights'))

    def test_hybrid_state_manager_enhanced_session_data(self):
        """Test saving and retrieving enhanced session data."""
        from organization.hybrid_state_manager import HybridStateManager
        
        manager = HybridStateManager(self.temp_dir)
        
        # Test enhanced session data
        session_data = {
            "session_id": "test_session_123",
            "document_count": 4,
            "quality_metrics": {
                "accuracy": 0.85,
                "rule_accuracy": 0.80,
                "ml_accuracy": 0.90,
                "uncertain_documents": 2,
                "ml_refined_documents": 2
            },
            "classified_documents": [
                {
                    "filename": "test1.pdf",
                    "category": "contracts",
                    "confidence": 0.9,
                    "classification_method": "rule_based"
                },
                {
                    "filename": "test2.pdf", 
                    "category": "reports",
                    "confidence": 0.75,
                    "classification_method": "ml_refinement"
                }
            ]
        }
        
        # Should save successfully
        success = manager.save_enhanced_session_data(session_data, processing_time=5.2)
        self.assertTrue(success)

    def test_enhanced_organization_engine_level_1(self):
        """Test enhanced engine works in Phase 1 compatibility mode."""
        from organization.enhanced_organization_engine import EnhancedOrganizationEngine
        
        # Level 1 should work like BasicOrganizationEngine
        engine = EnhancedOrganizationEngine(self.temp_dir, ml_enhancement_level=1)
        self.assertEqual(engine.ml_enhancement_level, 1)
        
        # Should still organize documents successfully
        processed_docs = []
        for doc in self.sample_docs:
            doc_info = {
                "filename": doc["filename"],
                "content": doc["content"], 
                "path": os.path.join(self.temp_dir, doc["filename"])
            }
            processed_docs.append(doc_info)
        
        result = engine.organize_documents(processed_docs)
        
        self.assertIn("success", result)
        self.assertTrue(result["success"])
        self.assertIn("quality_metrics", result)

    def test_enhanced_organization_engine_level_2(self):
        """Test enhanced engine with Phase 2 ML capabilities."""
        from organization.enhanced_organization_engine import EnhancedOrganizationEngine
        
        # Level 2 should include ML enhancement
        engine = EnhancedOrganizationEngine(self.temp_dir, ml_enhancement_level=2)
        self.assertEqual(engine.ml_enhancement_level, 2)
        
        # Should have ML components
        self.assertTrue(hasattr(engine, 'uncertainty_detector'))
        self.assertTrue(hasattr(engine, 'ml_refiner'))
        
        # Test ML stats
        ml_stats = engine.get_ml_stats()
        self.assertIsInstance(ml_stats, dict)
        self.assertEqual(ml_stats["enhancement_level"], 2)

    def test_enhanced_organization_engine_with_ml_documents(self):
        """Test enhanced engine processes documents with ML refinement."""
        from organization.enhanced_organization_engine import EnhancedOrganizationEngine
        
        engine = EnhancedOrganizationEngine(self.temp_dir, ml_enhancement_level=2)
        
        # Process documents
        processed_docs = []
        for doc in self.sample_docs:
            doc_info = {
                "filename": doc["filename"],
                "content": doc["content"],
                "path": os.path.join(self.temp_dir, doc["filename"])
            }
            processed_docs.append(doc_info)
        
        result = engine.organize_documents(processed_docs)
        
        # Should complete successfully
        self.assertTrue(result["success"])
        
        # Should include ML metrics
        self.assertIn("ml_metrics", result)
        ml_metrics = result["ml_metrics"]
        
        # ML should be attempted
        if ml_metrics.get("ml_applied", False):
            self.assertIn("total_documents", ml_metrics)
            self.assertIn("uncertain_documents", ml_metrics)
        
        # Should include enhanced quality metrics
        quality_metrics = result["quality_metrics"]
        self.assertIn("accuracy", quality_metrics)

    def test_uncertainty_detector_threshold_analysis(self):
        """Test uncertainty detector threshold analysis functionality."""
        from content_analysis.uncertainty_detector import UncertaintyDetector
        
        detector = UncertaintyDetector()
        
        # Create documents with various confidence levels
        test_docs = [
            {"filename": f"doc_{i}.pdf", "confidence": i * 0.1, "category": "test"}
            for i in range(1, 11)  # 0.1 to 1.0 confidence
        ]
        
        analysis = detector.get_threshold_analysis(test_docs)
        
        # Should return analysis for different thresholds
        self.assertIsInstance(analysis, dict)
        
        # Should have data for different threshold levels
        threshold_keys = [k for k in analysis.keys() if k.startswith("threshold_")]
        self.assertGreater(len(threshold_keys), 0)

    def test_enhanced_organization_graceful_degradation(self):
        """Test enhanced organization handles ML failures gracefully."""
        from organization.enhanced_organization_engine import EnhancedOrganizationEngine
        
        engine = EnhancedOrganizationEngine(self.temp_dir, ml_enhancement_level=2)
        
        # Even if ML components fail, should still work
        processed_docs = [
            {
                "filename": "test.pdf",
                "content": "test content",
                "path": os.path.join(self.temp_dir, "test.pdf")
            }
        ]
        
        result = engine.organize_documents(processed_docs)
        
        # Should not crash even if ML fails
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)

    def test_integration_with_file_organizer_ml_levels(self):
        """Test FileOrganizer integration works with different ML levels."""
        from file_organizer import FileOrganizer
        
        organizer = FileOrganizer()
        
        # Create test files
        processed_files = []
        for doc in self.sample_docs[:2]:  # Just test with 2 docs
            file_path = os.path.join(self.temp_dir, doc["filename"])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(doc["content"])
            processed_files.append(file_path)
        
        # Should work with ML enhancement
        result = organizer.run_post_processing_organization(
            processed_files, self.temp_dir, enable_organization=True
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)


class TestPhase3TemporalIntelligence(unittest.TestCase):
    """Test Phase 3 temporal intelligence features."""

    def setUp(self):
        """Set up test environment with temporal documents."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_docs = []
        
        # Create temporal test documents with varied dates and content
        temporal_test_files = [
            ("Q1_2024_Financial_Report.pdf", "financial analysis Q1 results revenue profit margin"),
            ("Invoice_2024_04_15.pdf", "invoice payment due amount $5000 April 2024"),
            ("Contract_Agreement_2024_01_30.pdf", "contract terms agreement January legal document"),
            ("Q2_2024_Sales_Report.pdf", "sales report Q2 performance quarterly metrics"),
            ("Meeting_Minutes_2024_03_20.pdf", "meeting minutes March discussion action items"),
            ("Yearly_Summary_2023.pdf", "annual summary 2023 year end comprehensive review"),
            ("Invoice_2024_07_08.pdf", "invoice billing July amount $3200 payment"),
            ("Q3_2024_Analysis.pdf", "quarterly analysis Q3 third quarter business review"),
        ]
        
        for filename, content in temporal_test_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.test_docs.append(file_path)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_temporal_organization_engine_initialization(self):
        """Test that Phase 3 temporal organization engine initializes correctly."""
        try:
            from organization.temporal_organization_engine import TemporalOrganizationEngine
            
            engine = TemporalOrganizationEngine(self.temp_dir, ml_enhancement_level=3)
            
            self.assertEqual(engine.ml_enhancement_level, 3)
            self.assertIsNotNone(engine.temporal_analyzer)
            self.assertTrue(hasattr(engine, 'get_temporal_insights'))
            self.assertTrue(hasattr(engine, 'get_temporal_stats'))
            
        except ImportError:
            self.skipTest("Temporal dependencies not available")

    def test_temporal_intelligence_with_phase3_documents(self):
        """Test temporal intelligence analysis with Phase 3 documents."""
        try:
            from organization.temporal_organization_engine import TemporalOrganizationEngine
            
            engine = TemporalOrganizationEngine(self.temp_dir, ml_enhancement_level=3)
            
            # Prepare document data for temporal analysis
            processed_documents = []
            for file_path in self.test_docs:
                filename = os.path.basename(file_path)
                content = "sample content for temporal analysis"
                
                processed_documents.append({
                    "path": file_path,
                    "filename": filename,
                    "content": content,
                })
            
            # Run temporal organization
            result = engine.organize_documents(processed_documents)
            
            # Verify temporal intelligence was applied
            self.assertIn("temporal_intelligence", result)
            temporal_intel = result["temporal_intelligence"]
            
            # Should have temporal enhancement applied
            if temporal_intel.get("temporal_enhancement_applied"):
                self.assertIn("confidence_metrics", temporal_intel)
                self.assertIn("organization_strategy", temporal_intel)
                self.assertIn("recommendations", temporal_intel)
            
            # Quality metrics should include temporal information
            quality_metrics = result.get("quality_metrics", {})
            if quality_metrics.get("temporal_enhancement_applied"):
                self.assertIn("temporal_confidence", quality_metrics)
                self.assertIn("temporal_organization_type", quality_metrics)
            
        except ImportError:
            self.skipTest("Temporal intelligence dependencies not available")

    def test_temporal_analyzer_seasonal_pattern_detection(self):
        """Test seasonal pattern detection in temporal analyzer."""
        try:
            from content_analysis.temporal_analyzer import AdvancedTemporalAnalyzer
            
            analyzer = AdvancedTemporalAnalyzer()
            
            # Create documents with seasonal patterns
            seasonal_docs = [
                {
                    "filename": "Q1_Report.pdf",
                    "category": "reports", 
                    "confidence": 0.8,
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": 3, "day": 15}]
                    }
                },
                {
                    "filename": "Q2_Report.pdf", 
                    "category": "reports",
                    "confidence": 0.9,
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": 6, "day": 10}]
                    }
                },
                {
                    "filename": "Q3_Report.pdf",
                    "category": "reports", 
                    "confidence": 0.85,
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": 9, "day": 20}]
                    }
                },
            ]
            
            analysis = analyzer.analyze_temporal_intelligence(seasonal_docs)
            
            # Should detect seasonal patterns
            self.assertIn("seasonal_insights", analysis)
            seasonal_insights = analysis["seasonal_insights"]
            
            # Check for category seasonal patterns
            if seasonal_insights.get("category_seasonal_patterns"):
                category_patterns = seasonal_insights["category_seasonal_patterns"]
                if "reports" in category_patterns:
                    reports_pattern = category_patterns["reports"]
                    # May or may not detect pattern with only 3 data points
                    self.assertIn("pattern_detected", reports_pattern)
            
        except ImportError:
            self.skipTest("Temporal analysis dependencies not available")

    def test_fiscal_year_detection(self):
        """Test fiscal year pattern detection."""
        try:
            from content_analysis.temporal_analyzer import AdvancedTemporalAnalyzer
            
            analyzer = AdvancedTemporalAnalyzer()
            
            # Create documents with fiscal year patterns
            fiscal_docs = [
                {
                    "filename": "FY2024_Q1_Report.pdf",
                    "category": "reports",
                    "confidence": 0.8,
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": 4, "day": 1}],
                        "fiscal_year_hints": {"fiscal_year_pattern": "financial"}
                    }
                },
                {
                    "filename": "FY2024_Q2_Report.pdf",
                    "category": "reports", 
                    "confidence": 0.9,
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": 7, "day": 15}],
                        "fiscal_year_hints": {"fiscal_year_pattern": "financial"}
                    }
                },
            ]
            
            analysis = analyzer.analyze_temporal_intelligence(fiscal_docs)
            
            # Should detect fiscal year pattern
            self.assertIn("fiscal_year_analysis", analysis)
            fiscal_analysis = analysis["fiscal_year_analysis"]
            
            self.assertIn("detected_fiscal_type", fiscal_analysis)
            self.assertIn("confidence", fiscal_analysis)
            
            # Should prefer financial fiscal year due to hints
            if fiscal_analysis.get("confidence", 0) > 0.5:
                self.assertEqual(fiscal_analysis["detected_fiscal_type"], "financial")
            
        except ImportError:
            self.skipTest("Temporal analysis dependencies not available")

    def test_workflow_pattern_recognition(self):
        """Test workflow pattern recognition in temporal analysis."""
        try:
            from content_analysis.temporal_analyzer import AdvancedTemporalAnalyzer
            
            analyzer = AdvancedTemporalAnalyzer()
            
            # Create documents with monthly invoice workflow pattern
            workflow_docs = []
            for month in [1, 2, 3, 4, 5]:  # 5 months of invoices
                workflow_docs.append({
                    "filename": f"Invoice_2024_{month:02d}.pdf",
                    "category": "invoices",
                    "confidence": 0.9,
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": month, "day": 15}]
                    }
                })
            
            analysis = analyzer.analyze_temporal_intelligence(workflow_docs)
            
            # Should detect workflow patterns
            self.assertIn("workflow_patterns", analysis)
            workflow_patterns = analysis["workflow_patterns"]
            
            if workflow_patterns.get("category_workflows"):
                category_workflows = workflow_patterns["category_workflows"]
                if "invoices" in category_workflows:
                    invoice_workflow = category_workflows["invoices"]
                    self.assertIn("workflow_detected", invoice_workflow)
                    if invoice_workflow.get("workflow_detected"):
                        self.assertIn("workflow_type", invoice_workflow)
                        # Should detect monthly pattern
                        self.assertEqual(invoice_workflow["workflow_type"], "monthly")
            
        except ImportError:
            self.skipTest("Temporal analysis dependencies not available")

    def test_temporal_organization_structure_generation(self):
        """Test temporal organization structure generation."""
        try:
            from organization.temporal_organization_engine import TemporalOrganizationEngine
            
            engine = TemporalOrganizationEngine(self.temp_dir, ml_enhancement_level=3)
            
            # Create documents spanning multiple years
            multi_year_docs = []
            for year in [2022, 2023, 2024]:
                for quarter in [1, 2, 3, 4]:
                    month = quarter * 3
                    filename = f"Report_{year}_Q{quarter}.pdf"
                    multi_year_docs.append({
                        "path": os.path.join(self.temp_dir, filename),
                        "filename": filename,
                        "category": "reports",
                        "confidence": 0.8,
                        "metadata": {
                            "date_detected": [{"year": year, "month": month, "day": 15}]
                        }
                    })
            
            result = engine.organize_documents(multi_year_docs)
            
            # Should generate temporal organization structure
            self.assertIn("organization_structure", result)
            org_structure = result["organization_structure"]
            
            # Should be temporal-aware
            if org_structure.get("organization_type") == "temporal_intelligence":
                self.assertIn("primary_structure", org_structure)
                self.assertIn("time_granularity", org_structure)
                self.assertIn("structure_details", org_structure)
                
                # Should have chronological structure due to multi-year span
                self.assertEqual(org_structure["primary_structure"], "chronological")
            
        except ImportError:
            self.skipTest("Temporal intelligence dependencies not available")

    def test_temporal_quality_metrics_calculation(self):
        """Test temporal quality metrics calculation."""
        try:
            from organization.temporal_organization_engine import TemporalOrganizationEngine
            
            engine = TemporalOrganizationEngine(self.temp_dir, ml_enhancement_level=3)
            
            # Create well-structured temporal documents
            temporal_docs = []
            for i, (filename, content) in enumerate([
                ("2024_Q1_Financial.pdf", "financial report Q1 revenue"),
                ("2024_Q2_Financial.pdf", "financial report Q2 profit"),
                ("2024_Q3_Financial.pdf", "financial report Q3 growth"),
                ("Invoice_2024_01.pdf", "invoice January billing"),
                ("Invoice_2024_02.pdf", "invoice February payment"),
            ]):
                temporal_docs.append({
                    "path": os.path.join(self.temp_dir, filename),
                    "filename": filename,
                    "category": "reports" if "Financial" in filename else "invoices", 
                    "confidence": 0.8 + (i * 0.02),  # Varying confidence
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": (i % 4) + 1, "day": 15}]
                    }
                })
            
            result = engine.organize_documents(temporal_docs)
            
            # Check quality metrics include temporal information
            quality_metrics = result.get("quality_metrics", {})
            
            if quality_metrics.get("temporal_enhancement_applied"):
                self.assertIn("temporal_confidence", quality_metrics)
                self.assertIn("date_coverage", quality_metrics)
                self.assertIn("pattern_strength", quality_metrics)
                
                # Temporal confidence should be reasonable
                temporal_confidence = quality_metrics.get("temporal_confidence", 0)
                self.assertGreaterEqual(temporal_confidence, 0.0)
                self.assertLessEqual(temporal_confidence, 1.0)
                
                # Date coverage should be reasonable (may be 0 if metadata extraction didn't work)
                date_coverage = quality_metrics.get("date_coverage", 0)
                self.assertGreaterEqual(date_coverage, 0.0)  # Should be non-negative
                self.assertLessEqual(date_coverage, 1.0)  # Should not exceed 1.0
            
        except ImportError:
            self.skipTest("Temporal intelligence dependencies not available")

    def test_phase3_file_organizer_integration(self):
        """Test Phase 3 integration with file organizer."""
        try:
            organizer = FileOrganizer()
            
            # Run post-processing with Phase 3 enabled
            result = organizer.run_post_processing_organization(
                self.test_docs,
                self.temp_dir,
                enable_organization=True,
                ml_enhancement_level=3
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)
            
            if result.get("success"):
                self.assertIn("organization_applied", result)
                if result.get("organization_applied"):
                    self.assertIn("engine_type", result)
                    # Should use temporal intelligence engine
                    self.assertIn("Temporal Intelligence", result["engine_type"])
                    
                    # Should have quality metrics
                    if result.get("quality_metrics"):
                        quality_metrics = result["quality_metrics"]
                        # May have temporal enhancement depending on document analysis
                        if quality_metrics.get("temporal_enhancement_applied"):
                            self.assertIn("temporal_confidence", quality_metrics)
            
        except ImportError:
            self.skipTest("Phase 3 temporal dependencies not available")

    def test_temporal_sensitivity_tuning(self):
        """Test temporal sensitivity tuning functionality."""
        try:
            from organization.temporal_organization_engine import TemporalOrganizationEngine
            
            engine = TemporalOrganizationEngine(self.temp_dir, ml_enhancement_level=3)
            
            # Create documents for sensitivity tuning
            tuning_docs = []
            for i in range(10):
                tuning_docs.append({
                    "filename": f"Document_{i:02d}.pdf",
                    "category": "reports",
                    "confidence": 0.6 + (i * 0.04),  # Varying confidence 
                    "metadata": {
                        "date_detected": [{"year": 2024, "month": (i % 12) + 1, "day": 15}]
                    }
                })
            
            # Test sensitivity tuning
            tuning_result = engine.tune_temporal_sensitivity(tuning_docs, target_temporal_usage=0.7)
            
            self.assertIn("optimal_threshold", tuning_result)
            self.assertIn("current_confidence", tuning_result)
            self.assertIn("expected_temporal_usage", tuning_result)
            self.assertIn("recommendations", tuning_result)
            
            # Optimal threshold should be reasonable
            optimal_threshold = tuning_result["optimal_threshold"]
            self.assertGreaterEqual(optimal_threshold, 0.5)
            self.assertLessEqual(optimal_threshold, 1.0)
            
        except ImportError:
            self.skipTest("Temporal intelligence dependencies not available")

    def test_temporal_stats_and_capabilities(self):
        """Test temporal statistics and capability reporting."""
        try:
            from organization.temporal_organization_engine import TemporalOrganizationEngine
            
            # Test Phase 3 engine capabilities
            engine_phase3 = TemporalOrganizationEngine(self.temp_dir, ml_enhancement_level=3)
            stats_phase3 = engine_phase3.get_temporal_stats()
            
            self.assertEqual(stats_phase3["enhancement_level"], 3)
            self.assertTrue(stats_phase3["temporal_available"])
            self.assertIn("temporal_features", stats_phase3)
            self.assertIn("supported_structures", stats_phase3)
            
            # Should support all temporal features
            features = stats_phase3["temporal_features"]
            expected_features = [
                "advanced_seasonal_analysis",
                "fiscal_year_detection", 
                "workflow_pattern_recognition",
                "business_cycle_intelligence",
                "adaptive_organization_strategies",
            ]
            for feature in expected_features:
                self.assertIn(feature, features)
            
            # Test Phase 2 engine limitations
            from organization.enhanced_organization_engine import EnhancedOrganizationEngine
            engine_phase2 = EnhancedOrganizationEngine(self.temp_dir, ml_enhancement_level=2)
            
            # Should not have temporal capabilities
            if hasattr(engine_phase2, 'get_temporal_stats'):
                stats_phase2 = engine_phase2.get_temporal_stats()
                self.assertEqual(stats_phase2["enhancement_level"], 2)
                self.assertFalse(stats_phase2.get("temporal_available", True))
            
        except ImportError:
            self.skipTest("Temporal intelligence dependencies not available")

    def test_graceful_degradation_without_temporal_dependencies(self):
        """Test graceful degradation when temporal dependencies are not available."""
        # This test simulates missing dependencies
        try:
            from organization.temporal_organization_engine import TemporalOrganizationEngine
            
            engine = TemporalOrganizationEngine(self.temp_dir, ml_enhancement_level=3)
            
            # Force temporal analyzer to None to simulate missing dependencies
            original_analyzer = engine.temporal_analyzer
            engine.temporal_analyzer = None
            
            # Should still work with degraded functionality
            test_docs = [{
                "path": os.path.join(self.temp_dir, "test.pdf"),
                "filename": "test.pdf",
                "category": "other",
                "confidence": 0.7,
                "metadata": {}
            }]
            
            result = engine.organize_documents(test_docs)
            
            # Should succeed but without temporal intelligence
            self.assertIn("success", result)
            if result.get("temporal_intelligence"):
                temporal_intel = result["temporal_intelligence"]
                self.assertEqual(temporal_intel.get("temporal_enhancement", False), False)
            
            # Restore original analyzer
            engine.temporal_analyzer = original_analyzer
            
        except ImportError:
            self.skipTest("Temporal intelligence dependencies not available")


if __name__ == "__main__":
    unittest.main()
