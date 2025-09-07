"""
Content Metadata Extractor

Extracts document metadata from processed content, reusing OCR content
from the filename generation phase for memory efficiency.
"""

import re
import spacy
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from dateutil import parser as date_parser


class ContentMetadataExtractor:
    """Extract structured metadata from document content."""

    def __init__(self):
        """Initialize metadata extractor with spaCy and date parsing."""
        try:
            # Load spaCy model for entity recognition
            self.nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger"])
        except OSError:
            logging.warning("spaCy model not available, using basic fallback")
            self.nlp = None

        # Date patterns for extraction
        self.date_patterns = [
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",  # MM/DD/YYYY or MM-DD-YYYY
            r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",  # YYYY/MM/DD or YYYY-MM-DD
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{4}\b",  # Month DD, YYYY
            r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}\b",  # DD Month YYYY
        ]

        # Amount/currency patterns
        self.amount_patterns = [
            r"\$[\d,]+\.?\d*",  # Dollar amounts
            r"[\d,]+\.\d{2}\s*(?:USD|dollars?)",  # Explicit currency
            r"amount[:\s]+\$?[\d,]+\.?\d*",  # Amount labels
        ]

    def extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from document content.

        Args:
            content: Document content text (from OCR processing)
            filename: Document filename for additional context

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            "filename": filename,
            "content_length": len(content),
            "extraction_timestamp": datetime.now().isoformat(),
        }

        # Extract document type using rule-based classification
        from .rule_classifier import EnhancedRuleBasedClassifier

        classifier = EnhancedRuleBasedClassifier()
        document_type, confidence = classifier.get_classification_confidence(content, filename)

        metadata["document_type"] = document_type
        metadata["confidence_score"] = confidence

        # Extract key entities using spaCy if available
        metadata["key_entities"] = self._extract_entities(content)

        # Extract dates from content
        metadata["date_detected"] = self._extract_dates(content)

        # Extract amounts/financial information
        metadata["amounts_detected"] = self._extract_amounts(content)

        # Extract document structure information
        metadata["structure_info"] = self._analyze_document_structure(content)

        # Extract potential fiscal year information
        metadata["fiscal_year_hints"] = self._extract_fiscal_year_hints(
            content, metadata["date_detected"]
        )

        return metadata

    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy."""
        entities = {
            "organizations": [],
            "persons": [],
            "locations": [],
            "dates": [],
            "money": [],
            "other": [],
        }

        if not self.nlp:
            return entities

        try:
            # Process content (limit for performance)
            doc = self.nlp(content[:3000])

            for ent in doc.ents:
                entity_text = ent.text.strip()
                if not entity_text:
                    continue

                if ent.label_ == "ORG":
                    entities["organizations"].append(entity_text)
                elif ent.label_ == "PERSON":
                    entities["persons"].append(entity_text)
                elif ent.label_ in ["GPE", "LOC"]:
                    entities["locations"].append(entity_text)
                elif ent.label_ == "DATE":
                    entities["dates"].append(entity_text)
                elif ent.label_ == "MONEY":
                    entities["money"].append(entity_text)
                else:
                    entities["other"].append(entity_text)

            # Remove duplicates and limit results
            for key in entities:
                entities[key] = list(set(entities[key]))[:5]  # Limit to 5 per category

        except Exception as e:
            logging.warning(f"Entity extraction failed: {e}")

        return entities

    def _extract_dates(self, content: str) -> List[Dict[str, Any]]:
        """Extract dates from content using multiple methods."""
        dates_found = []

        # Use regex patterns first
        for pattern in self.date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse the date
                    parsed_date = date_parser.parse(match, fuzzy=False)
                    dates_found.append(
                        {
                            "raw_text": match,
                            "parsed_date": parsed_date.isoformat()[:10],  # YYYY-MM-DD format
                            "year": parsed_date.year,
                            "method": "regex",
                        }
                    )
                except (ValueError, TypeError):
                    continue

        # Remove duplicates based on parsed date
        unique_dates = {}
        for date_info in dates_found:
            date_key = date_info.get("parsed_date")
            if date_key and date_key not in unique_dates:
                unique_dates[date_key] = date_info

        return list(unique_dates.values())[:10]  # Limit to 10 dates

    def _extract_amounts(self, content: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from content."""
        amounts_found = []

        for pattern in self.amount_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Clean up the amount
                clean_amount = re.sub(r"[^\d.,]", "", match)
                try:
                    # Try to convert to float
                    numeric_value = float(clean_amount.replace(",", ""))
                    amounts_found.append(
                        {
                            "raw_text": match.strip(),
                            "numeric_value": numeric_value,
                            "formatted": f"${numeric_value:,.2f}",
                        }
                    )
                except ValueError:
                    continue

        # Sort by value and limit results
        amounts_found.sort(key=lambda x: x["numeric_value"], reverse=True)
        return amounts_found[:5]  # Limit to 5 amounts

    def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analyze document structure for organization hints."""
        structure_info = {
            "paragraph_count": len(content.split("\n\n")),
            "line_count": len(content.split("\n")),
            "word_count": len(content.split()),
            "has_headers": False,
            "has_numbered_items": False,
            "has_bullet_points": False,
        }

        # Check for structural elements
        if re.search(r"^[A-Z][A-Z\s]+$", content, re.MULTILINE):
            structure_info["has_headers"] = True

        if re.search(r"^\s*\d+\.", content, re.MULTILINE):
            structure_info["has_numbered_items"] = True

        if re.search(r"^\s*[•\-\*]", content, re.MULTILINE):
            structure_info["has_bullet_points"] = True

        return structure_info

    def _extract_fiscal_year_hints(
        self, content: str, detected_dates: List[Dict]
    ) -> Dict[str, Any]:
        """Extract fiscal year information from content and dates."""
        fiscal_hints = {
            "detected_years": set(),
            "fiscal_year_pattern": None,
            "quarter_mentions": [],
            "fiscal_keywords": [],
        }

        # Collect years from detected dates
        for date_info in detected_dates:
            fiscal_hints["detected_years"].add(date_info["year"])

        # Convert to sorted list
        fiscal_hints["detected_years"] = sorted(list(fiscal_hints["detected_years"]))

        # Look for fiscal year patterns
        fy_patterns = [
            r"fy[\s-]?(\d{2,4})",  # FY-2024, FY 24
            r"fiscal\s+year\s+(\d{2,4})",  # Fiscal Year 2024
            r"(\d{4})[\s-]?(\d{2,4})\s+fiscal",  # 2023-24 fiscal
        ]

        for pattern in fy_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                fiscal_hints["fiscal_year_pattern"] = (
                    matches[0] if isinstance(matches[0], str) else matches[0][0]
                )
                break

        # Look for quarter mentions
        quarter_matches = re.findall(r"q([1-4])\s+(\d{4})", content, re.IGNORECASE)
        fiscal_hints["quarter_mentions"] = [f"Q{q} {year}" for q, year in quarter_matches]

        # Look for fiscal keywords
        fiscal_keywords = ["fiscal year", "fy", "budget year", "financial year", "tax year"]
        for keyword in fiscal_keywords:
            if keyword.lower() in content.lower():
                fiscal_hints["fiscal_keywords"].append(keyword)

        return fiscal_hints
