"""
Organization Service

Main orchestrating service for document organization domain.
Implements the progressive enhancement architecture from PRD_04.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .clustering_service import (
    ClassificationResult,
    ClusteringConfig,
    ClusteringMethod,
    ClusteringService,
)
from .folder_service import FiscalYearType, FolderService, FolderStructure, FolderStructureType
from .learning_service import LearningService


class OrganizationService:
    """Main service coordinating all organization domain operations."""

    def __init__(self, target_folder: str = None, config: Optional[ClusteringConfig] = None, spacy_model=None):
        """Initialize organization service.

        Args:
            target_folder: Target directory for organization
            config: Clustering configuration (optional)
            spacy_model: Pre-loaded spaCy model to use (for performance optimization)
        """
        self.target_folder = target_folder or "./output"  # Default if not provided
        self.logger = logging.getLogger(__name__)

        # Initialize domain services with shared spacy model
        self.clustering_service = ClusteringService(config, spacy_model=spacy_model)
        self.folder_service = FolderService()
        self.learning_service = LearningService(self.target_folder, spacy_model=spacy_model)

        # Load learned preferences
        self.preferences = self.learning_service.preferences

    def organize_processed_documents(
        self, documents: List[Dict[str, Any]], enable_learning: bool = True, ml_enhancement_level: int = 2
    ) -> Dict[str, Any]:
        """Organize processed documents using progressive enhancement.

        Args:
            documents: List of processed documents with content, filename, metadata
            enable_learning: Whether to learn from this session

        Returns:
            Dictionary with organization results
        """
        session_id = f"org_session_{int(datetime.now().timestamp())}"
        try:
            self.logger.info(
                "Starting organization session %s for %d documents", session_id, len(documents)
            )

            # Step 1: Classify documents using clustering service
            self.logger.info("Step 1: Classifying documents...")
            classifications = self.clustering_service.batch_classify_documents(documents)
            
            # Map classifications to actual file paths
            # The classifications dict might have doc IDs as keys, but we need actual file paths
            path_classifications = {}
            for doc_id, classification in classifications.items():
                # Find the corresponding document to get its actual path
                matching_doc = None
                for doc in documents:
                    # Check if this doc matches the doc_id
                    if (doc.get("current_path") == doc_id or 
                        doc.get("path") == doc_id or
                        doc.get("original_path") == doc_id or
                        doc.get("id") == doc_id):
                        matching_doc = doc
                        break
                
                if matching_doc:
                    # Use the current_path (renamed file) as the key for folder operations
                    actual_path = matching_doc.get("current_path") or matching_doc.get("path") or matching_doc.get("original_path")
                    if actual_path:
                        path_classifications[actual_path] = classification
                    else:
                        self.logger.warning("No valid path found for document: %s", doc_id)
                else:
                    # If doc_id is already a path, use it directly
                    if os.path.exists(doc_id) or os.path.isabs(doc_id):
                        path_classifications[doc_id] = classification
                    else:
                        self.logger.warning("Could not map classification for: %s", doc_id)

            # Step 2: Validate clustering quality
            quality_validation = self.clustering_service.validate_clustering_quality(
                path_classifications
            )
            if not quality_validation["valid"]:
                self.logger.warning(
                    "Clustering quality below threshold: %.1f", quality_validation['overall_score']
                )

                # Apply fallback strategy if quality is poor
                if quality_validation["overall_score"] < 40:  # Very poor quality
                    return self._fallback_to_time_based_organization(documents, session_id)

            # Step 3: Create folder structure
            self.logger.info("Step 3: Creating folder structure...")
            folder_structure, file_operations = self.folder_service.create_folder_structure(
                self.target_folder, path_classifications
            )

            # Step 4: Validate folder structure
            structure_validation = self.folder_service.validate_folder_structure(folder_structure)
            if not structure_validation["valid"]:
                raise RuntimeError(f"Invalid folder structure: {structure_validation['issues']}")

            # Step 5: Execute file operations
            self.logger.info("Step 5: Executing %d file operations...", len(file_operations))
            operation_results = self.folder_service.execute_file_operations(file_operations)

            # Step 6: Learn from session (if enabled)
            learning_results = {}
            if enable_learning and operation_results["successful_operations"] > 0:
                self.logger.info("Step 6: Learning from session results...")
                learning_results = self.learning_service.learn_from_session(
                    path_classifications,
                    folder_structure,
                    {
                        "overall_quality": quality_validation["overall_score"],
                        "success_rate": operation_results["successful_operations"]
                        / operation_results["total_operations"],
                        "method_distribution": self._get_method_distribution(path_classifications),
                    },
                )

            # Compile final results with expected API contract
            organization_results = {
                "session_id": session_id,
                "success": operation_results["successful_operations"] > 0,
                "documents_processed": len(documents),
                "files_organized": operation_results["moved_files"],
                "directories_created": operation_results["created_directories"],
                "classified_documents": self._format_classified_documents(path_classifications),
                "classification_results": path_classifications,
                # API Contract: Use organization_structure instead of folder_structure
                "organization_structure": self._format_organization_structure(folder_structure),
                "folder_structure": folder_structure,  # Keep for backward compatibility
                # API Contract: Map operation_results to execution_result
                "execution_result": self._format_execution_result(operation_results),
                "operation_results": operation_results,  # Keep for backward compatibility
                "quality_metrics": quality_validation,
                "learning_results": learning_results,
                "recommendations": quality_validation.get("recommendations", []),
                # API Contract: Add should_reorganize flag
                "should_reorganize": quality_validation["overall_score"] >= 70.0,
                # API Contract: Add ML metrics
                "ml_metrics": self._format_ml_metrics(path_classifications, ml_enhancement_level),
                # API Contract: Add temporal analysis for level 3
                "temporal_analysis": self._format_temporal_analysis(folder_structure, ml_enhancement_level),
            }

            self.logger.info(
                "Organization session %s completed: %d files organized", session_id, operation_results['moved_files']
            )
            return organization_results

        except Exception as e:
            self.logger.error("Document organization failed: %s", e)
            return {
                "session_id": session_id,
                "success": False,
                "error": str(e),
                "documents_processed": len(documents),
                "files_organized": 0,
                "recommendations": ["Manual organization recommended due to processing error"],
            }

    def _get_method_distribution(
        self, classifications: Dict[str, ClassificationResult]
    ) -> Dict[str, int]:
        """Get distribution of classification methods used."""
        distribution = {}

        for result in classifications.values():
            # Defensive check for None method
            if result.method is None:
                method = "unknown"
            else:
                method = result.method.value
            distribution[method] = distribution.get(method, 0) + 1

        return distribution

    def _fallback_to_time_based_organization(
        self, documents: List[Dict[str, Any]], session_id: str
    ) -> Dict[str, Any]:
        """Fallback to simple time-based organization when clustering fails."""
        self.logger.info("Falling back to time-based organization due to poor clustering quality")

        try:
            # Create simple time-based classification
            time_classifications = {}
            for doc in documents:
                file_path = doc.get("file_path", "")

                # Use file modification time for classification
                try:
                    mod_time = os.path.getmtime(file_path)
                    year = datetime.fromtimestamp(mod_time).year
                    category = f"documents_{year}"

                    time_classifications[file_path] = ClassificationResult(
                        category=category,
                        confidence=0.9,  # Time-based is always confident
                        method=ClusteringMethod.FALLBACK,
                        reasoning=f"Time-based fallback: {year}",
                        alternative_categories=[],
                        metadata={"fallback": True, "year": year},
                    )

                except Exception as e:
                    # Final fallback
                    time_classifications[file_path] = ClassificationResult(
                        category="uncategorized",
                        confidence=0.5,
                        method=ClusteringMethod.FALLBACK,
                        reasoning="Time detection failed",
                        alternative_categories=[],
                        metadata={"fallback": True, "error": str(e)},
                    )

            # Create simple folder structure
            time_structure = FolderStructure(
                structure_type=FolderStructureType.TIME_FIRST,
                fiscal_year_type=FiscalYearType.CALENDAR,
                time_granularity="year",
                base_path=self.target_folder,
                categories=list(set(r.category for r in time_classifications.values())),
                metadata={"fallback": True, "method": "time_based"},
            )

            # Execute time-based organization
            _, file_operations = self.folder_service.create_folder_structure(
                self.target_folder, time_classifications, time_structure
            )

            operation_results = self.folder_service.execute_file_operations(file_operations)

            return {
                "session_id": session_id,
                "success": True,
                "fallback_method": "time_based",
                "documents_processed": len(documents),
                "files_organized": operation_results["moved_files"],
                "directories_created": operation_results["created_directories"],
                "classified_documents": self._format_classified_documents(time_classifications),
                "classification_results": time_classifications,
                # API Contract: Use organization_structure instead of folder_structure
                "organization_structure": self._format_organization_structure(time_structure),
                "folder_structure": time_structure,  # Keep for backward compatibility
                # API Contract: Map operation_results to execution_result
                "execution_result": self._format_execution_result(operation_results),
                "operation_results": operation_results,  # Keep for backward compatibility
                "quality_metrics": {"overall_score": 40.0, "valid": False, "recommendations": ["Time-based fallback used"]},
                # API Contract: Add should_reorganize flag
                "should_reorganize": True,  # Always true for time-based fallback
                # API Contract: Add ML metrics (disabled for fallback)
                "ml_metrics": {"ml_applied": False, "ml_available": False, "ml_enhancement_level": 1},
                # API Contract: Add temporal analysis (empty for fallback)
                "temporal_analysis": {},
                "recommendations": [
                    "Used time-based fallback due to poor content clustering",
                    "Consider manual reorganization for better categorization",
                ],
            }

        except Exception as e:
            self.logger.error("Time-based fallback also failed: %s", e)
            return {
                "session_id": session_id,
                "success": False,
                "error": f"All organization methods failed: {e}",
                "documents_processed": len(documents),
                "files_organized": 0,
            }

    def preview_organization(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Preview organization without actually moving files.

        Args:
            documents: Documents to preview organization for

        Returns:
            Preview of proposed organization structure
        """
        try:
            # Classify documents
            classifications = self.clustering_service.batch_classify_documents(documents)

            # Create folder structure (but don't execute)
            folder_structure, file_operations = self.folder_service.create_folder_structure(
                self.target_folder, classifications
            )

            # Validate quality
            quality_validation = self.clustering_service.validate_clustering_quality(
                classifications
            )

            # Group operations by category for preview
            operations_by_category = {}
            for operation in file_operations:
                if operation.operation_type == "move":
                    category = operation.category
                    if category not in operations_by_category:
                        operations_by_category[category] = []
                    operations_by_category[category].append(operation.source_path)

            return {
                "preview": True,
                "folder_structure": folder_structure,
                "operations_by_category": operations_by_category,
                "total_operations": len(file_operations),
                "quality_metrics": quality_validation,
                "categories": folder_structure.categories,
                "structure_type": folder_structure.structure_type.value if folder_structure.structure_type else "unknown",
                "recommendations": quality_validation.get("recommendations", []),
            }

        except Exception as e:
            self.logger.error("Organization preview failed: %s", e)
            return {"preview": True, "error": str(e), "success": False}

    def get_organization_status(self) -> Dict[str, Any]:
        """Get current organization status and capabilities."""
        try:
            # Check target folder
            folder_stats = self.folder_service.get_folder_statistics(self.target_folder)

            # Get clustering capabilities
            clustering_stats = self.clustering_service.get_clustering_statistics()

            # Get learning metrics
            learning_metrics = self.learning_service.get_learning_metrics()

            return {
                "target_folder": self.target_folder,
                "folder_statistics": folder_stats,
                "clustering_capabilities": clustering_stats,
                "learning_status": {
                    "total_sessions": learning_metrics.total_sessions,
                    "average_quality": f"{learning_metrics.average_quality_score:.2f}",
                    "improvement_trend": f"{learning_metrics.improvement_trend:+.2f}",
                    "user_corrections": learning_metrics.user_corrections,
                },
                "current_preferences": {
                    k: v
                    for k, v in self.preferences.items()
                    if k in ["structure_type", "ml_threshold", "learning_enabled"]
                },
                "ready_for_organization": clustering_stats["capabilities"]["rule_classifier"],
            }

        except Exception as e:
            self.logger.error("Status check failed: %s", e)
            return {
                "target_folder": self.target_folder,
                "error": str(e),
                "ready_for_organization": False,
            }

    def configure_organization_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update organization preferences.

        Args:
            preferences: New preferences to apply

        Returns:
            True if preferences were updated successfully
        """
        try:
            # Validate preferences
            valid_preferences = self._validate_preferences(preferences)
            if not valid_preferences["valid"]:
                self.logger.error("Invalid preferences: %s", valid_preferences["errors"])
                return False

            # Update preferences
            self.preferences.update(preferences)

            # Save to persistent storage
            success = self.learning_service.state_manager.save_organization_preferences(
                self.preferences
            )

            if success:
                self.logger.info("Updated organization preferences: %s", list(preferences.keys()))

            return success

        except Exception as e:
            self.logger.error("Failed to configure preferences: %s", e)
            return False

    def _validate_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate organization preferences."""
        errors = []
        warnings = []

        # Validate specific preference values
        if "ml_threshold" in preferences:
            threshold = preferences["ml_threshold"]
            if not (0.0 <= threshold <= 1.0):
                errors.append("ML threshold must be between 0.0 and 1.0")

        if "max_categories" in preferences:
            max_cats = preferences["max_categories"]
            if not isinstance(max_cats, int) or max_cats < 1 or max_cats > 50:
                errors.append("Max categories must be integer between 1 and 50")

        if "quality_threshold" in preferences:
            quality_thresh = preferences["quality_threshold"]
            if not (0.0 <= quality_thresh <= 1.0):
                errors.append("Quality threshold must be between 0.0 and 1.0")

        # Validate structure type
        valid_structure_types = ["time_first", "category_first", "flat_time", "flat_category"]
        if "structure_type" in preferences:
            if preferences["structure_type"] not in valid_structure_types:
                errors.append(f"Structure type must be one of: {valid_structure_types}")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _format_classified_documents(self, classifications: Dict[str, ClassificationResult]) -> List[Dict[str, Any]]:
        """Format classification results for API contract."""
        classified_docs = []
        for doc_id, result in classifications.items():
            classified_docs.append({
                "document_id": doc_id,
                "category": result.category,
                "confidence": result.confidence,
                "method": result.method.value if result.method else "unknown",
                "reasoning": result.reasoning,
                "metadata": result.metadata,
            })
        return classified_docs

    def _format_organization_structure(self, folder_structure) -> Dict[str, Any]:
        """Format folder structure to match expected organization_structure API contract."""
        if not folder_structure:
            return {}
        
        return {
            "folders": folder_structure.categories,  # Map categories to folders for API contract
            "structure_type": folder_structure.structure_type.value if folder_structure.structure_type else "unknown",
            "time_granularity": folder_structure.time_granularity,
            "base_path": folder_structure.base_path,
            "categories": folder_structure.categories,
            "metadata": folder_structure.metadata,
        }

    def _format_execution_result(self, operation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format operation results to match expected execution_result API contract."""
        return {
            "success": operation_results.get("successful_operations", 0) > 0,
            "files_moved": operation_results.get("moved_files", 0),
            "files_failed": operation_results.get("failed_operations", 0),
            "total_files": operation_results.get("total_operations", 0),
            "created_directories": operation_results.get("created_directories", 0),
            "error_details": operation_results.get("operation_details", []),
            "operation_summary": operation_results.get("operation_summary", {}),
        }

    def _format_ml_metrics(self, classifications: Dict[str, ClassificationResult], ml_enhancement_level: int) -> Dict[str, Any]:
        """Format ML metrics to match expected API contract."""
        ml_applied_count = sum(1 for result in classifications.values() 
                              if result.metadata.get("ml_enhancement_applied", False))
        
        return {
            "ml_applied": ml_applied_count > 0,
            "ml_available": ml_enhancement_level >= 2,
            "ml_enhancement_level": ml_enhancement_level,
            "documents_enhanced": ml_applied_count,
            "total_documents": len(classifications),
            "ml_success_rate": (ml_applied_count / len(classifications)) if classifications else 0.0,
        }

    def _format_temporal_analysis(self, folder_structure, ml_enhancement_level: int) -> Dict[str, Any]:
        """Format temporal analysis to match expected API contract."""
        if ml_enhancement_level < 3:
            return {}
        
        return {
            "temporal_intelligence_applied": True,
            "recommended_time_structure": folder_structure.structure_type.value if folder_structure and folder_structure.structure_type else "year-based",
            "time_granularity": folder_structure.time_granularity if folder_structure else "year",
            "fiscal_year_type": folder_structure.fiscal_year_type.value if folder_structure and folder_structure.fiscal_year_type else "calendar",
            "temporal_patterns_detected": folder_structure.metadata.get("temporal_patterns", []) if folder_structure else [],
        }
