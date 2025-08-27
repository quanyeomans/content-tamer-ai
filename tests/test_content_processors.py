"""
Tests for content processing functionality.
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from content_processors import ContentProcessorFactory, ImageProcessor, PDFProcessor


class TestContentProcessorFactory(unittest.TestCase):
    """Test content processor factory."""

    def setUp(self):
        """Set up factory instance."""
        self.factory = ContentProcessorFactory()

    def test_get_processor_pdf(self):
        """Test getting processor for PDF files."""
        processor = self.factory.get_processor("test.pdf")
        self.assertIsInstance(processor, PDFProcessor)

    def test_get_processor_image(self):
        """Test getting processor for image files."""
        test_images = ["test.png", "test.jpg", "test.jpeg", "test.bmp"]
        for image_file in test_images:
            processor = self.factory.get_processor(image_file)
            self.assertIsInstance(processor, ImageProcessor)

    def test_get_processor_unsupported(self):
        """Test getting processor for unsupported file types."""
        processor = self.factory.get_processor("test.txt")
        self.assertIsNone(processor)

    def test_get_supported_extensions(self):
        """Test getting list of supported extensions."""
        extensions = self.factory.get_supported_extensions()
        self.assertIn(".pdf", extensions)
        self.assertIn(".png", extensions)
        self.assertIn(".jpg", extensions)


class TestPDFProcessor(unittest.TestCase):
    """Test PDF processing functionality."""

    def setUp(self):
        """Set up PDF processor."""
        self.processor = PDFProcessor()

    def test_can_process_pdf(self):
        """Test PDF file type detection."""
        self.assertTrue(self.processor.can_process("test.pdf"))
        self.assertTrue(self.processor.can_process("TEST.PDF"))
        self.assertFalse(self.processor.can_process("test.txt"))

    def test_get_file_extension(self):
        """Test getting PDF file extension."""
        self.assertEqual(self.processor.get_file_extension(), ".pdf")

    @patch("content_processors.HAVE_PYMUPDF", True)
    @patch("content_processors.fitz")
    def test_fitz_text_extraction(self, mock_fitz):
        """Test PyMuPDF text extraction."""
        # Mock fitz document and pages
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 content"

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page1, mock_page2]))
        mock_fitz.open.return_value = mock_doc

        result = self.processor._fitz_text("test.pdf")
        self.assertEqual(result, "Page 1 content\nPage 2 content")

    @patch("content_processors.HAVE_PYMUPDF", False)
    def test_fitz_text_extraction_unavailable(self):
        """Test PyMuPDF text extraction when library unavailable."""
        result = self.processor._fitz_text("test.pdf")
        self.assertEqual(result, "")

    @patch("builtins.open", unittest.mock.mock_open(read_data=b"fake pdf"))
    @patch("content_processors.pypdf.PdfReader")
    def test_pypdf_text_extraction(self, mock_reader_class):
        """Test pypdf text extraction."""
        # Mock PDF reader and pages
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted text"

        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        result = self.processor._pypdf_text("test.pdf")
        self.assertIn("Extracted text", result)

    @patch("builtins.open", unittest.mock.mock_open(read_data=b"fake pdf"))
    @patch("content_processors.pypdf.PdfReader")
    def test_pypdf_encrypted_pdf(self, mock_reader_class):
        """Test handling of encrypted PDFs."""
        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_reader_class.return_value = mock_reader

        result = self.processor._pypdf_text("test.pdf")
        self.assertIn("Error: PDF is encrypted", result)

    @patch("content_processors.HAVE_TESSERACT", True)
    @patch("content_processors.pytesseract")
    def test_detect_osd_angle(self, mock_pytesseract):
        """Test orientation and script detection."""
        mock_pytesseract.image_to_osd.return_value = "Rotate: 90\nOther info"

        mock_image = MagicMock()
        result = self.processor._detect_osd_angle(mock_image)
        self.assertEqual(result, 90)

    @patch("content_processors.HAVE_TESSERACT", False)
    def test_detect_osd_angle_unavailable(self):
        """Test OSD when Tesseract unavailable."""
        mock_image = MagicMock()
        result = self.processor._detect_osd_angle(mock_image)
        self.assertEqual(result, 0)

    def test_rotate_image(self):
        """Test image rotation."""
        mock_image = MagicMock()
        mock_image.rotate.return_value = "rotated_image"

        # Test rotation
        result = self.processor._rotate_image(mock_image, 90)
        mock_image.rotate.assert_called_with(270, expand=True)  # 360 - 90

        # Test no rotation needed
        result = self.processor._rotate_image(mock_image, 0)
        self.assertEqual(result, mock_image)

    @patch.object(PDFProcessor, "_fitz_text")
    @patch.object(PDFProcessor, "_pypdf_text")
    @patch.object(PDFProcessor, "_fitz_render_png_b64")
    def test_extract_text_and_image_fitz_success(
        self, mock_render, mock_pypdf, mock_fitz
    ):
        """Test successful extraction using PyMuPDF."""
        mock_fitz.return_value = "Fitz extracted text"
        mock_render.return_value = "base64_image_data"

        text, image = self.processor._extract_text_and_image("test.pdf")

        self.assertEqual(text, "Fitz extracted text")
        self.assertEqual(image, "base64_image_data")
        mock_pypdf.assert_not_called()  # Should not fallback to pypdf

    @patch.object(PDFProcessor, "_fitz_text")
    @patch.object(PDFProcessor, "_pypdf_text")
    @patch.object(PDFProcessor, "_ocr_tesseract_from_pdf")
    def test_extract_text_and_image_ocr_fallback(
        self, mock_ocr, mock_pypdf2, mock_fitz
    ):
        """Test OCR fallback for short text."""
        mock_fitz.return_value = "Short"  # Less than min_len
        mock_pypdf2.return_value = "Short"
        mock_ocr.return_value = "Much longer OCR extracted text content"

        text, image = self.processor._extract_text_and_image("test.pdf", min_len=20)

        self.assertEqual(text, "Much longer OCR extracted text content")


class TestImageProcessor(unittest.TestCase):
    """Test image processing functionality."""

    def setUp(self):
        """Set up image processor."""
        self.processor = ImageProcessor()

    def test_can_process_images(self):
        """Test image file type detection."""
        supported_formats = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"]
        for ext in supported_formats:
            self.assertTrue(self.processor.can_process(f"test{ext}"))
            self.assertTrue(self.processor.can_process(f"TEST{ext.upper()}"))

        self.assertFalse(self.processor.can_process("test.pdf"))
        self.assertFalse(self.processor.can_process("test.txt"))

    def test_get_file_extension(self):
        """Test getting primary image extension."""
        self.assertEqual(self.processor.get_file_extension(), ".png")

    def test_extract_content_success(self):
        """Test successful image content extraction."""
        # Create a temporary image file
        temp_dir = tempfile.mkdtemp()
        try:
            image_path = os.path.join(temp_dir, "test.png")

            # Create a minimal PNG file (1x1 pixel) - using base64 to avoid encoding issues
            import base64

            png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            png_data = base64.b64decode(png_b64)

            with open(image_path, "wb") as f:
                f.write(png_data)

            with patch("content_processors.HAVE_TESSERACT", True), patch(
                "content_processors.pytesseract.image_to_string"
            ) as mock_ocr:
                mock_ocr.return_value = "Extracted text from image"

                text, image_b64 = self.processor.extract_content(image_path)

                self.assertEqual(text, "Extracted text from image")
                self.assertTrue(image_b64.startswith("data:image/png;base64,"))

        finally:
            shutil.rmtree(temp_dir)

    @patch("content_processors.HAVE_TESSERACT", False)
    def test_extract_content_no_tesseract(self):
        """Test image extraction without Tesseract."""
        # Create a temporary image file
        temp_dir = tempfile.mkdtemp()
        try:
            image_path = os.path.join(temp_dir, "test.png")
            with open(image_path, "wb") as f:
                # Write PNG file signature
                f.write(b"\x89PNG\r\n\x1a\n")
                f.write(b"fake image data")

            text, image_b64 = self.processor.extract_content(image_path)

            # With security validation, invalid images return error
            if text.startswith("Error:"):
                self.assertTrue(
                    text.startswith("Error: File does not appear to be a valid image")
                )
                self.assertIsNone(image_b64)
            else:
                self.assertEqual(text, "")  # No OCR available
                self.assertTrue(image_b64.startswith("data:image/png;base64,"))

        finally:
            shutil.rmtree(temp_dir)

    def test_extract_content_file_error(self):
        """Test handling of file read errors."""
        text, image_b64 = self.processor.extract_content("nonexistent.png")

        # Security validation now returns "File does not exist" error
        self.assertTrue(text.startswith("Error: File does not exist"))
        self.assertIsNone(image_b64)


if __name__ == "__main__":
    unittest.main()
