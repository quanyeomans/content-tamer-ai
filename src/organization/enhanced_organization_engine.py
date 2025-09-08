"""
Enhanced Organization Engine

Extends BasicOrganizationEngine with Phase 2 ML capabilities:
- Selective ML refinement for uncertain classifications
- Advanced uncertainty detection
- Hybrid state management with analytics
- Maintains backward compatibility with Phase 1
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from content_analysis.ml_refiner import SelectiveMLRefinement
from content_analysis.uncertainty_detector import UncertaintyDetector

from .hybrid_state_manager import HybridStateManager
from .organization_engine import BasicOrganizationEngine


class EnhancedOrganizationEngine(BasicOrganizationEngine):
    """Enhanced organization engine with Phase 2 ML capabilities."""

    def __init__(self, target_folder: str, ml_enhancement_level: int = 2):
        """
        Initialize enhanced organization engine.

        Args:
            target_folder: Directory where documents will be organized
            ml_enhancement_level: 1=Phase1 only, 2=Phase2 ML, 3=Phase3 (future)
        """
        # Initialize base functionality
        super().__init__(target_folder)

        self.ml_enhancement_level = ml_enhancement_level

        # Replace state manager with hybrid version for Phase 2
        if ml_enhancement_level >= 2:
            self.state_manager = HybridStateManager(target_folder)
            self.uncertainty_detector = UncertaintyDetector()
            self.ml_refiner = SelectiveMLRefinement()

            logging.info(
                f"Enhanced organization engine initialized (Level {ml_enhancement_level})"
            )
        else:
            logging.info(
                "Enhanced organization engine running in Phase 1 compatibility mode"
            )

    def organize_documents(
        self, processed_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enhanced document organization with selective ML refinement.

        Args:
            processed_documents: List of document info dicts with filename, content, path

        Returns:
            Enhanced organization results including ML metrics
        """
        start_time = time.time()

        logging.info(
            f"Starting enhanced organization of {len(processed_documents)} documents"
        )

        # Step 1: Perform base classification (Phase 1)
        base_result = self._perform_base_classification(processed_documents)
        classified_docs = base_result["classified_documents"]

        # Step 2: Apply ML enhancement if enabled
        if self.ml_enhancement_level >= 2:
            ml_result = self._apply_ml_enhancement(classified_docs)
            classified_docs = ml_result["enhanced_documents"]
            ml_metrics = ml_result["ml_metrics"]
        else:
            ml_metrics = {"ml_applied": False, "reason": "ML enhancement disabled"}

        # Step 3: Generate organization structure with enhanced data
        temporal_analysis = self._analyze_temporal_patterns(classified_docs)
        organization_structure = self._generate_organization_structure(
            classified_docs, temporal_analysis
        )

        # Step 4: Calculate enhanced quality metrics
        quality_metrics = self._calculate_enhanced_quality_metrics(
            classified_docs, ml_metrics
        )

        # Step 5: Determine reorganization recommendation
        should_reorganize = self._should_apply_reorganization_logic(quality_metrics)

        processing_time = time.time() - start_time

        # Step 6: Save enhanced session data
        session_data = {
            "session_id": f"enhanced_org_session_{int(datetime.now().timestamp())}",
            "document_count": len(processed_documents),
            "classification_stats": self._get_classification_stats(classified_docs),
            "quality_metrics": quality_metrics,
            "temporal_analysis": temporal_analysis,
            "organization_structure": organization_structure,
            "should_reorganize": should_reorganize,
            "ml_enhancement_level": self.ml_enhancement_level,
            "processing_time": processing_time,
            "ml_metrics": ml_metrics,
        }

        # Save to hybrid state manager with analytics
        if self.ml_enhancement_level >= 2:
            self.state_manager.save_enhanced_session_data(
                session_data, processing_time, ml_metrics
            )
        else:
            self.state_manager.save_session_data(session_data)

        # Step 7: Execute organization plan if recommended
        execution_result = None
        if should_reorganize:
            try:
                from organization.file_executor import OrganizationFileExecutor
                executor = OrganizationFileExecutor(self.target_folder)
                
                # Validate plan before execution
                validation_result = executor.validate_organization_plan({
                    "success": True,
                    "organization_structure": organization_structure
                })
                
                if validation_result['valid']:
                    # Execute the organization plan
                    execution_result = executor.execute_organization_plan({
                        "success": True,
                        "organization_structure": organization_structure
                    })
                else:
                    execution_result = {
                        "success": False,
                        "reason": "Organization plan validation failed",
                        "validation_issues": validation_result['issues']
                    }
                    
            except ImportError as e:
                logging.warning(f"File executor not available: {e}")
                execution_result = {
                    "success": False,
                    "reason": "File execution components not available"
                }
            except Exception as e:
                logging.error(f"Organization execution failed: {e}")
                execution_result = {
                    "success": False,
                    "reason": f"Execution error: {str(e)}"
                }

        # Return comprehensive results including execution
        result = {
            "success": True,
            "organization_structure": organization_structure,
            "quality_metrics": quality_metrics,
            "classified_documents": classified_docs,
            "temporal_analysis": temporal_analysis,
            "should_reorganize": should_reorganize,
            "session_data": session_data,
            "ml_metrics": ml_metrics,
            "processing_time": processing_time,
        }
        
        if execution_result:
            result["execution_result"] = execution_result
            result["files_organized"] = execution_result.get("files_moved", 0)
        
        return result

    def _perform_base_classification(
        self, processed_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform base Phase 1 classification."""
        classified_docs = []
        classification_stats = defaultdict(int)

        for doc_info in processed_documents:
            try:
                # Extract content for classification
                content = self._extract_content_for_classification(doc_info)

                # Classify document using Phase 1 methods
                category, confidence = self.classifier.get_classification_confidence(
                    content, doc_info["filename"]
                )

                # Extract metadata
                metadata = self.metadata_extractor.extract_metadata(
                    content, doc_info["filename"]
                )

                # Create classified document record
                classified_doc = {
                    "original_path": doc_info["path"],
                    "filename": doc_info["filename"],
                    "category": category,
                    "confidence": confidence,
                    "metadata": metadata,
                    "content_preview": (
                        content[:200] + "..." if len(content) > 200 else content
                    ),
                    "classification_method": "rule_based",
                }

                classified_docs.append(classified_doc)
                classification_stats[category] += 1

            except Exception as e:
                logging.warning(f"Failed to classify {doc_info['filename']}: {e}")
                # Add as unclassified
                classified_docs.append(
                    {
                        "original_path": doc_info["path"],
                        "filename": doc_info["filename"],
                        "category": "other",
                        "confidence": 0.0,
                        "metadata": {},
                        "error": str(e),
                        "classification_method": "error",
                    }
                )
                classification_stats["other"] += 1

        return {
            "classified_documents": classified_docs,
            "classification_stats": classification_stats,
        }

    def _apply_ml_enhancement(
        self, classified_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply ML enhancement to uncertain classifications."""
        ml_start_time = time.time()

        try:
            # Detect uncertain classifications
            certain_docs, uncertain_docs = (
                self.uncertainty_detector.detect_uncertain_documents(classified_docs)
            )

            logging.info(
                f"ML enhancement: {len(certain_docs)} certain, {len(uncertain_docs)} uncertain"
            )

            # Apply ML refinement to uncertain documents
            ml_refined_classifications = {}
            if uncertain_docs and self.ml_refiner.is_ml_available():
                ml_refined_classifications = (
                    self.ml_refiner.refine_uncertain_classifications(
                        uncertain_docs, classified_docs
                    )
                )

            # Update classifications with ML refinement results
            enhanced_docs = []
            ml_refined_count = 0

            for doc in classified_docs:
                filename = doc["filename"]

                if filename in ml_refined_classifications:
                    # Update with ML refinement
                    ml_result = ml_refined_classifications[filename]
                    doc["category"] = ml_result["category"]
                    doc["confidence"] = ml_result["confidence"]
                    doc["classification_method"] = "ml_refinement"
                    doc["ml_details"] = {
                        "cluster_id": ml_result.get("cluster_id"),
                        "cluster_size": ml_result.get("cluster_size"),
                        "original_category": doc.get(
                            "original_category", doc["category"]
                        ),
                        "original_confidence": doc.get(
                            "original_confidence", doc["confidence"]
                        ),
                    }
                    ml_refined_count += 1

                enhanced_docs.append(doc)

            ml_processing_time = time.time() - ml_start_time

            # Prepare ML metrics
            ml_metrics = {
                "ml_applied": True,
                "ml_available": self.ml_refiner.is_ml_available(),
                "total_documents": len(classified_docs),
                "certain_documents": len(certain_docs),
                "uncertain_documents": len(uncertain_docs),
                "ml_refined_documents": ml_refined_count,
                "ml_refinement_rate": (
                    ml_refined_count / len(uncertain_docs) if uncertain_docs else 0
                ),
                "processing_time": ml_processing_time,
                "uncertainty_threshold": self.uncertainty_detector.confidence_threshold,
                "model_name": (
                    "all-mpnet-base-v2" if self.ml_refiner.is_ml_available() else None
                ),
            }

            return {"enhanced_documents": enhanced_docs, "ml_metrics": ml_metrics}

        except Exception as e:
            logging.warning(f"ML enhancement failed: {e}")
            # Fallback to original classifications
            return {
                "enhanced_documents": classified_docs,
                "ml_metrics": {
                    "ml_applied": False,
                    "error": str(e),
                    "fallback_used": True,
                },
            }

    def _calculate_enhanced_quality_metrics(
        self, classified_docs: List[Dict[str, Any]], ml_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate enhanced quality metrics including ML impact."""
        # Base quality metrics
        base_metrics = self._calculate_quality_metrics(
            classified_docs, self._get_classification_stats(classified_docs)
        )

        # Add ML-specific metrics
        if ml_metrics.get("ml_applied", False):
            # Calculate rule-based vs ML accuracy
            rule_based_docs = [
                doc
                for doc in classified_docs
                if doc.get("classification_method") == "rule_based"
            ]
            ml_refined_docs = [
                doc
                for doc in classified_docs
                if doc.get("classification_method") == "ml_refinement"
            ]

            if rule_based_docs:
                rule_accuracy = sum(
                    doc.get("confidence", 0) for doc in rule_based_docs
                ) / len(rule_based_docs)
                base_metrics["rule_accuracy"] = rule_accuracy

            if ml_refined_docs:
                ml_accuracy = sum(
                    doc.get("confidence", 0) for doc in ml_refined_docs
                ) / len(ml_refined_docs)
                base_metrics["ml_accuracy"] = ml_accuracy

            # Overall ML impact
            base_metrics.update(
                {
                    "ml_enhancement_applied": True,
                    "uncertain_documents": ml_metrics.get("uncertain_documents", 0),
                    "ml_refined_documents": ml_metrics.get("ml_refined_documents", 0),
                    "ml_refinement_rate": ml_metrics.get("ml_refinement_rate", 0),
                    "ml_processing_time": ml_metrics.get("processing_time", 0),
                }
            )
        else:
            base_metrics.update(
                {
                    "ml_enhancement_applied": False,
                    "ml_unavailable_reason": ml_metrics.get("error", "ML disabled"),
                }
            )

        return base_metrics

    def _get_classification_stats(
        self, classified_docs: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Get classification statistics from enhanced documents."""
        stats = defaultdict(int)
        for doc in classified_docs:
            stats[doc.get("category", "other")] += 1
        return dict(stats)

    def get_advanced_insights(self) -> Dict[str, Any]:
        """Get advanced insights using hybrid state manager analytics."""
        if self.ml_enhancement_level >= 2 and hasattr(
            self.state_manager, "get_advanced_insights"
        ):
            try:
                return self.state_manager.get_advanced_insights()
            except Exception as e:
                logging.warning(f"Failed to get advanced insights: {e}")
                return {"error": f"Advanced insights unavailable: {e}"}
        else:
            return {"error": "Advanced insights require Phase 2 or higher"}

    def get_uncertainty_analysis(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get detailed uncertainty analysis for documents."""
        if self.ml_enhancement_level >= 2:
            return self.uncertainty_detector.get_uncertainty_summary(documents)
        else:
            return {"error": "Uncertainty analysis requires Phase 2 or higher"}

    def get_ml_stats(self) -> Dict[str, Any]:
        """Get ML refinement statistics and capabilities."""
        if self.ml_enhancement_level >= 2:
            stats = self.ml_refiner.get_ml_stats()
            stats["uncertainty_detector"] = {
                "confidence_threshold": self.uncertainty_detector.confidence_threshold
            }
            stats["enhancement_level"] = self.ml_enhancement_level
            return stats
        else:
            return {
                "enhancement_level": self.ml_enhancement_level,
                "ml_available": False,
                "reason": "ML enhancement requires Phase 2 or higher",
            }

    def tune_uncertainty_threshold(
        self, documents: List[Dict[str, Any]], target_ml_rate: float = 0.2
    ) -> float:
        """
        Automatically tune uncertainty threshold to achieve target ML usage rate.

        Args:
            documents: Sample documents for threshold analysis
            target_ml_rate: Target ML refinement rate (0.0 to 1.0)

        Returns:
            Optimal threshold value
        """
        if self.ml_enhancement_level < 2:
            raise ValueError("Threshold tuning requires Phase 2 or higher")

        threshold_analysis = self.uncertainty_detector.get_threshold_analysis(documents)

        best_threshold = 0.7
        best_diff = float("inf")

        for threshold_key, analysis in threshold_analysis.items():
            if threshold_key.startswith("threshold_"):
                threshold = float(threshold_key.split("_")[1])
                ml_rate = analysis["uncertainty_rate"]
                diff = abs(ml_rate - target_ml_rate)

                if diff < best_diff:
                    best_diff = diff
                    best_threshold = threshold

        # Apply the optimal threshold
        self.uncertainty_detector.adjust_threshold(best_threshold)

        logging.info(
            f"Tuned uncertainty threshold to {best_threshold} for ~{target_ml_rate:.1%} ML usage"
        )

        return best_threshold
