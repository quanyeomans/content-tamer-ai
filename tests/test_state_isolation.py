"""
Test State Isolation - Verify container state isolation mechanisms work correctly.

This test file validates that TestApplicationContainer properly isolates
state between tests to prevent contamination and ensure reliable test execution.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock

from core.application_container import TestApplicationContainer, create_function_scoped_container
from tests.utils.rich_test_utils import RichTestCase, create_isolated_test_container, with_isolated_container


class TestStateIsolation(unittest.TestCase, RichTestCase):
    """Test state isolation mechanisms in TestApplicationContainer."""

    def setUp(self):
        """Set up test environment."""
        RichTestCase.setUp(self)
        self.original_sys_path_len = len(sys.path)

    def tearDown(self):
        """Clean up test environment."""
        RichTestCase.tearDown(self)

    def test_reset_state_clears_cached_services(self):
        """Test that reset_state() clears any cached services."""
        container = TestApplicationContainer()
        
        # Add some cached services
        container._cached_services['test_service'] = Mock()
        container._service_overrides['another_service'] = Mock()
        
        # Verify they exist
        self.assertIn('test_service', container._cached_services)
        self.assertIn('another_service', container._service_overrides)
        
        # Reset state
        container.reset_state()
        
        # Verify they're cleared
        self.assertEqual(len(container._cached_services), 0)
        self.assertEqual(len(container._service_overrides), 0)

    def test_sys_path_preservation_and_reset(self):
        """Test that sys.path modifications are properly preserved and reset."""
        container = TestApplicationContainer()
        original_path_len = len(sys.path)
        
        # Preserve original sys.path
        container.preserve_sys_path()
        
        # Modify sys.path
        test_path = "/fake/test/path"
        sys.path.append(test_path)
        
        # Verify modification
        self.assertIn(test_path, sys.path)
        self.assertEqual(len(sys.path), original_path_len + 1)
        
        # Reset state
        container.reset_state()
        
        # Verify sys.path was restored
        self.assertNotIn(test_path, sys.path)
        self.assertEqual(len(sys.path), original_path_len)

    def test_service_override_context_manager(self):
        """Test that service override context manager works correctly."""
        container = TestApplicationContainer()
        mock_service = Mock()
        
        # Test override context
        with container.override_services(content_service=mock_service):
            # Verify override is applied
            self.assertTrue(hasattr(container, 'create_content_service'))
            created_service = container.create_content_service()
            self.assertEqual(created_service, mock_service)
        
        # Verify override is restored after context exit
        # The original method should be restored or removed
        if hasattr(container, 'create_content_service'):
            # If method exists, it should be the original
            created_service = container.create_content_service()
            self.assertNotEqual(created_service, mock_service)

    def test_function_scoped_container_isolation(self):
        """Test that function-scoped containers provide isolation."""
        # Create first container and modify state
        container1 = create_function_scoped_container()
        container1._cached_services['test'] = Mock()
        
        # Create second container
        container2 = create_function_scoped_container()
        
        # Verify isolation - second container shouldn't have first container's state
        self.assertEqual(len(container2._cached_services), 0)
        
        # Cleanup
        container1.reset_state()
        container2.reset_state()

    def test_multiple_containers_do_not_interfere(self):
        """Test that multiple containers don't interfere with each other."""
        container1 = TestApplicationContainer()
        container2 = TestApplicationContainer()
        
        # Add different services to each
        mock_service1 = Mock(name="service1")
        mock_service2 = Mock(name="service2")
        
        container1._cached_services['service1'] = mock_service1
        container2._cached_services['service2'] = mock_service2
        
        # Verify isolation
        self.assertIn('service1', container1._cached_services)
        self.assertNotIn('service2', container1._cached_services)
        
        self.assertIn('service2', container2._cached_services)
        self.assertNotIn('service1', container2._cached_services)
        
        # Reset one container
        container1.reset_state()
        
        # Verify only container1 was affected
        self.assertEqual(len(container1._cached_services), 0)
        self.assertEqual(len(container2._cached_services), 1)
        self.assertIn('service2', container2._cached_services)
        
        # Cleanup
        container2.reset_state()

    @with_isolated_container
    def test_isolated_container_decorator(self, isolated_container):
        """Test the isolated container decorator provides proper isolation."""
        self.assertIsNotNone(isolated_container)
        self.assertTrue(hasattr(isolated_container, 'reset_state'))
        
        # Modify the container
        isolated_container._cached_services['decorator_test'] = Mock()
        
        # The decorator should automatically clean up after this test

    def test_console_output_isolation(self):
        """Test that console output is properly isolated between containers."""
        container1 = TestApplicationContainer(capture_output=True)
        container2 = TestApplicationContainer(capture_output=True)
        
        # Write to each console
        container1.console.print("Container 1 output")
        container2.console.print("Container 2 output")
        
        # Verify isolation
        output1 = container1.get_captured_output()
        output2 = container2.get_captured_output()
        
        self.assertIn("Container 1", output1)
        self.assertNotIn("Container 2", output1)
        
        self.assertIn("Container 2", output2)
        self.assertNotIn("Container 1", output2)
        
        # Clear one container
        container1.clear_output()
        
        # Verify only container1 was affected
        self.assertEqual(container1.get_captured_output(), "")
        self.assertIn("Container 2", container2.get_captured_output())

    def test_state_isolation_across_test_methods(self):
        """Test that state changes in one test don't affect others."""
        # This test intentionally modifies sys.path to verify isolation
        test_path = "/test/isolation/path"
        sys.path.append(test_path)
        
        # The RichTestCase tearDown should clean this up automatically
        # This will be verified by running this test multiple times


class TestStateIsolationIntegration(unittest.TestCase):
    """Integration tests for state isolation without RichTestCase."""

    def test_manual_container_isolation(self):
        """Test manual container creation and cleanup."""
        original_sys_path_len = len(sys.path)
        
        # Create and use container
        container = create_isolated_test_container()
        
        # Modify state
        test_path = "/manual/test/path"
        sys.path.append(test_path)
        container._cached_services['manual_test'] = Mock()
        
        # Manual cleanup
        container.reset_state()
        
        # Verify cleanup
        self.assertEqual(len(sys.path), original_sys_path_len)
        self.assertEqual(len(container._cached_services), 0)

    def test_repeated_container_creation(self):
        """Test that repeatedly creating containers doesn't cause state pollution."""
        original_sys_path_len = len(sys.path)
        
        for i in range(5):
            container = create_function_scoped_container()
            
            # Add unique state
            test_path = f"/repeated/test/path/{i}"
            sys.path.append(test_path)
            container._cached_services[f'repeated_service_{i}'] = Mock()
            
            # Verify current state
            self.assertIn(test_path, sys.path)
            self.assertIn(f'repeated_service_{i}', container._cached_services)
            
            # Clean up
            container.reset_state()
            
            # Verify cleanup
            self.assertNotIn(test_path, sys.path)
            self.assertEqual(len(container._cached_services), 0)
        
        # Verify no accumulated pollution
        self.assertEqual(len(sys.path), original_sys_path_len)


if __name__ == "__main__":
    unittest.main()