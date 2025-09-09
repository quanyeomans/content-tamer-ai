"""
Advanced Temporal Intelligence System

Analyzes document temporal patterns to provide intelligent organization
recommendations based on date distributions, seasonal patterns, and
business cycle insights.
"""

import calendar
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class AdvancedTemporalAnalyzer:
    """Advanced temporal pattern analysis for intelligent document organization."""

    def __init__(self):
        """Initialize temporal analyzer with business intelligence."""
        self.business_seasons = {
            "Q1": {"months": [1, 2, 3], "name": "Q1 (Jan-Mar)"},
            "Q2": {"months": [4, 5, 6], "name": "Q2 (Apr-Jun)"},
            "Q3": {"months": [7, 8, 9], "name": "Q3 (Jul-Sep)"},
            "Q4": {"months": [10, 11, 12], "name": "Q4 (Oct-Dec)"},
        }

        self.fiscal_year_patterns = {
            "calendar": {"start_month": 1, "name": "Calendar Year (Jan-Dec)"},
            "financial": {"start_month": 4, "name": "Financial Year (Apr-Mar)"},
            "academic": {"start_month": 9, "name": "Academic Year (Sep-Aug)"},
            "federal": {"start_month": 10, "name": "Federal FY (Oct-Sep)"},
        }

    def analyze_temporal_intelligence(
        self, classified_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive temporal analysis with business intelligence.

        Args:
            classified_documents: Documents with extracted metadata

        Returns:
            Advanced temporal insights for organization optimization
        """
        if not classified_documents:
            return self._get_empty_analysis()

        # Extract temporal data from documents
        temporal_data = self._extract_temporal_data(classified_documents)

        # Analyze patterns
        date_patterns = self._analyze_date_patterns(temporal_data)
        seasonal_insights = self._analyze_seasonal_patterns(temporal_data)
        fiscal_analysis = self._detect_fiscal_patterns(temporal_data)
        workflow_patterns = self._analyze_workflow_patterns(
            temporal_data, classified_documents
        )

        # Generate organization recommendations
        organization_strategy = self._generate_organization_strategy(
            date_patterns, seasonal_insights, fiscal_analysis, workflow_patterns
        )

        # Calculate confidence metrics
        confidence_metrics = self._calculate_temporal_confidence(temporal_data)

        return {
            "temporal_data_summary": {
                "total_documents": len(classified_documents),
                "documents_with_dates": len([d for d in temporal_data if d["dates"]]),
                "date_range": date_patterns.get("date_range"),
                "years_covered": date_patterns.get("years_covered", []),
            },
            "date_distribution": date_patterns,
            "seasonal_insights": seasonal_insights,
            "fiscal_year_analysis": fiscal_analysis,
            "workflow_patterns": workflow_patterns,
            "organization_strategy": organization_strategy,
            "confidence_metrics": confidence_metrics,
            "recommendations": self._generate_smart_recommendations(
                date_patterns, seasonal_insights, fiscal_analysis, workflow_patterns
            ),
        }

    def _extract_temporal_data(
        self, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract and normalize temporal data from documents."""
        temporal_data = []

        for doc in documents:
            metadata = doc.get("metadata", {})
            dates = metadata.get("date_detected", [])

            # Normalize dates to datetime objects
            normalized_dates = []
            for date_info in dates:
                try:
                    if "year" in date_info and "month" in date_info:
                        day = date_info.get("day", 1)
                        dt = datetime(date_info["year"], date_info["month"], day)
                        normalized_dates.append(
                            {
                                "datetime": dt,
                                "year": date_info["year"],
                                "month": date_info["month"],
                                "day": day,
                                "quarter": self._get_quarter(date_info["month"]),
                                "confidence": date_info.get("confidence", 0.5),
                            }
                        )
                except (ValueError, KeyError):
                    continue

            temporal_data.append(
                {
                    "filename": doc.get("filename", ""),
                    "category": doc.get("category", "other"),
                    "confidence": doc.get("confidence", 0.0),
                    "dates": normalized_dates,
                    "fiscal_hints": metadata.get("fiscal_year_hints", {}),
                    "classification_method": doc.get(
                        "classification_method", "rule_based"
                    ),
                }
            )

        return temporal_data

    def _analyze_date_patterns(
        self, temporal_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze date distribution patterns."""
        all_dates = []
        yearly_distribution = defaultdict(int)
        monthly_distribution = defaultdict(int)
        quarterly_distribution = defaultdict(int)

        for doc in temporal_data:
            for date_info in doc["dates"]:
                all_dates.append(date_info["datetime"])
                yearly_distribution[date_info["year"]] += 1
                monthly_distribution[date_info["month"]] += 1
                quarterly_distribution[date_info["quarter"]] += 1

        if not all_dates:
            return {"pattern_detected": False}

        # Calculate date range and coverage
        min_date = min(all_dates)
        max_date = max(all_dates)
        date_span_days = (max_date - min_date).days

        # Detect temporal density patterns
        density_pattern = self._analyze_temporal_density(all_dates)

        return {
            "pattern_detected": True,
            "date_range": {
                "earliest": min_date.isoformat(),
                "latest": max_date.isoformat(),
                "span_days": date_span_days,
                "span_years": date_span_days / 365.25,
            },
            "years_covered": sorted(yearly_distribution.keys()),
            "yearly_distribution": dict(yearly_distribution),
            "monthly_distribution": dict(monthly_distribution),
            "quarterly_distribution": dict(quarterly_distribution),
            "density_pattern": density_pattern,
            "peak_periods": self._identify_peak_periods(
                monthly_distribution, quarterly_distribution
            ),
        }

    def _analyze_seasonal_patterns(
        self, temporal_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze seasonal and cyclical patterns in document creation."""
        seasonal_analysis = {}

        # Group documents by category and season
        category_seasons = defaultdict(lambda: defaultdict(int))

        for doc in temporal_data:
            category = doc["category"]
            for date_info in doc["dates"]:
                quarter = date_info["quarter"]
                month = date_info["month"]
                category_seasons[category][quarter] += 1

        # Analyze seasonal patterns for each category
        for category, quarters in category_seasons.items():
            if sum(quarters.values()) >= 3:  # Need minimum data for pattern detection
                seasonal_pattern = self._detect_seasonal_pattern(quarters)
                seasonal_analysis[category] = seasonal_pattern

        # Overall seasonal insights
        overall_seasonal = self._calculate_overall_seasonal_trends(category_seasons)

        return {
            "category_seasonal_patterns": seasonal_analysis,
            "overall_seasonal_trends": overall_seasonal,
            "seasonal_recommendations": self._generate_seasonal_recommendations(
                seasonal_analysis
            ),
        }

    def _detect_fiscal_patterns(
        self, temporal_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect and analyze fiscal year patterns."""
        fiscal_hints = []
        document_months = []

        # Collect fiscal year hints and document months
        for doc in temporal_data:
            hints = doc.get("fiscal_hints", {})
            if hints.get("fiscal_year_pattern"):
                fiscal_hints.append(hints["fiscal_year_pattern"])

            for date_info in doc["dates"]:
                document_months.append(date_info["month"])

        # Analyze fiscal year patterns
        detected_fiscal_type = None
        if fiscal_hints:
            most_common_hint = Counter(fiscal_hints).most_common(1)[0][0]
            detected_fiscal_type = most_common_hint
        else:
            # Infer fiscal year from document distribution
            detected_fiscal_type = self._infer_fiscal_year_pattern(document_months)

        fiscal_info = self.fiscal_year_patterns.get(
            detected_fiscal_type, self.fiscal_year_patterns["calendar"]
        )

        # Generate fiscal year organization structure
        fiscal_structure = self._generate_fiscal_structure(temporal_data, fiscal_info)

        return {
            "detected_fiscal_type": detected_fiscal_type,
            "fiscal_info": fiscal_info,
            "confidence": self._calculate_fiscal_confidence(
                fiscal_hints, document_months
            ),
            "fiscal_structure": fiscal_structure,
            "fiscal_recommendations": self._generate_fiscal_recommendations(
                detected_fiscal_type, fiscal_structure
            ),
        }

    def _analyze_workflow_patterns(
        self,
        temporal_data: List[Dict[str, Any]],
        classified_documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze document workflow and business process patterns."""
        workflow_sequences = []
        category_timing = defaultdict(list)

        # Group documents by category and analyze timing patterns
        for doc_data, doc_info in zip(temporal_data, classified_documents):
            category = doc_data["category"]
            method = doc_data["classification_method"]

            for date_info in doc_data["dates"]:
                category_timing[category].append(
                    {
                        "datetime": date_info["datetime"],
                        "month": date_info["month"],
                        "quarter": date_info["quarter"],
                        "classification_method": method,
                        "confidence": doc_info.get("confidence", 0.0),
                    }
                )

        # Analyze workflow patterns
        workflow_insights = {}
        for category, timing_data in category_timing.items():
            if len(timing_data) >= 2:  # Need multiple documents for pattern analysis
                workflow_insights[category] = self._analyze_category_workflow(
                    timing_data
                )

        # Detect business process cycles
        process_cycles = self._detect_process_cycles(category_timing)

        return {
            "category_workflows": workflow_insights,
            "process_cycles": process_cycles,
            "workflow_recommendations": self._generate_workflow_recommendations(
                workflow_insights
            ),
        }

    def _generate_organization_strategy(
        self,
        date_patterns: Dict,
        seasonal_insights: Dict,
        fiscal_analysis: Dict,
        workflow_patterns: Dict,
    ) -> Dict[str, Any]:
        """Generate comprehensive organization strategy based on temporal analysis."""
        strategy = {
            "primary_structure": "chronological",
            "time_granularity": "year",
            "category_grouping": "mixed",
            "special_considerations": [],
        }

        # Determine optimal time granularity
        if date_patterns.get("pattern_detected"):
            date_range = date_patterns.get("date_range", {})
            span_years = date_range.get("span_years", 0)
            total_docs = sum(date_patterns.get("yearly_distribution", {}).values())

            if span_years > 3 and total_docs > 50:
                strategy["time_granularity"] = "year-quarter"
            elif span_years > 5 and total_docs > 100:
                strategy["time_granularity"] = "year-month"
            elif span_years < 2 and total_docs > 20:
                strategy["time_granularity"] = "quarter-month"

        # Consider fiscal year structure
        if fiscal_analysis.get("confidence", 0) > 0.7:
            fiscal_type = fiscal_analysis.get("detected_fiscal_type")
            if fiscal_type != "calendar":
                strategy["special_considerations"].append(
                    f"Use {fiscal_type} fiscal year structure"
                )

        # Consider seasonal patterns
        seasonal_categories = seasonal_insights.get("category_seasonal_patterns", {})
        if len(seasonal_categories) > 2:
            strategy["special_considerations"].append(
                "Strong seasonal patterns detected"
            )

        # Consider workflow patterns
        workflow_categories = workflow_patterns.get("category_workflows", {})
        if len(workflow_categories) > 1:
            strategy["category_grouping"] = "workflow_aware"

        return strategy

    def _calculate_temporal_confidence(
        self, temporal_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate confidence metrics for temporal analysis."""
        total_docs = len(temporal_data)
        docs_with_dates = len([d for d in temporal_data if d["dates"]])

        if total_docs == 0:
            return {"overall_confidence": 0.0}

        # Date coverage confidence
        date_coverage = docs_with_dates / total_docs

        # Date quality confidence (based on extracted date confidence)
        date_qualities = []
        for doc in temporal_data:
            for date_info in doc["dates"]:
                date_qualities.append(date_info.get("confidence", 0.5))

        avg_date_quality = np.mean(date_qualities) if date_qualities else 0.0

        # Pattern detection confidence
        pattern_strength = self._calculate_pattern_strength(temporal_data)

        overall_confidence = (
            date_coverage * 0.4 + avg_date_quality * 0.3 + pattern_strength * 0.3
        )

        return {
            "overall_confidence": float(overall_confidence),
            "date_coverage": float(date_coverage),
            "average_date_quality": float(avg_date_quality),
            "pattern_strength": float(pattern_strength),
        }

    def _generate_smart_recommendations(
        self,
        date_patterns: Dict,
        seasonal_insights: Dict,
        fiscal_analysis: Dict,
        workflow_patterns: Dict,
    ) -> List[str]:
        """Generate actionable recommendations based on temporal intelligence."""
        recommendations = []

        # Date pattern recommendations
        if date_patterns.get("pattern_detected"):
            span_years = date_patterns.get("date_range", {}).get("span_years", 0)
            if span_years > 5:
                recommendations.append(
                    "Long time span detected - consider year-based primary organization"
                )
            elif span_years < 1:
                recommendations.append(
                    "Recent documents - consider month/quarter organization"
                )

        # Seasonal recommendations
        seasonal_patterns = seasonal_insights.get("category_seasonal_patterns", {})
        if len(seasonal_patterns) > 2:
            recommendations.append(
                "Strong seasonal patterns - organize by business quarters within years"
            )

        # Fiscal year recommendations
        fiscal_confidence = fiscal_analysis.get("confidence", 0)
        if fiscal_confidence > 0.8:
            fiscal_type = fiscal_analysis.get("detected_fiscal_type", "calendar")
            if fiscal_type != "calendar":
                recommendations.append(
                    f"Use {fiscal_type} fiscal year structure for better business alignment"
                )

        # Workflow recommendations
        workflow_categories = workflow_patterns.get("category_workflows", {})
        if len(workflow_categories) > 3:
            recommendations.append(
                "Multiple workflow patterns detected - consider category-first organization"
            )

        if not recommendations:
            recommendations.append(
                "Temporal patterns are weak - rely on rule-based and ML classification"
            )

        return recommendations

    # Helper methods
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure when no documents are provided."""
        return {
            "temporal_data_summary": {"total_documents": 0},
            "date_distribution": {"pattern_detected": False},
            "seasonal_insights": {},
            "fiscal_year_analysis": {"detected_fiscal_type": "calendar"},
            "workflow_patterns": {},
            "organization_strategy": {"primary_structure": "category_only"},
            "confidence_metrics": {"overall_confidence": 0.0},
            "recommendations": [
                "No temporal data available - use category-based organization"
            ],
        }

    def _get_quarter(self, month: int) -> str:
        """Get quarter name for a given month."""
        if month in [1, 2, 3]:
            return "Q1"
        elif month in [4, 5, 6]:
            return "Q2"
        elif month in [7, 8, 9]:
            return "Q3"
        else:
            return "Q4"

    def _analyze_temporal_density(self, dates: List[datetime]) -> Dict[str, Any]:
        """Analyze temporal density and distribution patterns."""
        if not dates:
            return {"pattern_type": "none"}

        # Sort dates
        sorted_dates = sorted(dates)

        # Calculate gaps between dates
        gaps = [
            (sorted_dates[i + 1] - sorted_dates[i]).days
            for i in range(len(sorted_dates) - 1)
        ]

        if not gaps:
            return {"pattern_type": "single_point"}

        # Analyze gap patterns
        avg_gap = np.mean(gaps)
        gap_std = np.std(gaps)

        if gap_std < avg_gap * 0.3:  # Low variance = regular pattern
            pattern_type = "regular"
        elif len(set(gaps)) < len(gaps) * 0.5:  # Many repeated gaps = periodic
            pattern_type = "periodic"
        else:
            pattern_type = "irregular"

        return {
            "pattern_type": pattern_type,
            "average_gap_days": avg_gap,
            "gap_variability": gap_std,
            "total_span_days": (sorted_dates[-1] - sorted_dates[0]).days,
        }

    def _identify_peak_periods(
        self, monthly_dist: Dict, quarterly_dist: Dict
    ) -> Dict[str, Any]:
        """Identify peak periods in document creation."""
        peaks = {}

        if monthly_dist:
            peak_month = max(monthly_dist.items(), key=lambda x: x[1])
            peaks["peak_month"] = {
                "month": peak_month[0],
                "month_name": calendar.month_name[peak_month[0]],
                "document_count": peak_month[1],
            }

        if quarterly_dist:
            peak_quarter = max(quarterly_dist.items(), key=lambda x: x[1])
            peaks["peak_quarter"] = {
                "quarter": peak_quarter[0],
                "document_count": peak_quarter[1],
            }

        return peaks

    def _detect_seasonal_pattern(
        self, quarterly_data: Dict[str, int]
    ) -> Dict[str, Any]:
        """Detect seasonal patterns in quarterly document distribution."""
        if len(quarterly_data) < 2:
            return {"pattern_detected": False}

        # Calculate coefficient of variation
        values = list(quarterly_data.values())
        mean_val = np.mean(values)
        std_val = np.std(values)

        if mean_val == 0:
            return {"pattern_detected": False}

        coefficient_of_variation = std_val / mean_val

        # Strong seasonal pattern if high variation
        if coefficient_of_variation > 0.5:
            peak_quarter = max(quarterly_data.items(), key=lambda x: x[1])
            return {
                "pattern_detected": True,
                "pattern_strength": coefficient_of_variation,
                "peak_quarter": peak_quarter[0],
                "peak_count": peak_quarter[1],
                "seasonal_type": self._classify_seasonal_type(peak_quarter[0]),
            }

        return {"pattern_detected": False, "pattern_strength": coefficient_of_variation}

    def _classify_seasonal_type(self, peak_quarter: str) -> str:
        """Classify the type of seasonal pattern based on peak quarter."""
        seasonal_types = {
            "Q1": "year_end_reporting",
            "Q2": "mid_year_activity",
            "Q3": "summer_activity",
            "Q4": "year_end_closure",
        }
        return seasonal_types.get(peak_quarter, "unknown")

    def _calculate_overall_seasonal_trends(
        self, category_seasons: Dict
    ) -> Dict[str, Any]:
        """Calculate overall seasonal trends across all categories."""
        overall_quarters = defaultdict(int)

        for category_data in category_seasons.values():
            for quarter, count in category_data.items():
                overall_quarters[quarter] += count

        if not overall_quarters:
            return {"trend_detected": False}

        # Find dominant season
        peak_quarter = max(overall_quarters.items(), key=lambda x: x[1])
        total_docs = sum(overall_quarters.values())

        return {
            "trend_detected": True,
            "peak_quarter": peak_quarter[0],
            "peak_percentage": (peak_quarter[1] / total_docs) * 100,
            "quarterly_distribution": dict(overall_quarters),
            "seasonal_strength": self._calculate_seasonal_strength(overall_quarters),
        }

    def _calculate_seasonal_strength(self, quarterly_data: Dict) -> float:
        """Calculate the strength of seasonal patterns (0-1 scale)."""
        if len(quarterly_data) < 2:
            return 0.0

        values = list(quarterly_data.values())
        mean_val = np.mean(values)

        if mean_val == 0:
            return 0.0

        # Normalized coefficient of variation
        cv = np.std(values) / mean_val
        return float(min(1.0, cv))  # Cap at 1.0

    def _generate_seasonal_recommendations(self, seasonal_analysis: Dict) -> List[str]:
        """Generate recommendations based on seasonal analysis."""
        recommendations = []

        strong_seasonal_categories = []
        for category, pattern in seasonal_analysis.items():
            if (
                pattern.get("pattern_detected")
                and pattern.get("pattern_strength", 0) > 0.6
            ):
                strong_seasonal_categories.append(category)

        if len(strong_seasonal_categories) >= 2:
            recommendations.append(
                "Multiple categories show strong seasonal patterns - consider quarterly organization"
            )
        elif len(strong_seasonal_categories) == 1:
            recommendations.append(
                f"{strong_seasonal_categories[0]} shows seasonal pattern - organize by business quarters"
            )

        return recommendations

    def _infer_fiscal_year_pattern(self, document_months: List[int]) -> str:
        """Infer fiscal year pattern from document month distribution."""
        if not document_months:
            return "calendar"

        month_counts = Counter(document_months)

        # Look for patterns that suggest non-calendar fiscal years
        # Financial year (Apr-Mar) typically has more activity in Apr and Mar
        financial_score = month_counts.get(4, 0) + month_counts.get(3, 0)

        # Academic year (Sep-Aug) typically has more activity in Sep
        academic_score = month_counts.get(9, 0) * 1.5

        # Federal FY (Oct-Sep) typically has more activity in Sep-Oct
        federal_score = month_counts.get(9, 0) + month_counts.get(10, 0)

        # Calendar year baseline
        calendar_score = sum(month_counts.values()) / 12

        scores = {
            "financial": financial_score,
            "academic": academic_score,
            "federal": federal_score,
            "calendar": calendar_score,
        }

        return max(scores.keys(), key=lambda k: scores[k])

    def _calculate_fiscal_confidence(
        self, fiscal_hints: List, document_months: List[int]
    ) -> float:
        """Calculate confidence in fiscal year detection."""
        if not fiscal_hints and not document_months:
            return 0.0

        # Higher confidence if we have explicit fiscal hints
        hint_confidence = (
            len(fiscal_hints) / max(1, len(fiscal_hints) + len(document_months))
            if fiscal_hints
            else 0
        )

        # Pattern confidence based on month distribution
        if document_months:
            month_variety = (
                len(set(document_months)) / 12.0
            )  # How many different months
            pattern_confidence = min(
                1.0, month_variety * 2
            )  # More months = higher confidence
        else:
            pattern_confidence = 0

        return hint_confidence * 0.7 + pattern_confidence * 0.3

    def _generate_fiscal_structure(
        self, temporal_data: List, fiscal_info: Dict
    ) -> Dict[str, Any]:
        """Generate fiscal year-based organization structure."""
        fiscal_start_month = fiscal_info["start_month"]
        fiscal_years = defaultdict(list)

        for doc in temporal_data:
            for date_info in doc["dates"]:
                # Calculate fiscal year
                actual_year = date_info["year"]
                actual_month = date_info["month"]

                if actual_month >= fiscal_start_month:
                    fiscal_year = actual_year
                else:
                    fiscal_year = actual_year - 1

                fiscal_years[fiscal_year].append(
                    {
                        "filename": doc["filename"],
                        "category": doc["category"],
                        "month": actual_month,
                        "quarter": self._get_fiscal_quarter(
                            actual_month, fiscal_start_month
                        ),
                    }
                )

        return {
            "fiscal_years": dict(fiscal_years),
            "structure_recommendation": self._recommend_fiscal_structure(fiscal_years),
        }

    def _get_fiscal_quarter(self, month: int, fiscal_start_month: int) -> str:
        """Get fiscal quarter for a month given the fiscal year start month."""
        # Normalize month relative to fiscal year start
        normalized_month = ((month - fiscal_start_month) % 12) + 1

        if 1 <= normalized_month <= 3:
            return "FQ1"
        elif 4 <= normalized_month <= 6:
            return "FQ2"
        elif 7 <= normalized_month <= 9:
            return "FQ3"
        else:
            return "FQ4"

    def _recommend_fiscal_structure(self, fiscal_years: Dict) -> Dict[str, Any]:
        """Recommend fiscal year organization structure."""
        total_fiscal_years = len(fiscal_years)
        avg_docs_per_year = (
            np.mean([len(docs) for docs in fiscal_years.values()])
            if fiscal_years
            else 0
        )

        if total_fiscal_years > 3 and avg_docs_per_year > 20:
            return {
                "structure_type": "fiscal_year_quarter",
                "reasoning": "Multiple fiscal years with substantial document volume",
            }
        elif total_fiscal_years > 1:
            return {
                "structure_type": "fiscal_year_only",
                "reasoning": "Multiple fiscal years detected",
            }
        else:
            return {
                "structure_type": "fiscal_quarter_only",
                "reasoning": "Single fiscal year - organize by quarters",
            }

    def _generate_fiscal_recommendations(
        self, fiscal_type: str, fiscal_structure: Dict
    ) -> List[str]:
        """Generate fiscal year-based recommendations."""
        recommendations = []

        if fiscal_type and fiscal_type != "calendar":
            recommendations.append(
                f"Organize by {fiscal_type} fiscal year for business alignment"
            )

        structure_type = fiscal_structure.get("structure_recommendation", {}).get(
            "structure_type"
        )
        if structure_type == "fiscal_year_quarter":
            recommendations.append(
                "Use fiscal year/quarter hierarchy for detailed organization"
            )
        elif structure_type == "fiscal_year_only":
            recommendations.append("Organize by fiscal year with category subdivision")

        return recommendations

    def _analyze_category_workflow(self, timing_data: List[Dict]) -> Dict[str, Any]:
        """Analyze workflow patterns for a specific category."""
        # Sort by datetime
        sorted_timing = sorted(timing_data, key=lambda x: x["datetime"])

        # Analyze timing patterns
        time_gaps = []
        for i in range(len(sorted_timing) - 1):
            gap = (sorted_timing[i + 1]["datetime"] - sorted_timing[i]["datetime"]).days
            time_gaps.append(gap)

        if not time_gaps:
            return {"workflow_detected": False}

        # Detect regular patterns
        avg_gap = np.mean(time_gaps)
        gap_std = np.std(time_gaps)

        workflow_type = "irregular"
        if gap_std < avg_gap * 0.3:  # Regular intervals
            if 25 <= avg_gap <= 35:  # ~Monthly
                workflow_type = "monthly"
            elif 85 <= avg_gap <= 95:  # ~Quarterly
                workflow_type = "quarterly"
            elif 350 <= avg_gap <= 380:  # ~Yearly
                workflow_type = "yearly"
            else:
                workflow_type = "regular_custom"

        return {
            "workflow_detected": True,
            "workflow_type": workflow_type,
            "average_interval_days": avg_gap,
            "interval_consistency": 1.0 - (gap_std / avg_gap) if avg_gap > 0 else 0,
            "document_frequency": len(timing_data),
        }

    def _detect_process_cycles(self, category_timing: Dict) -> Dict[str, Any]:
        """Detect business process cycles across categories."""
        process_cycles = {}

        # Look for categories that might be part of business processes
        business_categories = ["invoices", "contracts", "reports", "correspondence"]

        for category in business_categories:
            if category in category_timing and len(category_timing[category]) > 2:
                cycle_analysis = self._analyze_process_cycle(category_timing[category])
                if cycle_analysis["cycle_detected"]:
                    process_cycles[category] = cycle_analysis

        return {
            "detected_cycles": process_cycles,
            "cycle_recommendations": self._generate_cycle_recommendations(
                process_cycles
            ),
        }

    def _analyze_process_cycle(self, timing_data: List[Dict]) -> Dict[str, Any]:
        """Analyze process cycle for a category."""
        months = [data["month"] for data in timing_data]
        month_counts = Counter(months)

        # Check for cyclical patterns
        if len(month_counts) >= 3:
            # Look for regular intervals
            sorted_months = sorted(month_counts.keys())
            intervals = [
                sorted_months[i + 1] - sorted_months[i]
                for i in range(len(sorted_months) - 1)
            ]

            if intervals and len(set(intervals)) <= 2:  # Consistent intervals
                return {
                    "cycle_detected": True,
                    "cycle_type": (
                        f"every_{intervals[0]}_months"
                        if len(set(intervals)) == 1
                        else "variable_cycle"
                    ),
                    "peak_months": [
                        month for month, count in month_counts.most_common(2)
                    ],
                }

        return {"cycle_detected": False}

    def _generate_cycle_recommendations(self, process_cycles: Dict) -> List[str]:
        """Generate recommendations based on process cycles."""
        recommendations = []

        if len(process_cycles) > 1:
            recommendations.append(
                "Multiple business process cycles detected - organize by process workflow"
            )

        for category, cycle_info in process_cycles.items():
            cycle_type = cycle_info.get("cycle_type", "")
            if "monthly" in cycle_type:
                recommendations.append(
                    f"{category} follows monthly cycle - organize by month within year"
                )
            elif "quarterly" in cycle_type:
                recommendations.append(
                    f"{category} follows quarterly cycle - organize by business quarter"
                )

        return recommendations

    def _generate_workflow_recommendations(self, workflow_insights: Dict) -> List[str]:
        """Generate workflow-based recommendations."""
        recommendations = []

        regular_workflows = []
        for category, workflow in workflow_insights.items():
            if (
                workflow.get("workflow_detected")
                and workflow.get("interval_consistency", 0) > 0.7
            ):
                regular_workflows.append((category, workflow["workflow_type"]))

        if len(regular_workflows) > 1:
            recommendations.append(
                "Multiple regular workflows detected - organize by workflow pattern"
            )

        return recommendations

    def _calculate_pattern_strength(self, temporal_data: List[Dict[str, Any]]) -> float:
        """Calculate overall pattern strength in temporal data."""
        if not temporal_data:
            return 0.0

        # Count documents with dates
        docs_with_dates = len([d for d in temporal_data if d["dates"]])
        if docs_with_dates == 0:
            return 0.0

        # Calculate date distribution variance (higher = more pattern)
        all_months = []
        for doc in temporal_data:
            for date_info in doc["dates"]:
                all_months.append(date_info["month"])

        if len(all_months) < 2:
            return 0.0

        # Normalized variance indicates pattern strength
        month_counts = Counter(all_months)
        values = list(month_counts.values())
        mean_val = np.mean(values)

        if mean_val == 0:
            return 0.0

        cv = np.std(values) / mean_val
        return float(min(1.0, cv * 0.5))  # Scale to 0-1 range
