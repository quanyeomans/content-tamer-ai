"""
Temporal Organization Engine - Phase 3

Advanced organization engine with complete temporal intelligence integration.
Combines Phase 1 rule-based classification, Phase 2 ML enhancement, and
Phase 3 temporal intelligence for optimal document organization.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .enhanced_organization_engine import EnhancedOrganizationEngine
from content_analysis.temporal_analyzer import AdvancedTemporalAnalyzer


class TemporalOrganizationEngine(EnhancedOrganizationEngine):
    """Phase 3 organization engine with complete temporal intelligence."""

    def __init__(self, target_folder: str, ml_enhancement_level: int = 3):
        """
        Initialize temporal organization engine.

        Args:
            target_folder: Directory where documents will be organized
            ml_enhancement_level: 1=Phase1, 2=Phase2, 3=Phase3 with temporal intelligence
        """
        # Initialize Phase 2 capabilities
        super().__init__(target_folder, ml_enhancement_level)

        # Add Phase 3 temporal intelligence
        if ml_enhancement_level >= 3:
            self.temporal_analyzer = AdvancedTemporalAnalyzer()
            logging.info(
                f"Temporal organization engine initialized (Level {ml_enhancement_level})"
            )
        else:
            self.temporal_analyzer = None
            logging.info("Temporal organization engine running in compatibility mode")

    def organize_documents(
        self, processed_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Advanced document organization with temporal intelligence.

        Args:
            processed_documents: List of document info dicts

        Returns:
            Complete organization results with temporal insights
        """
        start_time = time.time()

        logging.info(
            f"Starting temporal organization of {len(processed_documents)} documents "
            f"(Enhancement Level {self.ml_enhancement_level})"
        )

        # Step 1: Perform Phase 1 + Phase 2 processing
        enhanced_result = super().organize_documents(processed_documents)
        classified_docs = enhanced_result["classified_documents"]

        # Step 2: Apply Phase 3 temporal intelligence if enabled
        if self.ml_enhancement_level >= 3 and self.temporal_analyzer:
            temporal_intelligence = self._apply_temporal_intelligence(classified_docs)

            # Override temporal analysis with advanced insights
            enhanced_result["temporal_analysis"] = temporal_intelligence

            # Generate temporally-aware organization structure
            temporal_organization = self._generate_temporal_organization_structure(
                classified_docs, temporal_intelligence
            )
            enhanced_result["organization_structure"] = temporal_organization

            # Calculate temporal quality metrics
            temporal_quality = self._calculate_temporal_quality_metrics(
                classified_docs,
                temporal_intelligence,
                enhanced_result["quality_metrics"],
            )
            enhanced_result["quality_metrics"] = temporal_quality

            # Update recommendations with temporal insights
            enhanced_result["should_reorganize"] = (
                self._should_apply_temporal_reorganization(
                    temporal_quality, temporal_intelligence
                )
            )

        else:
            temporal_intelligence = {
                "temporal_enhancement": False,
                "reason": "Phase 3 not enabled",
            }

        processing_time = time.time() - start_time

        # Step 3: Save enhanced session data with temporal intelligence
        session_data = enhanced_result["session_data"]
        session_data.update(
            {
                "temporal_intelligence": temporal_intelligence,
                "ml_enhancement_level": self.ml_enhancement_level,
                "processing_time": processing_time,
            }
        )

        # Save using hybrid state manager with temporal data
        if self.ml_enhancement_level >= 2:
            ml_metrics = enhanced_result.get("ml_metrics", {})
            temporal_metrics = self._extract_temporal_metrics(temporal_intelligence)
            combined_ml_metrics = {**ml_metrics, **temporal_metrics}

            self.state_manager.save_enhanced_session_data(
                session_data, processing_time, combined_ml_metrics
            )

        # Return comprehensive results with temporal intelligence
        enhanced_result.update(
            {
                "temporal_intelligence": temporal_intelligence,
                "processing_time": processing_time,
            }
        )

        return enhanced_result

    def _apply_temporal_intelligence(
        self, classified_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply advanced temporal intelligence analysis."""
        temporal_start_time = time.time()

        try:
            logging.info("Applying Phase 3 temporal intelligence analysis")

            # Perform comprehensive temporal analysis
            temporal_insights = self.temporal_analyzer.analyze_temporal_intelligence(
                classified_docs
            )

            # Add Phase 3 specific metadata
            temporal_insights.update(
                {
                    "temporal_enhancement_applied": True,
                    "analysis_time": time.time() - temporal_start_time,
                    "phase": 3,
                    "advanced_features": [
                        "seasonal_pattern_detection",
                        "fiscal_year_analysis",
                        "workflow_pattern_recognition",
                        "business_cycle_intelligence",
                    ],
                }
            )

            return temporal_insights

        except Exception as e:
            logging.warning(f"Temporal intelligence analysis failed: {e}")
            return {
                "temporal_enhancement_applied": False,
                "error": str(e),
                "fallback_used": True,
            }

    def _generate_temporal_organization_structure(
        self,
        classified_docs: List[Dict[str, Any]],
        temporal_intelligence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate organization structure optimized with temporal intelligence."""

        if not temporal_intelligence.get("temporal_enhancement_applied"):
            # Fallback to Phase 2 organization
            return super()._generate_organization_structure(
                classified_docs, temporal_intelligence
            )

        # Extract temporal strategy
        organization_strategy = temporal_intelligence.get("organization_strategy", {})
        confidence_metrics = temporal_intelligence.get("confidence_metrics", {})

        # Build temporal-aware organization structure
        structure = {
            "organization_type": "temporal_intelligence",
            "confidence": confidence_metrics.get("overall_confidence", 0.0),
            "primary_structure": organization_strategy.get(
                "primary_structure", "chronological"
            ),
            "time_granularity": organization_strategy.get("time_granularity", "year"),
            "structure_details": {},
            "recommendations": temporal_intelligence.get("recommendations", []),
        }

        # Generate structure based on temporal strategy
        if organization_strategy.get("primary_structure") == "chronological":
            structure["structure_details"] = self._generate_chronological_structure(
                classified_docs, temporal_intelligence
            )
        elif organization_strategy.get("primary_structure") == "category":
            structure["structure_details"] = self._generate_category_temporal_structure(
                classified_docs, temporal_intelligence
            )
        else:
            # Hybrid approach
            structure["structure_details"] = self._generate_hybrid_temporal_structure(
                classified_docs, temporal_intelligence
            )

        # Add special considerations
        special_considerations = organization_strategy.get("special_considerations", [])
        if special_considerations:
            structure["special_features"] = special_considerations

        return structure

    def _generate_chronological_structure(
        self,
        classified_docs: List[Dict[str, Any]],
        temporal_intelligence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate chronological organization structure."""
        structure = {"type": "chronological", "folders": {}}

        # Extract temporal organization parameters
        organization_strategy = temporal_intelligence.get("organization_strategy", {})
        time_granularity = organization_strategy.get("time_granularity", "year")
        fiscal_analysis = temporal_intelligence.get("fiscal_year_analysis", {})

        # Use fiscal year if detected and confident
        use_fiscal = (
            fiscal_analysis.get("confidence", 0) > 0.7
            and fiscal_analysis.get("detected_fiscal_type") != "calendar"
        )

        if use_fiscal:
            structure["folders"] = self._generate_fiscal_year_folders(
                classified_docs, fiscal_analysis, time_granularity
            )
            structure["fiscal_year_structure"] = True
        else:
            structure["folders"] = self._generate_calendar_folders(
                classified_docs, time_granularity
            )
            structure["fiscal_year_structure"] = False

        return structure

    def _generate_category_temporal_structure(
        self,
        classified_docs: List[Dict[str, Any]],
        temporal_intelligence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate category-first structure with temporal subdivisions."""
        structure = {"type": "category_temporal", "folders": {}}

        # Group documents by category
        from collections import defaultdict

        category_docs = defaultdict(list)

        for doc in classified_docs:
            category = doc.get("category", "other")
            category_docs[category].append(doc)

        # Create category folders with temporal substructure
        seasonal_insights = temporal_intelligence.get("seasonal_insights", {})
        workflow_patterns = temporal_intelligence.get("workflow_patterns", {})

        for category, docs in category_docs.items():
            category_structure = {"document_count": len(docs), "subfolders": {}}

            # Check for seasonal patterns in this category
            seasonal_pattern = seasonal_insights.get(
                "category_seasonal_patterns", {}
            ).get(category)
            workflow_pattern = workflow_patterns.get("category_workflows", {}).get(
                category
            )

            if seasonal_pattern and seasonal_pattern.get("pattern_detected"):
                # Organize by quarters
                category_structure["temporal_organization"] = "quarterly"
                category_structure["subfolders"] = self._generate_quarterly_subfolders(
                    docs
                )
            elif workflow_pattern and workflow_pattern.get("workflow_detected"):
                # Organize by workflow pattern
                workflow_type = workflow_pattern.get("workflow_type", "irregular")
                category_structure["temporal_organization"] = workflow_type
                category_structure["subfolders"] = self._generate_workflow_subfolders(
                    docs, workflow_type
                )
            else:
                # Simple chronological organization
                category_structure["temporal_organization"] = "chronological"
                category_structure["subfolders"] = (
                    self._generate_simple_chronological_subfolders(docs)
                )

            structure["folders"][category] = category_structure

        return structure

    def _generate_hybrid_temporal_structure(
        self,
        classified_docs: List[Dict[str, Any]],
        temporal_intelligence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate hybrid structure balancing temporal and categorical organization."""
        structure = {"type": "hybrid_temporal", "folders": {}}

        # Analyze document distribution and patterns
        date_patterns = temporal_intelligence.get("date_distribution", {})
        seasonal_insights = temporal_intelligence.get("seasonal_insights", {})

        # Determine primary organization approach
        date_range = date_patterns.get("date_range", {})
        span_years = date_range.get("span_years", 0)

        if span_years > 3:
            # Long time span - year primary, category secondary
            structure["primary_dimension"] = "temporal"
            structure["secondary_dimension"] = "category"
            structure["folders"] = self._generate_year_category_structure(
                classified_docs, temporal_intelligence
            )
        else:
            # Shorter time span - category primary, temporal secondary
            structure["primary_dimension"] = "category"
            structure["secondary_dimension"] = "temporal"
            structure["folders"] = self._generate_category_temporal_structure(
                classified_docs, temporal_intelligence
            )

        return structure

    def _generate_fiscal_year_folders(
        self,
        classified_docs: List[Dict[str, Any]],
        fiscal_analysis: Dict[str, Any],
        time_granularity: str,
    ) -> Dict[str, Any]:
        """Generate fiscal year-based folder structure."""
        fiscal_structure = fiscal_analysis.get("fiscal_structure", {})
        fiscal_years = fiscal_structure.get("fiscal_years", {})

        folders = {}
        for fiscal_year, year_docs in fiscal_years.items():
            year_folder = {
                "fiscal_year": fiscal_year,
                "document_count": len(year_docs),
                "subfolders": {},
            }

            # Add granular structure based on time_granularity
            if time_granularity in ["year-quarter", "quarter-month"]:
                # Group by fiscal quarters
                from collections import defaultdict

                quarterly_docs = defaultdict(list)

                for doc_info in year_docs:
                    quarter = doc_info.get("quarter", "FQ1")
                    quarterly_docs[quarter].append(doc_info)

                for quarter, quarter_docs in quarterly_docs.items():
                    year_folder["subfolders"][quarter] = {
                        "document_count": len(quarter_docs),
                        "documents": quarter_docs,
                    }
            else:
                # Simple year-level organization
                year_folder["documents"] = year_docs

            folders[f"FY_{fiscal_year}"] = year_folder

        return folders

    def _generate_calendar_folders(
        self, classified_docs: List[Dict[str, Any]], time_granularity: str
    ) -> Dict[str, Any]:
        """Generate calendar-based folder structure."""
        from collections import defaultdict

        folders = {}
        yearly_docs = defaultdict(list)

        # Group documents by year
        for doc in classified_docs:
            metadata = doc.get("metadata", {})
            dates = metadata.get("date_detected", [])

            if dates:
                # Use first detected date
                primary_date = dates[0]
                year = primary_date.get("year", datetime.now().year)
                yearly_docs[year].append(doc)
            else:
                # No date detected - use current year
                yearly_docs[datetime.now().year].append(doc)

        # Create year folders with appropriate granularity
        for year, year_docs in yearly_docs.items():
            year_folder = {
                "year": year,
                "document_count": len(year_docs),
                "subfolders": {},
            }

            if (
                time_granularity in ["year-month", "quarter-month"]
                and len(year_docs) > 10
            ):
                # Monthly subfolders
                monthly_docs = defaultdict(list)
                for doc in year_docs:
                    metadata = doc.get("metadata", {})
                    dates = metadata.get("date_detected", [])
                    month = dates[0].get("month", 1) if dates else 1
                    monthly_docs[month].append(doc)

                for month, month_docs in monthly_docs.items():
                    month_name = datetime(year, month, 1).strftime("%B")
                    year_folder["subfolders"][f"{month:02d}_{month_name}"] = {
                        "document_count": len(month_docs),
                        "documents": month_docs,
                    }
            elif time_granularity == "year-quarter" and len(year_docs) > 5:
                # Quarterly subfolders
                quarterly_docs = defaultdict(list)
                for doc in year_docs:
                    metadata = doc.get("metadata", {})
                    dates = metadata.get("date_detected", [])
                    if dates:
                        month = dates[0].get("month", 1)
                        quarter = f"Q{((month - 1) // 3) + 1}"
                        quarterly_docs[quarter].append(doc)
                    else:
                        quarterly_docs["Q1"].append(doc)  # Default to Q1

                for quarter, quarter_docs in quarterly_docs.items():
                    year_folder["subfolders"][quarter] = {
                        "document_count": len(quarter_docs),
                        "documents": quarter_docs,
                    }
            else:
                # Simple year-level organization
                year_folder["documents"] = year_docs

            folders[str(year)] = year_folder

        return folders

    def _generate_quarterly_subfolders(
        self, docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate quarterly subfolders for a category."""
        from collections import defaultdict

        quarterly_docs = defaultdict(list)

        for doc in docs:
            metadata = doc.get("metadata", {})
            dates = metadata.get("date_detected", [])

            if dates:
                month = dates[0].get("month", 1)
                quarter = f"Q{((month - 1) // 3) + 1}"
                quarterly_docs[quarter].append(doc)
            else:
                quarterly_docs["Q1"].append(doc)  # Default

        subfolders = {}
        for quarter, quarter_docs in quarterly_docs.items():
            subfolders[quarter] = {
                "document_count": len(quarter_docs),
                "documents": quarter_docs,
            }

        return subfolders

    def _generate_workflow_subfolders(
        self, docs: List[Dict[str, Any]], workflow_type: str
    ) -> Dict[str, Any]:
        """Generate workflow-based subfolders."""
        if workflow_type == "monthly":
            return self._generate_monthly_subfolders(docs)
        elif workflow_type == "quarterly":
            return self._generate_quarterly_subfolders(docs)
        else:
            # Default chronological
            return self._generate_simple_chronological_subfolders(docs)

    def _generate_monthly_subfolders(
        self, docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate monthly subfolders."""
        from collections import defaultdict

        monthly_docs = defaultdict(list)

        for doc in docs:
            metadata = doc.get("metadata", {})
            dates = metadata.get("date_detected", [])

            if dates:
                year = dates[0].get("year", datetime.now().year)
                month = dates[0].get("month", 1)
                month_key = f"{year}-{month:02d}"
                monthly_docs[month_key].append(doc)
            else:
                current_month = f"{datetime.now().year}-{datetime.now().month:02d}"
                monthly_docs[current_month].append(doc)

        subfolders = {}
        for month_key, month_docs in monthly_docs.items():
            subfolders[month_key] = {
                "document_count": len(month_docs),
                "documents": month_docs,
            }

        return subfolders

    def _generate_simple_chronological_subfolders(
        self, docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate simple chronological subfolders by year."""
        from collections import defaultdict

        yearly_docs = defaultdict(list)

        for doc in docs:
            metadata = doc.get("metadata", {})
            dates = metadata.get("date_detected", [])

            year = (
                dates[0].get("year", datetime.now().year)
                if dates
                else datetime.now().year
            )
            yearly_docs[year].append(doc)

        subfolders = {}
        for year, year_docs in yearly_docs.items():
            subfolders[str(year)] = {
                "document_count": len(year_docs),
                "documents": year_docs,
            }

        return subfolders

    def _generate_year_category_structure(
        self,
        classified_docs: List[Dict[str, Any]],
        temporal_intelligence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate year-first, category-second structure."""
        from collections import defaultdict

        # Group by year first
        yearly_docs = defaultdict(list)
        for doc in classified_docs:
            metadata = doc.get("metadata", {})
            dates = metadata.get("date_detected", [])
            year = (
                dates[0].get("year", datetime.now().year)
                if dates
                else datetime.now().year
            )
            yearly_docs[year].append(doc)

        folders = {}
        for year, year_docs in yearly_docs.items():
            # Group year's documents by category
            category_docs = defaultdict(list)
            for doc in year_docs:
                category = doc.get("category", "other")
                category_docs[category].append(doc)

            year_folder = {
                "year": year,
                "document_count": len(year_docs),
                "categories": {},
            }

            for category, cat_docs in category_docs.items():
                year_folder["categories"][category] = {
                    "document_count": len(cat_docs),
                    "documents": cat_docs,
                }

            folders[str(year)] = year_folder

        return folders

    def _calculate_temporal_quality_metrics(
        self,
        classified_docs: List[Dict[str, Any]],
        temporal_intelligence: Dict[str, Any],
        base_quality_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate quality metrics enhanced with temporal intelligence."""

        # Start with base quality metrics
        quality_metrics = base_quality_metrics.copy()

        if not temporal_intelligence.get("temporal_enhancement_applied"):
            quality_metrics["temporal_enhancement_applied"] = False
            return quality_metrics

        # Add temporal-specific quality metrics
        confidence_metrics = temporal_intelligence.get("confidence_metrics", {})
        organization_strategy = temporal_intelligence.get("organization_strategy", {})

        quality_metrics.update(
            {
                "temporal_enhancement_applied": True,
                "temporal_confidence": confidence_metrics.get(
                    "overall_confidence", 0.0
                ),
                "date_coverage": confidence_metrics.get("date_coverage", 0.0),
                "pattern_strength": confidence_metrics.get("pattern_strength", 0.0),
                "temporal_organization_type": organization_strategy.get(
                    "primary_structure", "chronological"
                ),
                "time_granularity": organization_strategy.get(
                    "time_granularity", "year"
                ),
            }
        )

        # Calculate combined accuracy including temporal insights
        base_accuracy = quality_metrics.get("accuracy", 0.0)
        temporal_boost = (
            confidence_metrics.get("overall_confidence", 0.0) * 0.05
        )  # Up to 5% boost

        quality_metrics["combined_accuracy"] = min(1.0, base_accuracy + temporal_boost)
        quality_metrics["temporal_accuracy_boost"] = temporal_boost

        return quality_metrics

    def _should_apply_temporal_reorganization(
        self, quality_metrics: Dict[str, Any], temporal_intelligence: Dict[str, Any]
    ) -> bool:
        """Determine if temporal reorganization should be applied."""

        # Base decision on Phase 2 logic
        base_decision = self._should_apply_reorganization_logic(quality_metrics)

        if not temporal_intelligence.get("temporal_enhancement_applied"):
            return base_decision

        # Consider temporal factors
        temporal_confidence = quality_metrics.get("temporal_confidence", 0.0)
        date_coverage = quality_metrics.get("date_coverage", 0.0)

        # Strong temporal patterns suggest reorganization would be beneficial
        if temporal_confidence > 0.8 and date_coverage > 0.7:
            return True

        # Weak temporal patterns - rely on base decision
        if temporal_confidence < 0.3:
            return base_decision

        # Medium confidence - consider overall quality
        combined_accuracy = quality_metrics.get("combined_accuracy", 0.0)
        return combined_accuracy > 0.75

    def _extract_temporal_metrics(
        self, temporal_intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract temporal metrics for ML metrics storage."""
        if not temporal_intelligence.get("temporal_enhancement_applied"):
            return {"temporal_applied": False}

        confidence_metrics = temporal_intelligence.get("confidence_metrics", {})
        organization_strategy = temporal_intelligence.get("organization_strategy", {})

        return {
            "temporal_applied": True,
            "temporal_confidence": confidence_metrics.get("overall_confidence", 0.0),
            "date_coverage": confidence_metrics.get("date_coverage", 0.0),
            "pattern_strength": confidence_metrics.get("pattern_strength", 0.0),
            "temporal_processing_time": temporal_intelligence.get("analysis_time", 0.0),
            "organization_strategy": organization_strategy.get(
                "primary_structure", "chronological"
            ),
            "time_granularity": organization_strategy.get("time_granularity", "year"),
        }

    def get_temporal_insights(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed temporal insights for documents."""
        if self.ml_enhancement_level >= 3 and self.temporal_analyzer:
            return self.temporal_analyzer.analyze_temporal_intelligence(documents)
        else:
            return {"error": "Temporal insights require Phase 3 or higher"}

    def get_temporal_stats(self) -> Dict[str, Any]:
        """Get temporal analysis capabilities and statistics."""
        stats = {
            "enhancement_level": self.ml_enhancement_level,
            "temporal_available": self.ml_enhancement_level >= 3,
        }

        if self.ml_enhancement_level >= 3:
            stats.update(
                {
                    "temporal_features": [
                        "advanced_seasonal_analysis",
                        "fiscal_year_detection",
                        "workflow_pattern_recognition",
                        "business_cycle_intelligence",
                        "adaptive_organization_strategies",
                    ],
                    "supported_structures": [
                        "chronological",
                        "category_temporal",
                        "hybrid_temporal",
                        "fiscal_year_based",
                    ],
                }
            )
        else:
            stats.update(
                {
                    "reason": "Temporal intelligence requires Phase 3 or higher",
                    "available_phases": (
                        ["Phase 1: Rule-based", "Phase 2: ML Enhanced"]
                        if self.ml_enhancement_level >= 2
                        else ["Phase 1: Rule-based"]
                    ),
                }
            )

        return stats

    def tune_temporal_sensitivity(
        self, documents: List[Dict[str, Any]], target_temporal_usage: float = 0.8
    ) -> Dict[str, Any]:
        """
        Tune temporal analysis sensitivity for optimal organization results.

        Args:
            documents: Sample documents for sensitivity analysis
            target_temporal_usage: Target rate of temporal organization usage

        Returns:
            Tuning results and recommendations
        """
        if self.ml_enhancement_level < 3:
            raise ValueError("Temporal tuning requires Phase 3 or higher")

        if not self.temporal_analyzer:
            raise RuntimeError("Temporal analyzer not available")

        # Analyze current temporal intelligence performance
        current_analysis = self.temporal_analyzer.analyze_temporal_intelligence(
            documents
        )
        current_confidence = current_analysis.get("confidence_metrics", {}).get(
            "overall_confidence", 0.0
        )

        # Test different sensitivity levels
        sensitivity_results = {}
        test_confidences = [0.6, 0.7, 0.8, 0.9]

        for test_confidence in test_confidences:
            # Simulate temporal analysis at different confidence thresholds
            estimated_usage = min(1.0, current_confidence / test_confidence)
            sensitivity_results[test_confidence] = {
                "estimated_temporal_usage": estimated_usage,
                "confidence_threshold": test_confidence,
                "recommendation_strength": estimated_usage * current_confidence,
            }

        # Find optimal sensitivity
        best_threshold = 0.7
        best_diff = float("inf")

        for threshold, results in sensitivity_results.items():
            usage_diff = abs(
                results["estimated_temporal_usage"] - target_temporal_usage
            )
            if usage_diff < best_diff:
                best_diff = usage_diff
                best_threshold = threshold

        recommendations = []
        if best_threshold < 0.7:
            recommendations.append(
                "Lower confidence threshold for more temporal organization"
            )
        elif best_threshold > 0.8:
            recommendations.append(
                "Higher confidence threshold for more selective temporal organization"
            )
        else:
            recommendations.append("Current temporal sensitivity is well-calibrated")

        return {
            "optimal_threshold": best_threshold,
            "current_confidence": current_confidence,
            "expected_temporal_usage": sensitivity_results[best_threshold][
                "estimated_temporal_usage"
            ],
            "sensitivity_analysis": sensitivity_results,
            "recommendations": recommendations,
        }
