"""
Tests for HardwareDetector functionality.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from utils.hardware_detector import HardwareDetector, SystemInfo, ModelRecommendation


class TestHardwareDetector(unittest.TestCase):
    """Test HardwareDetector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = HardwareDetector()
        # Reset cached system info for each test
        self.detector._system_info = None

    @patch("utils.hardware_detector.HAVE_PSUTIL", True)
    @patch("utils.hardware_detector.psutil")
    def test_detect_system_info_with_psutil(self, mock_psutil):
        """Test system detection with psutil available."""
        # Mock psutil memory and CPU info
        mock_memory = MagicMock()
        mock_memory.total = 8 * 1024**3  # 8GB in bytes
        mock_memory.available = 6 * 1024**3  # 6GB available
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_count.return_value = 8

        with patch("platform.system", return_value="Linux"), \
             patch("platform.machine", return_value="x86_64"), \
             patch.object(self.detector, "_detect_gpu", return_value=(False, None)):
            
            info = self.detector.detect_system_info()
            
            self.assertAlmostEqual(info.total_ram_gb, 8.0, places=1)
            self.assertAlmostEqual(info.available_ram_gb, 6.0, places=1)
            self.assertEqual(info.cpu_count, 8)
            self.assertEqual(info.platform_system, "Linux")
            self.assertEqual(info.platform_machine, "x86_64")
            self.assertFalse(info.has_gpu)

    @patch("utils.hardware_detector.HAVE_PSUTIL", False)
    @patch("utils.hardware_detector.psutil", None)
    def test_detect_system_info_without_psutil(self):
        """Test system detection fallback without psutil."""
        with patch("platform.system", return_value="Darwin"), \
             patch("platform.machine", return_value="arm64"), \
             patch("os.cpu_count", return_value=4), \
             patch.object(self.detector, "_estimate_ram_without_psutil", return_value=8.0), \
             patch.object(self.detector, "_detect_gpu", return_value=(True, "Apple M1")):
            
            info = self.detector.detect_system_info()
            
            self.assertAlmostEqual(info.total_ram_gb, 8.0, places=1)
            self.assertAlmostEqual(info.available_ram_gb, 5.6, places=1)  # 70% of 8GB
            self.assertEqual(info.cpu_count, 4)
            self.assertEqual(info.platform_system, "Darwin")
            self.assertEqual(info.platform_machine, "arm64")
            self.assertTrue(info.has_gpu)
            self.assertEqual(info.gpu_info, "Apple M1")

    @patch("builtins.open", unittest.mock.mock_open(read_data="MemTotal:        8192000 kB\n"))
    @patch("platform.system", return_value="Linux")
    def test_estimate_ram_linux(self):
        """Test RAM estimation on Linux."""
        ram_gb = self.detector._estimate_ram_without_psutil()
        self.assertAlmostEqual(ram_gb, 8.0, places=1)

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_estimate_ram_macos(self, mock_run):
        """Test RAM estimation on macOS."""
        # Mock sysctl output (8GB in bytes)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "8589934592"  # 8GB in bytes
        mock_run.return_value = mock_result
        
        ram_gb = self.detector._estimate_ram_without_psutil()
        self.assertAlmostEqual(ram_gb, 8.0, places=1)

    @patch("platform.system", return_value="Windows")  
    @patch("subprocess.run")
    def test_estimate_ram_windows(self, mock_run):
        """Test RAM estimation on Windows."""
        # Mock wmic output
        mock_result = MagicMock()
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

    @patch("os.path.exists")
    @patch("platform.system", return_value="Linux")
    def test_detect_gpu_linux_nvidia(self, mock_exists):
        """Test GPU detection on Linux with NVIDIA."""
        mock_exists.side_effect = lambda path: path == "/proc/driver/nvidia/version"
        
        has_gpu, gpu_info = self.detector._detect_gpu()
        self.assertTrue(has_gpu)
        self.assertEqual(gpu_info, "NVIDIA GPU (detected)")

    @patch("os.path.exists") 
    @patch("platform.system", return_value="Linux")
    def test_detect_gpu_linux_generic(self, mock_exists):
        """Test GPU detection on Linux with generic GPU."""
        mock_exists.side_effect = lambda path: path == "/dev/dri"
        
        has_gpu, gpu_info = self.detector._detect_gpu()
        self.assertTrue(has_gpu)
        self.assertEqual(gpu_info, "GPU (detected)")

    @patch("os.path.exists", return_value=False)
    @patch("platform.system", return_value="Linux")
    def test_detect_gpu_none(self, mock_exists):
        """Test GPU detection when no GPU is found."""
        has_gpu, gpu_info = self.detector._detect_gpu()
        self.assertFalse(has_gpu)
        self.assertIsNone(gpu_info)

    def test_get_recommended_models_sufficient_ram(self):
        """Test model recommendations with sufficient RAM."""
        # Mock system with 8GB available RAM
        mock_system = SystemInfo(
            total_ram_gb=10.0,
            available_ram_gb=8.0,
            cpu_count=4,
            platform_system="Linux",
            platform_machine="x86_64"
        )
        self.detector._system_info = mock_system
        
        recommendations = self.detector.get_recommended_models()
        
        self.assertEqual(len(recommendations), 1)
        rec = recommendations[0]
        self.assertEqual(rec.model_name, "llama3.1-8b")  # Best model that fits
        self.assertEqual(rec.confidence, "low")  # 8.0 - 7.5 = 0.5GB headroom (< 1GB = low)
        self.assertIn("8.0GB RAM available", rec.reason)

    def test_get_recommended_models_insufficient_ram(self):
        """Test model recommendations with insufficient RAM."""
        # Mock system with only 2GB available RAM
        mock_system = SystemInfo(
            total_ram_gb=4.0,
            available_ram_gb=2.0,
            cpu_count=2,
            platform_system="Linux", 
            platform_machine="x86_64"
        )
        self.detector._system_info = mock_system
        
        recommendations = self.detector.get_recommended_models()
        
        self.assertEqual(len(recommendations), 1)
        rec = recommendations[0]
        self.assertEqual(rec.model_name, "none")
        self.assertEqual(rec.confidence, "high")
        self.assertIn("Insufficient RAM", rec.reason)

    def test_get_recommended_models_high_confidence(self):
        """Test model recommendations with high confidence (lots of headroom)."""
        # Mock system with 12GB available RAM
        mock_system = SystemInfo(
            total_ram_gb=16.0,
            available_ram_gb=12.0,
            cpu_count=8,
            platform_system="Linux",
            platform_machine="x86_64"
        )
        self.detector._system_info = mock_system
        
        recommendations = self.detector.get_recommended_models()
        
        self.assertEqual(len(recommendations), 1)
        rec = recommendations[0]
        self.assertEqual(rec.model_name, "llama3.1-8b")
        self.assertEqual(rec.confidence, "high")  # 12.0 - 7.5 = 4.5GB headroom
        self.assertIn("Excellent fit", rec.reason)

    def test_get_system_tier(self):
        """Test system tier classification."""
        test_cases = [
            (12.0, "premium"),
            (8.5, "enhanced"), 
            (7.0, "standard"),
            (3.0, "ultra_lightweight")
        ]
        
        for available_ram, expected_tier in test_cases:
            mock_system = SystemInfo(
                total_ram_gb=available_ram + 2,
                available_ram_gb=available_ram,
                cpu_count=4,
                platform_system="Linux",
                platform_machine="x86_64"
            )
            self.detector._system_info = mock_system
            
            tier = self.detector.get_system_tier()
            self.assertEqual(tier, expected_tier, f"Failed for {available_ram}GB RAM")

    def test_check_ollama_compatibility_compatible(self):
        """Test Ollama compatibility check for compatible system."""
        mock_system = SystemInfo(
            total_ram_gb=8.0,
            available_ram_gb=6.0,
            cpu_count=4,
            platform_system="Linux",
            platform_machine="x86_64"
        )
        self.detector._system_info = mock_system
        
        compatibility = self.detector.check_ollama_compatibility()
        
        self.assertTrue(compatibility["supported_platform"])
        self.assertTrue(compatibility["sufficient_ram"])
        self.assertTrue(compatibility["supported_architecture"])
        self.assertTrue(compatibility["recommended_ram"])
        self.assertTrue(compatibility["overall_compatible"])

    def test_check_ollama_compatibility_insufficient_ram(self):
        """Test Ollama compatibility check with insufficient RAM."""
        mock_system = SystemInfo(
            total_ram_gb=2.0,
            available_ram_gb=1.5,
            cpu_count=2,
            platform_system="Linux", 
            platform_machine="x86_64"
        )
        self.detector._system_info = mock_system
        
        compatibility = self.detector.check_ollama_compatibility()
        
        self.assertTrue(compatibility["supported_platform"])
        self.assertFalse(compatibility["sufficient_ram"])
        self.assertTrue(compatibility["supported_architecture"])
        self.assertFalse(compatibility["recommended_ram"])
        self.assertFalse(compatibility["overall_compatible"])

    def test_get_performance_estimate_good_performance(self):
        """Test performance estimation for good system."""
        mock_system = SystemInfo(
            total_ram_gb=16.0,
            available_ram_gb=12.0,
            cpu_count=8,
            platform_system="Linux",
            platform_machine="x86_64"
        )
        self.detector._system_info = mock_system
        
        estimate = self.detector.get_performance_estimate("mistral-7b")
        
        self.assertEqual(estimate["inference_speed"], "Fast (5-15 seconds)")
        self.assertEqual(estimate["memory_status"], "Comfortable")
        self.assertIn("Good choice", estimate["recommendation"])

    def test_get_performance_estimate_insufficient_ram(self):
        """Test performance estimation for insufficient RAM."""
        mock_system = SystemInfo(
            total_ram_gb=4.0,
            available_ram_gb=3.0,
            cpu_count=2,
            platform_system="Linux",
            platform_machine="x86_64" 
        )
        self.detector._system_info = mock_system
        
        estimate = self.detector.get_performance_estimate("mistral-7b")  # Needs 6.5GB
        
        self.assertEqual(estimate["inference_speed"], "Not supported")
        self.assertEqual(estimate["memory_status"], "Insufficient RAM")
        self.assertIn("smaller model", estimate["recommendation"])

    def test_get_performance_estimate_unknown_model(self):
        """Test performance estimation for unknown model."""
        estimate = self.detector.get_performance_estimate("unknown-model")
        self.assertIn("error", estimate)
        self.assertEqual(estimate["error"], "Unknown model")

    def test_get_system_summary(self):
        """Test comprehensive system summary."""
        mock_system = SystemInfo(
            total_ram_gb=8.0,
            available_ram_gb=6.0,
            cpu_count=4,
            platform_system="Linux",
            platform_machine="x86_64",
            has_gpu=True,
            gpu_info="NVIDIA RTX 3060"
        )
        self.detector._system_info = mock_system
        
        summary = self.detector.get_system_summary()
        
        # Check hardware section
        self.assertEqual(summary["hardware"]["total_ram_gb"], 8.0)
        self.assertEqual(summary["hardware"]["available_ram_gb"], 6.0)
        self.assertEqual(summary["hardware"]["cpu_count"], 4)
        self.assertEqual(summary["hardware"]["platform"], "Linux x86_64")
        self.assertEqual(summary["hardware"]["gpu"], "NVIDIA RTX 3060")
        
        # Check other sections exist
        self.assertIn("compatibility", summary)
        self.assertIn("tier", summary)
        self.assertIn("recommendations", summary)
        self.assertEqual(summary["tier"], "standard")


if __name__ == "__main__":
    unittest.main()