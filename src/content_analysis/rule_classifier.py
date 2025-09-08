"""
Enhanced Rule-Based Document Classifier

Provides reliable, immediate document classification using enhanced pattern matching
combined with modern NLP techniques. Designed to achieve 80%+ accuracy on first run
for one-shot client discovery scenarios.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import spacy


class EnhancedRuleBasedClassifier:
    """Enhanced rule-based classifier with spaCy NLP integration."""

    _spacy_warning_shown = False  # Class-level flag to prevent warning spam

    def __init__(self):
        """Initialize classifier with enhanced patterns and spaCy model."""
        try:
            # Load spaCy model with minimal components for speed
            self.nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger"])
        except OSError:
            # Graceful fallback if spaCy not available - warn only once
            if not EnhancedRuleBasedClassifier._spacy_warning_shown:
                logging.warning("spaCy model not available, using basic fallback")
                EnhancedRuleBasedClassifier._spacy_warning_shown = True
            self.nlp = None

        # Enhanced pattern rules based on research and common document types
        self.classification_rules = self._load_enhanced_patterns()

    def _load_enhanced_patterns(self) -> Dict[str, List[Dict]]:
        """Load enhanced classification patterns with confidence scores."""
        return {
            "contracts": [
                {
                    "patterns": [
                        r"service\s+agreement",
                        r"terms\s+and\s+conditions",
                        r"effective\s+date",
                    ],
                    "weight": 0.9,
                },
                {"patterns": [r"agreement", r"party", r"shall"], "weight": 0.8},
                {"patterns": [r"contract", r"legal", r"binding"], "weight": 0.7},
                {"patterns": [r"whereas", r"therefore", r"executed"], "weight": 0.8},
            ],
            "invoices": [
                {
                    "patterns": [
                        r"invoice\s*#?\d+",
                        r"amount\s+due",
                        r"payment\s+terms",
                    ],
                    "weight": 0.9,
                },
                {"patterns": [r"invoice", r"due\s+date", r"total"], "weight": 0.8},
                {"patterns": [r"billing", r"charge", r"remit"], "weight": 0.7},
                {
                    "patterns": [r"\$[\d,]+\.\d{2}", r"net\s+\d+", r"payable"],
                    "weight": 0.7,
                },
            ],
            "reports": [
                {"patterns": [r"report", r"analysis", r"findings"], "weight": 0.8},
                {"patterns": [r"quarterly", r"annual", r"summary"], "weight": 0.8},
                {"patterns": [r"revenue", r"expenses", r"performance"], "weight": 0.7},
                {
                    "patterns": [
                        r"executive\s+summary",
                        r"conclusion",
                        r"recommendation",
                    ],
                    "weight": 0.8,
                },
                {
                    "patterns": [
                        r"q[1-4]\s+\d{4}",
                        r"financial\s+report",
                        r"year.over.year",
                    ],
                    "weight": 0.9,
                },
            ],
            "correspondence": [
                {"patterns": [r"dear\s+\w+", r"sincerely", r"regards"], "weight": 0.8},
                {"patterns": [r"meeting", r"discussion", r"follow.up"], "weight": 0.7},
                {"patterns": [r"email", r"message", r"communication"], "weight": 0.6},
                {"patterns": [r"thank\s+you", r"please", r"update"], "weight": 0.6},
                {
                    "patterns": [
                        r"colleagues",
                        r"various\s+topics",
                        r"meeting\s+notes",
                    ],
                    "weight": 0.7,
                },
            ],
            "financial": [
                {
                    "patterns": [
                        r"balance\s+sheet",
                        r"income\s+statement",
                        r"cash\s+flow",
                    ],
                    "weight": 0.9,
                },
                {"patterns": [r"budget", r"forecast", r"financial"], "weight": 0.8},
                {"patterns": [r"profit", r"loss", r"revenue"], "weight": 0.7},
                {"patterns": [r"assets", r"liabilities", r"equity"], "weight": 0.8},
            ],
            "legal": [
                {
                    "patterns": [r"legal\s+document", r"court", r"jurisdiction"],
                    "weight": 0.9,
                },
                {
                    "patterns": [r"plaintiff", r"defendant", r"litigation"],
                    "weight": 0.8,
                },
                {"patterns": [r"statute", r"regulation", r"compliance"], "weight": 0.7},
                {"patterns": [r"hereby", r"witness", r"notarized"], "weight": 0.7},
            ],
        }

    def classify_document(self, content: str, filename: str) -> str:
        """
        Classify document using enhanced rules + spaCy NLP.

        Args:
            content: Document content text
            filename: Document filename for additional context

        Returns:
            Predicted document category
        """
        # Combine content and filename for classification
        full_text = f"{filename} {content}".lower()

        # Apply enhanced rule scoring
        category_scores = self._apply_enhanced_rules(full_text)

        # Apply modern entity recognition enhancement if available
        if self.nlp:
            entity_boost = self._score_modern_entity_patterns(content)
            category_scores = self._combine_scores(category_scores, entity_boost)

        # Select category with highest confidence
        if not category_scores:
            return "other"  # Fallback category

        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category]

        # Only return classification if confidence exceeds threshold
        if confidence >= 0.3:  # Minimum confidence threshold
            return best_category
        else:
            return "other"

    def _apply_enhanced_rules(self, text: str) -> Dict[str, float]:
        """Apply enhanced pattern matching rules."""
        category_scores = {}

        for category, rule_sets in self.classification_rules.items():
            total_score = 0.0
            matched_patterns = 0

            for rule_set in rule_sets:
                patterns = rule_set["patterns"]
                weight = rule_set["weight"]

                # Count pattern matches
                pattern_matches = 0
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        pattern_matches += 1

                # Calculate weighted score for this rule set
                if pattern_matches > 0:
                    rule_score = (pattern_matches / len(patterns)) * weight
                    total_score += rule_score
                    matched_patterns += 1

            # Normalize score by number of rule sets that matched
            if matched_patterns > 0:
                category_scores[category] = total_score / len(rule_sets)

        return category_scores

    def _score_modern_entity_patterns(self, content: str) -> Dict[str, float]:
        """Use spaCy entity recognition for additional scoring."""
        if not self.nlp:
            return {}

        try:
            # Process content with spaCy (limit to first 2000 chars for speed)
            doc = self.nlp(content[:2000])
            entity_scores = {}

            # Score based on entity types found
            for ent in doc.ents:
                if ent.label_ == "MONEY":
                    # Financial entities boost financial/invoice categories
                    entity_scores["invoices"] = entity_scores.get("invoices", 0) + 0.2
                    entity_scores["financial"] = entity_scores.get("financial", 0) + 0.1
                elif ent.label_ == "DATE":
                    # Date entities boost contracts/reports
                    entity_scores["contracts"] = entity_scores.get("contracts", 0) + 0.1
                    entity_scores["reports"] = entity_scores.get("reports", 0) + 0.1
                elif ent.label_ in ["ORG", "PERSON"]:
                    # Organization/person entities boost contracts/correspondence
                    entity_scores["contracts"] = entity_scores.get("contracts", 0) + 0.1
                    entity_scores["correspondence"] = (
                        entity_scores.get("correspondence", 0) + 0.1
                    )
                elif ent.label_ == "LAW":
                    # Legal entities boost legal category
                    entity_scores["legal"] = entity_scores.get("legal", 0) + 0.3

            return entity_scores

        except Exception as e:
            logging.warning(f"Entity recognition failed: {e}")
            return {}

    def _combine_scores(
        self, rule_scores: Dict[str, float], entity_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Intelligently combine rule and entity scores."""
        combined = rule_scores.copy()

        for category, boost in entity_scores.items():
            if category in combined:
                # Boost existing scores
                combined[category] += boost
            else:
                # Add new entity-based scores
                combined[category] = boost

        return combined

    def get_classification_confidence(
        self, content: str, filename: str
    ) -> Tuple[str, float]:
        """
        Get classification with confidence score.

        Returns:
            Tuple of (category, confidence_score)
        """
        full_text = f"{filename} {content}".lower()
        category_scores = self._apply_enhanced_rules(full_text)

        if self.nlp:
            entity_boost = self._score_modern_entity_patterns(content)
            category_scores = self._combine_scores(category_scores, entity_boost)

        if not category_scores:
            return ("other", 0.0)

        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category]

        return (best_category, confidence)
