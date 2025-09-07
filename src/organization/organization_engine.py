"""
Basic Organization Engine

Core engine that integrates classification, metadata extraction, and state management
to provide intelligent document organization following the balanced architecture.
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import logging
from collections import defaultdict

# Import our Phase 1 components
from content_analysis.rule_classifier import EnhancedRuleBasedClassifier
from content_analysis.metadata_extractor import ContentMetadataExtractor
from organization.state_manager import SimpleStateManager


class BasicOrganizationEngine:
    """Basic organization engine implementing Phase 1 balanced architecture."""

    def __init__(self, target_folder: str):
        """
        Initialize organization engine for target folder.

        Args:
            target_folder: Directory where documents will be organized
        """
        self.target_folder = target_folder

        # Initialize components
        self.classifier = EnhancedRuleBasedClassifier()
        self.metadata_extractor = ContentMetadataExtractor()
        self.state_manager = SimpleStateManager(target_folder)

        # Load preferences
        self.preferences = self.state_manager.load_preferences()

    def organize_documents(self, processed_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Organize processed documents using Phase 1 balanced architecture.

        Args:
            processed_documents: List of document info dicts with filename, content, path

        Returns:
            Organization results including structure, metrics, and classified documents
        """
        logging.info(f"Starting organization of {len(processed_documents)} documents")

        # Step 1: Classify and extract metadata for all documents
        classified_docs = []
        classification_stats = defaultdict(int)

        for doc_info in processed_documents:
            try:
                # Extract content for classification (reusing OCR content)
                content = self._extract_content_for_classification(doc_info)

                # Classify document
                category, confidence = self.classifier.get_classification_confidence(
                    content, doc_info["filename"]
                )

                # Extract metadata
                metadata = self.metadata_extractor.extract_metadata(content, doc_info["filename"])

                # Create classified document record
                classified_doc = {
                    "original_path": doc_info["path"],
                    "filename": doc_info["filename"],
                    "category": category,
                    "confidence": confidence,
                    "metadata": metadata,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
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
                    }
                )
                classification_stats["other"] += 1

        # Step 2: Analyze temporal patterns for intelligent organization
        temporal_analysis = self._analyze_temporal_patterns(classified_docs)

        # Step 3: Generate organization structure
        organization_structure = self._generate_organization_structure(
            classified_docs, temporal_analysis
        )

        # Step 4: Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(classified_docs, classification_stats)

        # Step 5: Determine if reorganization should be applied
        should_reorganize = self._should_apply_reorganization_logic(quality_metrics)

        # Step 6: Save session data
        session_data = {
            "session_id": f"org_session_{int(datetime.now().timestamp())}",
            "document_count": len(processed_documents),
            "classification_stats": dict(classification_stats),
            "quality_metrics": quality_metrics,
            "temporal_analysis": temporal_analysis,
            "organization_structure": organization_structure,
            "should_reorganize": should_reorganize,
        }

        self.state_manager.save_session_data(session_data)

        # Return comprehensive results
        return {
            "success": True,
            "organization_structure": organization_structure,
            "quality_metrics": quality_metrics,
            "classified_documents": classified_docs,
            "temporal_analysis": temporal_analysis,
            "should_reorganize": should_reorganize,
            "session_data": session_data,
        }

    def _extract_content_for_classification(self, doc_info: Dict[str, Any]) -> str:
        """Extract content from document info, handling various input formats."""
        # If content is directly provided
        if "content" in doc_info:
            return doc_info["content"]

        # If we need to read from file path
        if "path" in doc_info and os.path.exists(doc_info["path"]):
            try:
                # For text files, read directly
                if doc_info["path"].lower().endswith((".txt", ".md")):
                    with open(doc_info["path"], "r", encoding="utf-8") as f:
                        return f.read()
                else:
                    # For other files, use filename and any available metadata
                    return f"File: {doc_info['filename']}"
            except (IOError, UnicodeDecodeError):
                pass

        # Fallback to filename only
        return doc_info.get("filename", "")

    def _analyze_temporal_patterns(self, classified_docs: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in classified documents."""
        temporal_analysis = {
            "date_distribution": defaultdict(int),
            "year_distribution": defaultdict(int),
            "detected_fiscal_year": None,
            "seasonal_patterns": {},
            "recommended_time_structure": "year",  # Default
        }

        dates_found = []
        fiscal_year_hints = []

        # Collect dates and fiscal year hints from all documents
        for doc in classified_docs:
            metadata = doc.get("metadata", {})

            # Collect dates
            doc_dates = metadata.get("date_detected", [])
            for date_info in doc_dates:
                if "year" in date_info:
                    dates_found.append(date_info)
                    temporal_analysis["year_distribution"][date_info["year"]] += 1

            # Collect fiscal year hints
            fiscal_hints = metadata.get("fiscal_year_hints", {})
            if fiscal_hints.get("fiscal_year_pattern"):
                fiscal_year_hints.append(fiscal_hints["fiscal_year_pattern"])

        # Determine fiscal year pattern
        if fiscal_year_hints:
            # Use most common fiscal year pattern
            from collections import Counter

            most_common_fy = Counter(fiscal_year_hints).most_common(1)[0][0]
            temporal_analysis["detected_fiscal_year"] = most_common_fy

        # Determine recommended time structure
        total_docs = len(classified_docs)
        if total_docs > 50:
            temporal_analysis["recommended_time_structure"] = "year-month"
        else:
            temporal_analysis["recommended_time_structure"] = "year"

        return temporal_analysis

    def _generate_organization_structure(
        self, classified_docs: List[Dict], temporal_analysis: Dict
    ) -> Dict[str, Any]:
        """Generate recommended folder organization structure."""
        hierarchy_type = self.preferences.get("hierarchy_type", "category-first")
        time_granularity = self.preferences.get("time_granularity", "year")

        # Override time granularity with analysis recommendation if significantly different
        recommended_time = temporal_analysis.get("recommended_time_structure", "year")
        if recommended_time != time_granularity:
            time_granularity = recommended_time

        structure = {
            "hierarchy_type": hierarchy_type,
            "time_granularity": time_granularity,
            "folders": {},
            "file_assignments": [],
        }

        # Group documents by category and time
        category_groups = defaultdict(list)
        for doc in classified_docs:
            category_groups[doc["category"]].append(doc)

        # Generate folder structure based on hierarchy preference
        if hierarchy_type == "category-first":
            structure["folders"] = self._generate_category_first_structure(
                category_groups, time_granularity, temporal_analysis
            )
        else:  # time-first
            structure["folders"] = self._generate_time_first_structure(
                category_groups, time_granularity, temporal_analysis
            )

        # Create file assignments
        for category, docs in category_groups.items():
            for doc in docs:
                folder_path = self._determine_folder_path(
                    doc, hierarchy_type, time_granularity, temporal_analysis
                )
                structure["file_assignments"].append(
                    {
                        "filename": doc["filename"],
                        "current_path": doc["original_path"],
                        "target_folder": folder_path,
                        "category": category,
                        "confidence": doc["confidence"],
                    }
                )

        return structure

    def _generate_category_first_structure(
        self, category_groups: Dict, time_granularity: str, temporal_analysis: Dict
    ) -> Dict[str, Any]:
        """Generate category-first folder structure."""
        folders = {}

        for category, docs in category_groups.items():
            category_folder = category.title()
            folders[category_folder] = {"type": "category", "documents": len(docs)}

            # Add time-based subfolders if documents span multiple years
            years = set()
            for doc in docs:
                doc_years = self._extract_years_from_metadata(doc.get("metadata", {}))
                years.update(doc_years)

            if len(years) > 1:  # Multiple years found
                folders[category_folder]["subfolders"] = {}
                for year in sorted(years):
                    if time_granularity == "year":
                        subfolder_name = (
                            f"FY{year}"
                            if temporal_analysis.get("detected_fiscal_year")
                            else str(year)
                        )
                    else:  # year-month
                        subfolder_name = str(year)  # Month subfolders would be created dynamically

                    folders[category_folder]["subfolders"][subfolder_name] = {
                        "type": "time",
                        "year": year,
                    }

        return folders

    def _generate_time_first_structure(
        self, category_groups: Dict, time_granularity: str, temporal_analysis: Dict
    ) -> Dict[str, Any]:
        """Generate time-first folder structure."""
        folders = {}

        # Collect all years across documents
        all_years = set()
        for docs in category_groups.values():
            for doc in docs:
                doc_years = self._extract_years_from_metadata(doc.get("metadata", {}))
                all_years.update(doc_years)

        # Create year-based folders
        for year in sorted(all_years):
            if temporal_analysis.get("detected_fiscal_year"):
                year_folder = f"FY{year}"
            else:
                year_folder = str(year)

            folders[year_folder] = {"type": "time", "year": year, "subfolders": {}}

            # Add category subfolders
            for category in category_groups.keys():
                if category != "other":  # Skip 'other' category in subfolders
                    folders[year_folder]["subfolders"][category.title()] = {
                        "type": "category",
                        "category": category,
                    }

        return folders

    def _extract_years_from_metadata(self, metadata: Dict) -> set:
        """Extract years from document metadata."""
        years = set()

        # From detected dates
        for date_info in metadata.get("date_detected", []):
            if "year" in date_info:
                years.add(date_info["year"])

        # From fiscal year hints
        fiscal_hints = metadata.get("fiscal_year_hints", {})
        for year in fiscal_hints.get("detected_years", []):
            years.add(year)

        # Default to current year if no dates found
        if not years:
            years.add(datetime.now().year)

        return years

    def _determine_folder_path(
        self, doc: Dict, hierarchy_type: str, time_granularity: str, temporal_analysis: Dict
    ) -> str:
        """Determine the target folder path for a document."""
        category = doc["category"].title()
        metadata = doc.get("metadata", {})

        # Determine year for the document
        doc_years = self._extract_years_from_metadata(metadata)
        year = max(doc_years) if doc_years else datetime.now().year

        # Format year based on fiscal year detection
        if temporal_analysis.get("detected_fiscal_year"):
            year_folder = f"FY{year}"
        else:
            year_folder = str(year)

        # Generate path based on hierarchy
        if hierarchy_type == "category-first":
            if len(self._get_all_years_in_category(doc["category"])) > 1:
                return os.path.join(category, year_folder)
            else:
                return category
        else:  # time-first
            return os.path.join(year_folder, category)

    def _get_all_years_in_category(self, category: str) -> set:
        """Get all years for documents in a specific category."""
        # This would typically access the classified documents
        # For now, return a simple set
        return {datetime.now().year}

    def _calculate_quality_metrics(
        self, classified_docs: List[Dict], classification_stats: Dict
    ) -> Dict[str, Any]:
        """Calculate quality metrics for organization."""
        total_docs = len(classified_docs)
        if total_docs == 0:
            return {"accuracy": 0.0, "total_documents": 0}

        # Calculate confidence-based accuracy
        high_confidence_count = sum(1 for doc in classified_docs if doc.get("confidence", 0) >= 0.7)
        medium_confidence_count = sum(
            1 for doc in classified_docs if 0.4 <= doc.get("confidence", 0) < 0.7
        )
        low_confidence_count = sum(1 for doc in classified_docs if doc.get("confidence", 0) < 0.4)

        # Weighted accuracy calculation
        weighted_accuracy = (
            (
                (high_confidence_count * 1.0)
                + (medium_confidence_count * 0.7)
                + (low_confidence_count * 0.3)
            )
            / total_docs
            if total_docs > 0
            else 0.0
        )

        return {
            "accuracy": weighted_accuracy,
            "total_documents": total_docs,
            "high_confidence": high_confidence_count,
            "medium_confidence": medium_confidence_count,
            "low_confidence": low_confidence_count,
            "classification_distribution": dict(classification_stats),
            "average_confidence": sum(doc.get("confidence", 0) for doc in classified_docs)
            / total_docs,
        }

    def should_apply_reorganization(self, current_quality: float, proposed_quality: float) -> bool:
        """
        Determine if reorganization should be applied based on quality improvement threshold.

        Args:
            current_quality: Current organization quality score
            proposed_quality: Proposed organization quality score

        Returns:
            True if reorganization should be applied
        """
        threshold = self.preferences.get("quality_threshold", 0.15)  # 15% default
        improvement = proposed_quality - current_quality
        improvement_percentage = improvement / current_quality if current_quality > 0 else 1.0

        return improvement_percentage >= threshold

    def _should_apply_reorganization_logic(self, quality_metrics: Dict) -> bool:
        """Internal logic to determine if reorganization should be applied."""
        current_accuracy = quality_metrics.get("accuracy", 0.0)

        # Get last session quality for comparison
        last_quality = self.state_manager.get_last_session_quality()

        if last_quality is None:
            # First organization - apply if quality is good
            return current_accuracy >= 0.6  # 60% minimum for first organization
        else:
            # Compare with previous organization
            return self.should_apply_reorganization(last_quality, current_accuracy)
