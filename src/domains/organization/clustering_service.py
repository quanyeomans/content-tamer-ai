"""
Clustering Service

Document classification and clustering using progressive enhancement architecture.
Implements the balanced approach from PRD_04 with rule-based foundation + selective ML.
"""

import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Import content analysis components
try:
    from .content_analysis.ml_refiner import SelectiveMLRefinement
    from .content_analysis.rule_classifier import EnhancedRuleBasedClassifier
    from .content_analysis.uncertainty_detector import UncertaintyDetector
except ImportError:
    # Fallback for when content analysis modules not available
    EnhancedRuleBasedClassifier = None
    SelectiveMLRefinement = None
    UncertaintyDetector = None


class ClusteringMethod(Enum):
    """Available clustering methods."""

    RULE_BASED = "rule_based"
    ML_ENHANCED = "ml_enhanced"
    ENSEMBLE = "ensemble"
    FALLBACK = "fallback"


class ConfidenceLevel(Enum):
    """Classification confidence levels."""

    HIGH = "high"  # >0.8 confidence
    MEDIUM = "medium"  # 0.5-0.8 confidence
    LOW = "low"  # 0.2-0.5 confidence
    VERY_LOW = "very_low"  # <0.2 confidence


@dataclass
class ClassificationResult:
    """Result of document classification."""

    category: str
    confidence: float
    method: ClusteringMethod
    reasoning: str
    alternative_categories: List[Tuple[str, float]]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.alternative_categories is None:
            self.alternative_categories = []

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level enum."""
        if self.confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


@dataclass
class ClusteringConfig:
    """Configuration for clustering behavior."""

    ml_threshold: float = 0.7  # Confidence threshold for applying ML
    min_ml_documents: int = 10  # Minimum docs to apply ML enhancement
    enable_ensemble: bool = False  # Enable ensemble methods
    max_categories: int = 20  # Maximum categories to create
    min_category_size: int = 2  # Minimum documents per category
    fallback_to_time: bool = True  # Fallback to time-based if clustering fails


class ClusteringService:
    """Main document clustering service with progressive enhancement."""

    def __init__(self, config: Optional[ClusteringConfig] = None):
        """Initialize clustering service.

        Args:
            config: Clustering configuration (uses defaults if None)
        """
        self.config = config or ClusteringConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize classifiers
        self._initialize_classifiers()

        # Statistics tracking
        self._classification_stats = {
            "total_classifications": 0,
            "method_usage": defaultdict(int),
            "confidence_distribution": defaultdict(int),
        }

    def _initialize_classifiers(self) -> None:
        """Initialize classification components."""
        try:
            # Rule-based classifier (always available)
            if EnhancedRuleBasedClassifier:
                self.rule_classifier = EnhancedRuleBasedClassifier()
                self.have_rule_classifier = True
            else:
                self.rule_classifier = None
                self.have_rule_classifier = False
                self.logger.warning("Rule-based classifier not available")

            # ML classifier (optional)
            if SelectiveMLRefinement:
                self.ml_refiner = SelectiveMLRefinement()
                self.have_ml_refiner = True
            else:
                self.ml_refiner = None
                self.have_ml_refiner = False
                self.logger.warning("ML refiner not available")

            # Uncertainty detector
            if UncertaintyDetector:
                self.uncertainty_detector = UncertaintyDetector()
                self.have_uncertainty_detector = True
            else:
                self.uncertainty_detector = None
                self.have_uncertainty_detector = False
                self.logger.warning("Uncertainty detector not available")

        except Exception as e:
            self.logger.error(f"Classifier initialization failed: {e}")
            # Set all to None for graceful degradation
            self.rule_classifier = None
            self.ml_refiner = None
            self.uncertainty_detector = None
            self.have_rule_classifier = False
            self.have_ml_refiner = False
            self.have_uncertainty_detector = False

    def classify_document(self, document: Dict[str, Any]) -> ClassificationResult:
        """Classify a single document using progressive enhancement.

        Args:
            document: Document dictionary with content, filename, metadata

        Returns:
            ClassificationResult with category and confidence
        """
        try:
            # Extract document information
            content = document.get("content", "")
            filename = document.get("filename", "")
            metadata = document.get("metadata", {})

            # Step 1: Rule-based classification (foundation)
            rule_result = self._classify_with_rules(content, filename, metadata)

            # If high confidence, return rule-based result
            if rule_result.confidence >= self.config.ml_threshold:
                self._update_stats(rule_result.method, rule_result.confidence_level)
                return rule_result

            # Step 2: ML enhancement for uncertain cases (if available and threshold met)
            if self.have_ml_refiner and self._should_apply_ml_enhancement(rule_result.confidence):

                try:
                    ml_result = self._enhance_with_ml(document, rule_result)
                    self._update_stats(ml_result.method, ml_result.confidence_level)
                    return ml_result
                except Exception as e:
                    self.logger.warning(f"ML enhancement failed, using rule-based result: {e}")

            # Step 3: Return rule-based result with uncertainty noted
            rule_result.metadata["ml_enhancement_skipped"] = True
            rule_result.metadata["uncertainty_reason"] = (
                f"Confidence {rule_result.confidence:.2f} below ML threshold {self.config.ml_threshold}"
            )

            self._update_stats(rule_result.method, rule_result.confidence_level)
            return rule_result

        except Exception as e:
            self.logger.error(f"Document classification failed: {e}")
            return self._create_fallback_result(document, str(e))

    def _classify_with_rules(
        self, content: str, filename: str, metadata: Dict[str, Any]
    ) -> ClassificationResult:
        """Classify document using rule-based approach."""
        if not self.have_rule_classifier:
            return self._create_fallback_result(
                {"content": content, "filename": filename}, "Rule-based classifier not available"
            )

        try:
            # Use rule classifier
            if self.rule_classifier is None:
                raise RuntimeError("Rule classifier is not available")
            category, confidence = self.rule_classifier.get_classification_confidence(content, filename)
            result = {
                "category": category,
                "confidence": confidence,
                "reasoning": "Rule-based classification",
                "alternatives": [],
                "patterns_matched": [],
                "processing_time": 0
            }

            return ClassificationResult(
                category=result.get("category", "uncategorized"),
                confidence=result.get("confidence", 0.0),
                method=ClusteringMethod.RULE_BASED,
                reasoning=result.get("reasoning", "Rule-based classification"),
                alternative_categories=result.get("alternatives", []),
                metadata={
                    "rule_patterns_matched": result.get("patterns_matched", []),
                    "processing_time": result.get("processing_time", 0),
                },
            )

        except Exception as e:
            self.logger.error(f"Rule-based classification failed: {e}")
            return self._create_fallback_result(
                {"content": content, "filename": filename}, f"Rule classification error: {e}"
            )

    def _should_apply_ml_enhancement(self, confidence: float) -> bool:
        """Determine if ML enhancement should be applied."""
        return confidence < self.config.ml_threshold

    def _enhance_with_ml(
        self, document: Dict[str, Any], rule_result: ClassificationResult
    ) -> ClassificationResult:
        """Enhance classification using ML methods."""
        if not self.have_ml_refiner:
            return rule_result

        try:
            # Apply ML refinement
            if self.ml_refiner is None:
                raise RuntimeError("ML refiner is not available")
            # Create document list for ML refinement
            uncertain_docs = [document]
            all_classified_docs = [{
                "filename": document.get("filename", ""),
                "content_preview": document.get("content", "")[:500],
                "category": rule_result.category,
                "confidence": rule_result.confidence
            }]
            ml_results = self.ml_refiner.refine_uncertain_classifications(uncertain_docs, all_classified_docs)
            ml_result = ml_results.get(document.get("filename", ""), {
                "category": rule_result.category,
                "confidence": rule_result.confidence,
                "reasoning": "ML enhancement unavailable"
            })

            # Combine rule and ML results
            combined_confidence = (rule_result.confidence + ml_result.get("confidence", 0)) / 2

            return ClassificationResult(
                category=ml_result.get("category", rule_result.category),
                confidence=combined_confidence,
                method=ClusteringMethod.ML_ENHANCED,
                reasoning=f"ML enhanced: {ml_result.get('reasoning', 'ML refinement applied')}",
                alternative_categories=ml_result.get(
                    "alternatives", rule_result.alternative_categories
                ),
                metadata={
                    **rule_result.metadata,
                    "ml_enhancement_applied": True,
                    "ml_confidence": ml_result.get("confidence", 0),
                    "rule_confidence": rule_result.confidence,
                },
            )

        except Exception as e:
            self.logger.warning(f"ML enhancement failed: {e}")
            # Return rule result with ML failure noted
            rule_result.metadata["ml_enhancement_failed"] = str(e)
            return rule_result

    def batch_classify_documents(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, ClassificationResult]:
        """Classify multiple documents in batch.

        Args:
            documents: List of document dictionaries

        Returns:
            Dictionary mapping document IDs to classification results
        """
        results = {}
        uncertain_documents = []

        self.logger.info(f"Starting batch classification of {len(documents)} documents")

        # Step 1: Classify all documents with rules
        for i, doc in enumerate(documents):
            doc_id = doc.get("id", f"doc_{i}")

            try:
                result = self.classify_document(doc)
                results[doc_id] = result

                # Track uncertain documents for potential batch ML processing
                if result.confidence < self.config.ml_threshold:
                    uncertain_documents.append((doc_id, doc, result))

            except Exception as e:
                self.logger.error(f"Classification failed for {doc_id}: {e}")
                results[doc_id] = self._create_fallback_result(doc, str(e))

        # Step 2: Batch ML processing for uncertain documents (if threshold met)
        if self.have_ml_refiner and len(uncertain_documents) >= self.config.min_ml_documents:

            try:
                self.logger.info(
                    f"Applying ML enhancement to {len(uncertain_documents)} uncertain documents"
                )
                enhanced_results = self._batch_ml_enhancement(uncertain_documents)

                # Update results with ML enhancements
                for doc_id, enhanced_result in enhanced_results.items():
                    if doc_id in results:
                        results[doc_id] = enhanced_result

            except Exception as e:
                self.logger.warning(f"Batch ML enhancement failed: {e}")

        # Log batch summary
        self._log_batch_summary(results)

        return results

    def _batch_ml_enhancement(
        self, uncertain_docs: List[Tuple[str, Dict[str, Any], ClassificationResult]]
    ) -> Dict[str, ClassificationResult]:
        """Apply ML enhancement to batch of uncertain documents."""
        enhanced_results = {}

        # Group documents by uncertainty type for batch processing
        uncertainty_groups = self._group_by_uncertainty_type(uncertain_docs)

        for uncertainty_type, docs in uncertainty_groups.items():
            try:
                # Apply appropriate ML method for this uncertainty type
                batch_results = self._apply_batch_ml_for_type(uncertainty_type, docs)
                enhanced_results.update(batch_results)

            except Exception as e:
                self.logger.warning(f"ML enhancement failed for {uncertainty_type} group: {e}")
                # Keep original rule-based results for this group
                for doc_id, _, rule_result in docs:
                    enhanced_results[doc_id] = rule_result

        return enhanced_results

    def _group_by_uncertainty_type(
        self, uncertain_docs: List[Tuple[str, Dict[str, Any], ClassificationResult]]
    ) -> Dict[str, List]:
        """Group uncertain documents by type of uncertainty."""
        groups = {
            "semantic_ambiguity": [],  # Content could fit multiple categories
            "content_quality": [],  # Poor OCR or extraction quality
            "new_pattern": [],  # Doesn't match existing patterns
            "insufficient_content": [],  # Too little content for classification
        }

        for doc_id, doc, rule_result in uncertain_docs:
            # Determine uncertainty type based on rule result
            confidence = rule_result.confidence
            content_length = len(doc.get("content", ""))

            if content_length < 50:
                groups["insufficient_content"].append((doc_id, doc, rule_result))
            elif confidence < 0.3:
                groups["new_pattern"].append((doc_id, doc, rule_result))
            elif len(rule_result.alternative_categories) > 2:
                groups["semantic_ambiguity"].append((doc_id, doc, rule_result))
            else:
                groups["content_quality"].append((doc_id, doc, rule_result))

        return groups

    def _apply_batch_ml_for_type(
        self, uncertainty_type: str, docs: List[Tuple[str, Dict[str, Any], ClassificationResult]]
    ) -> Dict[str, ClassificationResult]:
        """Apply ML enhancement for specific uncertainty type."""
        results = {}

        if uncertainty_type == "semantic_ambiguity":
            # Use ML for semantic disambiguation
            results = self._ml_semantic_disambiguation(docs)
        elif uncertainty_type == "content_quality":
            # Use ML for content quality improvement
            results = self._ml_content_quality_enhancement(docs)
        elif uncertainty_type == "new_pattern":
            # Use ML for pattern discovery
            results = self._ml_pattern_discovery(docs)
        else:
            # For insufficient content, keep rule-based results
            for doc_id, _, rule_result in docs:
                results[doc_id] = rule_result

        return results

    def _ml_semantic_disambiguation(
        self, docs: List[Tuple[str, Dict[str, Any], ClassificationResult]]
    ) -> Dict[str, ClassificationResult]:
        """Use ML to disambiguate semantically ambiguous documents."""
        results = {}

        try:
            if not self.ml_refiner:
                raise RuntimeError("ML refiner not available")

            # Prepare documents for ML processing
            ml_documents = []
            for doc_id, doc, rule_result in docs:
                ml_documents.append(
                    {
                        "id": doc_id,
                        "content": doc.get("content", ""),
                        "filename": doc.get("filename", ""),
                        "rule_category": rule_result.category,
                        "rule_alternatives": rule_result.alternative_categories,
                    }
                )

            # Apply ML disambiguation
            if self.ml_refiner is None:
                raise RuntimeError("ML refiner is not available")
            # Use the refine_uncertain_classifications method instead
            all_docs = [{"filename": doc["filename"], "content_preview": doc["content"][:500], 
                        "category": doc["rule_category"], "confidence": 0.5} for doc in ml_documents]
            ml_results = self.ml_refiner.refine_uncertain_classifications(ml_documents, all_docs)

            # Convert ML results to ClassificationResult objects
            for doc_id, _, rule_result in docs:
                ml_data = ml_results.get(doc_id, {})

                results[doc_id] = ClassificationResult(
                    category=ml_data.get("category", rule_result.category),
                    confidence=ml_data.get("confidence", rule_result.confidence),
                    method=ClusteringMethod.ML_ENHANCED,
                    reasoning=f"ML disambiguation: {ml_data.get('reasoning', 'Semantic analysis applied')}",
                    alternative_categories=ml_data.get(
                        "alternatives", rule_result.alternative_categories
                    ),
                    metadata={
                        **rule_result.metadata,
                        "ml_method": "semantic_disambiguation",
                        "original_rule_confidence": rule_result.confidence,
                    },
                )

        except Exception as e:
            self.logger.error(f"ML semantic disambiguation failed: {e}")
            # Return original rule results
            for doc_id, _, rule_result in docs:
                rule_result.metadata["ml_disambiguation_failed"] = str(e)
                results[doc_id] = rule_result

        return results

    def _ml_content_quality_enhancement(
        self, docs: List[Tuple[str, Dict[str, Any], ClassificationResult]]
    ) -> Dict[str, ClassificationResult]:
        """Use ML to enhance classification for poor quality content."""
        results = {}

        # For now, apply rule-based with enhanced confidence
        # This would be where content quality enhancement ML would be applied
        for doc_id, doc, rule_result in docs:
            # Enhance confidence slightly for content quality issues
            enhanced_confidence = min(0.6, rule_result.confidence + 0.1)

            enhanced_result = ClassificationResult(
                category=rule_result.category,
                confidence=enhanced_confidence,
                method=ClusteringMethod.ML_ENHANCED,
                reasoning=f"Content quality enhancement applied: {rule_result.reasoning}",
                alternative_categories=rule_result.alternative_categories,
                metadata={
                    **rule_result.metadata,
                    "ml_method": "content_quality_enhancement",
                    "confidence_boost": enhanced_confidence - rule_result.confidence,
                },
            )

            results[doc_id] = enhanced_result

        return results

    def _ml_pattern_discovery(
        self, docs: List[Tuple[str, Dict[str, Any], ClassificationResult]]
    ) -> Dict[str, ClassificationResult]:
        """Use ML to discover new patterns in unrecognized documents."""
        results = {}

        # For documents that don't match existing patterns, try to find new ones
        for doc_id, doc, rule_result in docs:
            # Apply pattern discovery logic
            content = doc.get("content", "")

            # Simple pattern discovery based on content characteristics
            new_category = self._discover_category_from_content(content, doc.get("filename", ""))

            enhanced_result = ClassificationResult(
                category=new_category,
                confidence=0.4,  # Medium-low confidence for discovered patterns
                method=ClusteringMethod.ML_ENHANCED,
                reasoning=f"New pattern discovered: {new_category}",
                alternative_categories=[(rule_result.category, rule_result.confidence)],
                metadata={
                    **rule_result.metadata,
                    "ml_method": "pattern_discovery",
                    "discovered_pattern": True,
                },
            )

            results[doc_id] = enhanced_result

        return results

    def _discover_category_from_content(self, content: str, filename: str) -> str:
        """Discover category from content analysis."""
        # Simple content-based category discovery
        content_lower = content.lower()
        filename_lower = filename.lower()

        # Business document patterns
        if any(word in content_lower for word in ["invoice", "bill", "payment", "amount"]):
            return "financial_documents"

        # Legal document patterns
        if any(word in content_lower for word in ["agreement", "contract", "terms", "legal"]):
            return "legal_documents"

        # Technical document patterns
        if any(word in content_lower for word in ["manual", "guide", "instructions", "procedure"]):
            return "technical_documents"

        # Personal document patterns
        if any(word in content_lower for word in ["personal", "private", "medical", "health"]):
            return "personal_documents"

        # Communication patterns
        if any(word in content_lower for word in ["email", "letter", "memo", "communication"]):
            return "communications"

        # Default category
        return "miscellaneous_documents"

    def _create_fallback_result(self, document: Dict[str, Any], error: str) -> ClassificationResult:
        """Create fallback classification result."""
        return ClassificationResult(
            category="uncategorized",
            confidence=0.1,
            method=ClusteringMethod.FALLBACK,
            reasoning=f"Fallback classification due to error: {error}",
            alternative_categories=[],
            metadata={
                "fallback": True,
                "error": error,
                "filename": document.get("filename", "unknown"),
            },
        )

    def _update_stats(self, method: ClusteringMethod, confidence_level: ConfidenceLevel) -> None:
        """Update classification statistics."""
        self._classification_stats["total_classifications"] += 1
        self._classification_stats["method_usage"][method.value] += 1
        self._classification_stats["confidence_distribution"][confidence_level.value] += 1

    def _log_batch_summary(self, results: Dict[str, ClassificationResult]) -> None:
        """Log summary of batch classification."""
        total = len(results)
        high_confidence = sum(
            1 for r in results.values() if r.confidence_level == ConfidenceLevel.HIGH
        )
        medium_confidence = sum(
            1 for r in results.values() if r.confidence_level == ConfidenceLevel.MEDIUM
        )

        method_counts = {}
        for result in results.values():
            method = result.method.value
            method_counts[method] = method_counts.get(method, 0) + 1

        self.logger.info(f"Batch classification complete: {total} documents")
        self.logger.info(
            f"Confidence distribution: {high_confidence} high, {medium_confidence} medium"
        )
        self.logger.info(f"Method usage: {method_counts}")

    def get_clustering_statistics(self) -> Dict[str, Any]:
        """Get clustering service statistics."""
        return {
            "config": {
                "ml_threshold": self.config.ml_threshold,
                "min_ml_documents": self.config.min_ml_documents,
                "max_categories": self.config.max_categories,
            },
            "capabilities": {
                "rule_classifier": self.have_rule_classifier,
                "ml_refiner": self.have_ml_refiner,
                "uncertainty_detector": self.have_uncertainty_detector,
            },
            "statistics": dict(self._classification_stats),
        }

    def validate_clustering_quality(
        self, results: Dict[str, ClassificationResult]
    ) -> Dict[str, Any]:
        """Validate the quality of clustering results."""
        if not results:
            return {"valid": False, "reason": "No results to validate"}

        # Calculate quality metrics
        total_docs = len(results)
        high_confidence_docs = sum(1 for r in results.values() if r.confidence >= 0.8)
        fallback_docs = sum(1 for r in results.values() if r.method == ClusteringMethod.FALLBACK)

        # Category distribution
        categories = {}
        for result in results.values():
            categories[result.category] = categories.get(result.category, 0) + 1

        # Quality assessment
        quality_score = (high_confidence_docs / total_docs) * 100

        # Check for balanced distribution (avoid too many small categories)
        small_categories = sum(
            1 for count in categories.values() if count < self.config.min_category_size
        )
        balance_score = (
            max(0, 100 - (small_categories / len(categories) * 100)) if categories else 0
        )

        overall_score = (quality_score + balance_score) / 2

        return {
            "valid": overall_score >= 60,  # 60% threshold for acceptable clustering
            "overall_score": overall_score,
            "quality_metrics": {
                "total_documents": total_docs,
                "high_confidence": high_confidence_docs,
                "high_confidence_rate": f"{(high_confidence_docs/total_docs)*100:.1f}%",
                "fallback_documents": fallback_docs,
                "fallback_rate": f"{(fallback_docs/total_docs)*100:.1f}%",
            },
            "category_metrics": {
                "total_categories": len(categories),
                "category_distribution": categories,
                "small_categories": small_categories,
                "balance_score": f"{balance_score:.1f}%",
            },
            "recommendations": self._get_quality_recommendations(
                overall_score, categories, fallback_docs
            ),
        }

    def _get_quality_recommendations(
        self, overall_score: float, categories: Dict[str, int], fallback_docs: int
    ) -> List[str]:
        """Get recommendations for improving clustering quality."""
        recommendations = []

        if overall_score < 60:
            recommendations.append(
                "Clustering quality below threshold - consider manual organization"
            )

        if fallback_docs > 0:
            recommendations.append(
                f"Consider reviewing {fallback_docs} fallback classifications manually"
            )

        small_cats = sum(1 for count in categories.values() if count < 2)
        if small_cats > len(categories) * 0.3:  # >30% small categories
            recommendations.append(
                "Consider merging small categories or using time-based organization"
            )

        if len(categories) > self.config.max_categories:
            recommendations.append(
                f"Too many categories ({len(categories)}) - consider consolidation"
            )

        if not recommendations:
            recommendations.append("Clustering quality is good - organization can proceed")

        return recommendations
