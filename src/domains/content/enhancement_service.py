"""
Content Enhancement Service

Quality assessment, cleaning, and normalization of extracted content.
Provides content improvement and preparation for AI processing.
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple

from .extraction_service import ContentQuality, ExtractedContent


class EnhancementMethod(Enum):
    """Methods for content enhancement."""

    CLEANING = "cleaning"  # Remove artifacts, normalize text
    SUMMARIZATION = "summarization"  # Extract key information
    STRUCTURE = "structure"  # Improve text structure
    LANGUAGE = "language"  # Language detection and normalization


@dataclass
class EnhancementResult:
    """Result of content enhancement."""

    enhanced_content: str
    original_content: str
    quality_before: ContentQuality
    quality_after: ContentQuality
    methods_applied: List[EnhancementMethod]
    improvements: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.improvements is None:
            self.improvements = []
        if self.warnings is None:
            self.warnings = []


class ContentCleaner:
    """Text cleaning and normalization utilities."""

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize Unicode characters."""
        # Normalize to NFC form (canonical decomposition, then canonical composition)
        normalized = unicodedata.normalize("NFC", text)

        # Remove or replace problematic Unicode characters
        # Replace various quotation marks with standard ones
        replacements = {
            '"': '"',
            '"': '"',  # Smart quotes
            "'": "'",
            "'": "'",  # Smart apostrophes
            "–": "-",
            "—": "-",  # En/em dashes
            "…": "...",  # Ellipsis
            " ": " ",  # Non-breaking space
            "​": "",  # Zero-width space
        }

        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        return normalized

    @staticmethod
    def remove_extraction_artifacts(text: str) -> str:
        """Remove common PDF/OCR extraction artifacts."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove standalone numbers (often page numbers)
        text = re.sub(r"\b\d+\b\s*\n", "\n", text)

        # Remove repeated characters (OCR artifacts)
        text = re.sub(r"(.)\1{4,}", r"\1\1", text)

        # Fix common OCR mistakes
        ocr_fixes = {
            r"\bl\b": "I",  # lowercase l often mistaken for I
            r"\b0\b": "O",  # zero often mistaken for O in text
            r"\brn\b": "m",  # rn often mistaken for m
            r"\bvv\b": "w",  # vv often mistaken for w
        }

        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)

        # Remove header/footer patterns
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip likely header/footer content
            if (
                len(line) < 3
                or line.isdigit()  # Page numbers
                or line.lower() in ["confidential", "page", "draft"]
                or re.match(r"^page \d+", line.lower())
            ):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def improve_structure(text: str) -> str:
        """Improve text structure and formatting."""
        # Split into paragraphs
        paragraphs = text.split("\n\n")
        improved_paragraphs = []

        for paragraph in paragraphs:
            # Clean up paragraph
            para_lines = [line.strip() for line in paragraph.split("\n") if line.strip()]

            if para_lines:
                # Join lines with proper spacing
                improved_para = " ".join(para_lines)

                # Ensure proper sentence endings
                if improved_para and not improved_para.endswith((".", "!", "?", ":")):
                    improved_para += "."

                improved_paragraphs.append(improved_para)

        return "\n\n".join(improved_paragraphs)


class ContentSummarizer:
    """Content summarization for large documents."""

    def __init__(self, max_length: int = 2000):
        """Initialize summarizer.

        Args:
            max_length: Maximum length of summarized content
        """
        self.max_length = max_length
        self.logger = logging.getLogger(__name__)

    def summarize_for_ai(self, content: str) -> str:
        """Summarize content for AI processing."""
        if len(content) <= self.max_length:
            return content

        # Extract key information
        sentences = self._split_into_sentences(content)

        # Score sentences by importance
        sentence_scores = self._score_sentences(sentences)

        # Select top sentences that fit within limit
        selected_sentences = self._select_top_sentences(sentence_scores, self.max_length)

        return " ".join(selected_sentences)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r"[.!?]+\s+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _score_sentences(self, sentences: List[str]) -> List[Tuple[str, float]]:
        """Score sentences by importance."""
        scored = []

        for sentence in sentences:
            score = 0.0

            # Length scoring (prefer moderate length)
            length = len(sentence)
            if 30 <= length <= 200:
                score += 1.0
            elif 200 < length <= 400:
                score += 0.7

            # Content scoring
            sentence_lower = sentence.lower()

            # Prefer sentences with key information indicators
            key_indicators = [
                "date",
                "amount",
                "total",
                "invoice",
                "contract",
                "agreement",
                "summary",
                "conclusion",
                "purpose",
                "objective",
            ]
            score += 0.5 * sum(1 for word in key_indicators if word in sentence_lower)

            # Prefer sentences with numbers (often important data)
            if re.search(r"\d+", sentence):
                score += 0.3

            # Prefer sentences with proper capitalization
            if sentence[0].isupper() and not sentence.isupper():
                score += 0.2

            scored.append((sentence, score))

        return sorted(scored, key=lambda x: x[1], reverse=True)

    def _select_top_sentences(
        self, scored_sentences: List[Tuple[str, float]], max_length: int
    ) -> List[str]:
        """Select top sentences that fit within length limit."""
        selected = []
        current_length = 0

        for sentence, _score in scored_sentences:
            if current_length + len(sentence) <= max_length:
                selected.append(sentence)
                current_length += len(sentence)

            if current_length >= max_length * 0.9:  # Stop when 90% full
                break

        return selected


class EnhancementService:
    """Main content enhancement service."""

    def __init__(self, max_content_length: int = 2000):
        """Initialize enhancement service.

        Args:
            max_content_length: Maximum length for content sent to AI
        """
        self.max_content_length = max_content_length
        self.logger = logging.getLogger(__name__)

        self.cleaner = ContentCleaner()
        self.summarizer = ContentSummarizer(max_content_length)

    def enhance_content(self, content: ExtractedContent) -> EnhancementResult:
        """Enhance extracted content for AI processing.

        Args:
            content: ExtractedContent from extraction service

        Returns:
            EnhancementResult with improved content
        """
        if content.quality == ContentQuality.FAILED:
            return EnhancementResult(
                enhanced_content=content.text,
                original_content=content.text,
                quality_before=content.quality,
                quality_after=content.quality,
                methods_applied=[],
                improvements=[],
                warnings=["Content extraction failed, no enhancement possible"],
                metadata={"enhancement_skipped": True},
            )

        original_text = content.text
        enhanced_text = original_text
        methods_applied = []
        improvements = []
        warnings = []

        try:
            # Step 1: Clean and normalize
            if content.quality in [ContentQuality.POOR, ContentQuality.FAIR]:
                enhanced_text = self.cleaner.normalize_unicode(enhanced_text)
                enhanced_text = self.cleaner.remove_extraction_artifacts(enhanced_text)
                enhanced_text = self.cleaner.improve_structure(enhanced_text)

                methods_applied.append(EnhancementMethod.CLEANING)
                improvements.append("Applied text cleaning and normalization")

            # Step 2: Summarize if too long
            if len(enhanced_text) > self.max_content_length:
                enhanced_text = self.summarizer.summarize_for_ai(enhanced_text)
                methods_applied.append(EnhancementMethod.SUMMARIZATION)
                improvements.append(
                    f"Summarized from {len(original_text)} to {len(enhanced_text)} characters"
                )

            # Assess final quality
            final_quality = self._assess_enhanced_quality(enhanced_text, content.quality)

            return EnhancementResult(
                enhanced_content=enhanced_text,
                original_content=original_text,
                quality_before=content.quality,
                quality_after=final_quality,
                methods_applied=methods_applied,
                improvements=improvements,
                warnings=warnings,
                metadata={
                    "original_length": len(original_text),
                    "enhanced_length": len(enhanced_text),
                    "compression_ratio": (
                        len(enhanced_text) / len(original_text) if original_text else 0
                    ),
                },
            )

        except Exception as e:
            self.logger.error(f"Content enhancement failed: {e}")
            return EnhancementResult(
                enhanced_content=original_text,
                original_content=original_text,
                quality_before=content.quality,
                quality_after=content.quality,
                methods_applied=[],
                improvements=[],
                warnings=[f"Enhancement failed: {e}"],
                metadata={"enhancement_error": str(e)},
            )

    def _assess_enhanced_quality(
        self, enhanced_text: str, original_quality: ContentQuality
    ) -> ContentQuality:
        """Assess quality after enhancement."""
        if not enhanced_text or len(enhanced_text.strip()) < 10:
            return ContentQuality.FAILED

        # Enhancement typically improves quality by one level
        quality_order = [
            ContentQuality.FAILED,
            ContentQuality.POOR,
            ContentQuality.FAIR,
            ContentQuality.GOOD,
            ContentQuality.EXCELLENT,
        ]

        try:
            current_index = quality_order.index(original_quality)
            improved_index = min(current_index + 1, len(quality_order) - 1)
            return quality_order[improved_index]
        except ValueError:
            # If original quality not in list, assess directly
            return self._direct_quality_assessment(enhanced_text)

    def _direct_quality_assessment(self, text: str) -> ContentQuality:
        """Direct quality assessment of text."""
        if not text or len(text.strip()) < 10:
            return ContentQuality.FAILED

        # Count quality indicators
        words = text.split()
        sentences = text.count(".") + text.count("!") + text.count("?")

        # Quality scoring
        if len(words) >= 50 and sentences >= 3 and len(text) >= 200:
            return ContentQuality.EXCELLENT
        elif len(words) >= 20 and sentences >= 1 and len(text) >= 100:
            return ContentQuality.GOOD
        elif len(words) >= 10 and len(text) >= 50:
            return ContentQuality.FAIR
        else:
            return ContentQuality.POOR

    def prepare_for_ai_processing(self, content: ExtractedContent) -> str:
        """Prepare content specifically for AI processing.

        Args:
            content: Extracted content to prepare

        Returns:
            Content optimized for AI processing
        """
        # Enhance content first
        enhancement_result = self.enhance_content(content)

        # Additional AI-specific preparation
        ai_ready_content = enhancement_result.enhanced_content

        # Add context if available
        if content.file_type:
            ai_ready_content = f"[{content.file_type.upper()} DOCUMENT]\n{ai_ready_content}"

        # Add extraction method context for quality assessment
        if content.extraction_method:
            ai_ready_content += f"\n[Extracted via: {content.extraction_method}]"

        return ai_ready_content

    def get_enhancement_statistics(self) -> Dict[str, Any]:
        """Get statistics about enhancement operations."""
        # This could be enhanced to track historical statistics
        return {
            "max_content_length": self.max_content_length,
            "available_methods": [method.value for method in EnhancementMethod],
            "cleaner_available": True,
            "summarizer_available": True,
        }
