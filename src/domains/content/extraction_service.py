"""
Content Extraction Service

Unified document content extraction supporting multiple file types.
Consolidates extraction logic from content_processors.py into domain service.
"""

import os
import base64
import io
from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Import security utilities from shared infrastructure
try:
    from ...shared.infrastructure.security import (
        ContentValidator as SecurityContentValidator,
        PathValidator as SecurityPathValidator,
        PDFAnalyzer as SecurityPDFAnalyzer,
        SecurityError as SecuritySecurityError,
        ThreatLevel,
    )
    # Create local aliases to avoid type conflicts
    ContentValidator = SecurityContentValidator  # type: ignore[assignment]
    PathValidator = SecurityPathValidator  # type: ignore[assignment]
    PDFAnalyzer = SecurityPDFAnalyzer  # type: ignore[assignment]
    SecurityError = SecuritySecurityError  # type: ignore[assignment]
except ImportError:
    # Fallback for when security module not available
    class ContentValidator:
        @staticmethod
        def validate_extracted_content(content: str, file_path: str) -> str:
            return content

    class PathValidator:
        @staticmethod
        def validate_file_path(path: str) -> bool:
            return True

    class PDFAnalyzer:
        def analyze_pdf(self, file_path: str) -> None:
            pass

    class SecurityError(Exception):
        pass


class ContentQuality(Enum):
    """Quality levels for extracted content."""
    EXCELLENT = "excellent"  # Clean, complete text extraction
    GOOD = "good"           # Mostly clean with minor issues
    FAIR = "fair"           # Readable but with OCR artifacts
    POOR = "poor"           # Fragmented or low quality
    FAILED = "failed"       # No usable content extracted


@dataclass
class ExtractedContent:
    """Result of content extraction."""
    text: str
    image_data: Optional[str] = None  # Base64 encoded
    quality: ContentQuality = ContentQuality.FAILED
    extraction_method: str = "unknown"
    file_type: str = "unknown"
    metadata: Optional[Dict[str, Any]] = None
    security_warnings: Optional[List[str]] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
        if self.security_warnings is None:
            self.security_warnings = []


class ContentProcessor(ABC):
    """Abstract base for content processors."""

    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the file."""
        pass

    @abstractmethod
    def extract_content(self, file_path: str) -> ExtractedContent:
        """Extract content from the file."""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        pass


class PDFContentProcessor(ContentProcessor):
    """PDF content extraction with multiple methods."""

    def __init__(self, ocr_lang: str = "eng"):
        """Initialize PDF processor.

        Args:
            ocr_lang: OCR language code (e.g., 'eng', 'eng+fra')
        """
        self.ocr_lang = ocr_lang
        self.logger = logging.getLogger(__name__)

        # Import dependencies with availability checking
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check availability of PDF processing dependencies."""
        # PyMuPDF
        try:
            import fitz
            self.have_pymupdf = True
        except ImportError:
            self.have_pymupdf = False

        # Tesseract OCR
        try:
            import pytesseract
            from PIL import Image
            from ...shared.infrastructure.dependency_manager import get_dependency_manager

            dep_manager = get_dependency_manager()
            tesseract_path = dep_manager.find_dependency("tesseract")

            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                self.have_tesseract = True
            else:
                self.have_tesseract = False
        except ImportError:
            self.have_tesseract = False

    def can_process(self, file_path: str) -> bool:
        """Check if file is a PDF."""
        return file_path.lower().endswith(".pdf")

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return [".pdf"]

    def extract_content(self, file_path: str) -> ExtractedContent:
        """Extract content from PDF with security validation."""
        try:
            # Security validation
            if not self._validate_file_security(file_path):
                return ExtractedContent(
                    text="Security validation failed",
                    quality=ContentQuality.FAILED,
                    error_message="File failed security validation"
                )

            # Try multiple extraction methods in order of preference
            methods = [
                ("pymupdf_text", self._extract_with_pymupdf),
                ("pypdf_text", self._extract_with_pypdf),
                ("ocr_extraction", self._extract_with_ocr)
            ]

            best_result = None

            for method_name, method_func in methods:
                if not self._method_available(method_name):
                    continue

                try:
                    result = method_func(file_path)
                    if result and result.quality != ContentQuality.FAILED:
                        result.extraction_method = method_name

                        # Return first successful extraction
                        if result.quality in [ContentQuality.EXCELLENT, ContentQuality.GOOD]:
                            return result

                        # Keep best result as fallback
                        if best_result is None or result.quality.value > best_result.quality.value:
                            best_result = result

                except Exception as e:
                    self.logger.warning(f"Extraction method {method_name} failed: {e}")
                    continue

            # Return best result found, or failure
            if best_result:
                return best_result

            return ExtractedContent(
                text="No extraction method succeeded",
                quality=ContentQuality.FAILED,
                error_message="All extraction methods failed"
            )

        except Exception as e:
            self.logger.error(f"PDF extraction failed for {file_path}: {e}")
            return ExtractedContent(
                text=f"Extraction error: {e}",
                quality=ContentQuality.FAILED,
                error_message=str(e)
            )

    def _validate_file_security(self, file_path: str) -> bool:
        """Validate file security before processing."""
        try:
            # Basic file validation
            if not os.path.isfile(file_path):
                return False

            # Check file size (50MB limit for security)
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                self.logger.warning(f"File too large: {file_path} ({file_size / 1024 / 1024:.1f}MB)")
                return False

            if file_size == 0:
                return False

            # Perform PDF threat analysis
            try:
                analyzer = PDFAnalyzer()
                analyzer.analyze_pdf(file_path)
                # Continue processing regardless of threat level (non-destructive approach)
                return True
            except (NameError, Exception) as e:
                self.logger.warning(f"PDF security analysis failed: {e}")
                return True  # Allow processing if security analysis fails

        except Exception as e:
            self.logger.error(f"Security validation error for {file_path}: {e}")
            return False

    def _method_available(self, method_name: str) -> bool:
        """Check if extraction method is available."""
        if method_name == "pymupdf_text":
            return self.have_pymupdf
        elif method_name == "pypdf_text":
            return True  # pypdf is always available
        elif method_name == "ocr_extraction":
            return self.have_tesseract and self.have_pymupdf
        return False

    def _extract_with_pymupdf(self, file_path: str) -> ExtractedContent:
        """Extract content using PyMuPDF."""
        if not self.have_pymupdf:
            raise RuntimeError("PyMuPDF not available")

        import fitz

        try:
            doc = fitz.open(file_path)
            text_parts = []
            image_data = None

            # Extract text from all pages
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()  # type: ignore[attr-defined]
                if text.strip():
                    text_parts.append(text)

                # Get image of first page for vision models
                if page_num == 0:
                    image_data = self._render_page_as_image(page)

            # Get page count before closing document
            page_count = len(doc) 
            doc.close()

            full_text = "\n".join(text_parts)

            # Assess quality
            quality = self._assess_text_quality(full_text)

            return ExtractedContent(
                text=full_text,
                image_data=image_data,
                quality=quality,
                extraction_method="pymupdf",
                file_type="pdf",
                metadata={"page_count": page_count, "method": "fitz"}
            )

        except Exception as e:
            raise RuntimeError(f"PyMuPDF extraction failed: {e}")

    def _extract_with_pypdf(self, file_path: str) -> ExtractedContent:
        """Extract content using pypdf."""
        import pypdf
        from pypdf.errors import PdfReadError

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    return ExtractedContent(
                        text="Error: PDF is encrypted and cannot be processed",
                        quality=ContentQuality.FAILED,
                        error_message="PDF is encrypted"
                    )

                # Extract text from all pages
                text_parts = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)

                full_text = "\n".join(text_parts)
                quality = self._assess_text_quality(full_text)

                return ExtractedContent(
                    text=full_text,
                    quality=quality,
                    extraction_method="pypdf",
                    file_type="pdf",
                    metadata={"page_count": len(pdf_reader.pages), "method": "pypdf"}
                )

        except PdfReadError as e:
            return ExtractedContent(
                text=f"Error: PDF read error - {e}",
                quality=ContentQuality.FAILED,
                error_message=str(e)
            )
        except Exception as e:
            raise RuntimeError(f"pypdf extraction failed: {e}")

    def _extract_with_ocr(self, file_path: str) -> ExtractedContent:
        """Extract content using OCR."""
        if not (self.have_pymupdf and self.have_tesseract):
            raise RuntimeError("OCR dependencies not available")

        import fitz
        import pytesseract
        from PIL import Image

        try:
            doc = fitz.open(file_path)
            text_parts = []

            # Process up to 4 pages for OCR
            max_pages = min(4, len(doc))

            for page_num in range(max_pages):
                page = doc[page_num]

                # Render page as image
                mat = fitz.Matrix(3.5, 3.5)  # High resolution for OCR
                pix = page.get_pixmap(matrix=mat)  # type: ignore[attr-defined]
                img_data = pix.tobytes("png")

                # Convert to PIL Image
                pil_image = Image.open(io.BytesIO(img_data))

                # Extract text with OCR
                ocr_text = pytesseract.image_to_string(
                    pil_image,
                    lang=self.ocr_lang,
                    config='--oem 3 --psm 6'
                )

                if ocr_text.strip():
                    text_parts.append(ocr_text)

            doc.close()

            full_text = "\n".join(text_parts)
            quality = self._assess_ocr_quality(full_text)

            return ExtractedContent(
                text=full_text,
                quality=quality,
                extraction_method="ocr",
                file_type="pdf",
                metadata={"pages_processed": max_pages, "ocr_lang": self.ocr_lang}
            )

        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {e}")

    def _render_page_as_image(self, page) -> Optional[str]:
        """Render page as base64 encoded image."""
        try:
            import fitz
            mat = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # type: ignore[attr-defined]
            img_data = mat.tobytes("png")
            return base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            self.logger.warning(f"Page rendering failed: {e}")
            return None

    def _assess_text_quality(self, text: str) -> ContentQuality:
        """Assess quality of extracted text."""
        if not text or len(text.strip()) < 10:
            return ContentQuality.FAILED

        # Check for common extraction quality indicators
        text_lower = text.lower()

        # Poor quality indicators
        poor_indicators = len([
            indicator for indicator in [
                text.count('�') > len(text) * 0.01,  # Many replacement characters
                text.count('\n') > len(text) * 0.1,   # Too many line breaks
                len(text.split()) < len(text) * 0.1,  # Too few words relative to characters
                sum(1 for c in text if not c.isalnum() and c not in ' \n\t.,!?') > len(text) * 0.1  # Too many special chars
            ] if indicator
        ])

        if poor_indicators >= 2:
            return ContentQuality.POOR
        elif poor_indicators == 1:
            return ContentQuality.FAIR

        # Good quality indicators
        has_sentences = '.' in text and len(text.split('.')) > 1
        has_reasonable_length = 50 <= len(text) <= 50000
        has_readable_words = len([word for word in text.split() if len(word) >= 3]) > 10

        if has_sentences and has_reasonable_length and has_readable_words:
            return ContentQuality.EXCELLENT
        elif has_reasonable_length and has_readable_words:
            return ContentQuality.GOOD
        else:
            return ContentQuality.FAIR

    def _assess_ocr_quality(self, text: str) -> ContentQuality:
        """Assess quality of OCR-extracted text."""
        base_quality = self._assess_text_quality(text)

        # OCR typically produces lower quality, so adjust downwards
        if base_quality == ContentQuality.EXCELLENT:
            return ContentQuality.GOOD
        elif base_quality == ContentQuality.GOOD:
            return ContentQuality.FAIR
        else:
            return base_quality


class ImageContentProcessor(ContentProcessor):
    """Image content extraction using OCR."""

    def __init__(self, ocr_lang: str = "eng"):
        """Initialize image processor."""
        self.ocr_lang = ocr_lang
        self.logger = logging.getLogger(__name__)
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check OCR dependencies."""
        try:
            import pytesseract
            from PIL import Image
            from ...shared.infrastructure.dependency_manager import get_dependency_manager

            dep_manager = get_dependency_manager()
            tesseract_path = dep_manager.find_dependency("tesseract")

            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                self.have_tesseract = True
            else:
                self.have_tesseract = False
        except ImportError:
            self.have_tesseract = False

    def can_process(self, file_path: str) -> bool:
        """Check if file is a supported image."""
        supported_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif']
        return any(file_path.lower().endswith(ext) for ext in supported_extensions)

    def get_supported_extensions(self) -> List[str]:
        """Get supported image extensions."""
        return ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif']

    def extract_content(self, file_path: str) -> ExtractedContent:
        """Extract text from image using OCR."""
        if not self.have_tesseract:
            return ExtractedContent(
                text="OCR not available - install Tesseract",
                quality=ContentQuality.FAILED,
                error_message="Tesseract OCR not available"
            )

        try:
            import pytesseract
            from PIL import Image

            # Load and process image
            image = Image.open(file_path)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Extract text with OCR
            ocr_text = pytesseract.image_to_string(
                image,
                lang=self.ocr_lang,
                config='--oem 3 --psm 6'
            )

            # Convert image to base64 for vision models
            image_b64 = self._image_to_base64(image)

            # Assess quality
            quality = self._assess_ocr_quality(ocr_text)

            return ExtractedContent(
                text=ocr_text,
                image_data=image_b64,
                quality=quality,
                extraction_method="tesseract_ocr",
                file_type="image",
                metadata={
                    "image_size": image.size,
                    "image_mode": image.mode,
                    "ocr_lang": self.ocr_lang
                }
            )

        except Exception as e:
            self.logger.error(f"Image OCR failed for {file_path}: {e}")
            return ExtractedContent(
                text=f"OCR error: {e}",
                quality=ContentQuality.FAILED,
                error_message=str(e)
            )

    def _image_to_base64(self, image) -> str:
        """Convert PIL image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')

    def _assess_ocr_quality(self, text: str) -> ContentQuality:
        """Assess OCR text quality."""
        if not text or len(text.strip()) < 5:
            return ContentQuality.FAILED

        # OCR-specific quality checks
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        if len(non_empty_lines) < 2:
            return ContentQuality.POOR

        # Check for readable words
        words = text.split()
        readable_words = [word for word in words if len(word) >= 3 and word.isalpha()]

        if len(readable_words) < 5:
            return ContentQuality.POOR
        elif len(readable_words) < 15:
            return ContentQuality.FAIR
        else:
            return ContentQuality.GOOD


class ExtractionService:
    """Main content extraction service."""

    def __init__(self, ocr_lang: str = "eng"):
        """Initialize extraction service.

        Args:
            ocr_lang: OCR language code for text extraction
        """
        self.ocr_lang = ocr_lang
        self.logger = logging.getLogger(__name__)

        # Initialize processors
        self.processors = [
            PDFContentProcessor(ocr_lang),
            ImageContentProcessor(ocr_lang)
        ]

        # Create processor mapping
        self._processor_map = {}
        for processor in self.processors:
            for ext in processor.get_supported_extensions():
                self._processor_map[ext.lower()] = processor

    def extract_from_file(self, file_path: str) -> ExtractedContent:
        """Extract content from any supported file type.

        Args:
            file_path: Path to file to process

        Returns:
            ExtractedContent with extracted text and metadata
        """
        try:
            # Find appropriate processor
            processor = self._find_processor_for_file(file_path)
            if not processor:
                return ExtractedContent(
                    text="Unsupported file type",
                    quality=ContentQuality.FAILED,
                    error_message=f"No processor available for {file_path}"
                )

            # Extract content
            result = processor.extract_content(file_path)

            # Validate and sanitize content
            if result.quality != ContentQuality.FAILED and result.text:
                try:
                    validated_content = ContentValidator.validate_extracted_content(
                        result.text, file_path
                    )
                    result.text = validated_content
                except Exception as e:
                    if result.security_warnings is not None:
                        result.security_warnings.append(f"Content validation warning: {e}")

            return result

        except Exception as e:
            self.logger.error(f"Content extraction failed for {file_path}: {e}")
            return ExtractedContent(
                text=f"Extraction error: {e}",
                quality=ContentQuality.FAILED,
                error_message=str(e)
            )

    def _find_processor_for_file(self, file_path: str) -> Optional[ContentProcessor]:
        """Find appropriate processor for file."""
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        return self._processor_map.get(ext)

    def get_supported_file_types(self) -> List[str]:
        """Get list of all supported file extensions."""
        return list(self._processor_map.keys())

    def get_processor_capabilities(self) -> Dict[str, Any]:
        """Get information about available processors."""
        capabilities = {}

        for processor in self.processors:
            processor_name = type(processor).__name__
            capabilities[processor_name] = {
                "supported_extensions": processor.get_supported_extensions(),
                "available": True  # If processor is instantiated, it's available
            }

        return capabilities

    def batch_extract(self, file_paths: List[str]) -> Dict[str, ExtractedContent]:
        """Extract content from multiple files.

        Args:
            file_paths: List of file paths to process

        Returns:
            Dictionary mapping file paths to extraction results
        """
        results = {}

        for file_path in file_paths:
            try:
                result = self.extract_from_file(file_path)
                results[file_path] = result

                self.logger.debug(f"Extracted content from {file_path}: {result.quality.value}")

            except Exception as e:
                self.logger.error(f"Batch extraction failed for {file_path}: {e}")
                results[file_path] = ExtractedContent(
                    text=f"Batch extraction error: {e}",
                    quality=ContentQuality.FAILED,
                    error_message=str(e)
                )

        return results
