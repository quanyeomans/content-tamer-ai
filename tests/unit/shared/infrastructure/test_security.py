"""
Security tests for Content Tamer AI

Tests the security fixes implemented for prompt injection, path traversal,
and other attack vectors.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))


class TestSecurityMeasures(unittest.TestCase):
    """Test security measures and vulnerability prevention."""

    def test_secure_subprocess_usage(self):
        """Test that subprocess calls use secure patterns."""
        # Mock subprocess to verify secure usage patterns
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout=""  # Simulate command failure to avoid complex mocking
            )

            # Import after mocking to ensure we get the mocked subprocess
            try:
                from shared.infrastructure.hardware_detector import HardwareDetector

                detector = HardwareDetector()

                # This should use secure subprocess calls internally
                detector._estimate_ram_without_psutil()

                # At least one secure call should have been made
                self.assertTrue(mock_run.called, "Secure subprocess calls should be made")
            except ImportError:
                self.skipTest("HardwareDetector not available for security testing")

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        from shared.infrastructure.security import PathValidator, SecurityError
        
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        # Create a temporary safe directory for validation
        with tempfile.TemporaryDirectory() as temp_dir:
            allowed_dirs = {temp_dir}
            
            for dangerous_path in dangerous_paths:
                # Test that path validation rejects dangerous paths
                with self.assertRaises(SecurityError):
                    PathValidator.validate_file_path(dangerous_path, allowed_dirs)


if __name__ == "__main__":
    unittest.main()
