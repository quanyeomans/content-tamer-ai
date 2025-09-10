"""
Metadata Service

Document metadata extraction and analysis.
Provides document properties, structure analysis, and contextual information.
"""

# type: ignore

import datetime
import logging
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .extraction_service import ContentQuality, ExtractedContent


@dataclass
class DocumentMetadata:
    """Comprehensive document metadata."""

    # File system metadata
    file_path: str
    file_name: str
    file_size: int
    file_extension: str
    mime_type: Optional[str]
    creation_date: Optional[datetime.datetime]
    modification_date: Optional[datetime.datetime]

    # Content metadata
    content_length: int
    word_count: int
    line_count: int
    paragraph_count: int

    # Document structure
    has_headers: bool
    has_numbers: bool
    has_dates: bool
    has_currency: bool
    language: Optional[str]

    # Quality indicators
    content_quality: ContentQuality
    readability_score: Optional[float]

    # Extracted entities
    dates_found: List[str]
    numbers_found: List[str]
    currency_found: List[str]

    # Additional properties
    properties: Dict[str, Any]

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.dates_found is None:
            self.dates_found = []
        if self.numbers_found is None:
            self.numbers_found = []
        if self.currency_found is None:
            self.currency_found = []


class MetadataExtractor:
    """Extracts various metadata from documents."""

    def __init__(self):
        """Initialize metadata extractor."""
        self.logger = logging.getLogger(__name__)

    def extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract file system metadata."""
        try:
            file_stat = os.stat(file_path)
            path_obj = Path(file_path)

            return {
                "file_path": file_path,
                "file_name": path_obj.name,
                "file_size": file_stat.st_size,
                "file_extension": path_obj.suffix.lower(),
                "mime_type": mimetypes.guess_type(file_path)[0],
                "creation_date": datetime.datetime.fromtimestamp(file_stat.st_ctime),
                "modification_date": datetime.datetime.fromtimestamp(file_stat.st_mtime),
            }
        except Exception as e:
            self.logger.error(f"Failed to extract file metadata from {file_path}: {e}")
            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "error": str(e),
            }

    def extract_content_metadata(self, text: str) -> Dict[str, Any]:
        """Extract content-based metadata."""
        if not text:
            return {"content_length": 0, "word_count": 0, "line_count": 0, "paragraph_count": 0}

        # Basic counts
        lines = text.split("\n")
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        words = text.split()

        return {
            "content_length": len(text),
            "word_count": len(words),
            "line_count": len(lines),
            "paragraph_count": len(paragraphs),
        }

    def extract_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure."""
        import re

        if not text:
            return {
                "has_headers": False,
                "has_numbers": False,
                "has_dates": False,
                "has_currency": False,
            }

        # Header detection (lines that are short and followed by longer content)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        has_headers = any(
            len(line) < 50 and i < len(lines) - 1 and len(lines[i + 1]) > len(line)
            for i, line in enumerate(lines)
        )

        # Number detection
        has_numbers = bool(re.search(r"\d+", text))

        # Date detection (various formats)
        date_patterns = [
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # MM/DD/YYYY, DD/MM/YYYY
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",  # YYYY/MM/DD
            r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b",
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        ]
        has_dates = any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)

        # Currency detection
        currency_patterns = [
            r"\$\d+",  # $123
            r"USD\s*\d+",  # USD 123
            r"€\d+",  # €123
            r"£\d+",  # £123
            r"\d+\.\d{2}\s*(USD|EUR|GBP|CAD|AUD)",  # 123.45 USD
        ]
        has_currency = any(re.search(pattern, text, re.IGNORECASE) for pattern in currency_patterns)

        return {
            "has_headers": has_headers,
            "has_numbers": has_numbers,
            "has_dates": has_dates,
            "has_currency": has_currency,
        }

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities (dates, numbers, currency) from text."""
        import re

        entities = {"dates_found": [], "numbers_found": [], "currency_found": []}

        if not text:
            return entities

        # Date extraction
        date_patterns = {
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}": "date_slash",
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}": "date_iso",
            r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b": "date_abbrev",
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b": "date_full",
        }

        for pattern, _date_type in date_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["dates_found"].extend(matches)

        # Number extraction (significant numbers, not just any digit)
        number_patterns = [
            r"\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b",  # Formatted numbers
            r"\b\d+\.\d{2}\b",  # Decimal numbers
            r"\b\d{4,}\b",  # Large numbers (years, IDs, etc.)
        ]

        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            entities["numbers_found"].extend(matches)

        # Currency extraction
        currency_patterns = [
            r"\$\d+(?:\.\d{2})?",
            r"USD\s*\d+(?:\.\d{2})?",
            r"€\d+(?:\.\d{2})?",
            r"£\d+(?:\.\d{2})?",
            r"\d+\.\d{2}\s*(?:USD|EUR|GBP|CAD|AUD)",
        ]

        for pattern in currency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["currency_found"].extend(matches)

        # Deduplicate and limit results
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]  # Keep top 10 unique entities

        return entities

    def extract_comprehensive_metadata(
        self, file_path: str, content: ExtractedContent
    ) -> DocumentMetadata:
        """Extract comprehensive metadata from file and content.

        Args:
            file_path: Path to the document file
            content: Extracted content from the file

        Returns:
            DocumentMetadata with comprehensive information
        """
        try:
            # Extract file metadata
            file_meta = self.extract_file_metadata(file_path)
            # Extract content metadata
            content_meta = self.extract_content_metadata(content.text)
            # Extract document structure
            structure_meta = self.extract_document_structure(content.text)
            # Extract entities
            entities = self.extract_entities(content.text)
            # Calculate readability score
            readability = self._calculate_readability_score(content.text)
            return DocumentMetadata(
                # File metadata
                file_path=file_meta.get("file_path", file_path),
                file_name=file_meta.get("file_name", os.path.basename(file_path)),
                file_size=file_meta.get("file_size", 0),
                file_extension=file_meta.get("file_extension", ""),
                mime_type=file_meta.get("mime_type"),
                creation_date=file_meta.get("creation_date"),
                modification_date=file_meta.get("modification_date"),
                # Content metadata
                content_length=content_meta.get("content_length", 0),
                word_count=content_meta.get("word_count", 0),
                line_count=content_meta.get("line_count", 0),
                paragraph_count=content_meta.get("paragraph_count", 0),
                # Document structure
                has_headers=structure_meta.get("has_headers", False),
                has_numbers=structure_meta.get("has_numbers", False),
                has_dates=structure_meta.get("has_dates", False),
                has_currency=structure_meta.get("has_currency", False),
                language=self._detect_language(content.text),
                # Quality
                content_quality=content.quality,
                readability_score=readability,
                # Entities
                dates_found=entities.get("dates_found", []),
                numbers_found=entities.get("numbers_found", []),
                currency_found=entities.get("currency_found", []),
                # Additional properties
                properties={
                    "extraction_method": content.extraction_method,
                    "security_warnings": content.security_warnings,
                    **(content.metadata or {}),
                },
            )

        except Exception as e:
            self.logger.error(f"Metadata extraction failed for {file_path}: {e}")

            # Return minimal metadata on error
            return DocumentMetadata(
                file_path=file_path,
                file_name=os.path.basename(file_path),
                file_size=0,
                file_extension="",
                mime_type=None,
                creation_date=None,
                modification_date=None,
                content_length=0,
                word_count=0,
                line_count=0,
                paragraph_count=0,
                has_headers=False,
                has_numbers=False,
                has_dates=False,
                has_currency=False,
                language=None,
                content_quality=ContentQuality.FAILED,
                readability_score=None,
                dates_found=[],
                numbers_found=[],
                currency_found=[],
                properties={"error": str(e)},
            )

    def _calculate_readability_score(self, text: str) -> Optional[float]:
        """Calculate simple readability score."""
        if not text:
            return None

        try:
            words = text.split()
            sentences = text.count(".") + text.count("!") + text.count("?")

            if sentences == 0:
                return 0.0

            # Simple readability approximation (Flesch-like)
            avg_words_per_sentence = len(words) / sentences
            avg_chars_per_word = sum(len(word) for word in words) / len(words) if words else 0

            # Normalize to 0-100 scale (higher = more readable)
            score = 100 - (avg_words_per_sentence * 1.5) - (avg_chars_per_word * 5)
            return max(0.0, min(100.0, score))

        except Exception as e:
            self.logger.warning(f"Readability calculation failed: {e}")
            return None

    def _detect_language(self, text: str) -> Optional[str]:
        """Detect document language (basic implementation)."""
        if not text or len(text.strip()) < 50:
            return None

        # Simple language detection based on common words
        text_lower = text.lower()

        # English indicators
        english_words = [
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        ]
        english_score = sum(1 for word in english_words if word in text_lower)

        # Spanish indicators
        spanish_words = ["el", "la", "de", "en", "y", "que", "es", "se", "no", "te", "lo", "por"]
        spanish_score = sum(1 for word in spanish_words if word in text_lower)

        # French indicators
        french_words = [
            "le",
            "de",
            "et",
            "à",
            "un",
            "il",
            "être",
            "et",
            "en",
            "avoir",
            "que",
            "pour",
        ]
        french_score = sum(1 for word in french_words if word in text_lower)

        # German indicators
        german_words = [
            "der",
            "die",
            "und",
            "in",
            "den",
            "von",
            "zu",
            "das",
            "mit",
            "sich",
            "des",
            "auf",
        ]
        german_score = sum(1 for word in german_words if word in text_lower)

        scores = {"en": english_score, "es": spanish_score, "fr": french_score, "de": german_score}

        # Return language with highest score if above threshold
        max_score = max(scores.values())
        if max_score >= 3:  # At least 3 matching words
            return max(scores, key=lambda k: scores[k])

        return "unknown"


class MetadataAnalyzer:  # Renamed to avoid duplicate class names
    """Metadata analysis and document type detection service."""

    def __init__(self):
        """Initialize metadata analyzer."""
        self.logger = logging.getLogger(__name__)
        self.extractor = MetadataExtractor()

    def extract_comprehensive_metadata(
        self, file_path: str, content: ExtractedContent
    ) -> DocumentMetadata:
        """Extract comprehensive metadata from file and content.

        Args:
            file_path: Path to the document file
            content: Extracted content from the file

        Returns:
            DocumentMetadata with comprehensive information
        """
        try:
            # Extract file metadata
            file_meta = self.extractor.extract_file_metadata(file_path)
            # Extract content metadata
            content_meta = self.extractor.extract_content_metadata(content.text)
            # Extract document structure
            structure_meta = self.extractor.extract_document_structure(content.text)
            # Extract entities
            entities = self.extractor.extract_entities(content.text)
            # Calculate readability score
            readability = self.extractor._calculate_readability_score(content.text)
            return DocumentMetadata(
                # File metadata
                file_path=file_meta.get("file_path", file_path),
                file_name=file_meta.get("file_name", os.path.basename(file_path)),
                file_size=file_meta.get("file_size", 0),
                file_extension=file_meta.get("file_extension", ""),
                mime_type=file_meta.get("mime_type"),
                creation_date=file_meta.get("creation_date"),
                modification_date=file_meta.get("modification_date"),
                # Content metadata
                content_length=content_meta.get("content_length", 0),
                word_count=content_meta.get("word_count", 0),
                line_count=content_meta.get("line_count", 0),
                paragraph_count=content_meta.get("paragraph_count", 0),
                # Document structure
                has_headers=structure_meta.get("has_headers", False),
                has_numbers=structure_meta.get("has_numbers", False),
                has_dates=structure_meta.get("has_dates", False),
                has_currency=structure_meta.get("has_currency", False),
                language=self.extractor._detect_language(content.text),
                # Quality
                content_quality=content.quality,
                readability_score=readability,
                # Entities
                dates_found=entities.get("dates_found", []),
                numbers_found=entities.get("numbers_found", []),
                currency_found=entities.get("currency_found", []),
                # Additional properties
                properties={
                    "extraction_method": content.extraction_method,
                    "security_warnings": content.security_warnings,
                    **(content.metadata or {}),
                },
            )

        except Exception as e:
            self.logger.error(f"Metadata extraction failed for {file_path}: {e}")

            # Return minimal metadata on error
            return DocumentMetadata(
                file_path=file_path,
                file_name=os.path.basename(file_path),
                file_size=0,
                file_extension="",
                mime_type=None,
                creation_date=None,
                modification_date=None,
                content_length=0,
                word_count=0,
                line_count=0,
                paragraph_count=0,
                has_headers=False,
                has_numbers=False,
                has_dates=False,
                has_currency=False,
                language=None,
                content_quality=ContentQuality.FAILED,
                readability_score=None,
                dates_found=[],
                numbers_found=[],
                currency_found=[],
                properties={"error": str(e)},
            )

    def _calculate_readability_score(self, text: str) -> Optional[float]:
        """Calculate simple readability score."""
        if not text:
            return None

        try:
            words = text.split()
            sentences = text.count(".") + text.count("!") + text.count("?")

            if sentences == 0:
                return 0.0

            # Simple readability approximation (Flesch-like)
            avg_words_per_sentence = len(words) / sentences
            avg_chars_per_word = sum(len(word) for word in words) / len(words) if words else 0

            # Normalize to 0-100 scale (higher = more readable)
            score = 100 - (avg_words_per_sentence * 1.5) - (avg_chars_per_word * 5)
            return max(0.0, min(100.0, score))

        except Exception as e:
            self.logger.warning(f"Readability calculation failed: {e}")
            return None

    def _detect_language(self, text: str) -> Optional[str]:
        """Detect document language (basic implementation)."""
        if not text or len(text.strip()) < 50:
            return None

        # Simple language detection based on common words
        text_lower = text.lower()

        # English indicators
        english_words = [
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        ]
        english_score = sum(1 for word in english_words if word in text_lower)

        # Spanish indicators
        spanish_words = ["el", "la", "de", "en", "y", "que", "es", "se", "no", "te", "lo", "por"]
        spanish_score = sum(1 for word in spanish_words if word in text_lower)

        # French indicators
        french_words = [
            "le",
            "de",
            "et",
            "à",
            "un",
            "il",
            "être",
            "et",
            "en",
            "avoir",
            "que",
            "pour",
        ]
        french_score = sum(1 for word in french_words if word in text_lower)

        # German indicators
        german_words = [
            "der",
            "die",
            "und",
            "in",
            "den",
            "von",
            "zu",
            "das",
            "mit",
            "sich",
            "des",
            "auf",
        ]
        german_score = sum(1 for word in german_words if word in text_lower)

        scores = {"en": english_score, "es": spanish_score, "fr": french_score, "de": german_score}

        # Return language with highest score if above threshold
        max_score = max(scores.values())
        if max_score >= 3:  # At least 3 matching words
            return max(scores, key=lambda k: scores[k])

        return "unknown"

    def analyze_document_type(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Analyze document type based on metadata."""
        type_indicators = {}
        confidence_scores = {}

        # Financial document indicators
        financial_score = 0
        if metadata.has_currency:
            financial_score += 0.4
        if metadata.has_numbers:
            financial_score += 0.2
        if any(
            word in metadata.file_name.lower()
            for word in ["invoice", "bill", "statement", "receipt"]
        ):
            financial_score += 0.4

        confidence_scores["financial"] = financial_score

        # Legal document indicators
        legal_score = 0
        legal_words = ["contract", "agreement", "terms", "conditions", "legal", "law", "clause"]
        if any(word in metadata.file_name.lower() for word in legal_words):
            legal_score += 0.5
        if metadata.word_count > 500:  # Legal docs tend to be longer
            legal_score += 0.2
        if metadata.has_dates:
            legal_score += 0.2

        confidence_scores["legal"] = legal_score

        # Personal document indicators
        personal_score = 0
        personal_words = ["personal", "private", "medical", "health", "family"]
        if any(word in metadata.file_name.lower() for word in personal_words):
            personal_score += 0.6
        if metadata.file_size < 1024 * 1024:  # Smaller files often personal
            personal_score += 0.2

        confidence_scores["personal"] = personal_score

        # Technical document indicators
        technical_score = 0
        technical_words = ["manual", "guide", "documentation", "spec", "technical", "api"]
        if any(word in metadata.file_name.lower() for word in technical_words):
            technical_score += 0.5
        if metadata.word_count > 1000:  # Technical docs tend to be comprehensive
            technical_score += 0.2
        if metadata.has_headers:
            technical_score += 0.2

        confidence_scores["technical"] = technical_score

        # Determine primary type
        max_score = max(confidence_scores.values()) if confidence_scores else 0
        if max_score >= 0.5:
            primary_type = max(confidence_scores, key=lambda k: confidence_scores[k])
        else:
            primary_type = "unknown"

        return {
            "primary_type": primary_type,
            "confidence": max_score,
            "all_scores": confidence_scores,
            "indicators": type_indicators,
        }

    def get_document_summary(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Get concise document summary for display."""
        doc_type = self.analyze_document_type(metadata)

        return {
            "name": metadata.file_name,
            "type": doc_type["primary_type"],
            "size": f"{metadata.file_size / 1024:.1f}KB",
            "quality": metadata.content_quality.value,
            "words": metadata.word_count,
            "language": metadata.language or "unknown",
            "has_important_data": any(
                [metadata.has_dates, metadata.has_currency, metadata.has_numbers]
            ),
        }


class MetadataService:
    """Main metadata extraction service."""

    def __init__(self):
        """Initialize metadata service."""
        self.logger = logging.getLogger(__name__)
        self.extractor = MetadataExtractor()

    def analyze_document(self, file_path: str, content: ExtractedContent) -> DocumentMetadata:
        """Analyze document and extract comprehensive metadata.

        Args:
            file_path: Path to document file
            content: Extracted content from the document

        Returns:
            DocumentMetadata with comprehensive analysis
        """
        return self.extract_comprehensive_metadata(file_path, content)

    def batch_analyze(
        self, file_paths: List[str], content_map: Dict[str, ExtractedContent]
    ) -> Dict[str, DocumentMetadata]:
        """Analyze multiple documents in batch.

        Args:
            file_paths: List of file paths to analyze
            content_map: Map of file paths to their extracted content

        Returns:
            Dictionary mapping file paths to their metadata
        """
        results = {}

        for file_path in file_paths:
            try:
                content = content_map.get(file_path)
                if content is None:
                    # Create minimal extracted content for metadata-only analysis
                    content = ExtractedContent(
                        text="",
                        quality=ContentQuality.FAILED,
                        file_type=os.path.splitext(file_path)[1][1:],  # Extension without dot
                    )

                metadata = self.analyze_document(file_path, content)
                results[file_path] = metadata

            except Exception as e:
                self.logger.error(f"Metadata analysis failed for {file_path}: {e}")
                results[file_path] = self._create_error_metadata(file_path, str(e))

        return results

    def _create_error_metadata(self, file_path: str, error: str) -> DocumentMetadata:
        """Create minimal metadata for failed analysis."""
        return DocumentMetadata(
            file_path=file_path,
            file_name=os.path.basename(file_path),
            file_size=0,
            file_extension=os.path.splitext(file_path)[1],
            mime_type=None,
            creation_date=None,
            modification_date=None,
            content_length=0,
            word_count=0,
            line_count=0,
            paragraph_count=0,
            has_headers=False,
            has_numbers=False,
            has_dates=False,
            has_currency=False,
            language=None,
            content_quality=ContentQuality.FAILED,
            readability_score=None,
            dates_found=[],
            numbers_found=[],
            currency_found=[],
            properties={"analysis_error": error},
        )

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "extractor_available": True,
            "supported_analyses": [
                "file_metadata",
                "content_metadata",
                "document_structure",
                "entity_extraction",
                "document_type_detection",
                "language_detection",
            ],
        }

    def extract_comprehensive_metadata(
        self, file_path: str, content: ExtractedContent
    ) -> DocumentMetadata:
        """Extract comprehensive metadata from file and content.

        Args:
            file_path: Path to the document file
            content: Extracted content from the file

        Returns:
            DocumentMetadata with comprehensive information
        """
        try:
            # Extract file metadata
            file_meta = self.extractor.extract_file_metadata(file_path)
            # Extract content metadata
            content_meta = self.extractor.extract_content_metadata(content.text)
            # Extract document structure
            structure_meta = self.extractor.extract_document_structure(content.text)
            # Extract entities
            entities = self.extractor.extract_entities(content.text)
            # Calculate readability score (need to implement this)
            readability = self.extractor._calculate_readability_score(content.text)
            return DocumentMetadata(
                # File metadata
                file_path=file_meta.get("file_path", file_path),
                file_name=file_meta.get("file_name", os.path.basename(file_path)),
                file_size=file_meta.get("file_size", 0),
                file_extension=file_meta.get("file_extension", ""),
                mime_type=file_meta.get("mime_type"),
                creation_date=file_meta.get("creation_date"),
                modification_date=file_meta.get("modification_date"),
                # Content metadata
                content_length=content_meta.get("content_length", 0),
                word_count=content_meta.get("word_count", 0),
                line_count=content_meta.get("line_count", 0),
                paragraph_count=content_meta.get("paragraph_count", 0),
                # Document structure
                has_headers=structure_meta.get("has_headers", False),
                has_numbers=structure_meta.get("has_numbers", False),
                has_dates=structure_meta.get("has_dates", False),
                has_currency=structure_meta.get("has_currency", False),
                language=self.extractor._detect_language(content.text),
                # Quality
                content_quality=content.quality,
                readability_score=readability,
                # Entities
                dates_found=entities.get("dates_found", []),
                numbers_found=entities.get("numbers_found", []),
                currency_found=entities.get("currency_found", []),
                # Additional properties
                properties={
                    "extraction_method": content.extraction_method,
                    "security_warnings": content.security_warnings,
                    **(content.metadata or {}),
                },
            )

        except Exception as e:
            self.logger.error(f"Metadata extraction failed for {file_path}: {e}")

            # Return minimal metadata on error
            return DocumentMetadata(
                file_path=file_path,
                file_name=os.path.basename(file_path),
                file_size=0,
                file_extension="",
                mime_type=None,
                creation_date=None,
                modification_date=None,
                content_length=0,
                word_count=0,
                line_count=0,
                paragraph_count=0,
                has_headers=False,
                has_numbers=False,
                has_dates=False,
                has_currency=False,
                language=None,
                content_quality=ContentQuality.FAILED,
                readability_score=None,
                dates_found=[],
                numbers_found=[],
                currency_found=[],
                properties={"error": str(e)},
            )

    def _calculate_readability_score(self, text: str) -> Optional[float]:
        """Calculate simple readability score."""
        if not text:
            return None

        try:
            words = text.split()
            sentences = text.count(".") + text.count("!") + text.count("?")

            if sentences == 0:
                return 0.0

            # Simple readability approximation (Flesch-like)
            avg_words_per_sentence = len(words) / sentences
            avg_chars_per_word = sum(len(word) for word in words) / len(words) if words else 0

            # Normalize to 0-100 scale (higher = more readable)
            score = 100 - (avg_words_per_sentence * 1.5) - (avg_chars_per_word * 5)
            return max(0.0, min(100.0, score))

        except Exception as e:
            self.logger.warning(f"Readability calculation failed: {e}")
            return None
