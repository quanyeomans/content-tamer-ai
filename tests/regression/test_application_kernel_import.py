"""
Regression test for application_kernel import issue.

Bug: Application fails to start with "Domain architecture components missing"
Root cause: Incorrect import path in application_container.py
"""

import sys
import os
import unittest
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestApplicationKernelImport(unittest.TestCase):
    """Test that application_kernel can be properly imported and created."""

    def test_bug_reproduction_missing_kernel(self):
        """Reproduce the bug where application_kernel cannot be imported."""
        from core.application_container import ApplicationContainer
        
        # This should fail with the current bug
        container = ApplicationContainer()
        kernel = container.create_application_kernel()
        
        # With the bug, kernel will be None due to import error
        # After fix, kernel should be a valid ApplicationKernel instance
        self.assertIsNotNone(kernel, "ApplicationKernel should be created successfully")

    def test_application_kernel_exists(self):
        """Verify ApplicationKernel class exists and can be imported."""
        try:
            # This is the correct import that should work
            from orchestration.application_kernel import ApplicationKernel
            self.assertIsNotNone(ApplicationKernel)
        except ImportError as e:
            self.fail(f"ApplicationKernel import failed: {e}")

    def test_container_creates_kernel_after_fix(self):
        """Test that container can create kernel after import fix."""
        from core.application_container import ApplicationContainer
        
        container = ApplicationContainer()
        kernel = container.create_application_kernel()
        
        # After fix, these should all pass
        self.assertIsNotNone(kernel)
        self.assertTrue(hasattr(kernel, 'process_documents'))
        self.assertTrue(hasattr(kernel, 'container'))


if __name__ == '__main__':
    unittest.main()