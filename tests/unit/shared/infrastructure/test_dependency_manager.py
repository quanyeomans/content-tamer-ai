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
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from shared.infrastructure.dependency_manager import DependencyManager

class TestDependencyManager(unittest.TestCase):
    """Test dependency management functionality."""
    
    def setUp(self):
        """Set up test dependency manager."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DependencyManager(config_dir=self.temp_dir)
    
    @patch('subprocess.run')
    def test_version_extraction_unexpected_format(self, mock_run):
        """Test handling of unexpected version output format."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "unexpected format without version info"
        mock_run.return_value = mock_result

        version = self.manager._get_version("ollama", "/usr/bin/ollama")

        # Should handle gracefully and extract what it can
        self.assertIsNone(version)
        
    def test_dependency_detection_basic(self):
        """Test basic dependency detection functionality."""
        # Should not raise exceptions
        dependencies = self.manager.refresh_all_dependencies()
        self.assertIsInstance(dependencies, dict)

if __name__ == '__main__':
    unittest.main()