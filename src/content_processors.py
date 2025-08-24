"""
Content processing implementations for different file types.

This module contains file type processors that extract content and metadata
for AI-based filename generation. Designed for easy extension to new file types.
"""

import base64
import io
import os
import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

import PyPDF2
from PyPDF2.errors import PdfReadError

# Optional dependencies for OCR / rendering
HAVE_PYMUPDF = False
HAVE_TESSERACT = False
try:
    import fitz  # PyMuPDF

    HAVE_PYMUPDF = True
except ImportError:
    HAVE_PYMUPDF = False

try:
    import pytesseract
    from PIL import Image

    HAVE_TESSERACT = True
except ImportError:
    HAVE_TESSERACT = False

# OCR configuration constants
OCR_LANG = "eng"  # Tesseract language code (e.g., 'eng', 'eng+ind')
OCR_PAGES = 4  # Number of pages to process for OCR
OCR_ZOOM = 3.5  # PDF-to-image zoom factor (higher = better quality)
OCR_USE_OSD = True  # Enable Tesseract orientation/script detection


class ContentProcessor(ABC):
    """Abstract base class for content processors."""

    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Return True if this processor can handle the given file."""
        pass

    @abstractmethod
    def extract_content(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extract text content and optional image from file.

        Returns:
            Tuple of (text_content, base64_encoded_image)
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return the file extension this processor handles."""
        pass


class PDFProcessor(ContentProcessor):
    """Processes PDF files with multiple extraction methods."""

    def __init__(self, ocr_lang: str = OCR_LANG) -> None:
        self.ocr_lang = ocr_lang

    def can_process(self, file_path: str) -> bool:
        """Check if file is a PDF."""
        return file_path.lower().endswith(".pdf")

    def get_file_extension(self) -> str:
        """Return PDF extension."""
        return ".pdf"

    def extract_content(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extract all possible content from a PDF with security validation."""
        # Validate file path and content
        try:
            from utils.security import PathValidator, ContentValidator, SecurityError, PDFAnalyzer, ThreatLevel
        except ImportError:
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            from utils.security import PathValidator, ContentValidator, SecurityError, PDFAnalyzer, ThreatLevel
        
        try:
            # Basic file validation - check it's actually a file and reasonable size
            if not os.path.isfile(file_path):
                return "Error: File does not exist or is not a regular file", None
            
            # Check file size (50MB limit for security)
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                return "Error: File too large for processing (50MB limit)", None
                
            if file_size == 0:
                return "Error: File is empty", None
            
            # Perform PDF threat analysis
            analyzer = PDFAnalyzer()
            threat_analysis = analyzer.analyze_pdf(file_path)
            
            # Log threat analysis results (avoiding unicode in print for Windows compatibility)
            if threat_analysis.should_warn:
                print(f"PDF Security Warning [{threat_analysis.threat_level.value.upper()}]: {threat_analysis.summary}")
            elif threat_analysis.threat_level != ThreatLevel.SAFE:
                print(f"PDF Analysis [{threat_analysis.threat_level.value.upper()}]: {threat_analysis.summary}")
            
            # Continue with content extraction regardless of threat level
            # (non-destructive approach - we warn but don't block)
            
            # Extract content using existing method
            content, image_b64 = self._extract_text_and_image(
                file_path, min_len=40, ocr_lang=self.ocr_lang
            )
            
            # Validate extracted content for security
            if content and not content.startswith("Error:"):
                content = ContentValidator.validate_extracted_content(content, file_path)
            
            return content, image_b64
            
        except SecurityError as e:
            return f"Security error: {e}", None
        except Exception as e:
            return f"Error processing file: {str(e)}", None

    def _extract_text_and_image(
        self, pdf_path: str, min_len: int = 40, ocr_lang: str = OCR_LANG
    ) -> Tuple[str, Optional[str]]:
        """
        Extracts all possible content from a PDF, including text and images.
        It tries multiple methods to ensure the best possible result.
        Returns the extracted text and the first page rendered as an image.
        """
        # 1. Try to get text using PyMuPDF, which is fast.
        text = self._fitz_text(pdf_path) if HAVE_PYMUPDF else ""

        # 2. If PyMuPDF fails, try PyPDF2 as a fallback.
        if not text:
            pypdf2_text = self._pypdf2_text(pdf_path)
            # If PyPDF2 returns an error (e.g., encrypted PDF), stop and return the error.
            if pypdf2_text.startswith("Error"):
                return pypdf2_text, None
            text = pypdf2_text or ""

        # 3. Render the first page as an image, to be used by vision-capable AI models.
        img_b64 = (
            self._fitz_render_png_b64(pdf_path, 0, OCR_ZOOM, auto_orient=True)
            if HAVE_PYMUPDF
            else None
        )

        # 4. If the extracted text is very short, it might be a scanned PDF. Try OCR.
        if len(text) < min_len:
            ocr_text = self._ocr_tesseract_from_pdf(pdf_path, lang=ocr_lang)
            if len(ocr_text) > len(text):
                text = ocr_text

        return text.strip(), img_b64

    def _fitz_text(self, pdf_path: str, max_pages: int = 5) -> str:
        """Extracts text from a PDF using the PyMuPDF library (fitz), which is fast and efficient."""
        if not HAVE_PYMUPDF:
            return ""
        try:
            doc = fitz.open(pdf_path)
            chunks: List[str] = []
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                # Using "text" mode helps maintain the original reading order of the document.
                chunks.append(page.get_text("text") or "")
            return "\n".join(chunks).strip()
        except RuntimeError:
            return ""

    def _fitz_render_png_b64(
        self,
        pdf_path: str,
        page_index: int = 0,
        zoom: float = OCR_ZOOM,
        auto_orient: bool = True,
    ) -> Optional[str]:
        if not HAVE_PYMUPDF:
            return None
        try:
            doc = fitz.open(pdf_path)
            if page_index >= len(doc):
                return None
            page = doc[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            png_bytes = pix.tobytes("png")

            # If Tesseract is installed, we can automatically detect and correct the image's orientation before processing.
            if HAVE_TESSERACT and auto_orient:
                try:
                    img = Image.open(io.BytesIO(png_bytes))
                    angle = self._detect_osd_angle(img)
                    img = self._rotate_image(img, angle)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    png_bytes = buf.getvalue()
                except (IOError, ValueError):
                    pass

            b64 = base64.b64encode(png_bytes).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except RuntimeError:
            return None

    def _ocr_tesseract_from_pdf(
        self,
        pdf_path: str,
        pages: int = OCR_PAGES,
        zoom: float = OCR_ZOOM,
        lang: str = OCR_LANG,
    ) -> str:
        if not (HAVE_PYMUPDF and HAVE_TESSERACT):
            return ""
        try:
            doc = fitz.open(pdf_path)
        except RuntimeError:
            return ""
        out = []
        for i, page in enumerate(doc):
            if i >= pages:
                break
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                angle = self._detect_osd_angle(img)
                img = self._rotate_image(img, angle)
                text = pytesseract.image_to_string(
                    img, lang=lang, config="--psm 6 --oem 1"
                )
                out.append(text or "")
            except (RuntimeError, IOError, ValueError, pytesseract.TesseractError):
                continue
        return "\n".join(out).strip()

    def _pypdf2_text(self, pdf_path: str, max_pages: Optional[int] = None) -> str:
        """Extracts text from a PDF's text layer using the PyPDF2 library. This is a fallback method."""
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    return "Error: PDF is encrypted and cannot be processed without a password."

                total_pages = len(reader.pages)
                if max_pages is None and total_pages > 100:
                    max_pages = 100
                    print(
                        f"Warning: PDF has {total_pages} pages. Limiting to first {max_pages} pages for performance."
                    )

                pages_to_process = (
                    reader.pages
                    if not max_pages or total_pages <= max_pages
                    else reader.pages[:max_pages]
                )

                content = []
                for page in pages_to_process:
                    try:
                        page_text = page.extract_text() or ""
                        content.append(page_text)
                    except (TypeError, KeyError, ValueError) as e:
                        print(
                            f"Warning: Could not extract text from a page due to malformed content: {str(e)}"
                        )

                joined = (" ".join(content)).strip()
                if not joined:
                    return ""
                from utils.text_utils import (  # Import here to avoid circular import
                    truncate_content_to_token_limit,
                )

                return truncate_content_to_token_limit(
                    joined, 20000
                )  # Increased for better context
        except (IOError, OSError) as e:
            return f"Error opening PDF: {str(e)}"
        except PdfReadError as e:
            return f"Error reading PDF: {str(e)}"

    def _detect_osd_angle(self, img: Any) -> int:
        """Uses Tesseract's Orientation and Script Detection (OSD) to find out if an image is rotated."""
        if not HAVE_TESSERACT or not OCR_USE_OSD:
            return 0
        try:
            osd = pytesseract.image_to_osd(img)
            m = re.search(r"Rotate:\s*(\d+)", osd)
            return (int(m.group(1)) % 360) if m else 0
        except pytesseract.TesseractError:
            return 0

    def _rotate_image(self, img: Any, angle: int) -> Any:
        if not angle:
            return img
        # Tesseract's angle is clockwise, but the Python Imaging Library (PIL) rotates counter-clockwise, so we invert the angle.
        return img.rotate(360 - angle, expand=True)


class ImageProcessor(ContentProcessor):
    """Processes image files (screenshots, photos, etc.)."""

    def __init__(self, ocr_lang: str = OCR_LANG) -> None:
        self.ocr_lang = ocr_lang
        self.supported_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"}

    def can_process(self, file_path: str) -> bool:
        """Check if file is a supported image format."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions

    def get_file_extension(self) -> str:
        """Return primary image extension."""
        return ".png"

    def extract_content(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extract text from image via OCR and return image as base64 with security validation."""
        # Security validation
        try:
            from utils.security import SecurityError
        except ImportError:
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            from utils.security import SecurityError
        
        text = ""
        img_b64 = None

        try:
            # Basic file validation
            if not os.path.isfile(file_path):
                return "Error: File does not exist or is not a regular file", None
            
            # Check file size (10MB limit for images)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                return "Error: Image file too large for processing (10MB limit)", None
                
            if file_size == 0:
                return "Error: Image file is empty", None

            # Convert image to base64
            with open(file_path, "rb") as img_file:
                img_bytes = img_file.read()
                
                # Validate image header (magic bytes) for security
                if not self._is_valid_image(img_bytes):
                    return "Error: File does not appear to be a valid image", None
                
                img_b64 = f"data:image/png;base64,{base64.b64encode(img_bytes).decode('utf-8')}"

            # Extract text via OCR if available
            if HAVE_TESSERACT:
                try:
                    text = pytesseract.image_to_string(file_path, lang=self.ocr_lang)
                except (pytesseract.TesseractError, Exception):
                    text = ""

            return text.strip(), img_b64

        except (IOError, OSError) as e:
            return f"Error reading image: {str(e)}", None
    
    def _is_valid_image(self, img_bytes: bytes) -> bool:
        """Validate image file by checking magic bytes."""
        if not img_bytes or len(img_bytes) < 8:
            return False
        
        # Check common image format magic bytes
        magic_bytes = {
            b'\xFF\xD8\xFF': 'JPEG',
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'GIF87a': 'GIF87a',
            b'GIF89a': 'GIF89a', 
            b'BM': 'BMP',
            b'II*\x00': 'TIFF (little endian)',
            b'MM\x00*': 'TIFF (big endian)',
            b'RIFF': 'WebP (needs further check)',
        }
        
        for magic, format_name in magic_bytes.items():
            if img_bytes.startswith(magic):
                # Special case for WebP - needs to check for WEBP signature
                if magic == b'RIFF' and len(img_bytes) >= 12:
                    if img_bytes[8:12] == b'WEBP':
                        return True
                    else:
                        continue
                return True
                
        return False


class ContentProcessorFactory:
    """Factory for creating appropriate content processors based on file type."""

    def __init__(self, ocr_lang: str = OCR_LANG) -> None:
        self.ocr_lang = ocr_lang
        self.processors = [
            PDFProcessor(ocr_lang),
            ImageProcessor(ocr_lang),
            # Future: OfficeProcessor, TextProcessor, etc.
        ]

    def get_processor(self, file_path: str) -> Optional[ContentProcessor]:
        """Return appropriate processor for the given file, or None if unsupported."""
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor
        return None

    def get_supported_extensions(self) -> List[str]:
        """Return list of all supported file extensions."""
        extensions = []
        for processor in self.processors:
            if hasattr(processor, "supported_extensions"):
                extensions.extend(processor.supported_extensions)
            else:
                extensions.append(processor.get_file_extension())
        return list(set(extensions))
