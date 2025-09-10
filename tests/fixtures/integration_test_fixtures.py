"""
Centralized Integration Test Fixtures and Data Management

Provides consistent test data, directory structures, and mock configurations
for high-quality integration testing across components.
"""

import os
import shutil
import tempfile
from typing import Dict, List


class PerformanceTestFixtures:
    """Performance testing baselines and utilities."""

    @staticmethod
    def get_performance_baselines() -> Dict[str, float]:
        """Define performance baselines for regression testing."""
        return {
            "single_file_processing_max_seconds": 2.0,
            "batch_10_files_max_seconds": 15.0,
            "memory_usage_max_mb": 100.0,
            "ai_call_timeout_seconds": 30.0,
        }

    @staticmethod
    def create_stress_test_data(file_count: int = 100) -> List[Dict]:
        """Create large dataset for stress testing."""
        stress_files = []
        for i in range(file_count):
            # Create files of varying sizes
            content_size = min(1000 + (i * 50), 10000)  # 1KB to 10KB range
            content = f"Large test document {i}\n" + (
                "Sample content line.\n" * (content_size // 20)
            )

            stress_files.append(
                {
                    "filename": f"stress_test_{i:04d}.txt",
                    "content": content.encode(),
                    "expected_content": content[:100] + "...",  # Truncated for testing
                    "file_type": "txt",
                }
            )

        return stress_files


class FailureScenarioFixtures:
    """Fixtures for testing failure propagation across components."""

    @staticmethod
    def create_ai_failure_scenario():
        """Create scenario where AI consistently fails."""
        return {"success_rate": 0.0, "scenario": "ai_failure"}

    @staticmethod
    def create_content_extraction_failure_scenario():
        """Create scenario where content extraction fails."""
        return {"extraction_success_rate": 0.0, "scenario": "content_extraction_failure"}

    @staticmethod
    def create_file_system_failure_scenario(temp_dir: str):
        """Create scenario where file operations fail (permissions, disk full, etc)."""
        # Make directory read-only to simulate permission failures
        os.chmod(temp_dir, 0o444)
        return temp_dir

    @staticmethod
    def create_intermittent_failure_scenario():
        """Create scenario with intermittent failures (50% success rate)."""
        return {
            "ai_mock": {"success_rate": 0.5, "scenario": "ai_intermittent"},
            "content_mock": {"extraction_success_rate": 0.5, "scenario": "content_intermittent"},
        }


# Convenience factory instance
performance_fixtures = PerformanceTestFixtures()
failure_fixtures = FailureScenarioFixtures()
