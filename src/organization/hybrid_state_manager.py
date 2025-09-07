"""
Hybrid State Manager

Combines simple JSON configuration with SQLite analytics for advanced
historical analysis and ML performance tracking. Maintains backward
compatibility with Phase 1 SimpleStateManager.
"""

import os
import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import tempfile

from .state_manager import SimpleStateManager


class HybridStateManager(SimpleStateManager):
    """Advanced state manager with SQLite analytics and JSON config compatibility."""

    def __init__(self, target_folder: str):
        """
        Initialize hybrid state manager.

        Args:
            target_folder: Target directory for state management
        """
        # Initialize base JSON functionality
        super().__init__(target_folder)

        # SQLite database for advanced analytics
        self.analytics_db_path = os.path.join(self.organization_dir, "analytics.db")
        self.analytics_enabled = True

        try:
            self._init_analytics_database()
        except Exception as e:
            logging.warning(f"Failed to initialize analytics database: {e}")
            self.analytics_enabled = False

    def _init_analytics_database(self) -> None:
        """Initialize SQLite database with required schema."""
        try:
            with sqlite3.connect(self.analytics_db_path) as conn:
                cursor = conn.cursor()

                # Create tables for advanced analytics
                cursor.executescript(
                    """
                    -- Organization sessions with detailed metrics
                    CREATE TABLE IF NOT EXISTS organization_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        timestamp TEXT NOT NULL,
                        document_count INTEGER NOT NULL,
                        rule_accuracy REAL,
                        ml_accuracy REAL,
                        combined_accuracy REAL,
                        uncertain_documents INTEGER DEFAULT 0,
                        ml_refined_documents INTEGER DEFAULT 0,
                        processing_time_seconds REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Document classifications for pattern analysis
                    CREATE TABLE IF NOT EXISTS document_classifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        category TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        method TEXT NOT NULL, -- 'rule_based', 'ml_refinement'
                        content_preview TEXT,
                        metadata_json TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES organization_sessions(session_id)
                    );
                    
                    -- ML performance metrics
                    CREATE TABLE IF NOT EXISTS ml_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        model_name TEXT NOT NULL,
                        cluster_count INTEGER,
                        silhouette_score REAL,
                        processing_time_seconds REAL,
                        documents_processed INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES organization_sessions(session_id)
                    );
                    
                    -- Quality trends over time
                    CREATE TABLE IF NOT EXISTS quality_trends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        avg_accuracy REAL NOT NULL,
                        session_count INTEGER NOT NULL,
                        document_count INTEGER NOT NULL,
                        ml_usage_rate REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Create indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON organization_sessions(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_classifications_session ON document_classifications(session_id);
                    CREATE INDEX IF NOT EXISTS idx_classifications_category ON document_classifications(category);
                    CREATE INDEX IF NOT EXISTS idx_performance_session ON ml_performance(session_id);
                    CREATE INDEX IF NOT EXISTS idx_trends_date ON quality_trends(date);
                """
                )

                conn.commit()
                logging.info("Analytics database initialized successfully")

        except sqlite3.Error as e:
            logging.error(f"Failed to initialize analytics database: {e}")
            raise

    def save_enhanced_session_data(
        self,
        session_data: Dict[str, Any],
        processing_time: float = 0.0,
        ml_metrics: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Save enhanced session data with ML metrics to both JSON and SQLite.

        Args:
            session_data: Enhanced session data with ML information
            processing_time: Total processing time in seconds
            ml_metrics: ML-specific performance metrics

        Returns:
            Success status
        """
        # Save to JSON for backward compatibility
        json_success = self.save_session_data(session_data)

        if not self.analytics_enabled:
            return json_success

        try:
            with sqlite3.connect(self.analytics_db_path) as conn:
                cursor = conn.cursor()

                # Insert session record
                quality_metrics = session_data.get("quality_metrics", {})
                session_id = session_data.get("session_id", "unknown")

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO organization_sessions 
                    (session_id, timestamp, document_count, rule_accuracy, ml_accuracy, 
                     combined_accuracy, uncertain_documents, ml_refined_documents, processing_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_id,
                        datetime.now().isoformat(),
                        session_data.get("document_count", 0),
                        quality_metrics.get("rule_accuracy", 0.0),
                        quality_metrics.get("ml_accuracy", 0.0),
                        quality_metrics.get("accuracy", 0.0),
                        quality_metrics.get("uncertain_documents", 0),
                        quality_metrics.get("ml_refined_documents", 0),
                        processing_time,
                    ),
                )

                # Insert document classifications
                classified_docs = session_data.get("classified_documents", [])
                for doc in classified_docs:
                    cursor.execute(
                        """
                        INSERT INTO document_classifications
                        (session_id, filename, category, confidence, method, content_preview, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            session_id,
                            doc.get("filename", ""),
                            doc.get("category", "other"),
                            doc.get("confidence", 0.0),
                            doc.get("classification_method", "rule_based"),
                            doc.get("content_preview", "")[:500],  # Limit size
                            json.dumps(doc.get("metadata", {})) if doc.get("metadata") else None,
                        ),
                    )

                # Insert ML performance metrics if available
                if ml_metrics:
                    cursor.execute(
                        """
                        INSERT INTO ml_performance
                        (session_id, model_name, cluster_count, silhouette_score, 
                         processing_time_seconds, documents_processed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            session_id,
                            ml_metrics.get("model_name", "unknown"),
                            ml_metrics.get("cluster_count", 0),
                            ml_metrics.get("silhouette_score", 0.0),
                            ml_metrics.get("processing_time", 0.0),
                            ml_metrics.get("documents_processed", 0),
                        ),
                    )

                conn.commit()
                return True

        except sqlite3.Error as e:
            logging.error(f"Failed to save enhanced session data: {e}")
            return json_success  # At least JSON save succeeded

    def get_advanced_insights(self) -> Dict[str, Any]:
        """Generate advanced insights using SQLite analytics."""
        if not self.analytics_enabled:
            return {"error": "Analytics not available"}

        try:
            with sqlite3.connect(self.analytics_db_path) as conn:
                insights = {}

                # Overall statistics
                insights["overview"] = self._get_overview_stats(conn)

                # Quality trends
                insights["quality_trends"] = self._get_quality_trends(conn)

                # ML performance analysis
                insights["ml_performance"] = self._get_ml_performance_analysis(conn)

                # Category distribution analysis
                insights["category_analysis"] = self._get_category_analysis(conn)

                # Improvement recommendations
                insights["recommendations"] = self._generate_recommendations(insights)

                return insights

        except sqlite3.Error as e:
            logging.error(f"Failed to generate advanced insights: {e}")
            return {"error": f"Database error: {e}"}

    def _get_overview_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get overall statistics from the database."""
        cursor = conn.cursor()

        # Session statistics
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_sessions,
                AVG(combined_accuracy) as avg_accuracy,
                MAX(combined_accuracy) as best_accuracy,
                SUM(document_count) as total_documents,
                AVG(processing_time_seconds) as avg_processing_time
            FROM organization_sessions
        """
        )

        row = cursor.fetchone()
        if row:
            return {
                "total_sessions": row[0] or 0,
                "average_accuracy": row[1] or 0.0,
                "best_accuracy": row[2] or 0.0,
                "total_documents_processed": row[3] or 0,
                "average_processing_time": row[4] or 0.0,
            }

        return {}

    def _get_quality_trends(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Analyze quality trends over time."""
        cursor = conn.cursor()

        # Get recent sessions with quality metrics
        cursor.execute(
            """
            SELECT 
                DATE(timestamp) as date,
                AVG(combined_accuracy) as avg_accuracy,
                COUNT(*) as session_count,
                SUM(document_count) as document_count,
                AVG(CAST(ml_refined_documents AS REAL) / document_count) as ml_usage_rate
            FROM organization_sessions
            WHERE timestamp >= date('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        """
        )

        trends = []
        for row in cursor.fetchall():
            trends.append(
                {
                    "date": row[0],
                    "accuracy": row[1] or 0.0,
                    "sessions": row[2] or 0,
                    "documents": row[3] or 0,
                    "ml_usage_rate": row[4] or 0.0,
                }
            )

        return {"daily_trends": trends}

    def _get_ml_performance_analysis(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Analyze ML refinement performance."""
        cursor = conn.cursor()

        # ML usage statistics
        cursor.execute(
            """
            SELECT 
                COUNT(*) as sessions_with_ml,
                AVG(silhouette_score) as avg_silhouette_score,
                AVG(cluster_count) as avg_cluster_count,
                AVG(processing_time_seconds) as avg_ml_processing_time,
                SUM(documents_processed) as total_ml_documents
            FROM ml_performance
        """
        )

        ml_row = cursor.fetchone()

        # Compare accuracy with and without ML
        cursor.execute(
            """
            SELECT 
                AVG(CASE WHEN ml_refined_documents > 0 THEN combined_accuracy END) as accuracy_with_ml,
                AVG(CASE WHEN ml_refined_documents = 0 THEN combined_accuracy END) as accuracy_without_ml
            FROM organization_sessions
        """
        )

        accuracy_row = cursor.fetchone()

        analysis = {}
        if ml_row:
            analysis["ml_usage"] = {
                "sessions_using_ml": ml_row[0] or 0,
                "average_silhouette_score": ml_row[1] or 0.0,
                "average_cluster_count": ml_row[2] or 0.0,
                "average_ml_processing_time": ml_row[3] or 0.0,
                "total_documents_processed": ml_row[4] or 0,
            }

        if accuracy_row:
            analysis["ml_impact"] = {
                "accuracy_with_ml": accuracy_row[0] or 0.0,
                "accuracy_without_ml": accuracy_row[1] or 0.0,
                "ml_improvement": (accuracy_row[0] or 0.0) - (accuracy_row[1] or 0.0),
            }

        return analysis

    def _get_category_analysis(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Analyze document category patterns."""
        cursor = conn.cursor()

        # Category distribution
        cursor.execute(
            """
            SELECT 
                category,
                COUNT(*) as document_count,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN method = 'ml_refinement' THEN 1 END) as ml_refined_count
            FROM document_classifications
            GROUP BY category
            ORDER BY document_count DESC
        """
        )

        categories = []
        for row in cursor.fetchall():
            categories.append(
                {
                    "category": row[0],
                    "document_count": row[1],
                    "average_confidence": row[2] or 0.0,
                    "ml_refined_count": row[3] or 0,
                    "ml_refinement_rate": (row[3] or 0) / row[1] if row[1] > 0 else 0,
                }
            )

        return {"category_distribution": categories}

    def _generate_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on insights."""
        recommendations = []

        overview = insights.get("overview", {})
        ml_performance = insights.get("ml_performance", {})

        # Accuracy recommendations
        avg_accuracy = overview.get("average_accuracy", 0.0)
        if avg_accuracy < 0.8:
            recommendations.append(
                "Consider improving rule-based classification patterns - accuracy below 80%"
            )

        # ML usage recommendations
        ml_impact = ml_performance.get("ml_impact", {})
        ml_improvement = ml_impact.get("ml_improvement", 0.0)

        if ml_improvement > 0.05:
            recommendations.append(
                f"ML refinement is providing {ml_improvement:.1%} accuracy improvement - consider using Phase 3"
            )
        elif ml_improvement < 0.02:
            recommendations.append(
                "ML refinement showing minimal impact - rule-based classification may be sufficient"
            )

        # Performance recommendations
        avg_time = overview.get("average_processing_time", 0.0)
        if avg_time > 60:
            recommendations.append(
                "Processing time is high - consider optimizing ML model or increasing confidence threshold"
            )

        if not recommendations:
            recommendations.append("System performing well - no immediate optimizations needed")

        return recommendations

    def export_analytics_data(self, output_file: Optional[str] = None) -> str:
        """Export analytics data to CSV format."""
        if not self.analytics_enabled:
            raise RuntimeError("Analytics not available")

        if output_file is None:
            output_file = os.path.join(self.organization_dir, "analytics_export.csv")

        try:
            with sqlite3.connect(self.analytics_db_path) as conn:
                cursor = conn.cursor()

                # Export comprehensive session data
                cursor.execute(
                    """
                    SELECT 
                        s.session_id,
                        s.timestamp,
                        s.document_count,
                        s.combined_accuracy,
                        s.uncertain_documents,
                        s.ml_refined_documents,
                        s.processing_time_seconds,
                        COUNT(d.id) as classified_documents,
                        AVG(d.confidence) as avg_document_confidence
                    FROM organization_sessions s
                    LEFT JOIN document_classifications d ON s.session_id = d.session_id
                    GROUP BY s.session_id
                    ORDER BY s.timestamp DESC
                """
                )

                # Write CSV
                import csv

                with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)

                    # Header
                    writer.writerow(
                        [
                            "session_id",
                            "timestamp",
                            "document_count",
                            "accuracy",
                            "uncertain_documents",
                            "ml_refined_documents",
                            "processing_time",
                            "classified_documents",
                            "avg_confidence",
                        ]
                    )

                    # Data
                    for row in cursor.fetchall():
                        writer.writerow(row)

                return output_file

        except (sqlite3.Error, IOError) as e:
            logging.error(f"Failed to export analytics data: {e}")
            raise

    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old analytics data to prevent database growth."""
        if not self.analytics_enabled:
            return

        try:
            with sqlite3.connect(self.analytics_db_path) as conn:
                cursor = conn.cursor()

                cutoff_date = datetime.now().replace(day=datetime.now().day - days_to_keep)
                cutoff_str = cutoff_date.isoformat()

                # Clean up old records
                cursor.execute(
                    "DELETE FROM document_classifications WHERE created_at < ?", (cutoff_str,)
                )
                cursor.execute("DELETE FROM ml_performance WHERE created_at < ?", (cutoff_str,))
                cursor.execute(
                    "DELETE FROM organization_sessions WHERE created_at < ?", (cutoff_str,)
                )

                # Vacuum to reclaim space
                cursor.execute("VACUUM")

                conn.commit()
                logging.info(f"Cleaned up analytics data older than {days_to_keep} days")

        except sqlite3.Error as e:
            logging.warning(f"Failed to cleanup old data: {e}")
