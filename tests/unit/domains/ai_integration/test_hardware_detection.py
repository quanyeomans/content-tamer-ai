"""
Tests for HardwareDetector functionality.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from shared.infrastructure.hardware_detector import HardwareDetector


class TestHardwareDetection(unittest.TestCase):
    """Test hardware detection functionality."""

    def setUp(self):
        """Set up test hardware detector."""
        self.detector = HardwareDetector()

    @patch("subprocess.run")
    def test_estimate_ram_windows(self, mock_run):
        """Test RAM estimation on Windows."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "TotalPhysicalMemory  \n8589934592          \n"
        mock_run.return_value = mock_result

        ram_gb = self.detector._estimate_ram_without_psutil()
        self.assertAlmostEqual(ram_gb, 8.0, places=1)

    def test_estimate_ram_fallback(self):
        """Test RAM estimation fallback when all methods fail."""
        with patch("platform.system", return_value="UnknownOS"):
            ram_gb = self.detector._estimate_ram_without_psutil()
            self.assertEqual(ram_gb, 8.0)  # Default fallback

    def test_detect_gpu_presence(self):
        """Test basic GPU detection functionality."""
        # Should not raise exceptions
        has_gpu, gpu_name = self.detector._detect_gpu()
        self.assertIsInstance(has_gpu, bool)
        self.assertTrue(gpu_name is None or isinstance(gpu_name, str))


if __name__ == "__main__":
    unittest.main()
