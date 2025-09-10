#!/usr/bin/env python3
"""
Comprehensive Tests for DependencyManager

Tests the centralized dependency detection, configuration, and caching system
according to TDD principles with comprehensive edge case coverage.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from shared.infrastructure.dependency_manager import DependencyManager


class TestDependencyManager(unittest.TestCase):
    """Test dependency management functionality."""

    def setUp(self):
        """Set up test dependency manager."""
        # tmp_path will be injected by pytest fixture
        pass

    @pytest.mark.usefixtures("tmp_path")
    @patch("subprocess.run")
    def test_version_extraction_unexpected_format(self, mock_run):
        """Test handling of unexpected version output format."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = DependencyManager(config_dir=tmp_dir)
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "unexpected format without version info"
            mock_run.return_value = mock_result

            version = manager._get_version("ollama", "/usr/bin/ollama")

            # Should handle gracefully and extract what it can
            self.assertIsNone(version)

    def test_dependency_detection_basic(self):
        """Test basic dependency detection functionality."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = DependencyManager(config_dir=tmp_dir)
            # Should not raise exceptions
            dependencies = manager.refresh_all_dependencies()
        self.assertIsInstance(dependencies, dict)


if __name__ == "__main__":
    unittest.main()
