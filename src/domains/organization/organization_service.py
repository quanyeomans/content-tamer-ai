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

    def __init__(self, target_folder: str, config: Optional[ClusteringConfig] = None):
        """Initialize organization service.

        Args:
            target_folder: Target directory for organization
            config: Clustering configuration (optional)
        """
        self.target_folder = target_folder
        self.logger = logging.getLogger(__name__)

        # Initialize domain services
        self.clustering_service = ClusteringService(config)
        self.folder_service = FolderService()
        self.learning_service = LearningService(target_folder)

        # Load learned preferences
        self.preferences = self.learning_service.preferences

    def organize_processed_documents(
        self, documents: List[Dict[str, Any]], enable_learning: bool = True
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
                f"Starting organization session {session_id} for {len(documents)} documents"
            )

            # Step 1: Classify documents using clustering service
            self.logger.info("Step 1: Classifying documents...")
            classifications = self.clustering_service.batch_classify_documents(documents)

            # Step 2: Validate clustering quality
            quality_validation = self.clustering_service.validate_clustering_quality(
                classifications
            )
            if not quality_validation["valid"]:
                self.logger.warning(
                    f"Clustering quality below threshold: {quality_validation['overall_score']:.1f}"
                )

                # Apply fallback strategy if quality is poor
                if quality_validation["overall_score"] < 40:  # Very poor quality
                    return self._fallback_to_time_based_organization(documents, session_id)

            # Step 3: Create folder structure
            self.logger.info("Step 3: Creating folder structure...")
            folder_structure, file_operations = self.folder_service.create_folder_structure(
                self.target_folder, classifications
            )

            # Step 4: Validate folder structure
            structure_validation = self.folder_service.validate_folder_structure(folder_structure)
            if not structure_validation["valid"]:
                raise RuntimeError(f"Invalid folder structure: {structure_validation['issues']}")

            # Step 5: Execute file operations
            self.logger.info(f"Step 5: Executing {len(file_operations)} file operations...")
            operation_results = self.folder_service.execute_file_operations(file_operations)

            # Step 6: Learn from session (if enabled)
            learning_results = {}
            if enable_learning and operation_results["successful_operations"] > 0:
                self.logger.info("Step 6: Learning from session results...")
                learning_results = self.learning_service.learn_from_session(
                    classifications,
                    folder_structure,
                    {
                        "overall_quality": quality_validation["overall_score"],
                        "success_rate": operation_results["successful_operations"]
                        / operation_results["total_operations"],
                        "method_distribution": self._get_method_distribution(classifications),
                    },
                )

            # Compile final results
            organization_results = {
                "session_id": session_id,
                "success": operation_results["successful_operations"] > 0,
                "documents_processed": len(documents),
                "files_organized": operation_results["moved_files"],
                "directories_created": operation_results["created_directories"],
                "classification_results": classifications,
                "folder_structure": folder_structure,
                "operation_results": operation_results,
                "quality_metrics": quality_validation,
                "learning_results": learning_results,
                "recommendations": quality_validation.get("recommendations", []),
            }

            self.logger.info(
                f"Organization session {session_id} completed: {operation_results['moved_files']} files organized"
            )
            return organization_results

        except Exception as e:
            self.logger.error(f"Document organization failed: {e}")
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
                "classification_results": time_classifications,
                "folder_structure": time_structure,
                "operation_results": operation_results,
                "recommendations": [
                    "Used time-based fallback due to poor content clustering",
                    "Consider manual reorganization for better categorization",
                ],
            }

        except Exception as e:
            self.logger.error(f"Time-based fallback also failed: {e}")
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
                "structure_type": folder_structure.structure_type.value,
                "recommendations": quality_validation.get("recommendations", []),
            }

        except Exception as e:
            self.logger.error(f"Organization preview failed: {e}")
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
            self.logger.error(f"Status check failed: {e}")
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
                self.logger.error(f"Invalid preferences: {valid_preferences['errors']}")
                return False

            # Update preferences
            self.preferences.update(preferences)

            # Save to persistent storage
            success = self.learning_service.state_manager.save_organization_preferences(
                self.preferences
            )

            if success:
                self.logger.info(f"Updated organization preferences: {list(preferences.keys())}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to configure preferences: {e}")
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
