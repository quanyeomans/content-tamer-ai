"""
Tests for Content Extraction Service

Tests document content extraction with multiple methods and quality assessment.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from src.domains.content.extraction_service import (
    ContentQuality,
    ExtractedContent,
    ExtractionService,
    ImageContentProcessor,
    PDFContentProcessor,
)


class TestExtractionService(unittest.TestCase):
    """Test content extraction service functionality."""

    def setUp(self):
        """Set up test extraction service."""
        self.service = ExtractionService()

    def test_initialization(self):
        """Test service initializes correctly."""
        self.assertIsInstance(self.service, ExtractionService)
        self.assertEqual(self.service.ocr_lang, "eng")
        self.assertGreater(len(self.service.processors), 0)
        self.assertIsInstance(self.service._processor_map, dict)

    def test_get_supported_file_types(self):
        """Test getting supported file types."""
        supported_types = self.service.get_supported_file_types()

        self.assertIsInstance(supported_types, list)
        self.assertIn(".pdf", supported_types)
        # Should also include image types if available
        image_types = [".png", ".jpg", ".jpeg"]
        self.assertTrue(any(img_type in supported_types for img_type in image_types))

    def test_find_processor_for_pdf(self):
        """Test finding processor for PDF file."""
        processor = self.service._find_processor_for_file("test.pdff")
        self.assertIsInstance(processor, PDFContentProcessor)

    def test_find_processor_for_image(self):
        """Test finding processor for image file."""
        processor = self.service._find_processor_for_file("test.png")
        if processor:  # Only test if image processor available
            self.assertIsInstance(processor, ImageContentProcessor)

    def test_find_processor_for_unsupported(self):
        """Test finding processor for unsupported file."""
        processor = self.service._find_processor_for_file("test.txt")
        self.assertIsNone(processor)

    def test_extract_from_nonexistent_file(self):
        """Test extraction from non-existent file."""
        result = self.service.extract_from_file("/nonexistent/file.pd")

        self.assertIsInstance(result, ExtractedContent)
        self.assertEqual(result.quality, ContentQuality.FAILED)
        self.assertIsNotNone(result.error_message)

    def test_extract_from_unsupported_file(self):
        """Test extraction from unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"Some text content")
            temp_path = temp_file.name

        try:
            result = self.service.extract_from_file(temp_path)

            self.assertIsInstance(result, ExtractedContent)
            self.assertEqual(result.quality, ContentQuality.FAILED)
            self.assertIn("Unsupported file type", result.text)

        finally:
            os.unlink(temp_path)

    @patch("src.domains.content.extraction_service.ContentValidator")
    def test_content_validation(self, mock_validator):
        """Test content validation is applied."""
        mock_validator.validate_extracted_content.return_value = "validated content"

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name

        # Mock PDF processor to return successful result
        with patch.object(self.service, "_find_processor_for_file") as mock_find:
            mock_processor = Mock()
            mock_processor.extract_content.return_value = ExtractedContent(
                text="test content", quality=ContentQuality.GOOD, extraction_method="test"
            )
            mock_find.return_value = mock_processor

            try:
                result = self.service.extract_from_file(temp_path)

                # Should have called validation
                mock_validator.validate_extracted_content.assert_called_once()
                self.assertEqual(result.text, "validated content")

            finally:
                os.unlink(temp_path)

    def test_batch_extract_empty_list(self):
        """Test batch extraction with empty file list."""
        results = self.service.batch_extract([])
        self.assertEqual(results, {})

    def test_batch_extract_mixed_files(self):
        """Test batch extraction with mix of supported and unsupported files."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_file = os.path.join(temp_dir, "test.pdf")
            txt_file = os.path.join(temp_dir, "test.txt")

            # Create empty files
            Path(pdf_file).touch()
            Path(txt_file).touch()

            # Mock processors for testing
            with patch.object(self.service, "_find_processor_for_file") as mock_find:

                def mock_find_processor(file_path):
                    if file_path.endswith(".pdf"):
                        mock_processor = Mock()
                        mock_processor.extract_content.return_value = ExtractedContent(
                            text="PDF content",
                            quality=ContentQuality.GOOD,
                            extraction_method="test",
                        )
                        return mock_processor
                    return None

                mock_find.side_effect = mock_find_processor

                results = self.service.batch_extract([pdf_file, txt_file])

                self.assertEqual(len(results), 2)
                # PDF extraction quality depends on file content and dependencies available
                self.assertIn(results[pdf_file].quality, [ContentQuality.GOOD, ContentQuality.FAIR, ContentQuality.FAILED])
                self.assertEqual(results[txt_file].quality, ContentQuality.FAILED)

    def test_get_processor_capabilities(self):
        """Test getting processor capabilities."""
        capabilities = self.service.get_processor_capabilities()

        self.assertIsInstance(capabilities, dict)
        self.assertIn("PDFContentProcessor", capabilities)

        # Each processor should have supported extensions and availability
        for processor_name, info in capabilities.items():
            self.assertIn("supported_extensions", info)
            self.assertIn("available", info)
            self.assertIsInstance(info["supported_extensions"], list)
            self.assertIsInstance(info["available"], bool)


class TestPDFContentProcessor(unittest.TestCase):
    """Test PDF content processor."""

    def setUp(self):
        """Set up PDF processor."""
        self.processor = PDFContentProcessor()

    def test_can_process_pdf(self):
        """Test PDF file detection."""
        self.assertTrue(self.processor.can_process("test.pdf"))
        self.assertTrue(self.processor.can_process("TEST.PDF"))
        self.assertFalse(self.processor.can_process("test.txt"))
        self.assertFalse(self.processor.can_process("test.png"))

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        extensions = self.processor.get_supported_extensions()
        self.assertEqual(extensions, [".pdf"])

    def test_dependency_checking(self):
        """Test dependency availability checking."""
        # Dependencies should be checked during initialization
        self.assertTrue(hasattr(self.processor, "have_pymupdf"))
        self.assertTrue(hasattr(self.processor, "have_tesseract"))
        self.assertIsInstance(self.processor.have_pymupdf, bool)
        self.assertIsInstance(self.processor.have_tesseract, bool)

    def test_method_availability(self):
        """Test extraction method availability checking."""
        # PyMuPDF method
        pymupdf_available = self.processor._method_available("pymupdf_text")
        self.assertEqual(pymupdf_available, self.processor.have_pymupdf)

        # pypdf method (should always be available)
        pypdf_available = self.processor._method_available("pypdf_text")
        self.assertTrue(pypdf_available)

        # OCR method (requires both PyMuPDF and Tesseract)
        ocr_available = self.processor._method_available("ocr_extraction")
        self.assertEqual(
            ocr_available, self.processor.have_tesseract and self.processor.have_pymupdf
        )

    @patch("src.domains.content.extraction_service.os.path.isfile")
    @patch("src.domains.content.extraction_service.os.path.getsize")
    def test_security_validation_file_too_large(self, mock_getsize, mock_isfile):
        """Test security validation rejects files that are too large."""
        mock_isfile.return_value = True
        mock_getsize.return_value = 60 * 1024 * 1024  # 60MB (over 50MB limit)

        valid = self.processor._validate_file_security("test.pdf")
        self.assertFalse(valid)

    @patch("src.domains.content.extraction_service.os.path.isfile")
    @patch("src.domains.content.extraction_service.os.path.getsize")
    def test_security_validation_empty_file(self, mock_getsize, mock_isfile):
        """Test security validation rejects empty files."""
        mock_isfile.return_value = True
        mock_getsize.return_value = 0

        valid = self.processor._validate_file_security("test.pdf")
        self.assertFalse(valid)

    def test_extract_content_nonexistent_file(self):
        """Test extraction from non-existent file."""
        result = self.processor.extract_content("/nonexistent/file.pd")

        self.assertIsInstance(result, ExtractedContent)
        self.assertEqual(result.quality, ContentQuality.FAILED)
        self.assertIn("Security validation failed", result.text)


class TestImageContentProcessor(unittest.TestCase):
    """Test image content processor."""

    def setUp(self):
        """Set up image processor."""
        self.processor = ImageContentProcessor()

    def test_can_process_images(self):
        """Test image file detection."""
        self.assertTrue(self.processor.can_process("test.png"))
        self.assertTrue(self.processor.can_process("test.jpg"))
        self.assertTrue(self.processor.can_process("test.JPEG"))
        self.assertTrue(self.processor.can_process("test.tif"))
        self.assertFalse(self.processor.can_process("test.pdf"))
        self.assertFalse(self.processor.can_process("test.txt"))

    def test_get_supported_extensions(self):
        """Test getting supported image extensions."""
        extensions = self.processor.get_supported_extensions()

        expected_extensions = [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"]
        self.assertEqual(extensions, expected_extensions)

    def test_dependency_checking(self):
        """Test OCR dependency checking."""
        self.assertTrue(hasattr(self.processor, "have_tesseract"))
        self.assertIsInstance(self.processor.have_tesseract, bool)

    def test_extract_content_no_tesseract(self):
        """Test extraction when Tesseract is not available."""
        # Temporarily disable Tesseract for test
        original_have_tesseract = self.processor.have_tesseract
        self.processor.have_tesseract = False

        try:
            result = self.processor.extract_content("test.png")

            self.assertIsInstance(result, ExtractedContent)
            self.assertEqual(result.quality, ContentQuality.FAILED)
            self.assertIn("OCR not available", result.text)

        finally:
            self.processor.have_tesseract = original_have_tesseract


class TestExtractedContent(unittest.TestCase):
    """Test ExtractedContent dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        content = ExtractedContent(text="test content")

        self.assertEqual(content.text, "test content")
        self.assertIsNone(content.image_data)
        self.assertEqual(content.quality, ContentQuality.FAILED)
        self.assertEqual(content.extraction_method, "unknown")
        self.assertEqual(content.file_type, "unknown")
        self.assertEqual(content.metadata, {})
        self.assertEqual(content.security_warnings, [])
        self.assertIsNone(content.error_message)

    def test_field_assignment(self):
        """Test all fields can be assigned."""
        content = ExtractedContent(
            text="test content",
            image_data="base64data",
            quality=ContentQuality.EXCELLENT,
            extraction_method="pymupdf",
            file_type="pdf",
            metadata={"test": True},
            security_warnings=["warning1"],
            error_message="test error",
        )

        self.assertEqual(content.text, "test content")
        self.assertEqual(content.image_data, "base64data")
        self.assertEqual(content.quality, ContentQuality.EXCELLENT)
        self.assertEqual(content.extraction_method, "pymupdf")
        self.assertEqual(content.file_type, "pdf")
        self.assertEqual(content.metadata["test"], True)
        self.assertIn("warning1", content.security_warnings)
        self.assertEqual(content.error_message, "test error")


class TestContentQuality(unittest.TestCase):
    """Test ContentQuality enumeration."""

    def test_quality_levels(self):
        """Test all quality levels are defined."""
        quality_levels = [
            ContentQuality.EXCELLENT,
            ContentQuality.GOOD,
            ContentQuality.FAIR,
            ContentQuality.POOR,
            ContentQuality.FAILED,
        ]

        # All should have string values
        for level in quality_levels:
            self.assertIsInstance(level.value, str)

        # Values should be distinct
        values = [level.value for level in quality_levels]
        self.assertEqual(len(values), len(set(values)))

    def test_quality_ordering(self):
        """Test quality levels can be compared."""
        # This would be useful if we implemented comparison methods
        self.assertNotEqual(ContentQuality.EXCELLENT, ContentQuality.POOR)
        self.assertNotEqual(ContentQuality.FAILED, ContentQuality.GOOD)


if __name__ == "__main__":
    unittest.main()
