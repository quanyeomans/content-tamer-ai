"""
Content Service

Main orchestrating service for all content-related operations.
Coordinates extraction, enhancement, and metadata analysis.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from .enhancement_service import EnhancementService
from .extraction_service import ContentQuality, ExtractedContent, ExtractionService
from .metadata_service import MetadataService


class ContentService:
    """Main service coordinating all content domain operations."""

    def __init__(self, ocr_lang: str = "eng", max_content_length: int = 2000):
        """Initialize content service.

        Args:
            ocr_lang: OCR language for text extraction
            max_content_length: Maximum content length for AI processing
        """
        self.ocr_lang = ocr_lang
        self.max_content_length = max_content_length
        self.logger = logging.getLogger(__name__)

        # Initialize domain services
        self.extraction_service = ExtractionService(ocr_lang)
        self.enhancement_service = EnhancementService(max_content_length)
        self.metadata_service = MetadataService()

    def process_document_complete(self, file_path: str) -> Dict[str, Any]:
        """Complete document processing: extraction + enhancement + metadata.

        Args:
            file_path: Path to document to process

        Returns:
            Dictionary with all processing results
        """
        try:
            # Step 1: Extract content
            extracted = self.extraction_service.extract_from_file(file_path)

            # Step 2: Enhance content if extraction was successful
            enhancement = None
            if extracted.quality != ContentQuality.FAILED:
                enhancement = self.enhancement_service.enhance_content(extracted)

            # Step 3: Extract metadata
            metadata = self.metadata_service.analyze_document(file_path, extracted)

            # Prepare AI-ready content
            ai_content = ""
            if enhancement and enhancement.quality_after != ContentQuality.FAILED:
                ai_content = enhancement.enhanced_content
            elif extracted.quality != ContentQuality.FAILED:
                ai_content = self.enhancement_service.prepare_for_ai_processing(extracted)

            return {
                "file_path": file_path,
                "extraction": extracted,
                "enhancement": enhancement,
                "metadata": metadata,
                "ai_ready_content": ai_content,
                "success": extracted.quality != ContentQuality.FAILED,
                "ready_for_ai": bool(ai_content and len(ai_content.strip()) > 10),
            }

        except Exception as e:
            self.logger.error("Complete document processing failed for %s: %s", file_path, e)
            return {
                "file_path": file_path,
                "extraction": ExtractedContent(
                    text=f"Processing error: {e}",
                    quality=ContentQuality.FAILED,
                    error_message=str(e),
                ),
                "enhancement": None,
                "metadata": None,
                "ai_ready_content": "",
                "success": False,
                "ready_for_ai": False,
                "error": str(e),
            }

    def batch_process_documents(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """Process multiple documents in batch.

        Args:
            file_paths: List of file paths to process

        Returns:
            Dictionary mapping file paths to processing results
        """
        results = {}

        self.logger.info("Starting batch processing of %d documents", len(file_paths))

        for i, file_path in enumerate(file_paths):
            try:
                self.logger.debug("Processing %d/%d: %s", i + 1, len(file_paths), file_path)
                result = self.process_document_complete(file_path)
                results[file_path] = result

            except Exception as e:
                self.logger.error("Batch processing failed for %s: %s", file_path, e)
                results[file_path] = {"file_path": file_path, "success": False, "error": str(e)}

        # Log batch summary
        successful = sum(1 for result in results.values() if result.get("success", False))
        self.logger.info("Batch processing complete: %d/%d successful", successful, len(file_paths))

        return results

    def get_ai_ready_content(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Get content ready for AI processing (legacy interface).

        Args:
            file_path: Path to document

        Returns:
            Tuple of (text_content, image_data_b64)
        """
        try:
            result = self.process_document_complete(file_path)

            if result["success"]:
                text_content = result["ai_ready_content"]
                image_data = result["extraction"].image_data if result["extraction"] else None
                return text_content, image_data
            error_msg = result.get("error", "Processing failed")
            return f"Error: {error_msg}", None

        except Exception as e:
            self.logger.error("AI content preparation failed for %s: %s", file_path, e)
            return f"Error: {e}", None

    def validate_file_for_processing(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate if file can be processed.

        Args:
            file_path: Path to file to validate

        Returns:
            Tuple of (can_process, error_message)
        """
        try:
            # Check file exists
            if not os.path.isfile(file_path):
                return False, f"File not found: {file_path}"

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "File is empty"
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                return False, f"File too large: {file_size / 1024 / 1024:.1f}MB (50MB limit)"

            # Check if we have a processor for this file type
            supported_types = self.extraction_service.get_supported_file_types()
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext not in supported_types:
                return False, f"Unsupported file type: {file_ext}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {e}"

    def get_service_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive service capabilities."""
        return {
            "extraction": self.extraction_service.get_processor_capabilities(),
            "enhancement": self.enhancement_service.get_enhancement_statistics(),
            "metadata": self.metadata_service.get_service_statistics(),
            "supported_file_types": self.extraction_service.get_supported_file_types(),
            "ocr_language": self.ocr_lang,
            "max_content_length": self.max_content_length,
        }

    def get_processing_summary(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of batch processing results.

        Args:
            results: Results from batch_process_documents

        Returns:
            Processing summary statistics
        """
        total_files = len(results)
        successful_files = sum(1 for r in results.values() if r.get("success", False))
        failed_files = total_files - successful_files

        # Quality distribution
        quality_counts = {}
        extraction_methods = {}
        file_types = {}

        for result in results.values():
            if result.get("extraction"):
                quality = result["extraction"].quality.value
                quality_counts[quality] = quality_counts.get(quality, 0) + 1

                method = result["extraction"].extraction_method
                extraction_methods[method] = extraction_methods.get(method, 0) + 1

                file_type = result["extraction"].file_type
                file_types[file_type] = file_types.get(file_type, 0) + 1

        return {
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "success_rate": (
                f"{(successful_files / total_files * 100):.1f}%" if total_files > 0 else "0%"
            ),
            "quality_distribution": quality_counts,
            "extraction_methods": extraction_methods,
            "file_types": file_types,
        }
