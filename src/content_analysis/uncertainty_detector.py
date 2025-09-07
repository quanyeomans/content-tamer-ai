"""
Uncertainty Detection System

Identifies documents that would benefit from ML refinement based on
classification confidence, feature analysis, and document characteristics.
"""

import logging
from typing import Dict, List, Tuple, Any
import numpy as np
from collections import Counter


class UncertaintyDetector:
    """Detects uncertain classifications that would benefit from ML refinement."""

    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize uncertainty detector.

        Args:
            confidence_threshold: Confidence below which documents are considered uncertain
        """
        self.confidence_threshold = confidence_threshold
        self.uncertainty_factors = {
            "low_confidence": 1.0,  # Primary factor
            "mixed_signals": 0.3,  # Multiple categories with similar scores
            "sparse_content": 0.2,  # Limited content for classification
            "ambiguous_filename": 0.15,  # Generic or unclear filename
            "missing_metadata": 0.1,  # Lack of classification signals
        }

    def detect_uncertain_documents(
        self, classified_documents: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Separate documents into certain and uncertain classifications.

        Args:
            classified_documents: All classified documents with confidence scores

        Returns:
            Tuple of (certain_documents, uncertain_documents)
        """
        certain_docs = []
        uncertain_docs = []

        for doc in classified_documents:
            uncertainty_score = self._calculate_uncertainty_score(doc)

            if uncertainty_score >= self.confidence_threshold:
                # Add uncertainty analysis to document
                doc["uncertainty_analysis"] = {
                    "uncertainty_score": uncertainty_score,
                    "factors": self._analyze_uncertainty_factors(doc),
                    "needs_ml_refinement": True,
                }
                uncertain_docs.append(doc)
            else:
                doc["uncertainty_analysis"] = {
                    "uncertainty_score": uncertainty_score,
                    "needs_ml_refinement": False,
                }
                certain_docs.append(doc)

        logging.info(
            f"Uncertainty detection: {len(certain_docs)} certain, "
            f"{len(uncertain_docs)} uncertain documents"
        )

        return certain_docs, uncertain_docs

    def _calculate_uncertainty_score(self, document: Dict[str, Any]) -> float:
        """Calculate overall uncertainty score for a document."""
        confidence = document.get("confidence", 0.0)

        # Primary uncertainty from low confidence
        uncertainty = 1.0 - confidence

        # Additional uncertainty factors
        factors = self._analyze_uncertainty_factors(document)

        for factor_name, factor_value in factors.items():
            if factor_value > 0:
                weight = self.uncertainty_factors.get(factor_name, 0.1)
                uncertainty += factor_value * weight

        # Normalize to [0, 1] range
        return min(1.0, uncertainty)

    def _analyze_uncertainty_factors(self, document: Dict[str, Any]) -> Dict[str, float]:
        """Analyze specific uncertainty factors for a document."""
        factors = {}

        # Factor 1: Mixed signals (multiple similar category scores)
        factors["mixed_signals"] = self._detect_mixed_signals(document)

        # Factor 2: Sparse content
        factors["sparse_content"] = self._detect_sparse_content(document)

        # Factor 3: Ambiguous filename
        factors["ambiguous_filename"] = self._detect_ambiguous_filename(document)

        # Factor 4: Missing metadata
        factors["missing_metadata"] = self._detect_missing_metadata(document)

        return factors

    def _detect_mixed_signals(self, document: Dict[str, Any]) -> float:
        """Detect if document has competing classification signals."""
        # This would ideally use internal classifier scores
        # For now, we'll use confidence as a proxy
        confidence = document.get("confidence", 0.0)

        # If confidence is in the "uncertain" range (0.4-0.7), likely mixed signals
        if 0.4 <= confidence <= 0.7:
            return (0.7 - confidence) / 0.3  # Scale to [0, 1]

        return 0.0

    def _detect_sparse_content(self, document: Dict[str, Any]) -> float:
        """Detect if document has insufficient content for reliable classification."""
        content = document.get("content_preview", "")
        filename = document.get("filename", "")

        # Calculate content richness
        total_chars = len(content) + len(filename)
        word_count = len(content.split()) if content else 0

        # Sparse content indicators
        if total_chars < 50:
            return 0.8  # Very sparse
        elif total_chars < 100 or word_count < 10:
            return 0.5  # Moderately sparse
        elif word_count < 20:
            return 0.3  # Slightly sparse

        return 0.0

    def _detect_ambiguous_filename(self, document: Dict[str, Any]) -> float:
        """Detect if filename provides unclear classification signals."""
        filename = document.get("filename", "").lower()

        if not filename:
            return 0.8

        # Check for generic patterns
        generic_patterns = [
            "document",
            "file",
            "untitled",
            "scan",
            "image",
            "photo",
            "new",
            "copy",
            "temp",
            "draft",
            "unknown",
        ]

        # Check for very generic names
        for pattern in generic_patterns:
            if pattern in filename:
                return 0.6

        # Check for mostly numbers/dates (often unclear)
        import re

        if re.match(r"^[\d\-_\.]+$", filename.replace(".pdf", "")):
            return 0.4

        # Check for very short names
        if len(filename.replace(".pdf", "")) < 5:
            return 0.3

        return 0.0

    def _detect_missing_metadata(self, document: Dict[str, Any]) -> float:
        """Detect if document lacks metadata signals for classification."""
        metadata = document.get("metadata", {})

        if not metadata:
            return 0.8

        # Check for missing key metadata components
        missing_score = 0.0

        # Missing entities
        entities = metadata.get("key_entities", {})
        if not entities or all(not entity_list for entity_list in entities.values()):
            missing_score += 0.3

        # Missing dates
        dates = metadata.get("date_detected", [])
        if not dates:
            missing_score += 0.2

        # Missing amounts (for financial docs)
        amounts = metadata.get("amounts_detected", [])
        structure = metadata.get("structure_info", {})
        word_count = structure.get("word_count", 0)

        # If it looks like a financial document but missing amounts
        content = document.get("content_preview", "").lower()
        if any(word in content for word in ["invoice", "payment", "bill", "$"]) and not amounts:
            missing_score += 0.3

        # Very low word count
        if word_count < 20:
            missing_score += 0.2

        return min(1.0, missing_score)

    def get_uncertainty_summary(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics about uncertainty detection."""
        certain_docs, uncertain_docs = self.detect_uncertain_documents(documents)

        # Analyze uncertainty factors
        factor_stats = {}
        if uncertain_docs:
            for factor in self.uncertainty_factors.keys():
                factor_values = [
                    doc.get("uncertainty_analysis", {}).get("factors", {}).get(factor, 0)
                    for doc in uncertain_docs
                ]
                factor_stats[factor] = {
                    "avg_score": np.mean(factor_values) if factor_values else 0,
                    "max_score": np.max(factor_values) if factor_values else 0,
                    "documents_affected": sum(1 for v in factor_values if v > 0.1),
                }

        return {
            "total_documents": len(documents),
            "certain_documents": len(certain_docs),
            "uncertain_documents": len(uncertain_docs),
            "uncertainty_rate": len(uncertain_docs) / len(documents) if documents else 0,
            "confidence_threshold": self.confidence_threshold,
            "factor_analysis": factor_stats,
            "recommendation": self._get_processing_recommendation(certain_docs, uncertain_docs),
        }

    def _get_processing_recommendation(
        self, certain_docs: List[Dict], uncertain_docs: List[Dict]
    ) -> str:
        """Provide recommendation for processing approach."""
        total_docs = len(certain_docs) + len(uncertain_docs)
        if total_docs == 0:
            return "No documents to process"

        uncertainty_rate = len(uncertain_docs) / total_docs

        if uncertainty_rate < 0.1:
            return "High confidence - ML refinement not needed"
        elif uncertainty_rate < 0.3:
            return "Moderate uncertainty - ML refinement recommended for uncertain documents"
        elif uncertainty_rate < 0.6:
            return "High uncertainty - ML refinement strongly recommended"
        else:
            return "Very high uncertainty - consider improving rule-based classification or content quality"

    def adjust_threshold(self, new_threshold: float) -> None:
        """Adjust the confidence threshold for uncertainty detection."""
        if 0.0 <= new_threshold <= 1.0:
            self.confidence_threshold = new_threshold
            logging.info(f"Uncertainty threshold updated to {new_threshold}")
        else:
            raise ValueError("Threshold must be between 0.0 and 1.0")

    def get_threshold_analysis(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how different thresholds would affect uncertainty detection."""
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
        analysis = {}

        original_threshold = self.confidence_threshold

        try:
            for threshold in thresholds:
                self.confidence_threshold = threshold
                certain, uncertain = self.detect_uncertain_documents(documents)

                analysis[f"threshold_{threshold}"] = {
                    "certain_count": len(certain),
                    "uncertain_count": len(uncertain),
                    "uncertainty_rate": len(uncertain) / len(documents) if documents else 0,
                }
        finally:
            # Restore original threshold
            self.confidence_threshold = original_threshold

        return analysis
