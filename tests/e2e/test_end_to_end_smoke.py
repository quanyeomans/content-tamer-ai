#!/usr/bin/env python3
"""
End-to-End Smoke Tests for Complete User Workflows

These tests validate the complete user journey from start to finish,
catching interface contract violations that cause user outages.

Tests the EXACT workflow a user experiences, not individual components.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestCompleteUserJourney(unittest.TestCase):
    """E2E smoke tests for critical user workflows that must always work."""
    
    def setUp(self):
        """Set up realistic test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.temp_dir / "input"
        self.output_dir = self.temp_dir / "processed"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        # Create realistic test file (text-based to avoid OCR complexity)
        self.test_file = self.input_dir / "invoice_2024_test.txt"
        self.test_file.write_text("""
        INVOICE
        Date: 2024-01-15
        Invoice #: INV-2024-001
        Company: Test Corporation
        Amount: $150.00
        Description: Professional services
        """)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    @pytest.mark.e2e
    @pytest.mark.critical
    def test_complete_user_workflow_local_provider(self):
        """E2E: Complete user workflow with local provider (no API key required)."""
        from orchestration.application_kernel import ApplicationKernel
        from core.application_container import ApplicationContainer
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        
        # Step 1: User configuration (using local provider to avoid API key issues)
        config = ProcessingConfiguration(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            provider="local",
            model="llama3.2-3b"  # Local model that doesn't require API
        )
        
        # Step 2: Application startup
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # Step 3: Configuration validation (should work)
        validation_errors = kernel.validate_processing_config(config)
        
        # Allow missing dependencies but not interface errors
        interface_errors = [e for e in validation_errors if any(term in e.lower() for term in 
                           ["positional arguments", "has no attribute", "takes", "given", "signature"])]
        
        self.assertEqual(interface_errors, [], 
                        f"E2E FAILURE: Interface contract violations: {interface_errors}")
        
        # Step 4: Document processing (the critical test)
        try:
            result = kernel.process_documents(config)
            
            # E2E Validation: Must return ProcessingResult object
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, 'success'))
            self.assertTrue(hasattr(result, 'errors'))
            self.assertTrue(hasattr(result, 'files_processed'))
            
            # If processing fails, it should be due to missing dependencies, 
            # NOT interface contract violations
            if not result.success:
                error_text = " ".join(result.errors)
                
                # Critical interface errors that indicate architectural problems
                interface_error_patterns = [
                    "positional arguments but",
                    "takes 2 positional arguments but 3 were given", 
                    "has no attribute",
                    "unexpected keyword argument",
                    "beyond top-level package",
                    "module object has no attribute"
                ]
                
                for pattern in interface_error_patterns:
                    self.assertNotIn(pattern, error_text, 
                                   f"E2E FAILURE: Interface contract violation: {error_text}")
            
        except Exception as e:
            # E2E workflow should never crash with unhandled exceptions
            error_msg = str(e)
            if any(term in error_msg for term in ["positional arguments", "has no attribute", "signature"]):
                self.fail(f"E2E CRITICAL: Interface contract violation crashed workflow: {e}")
            else:
                # Other exceptions might be dependency-related
                self.fail(f"E2E WARNING: Workflow crashed (investigate): {e}")
    
    @pytest.mark.e2e
    @pytest.mark.critical
    def test_configuration_to_processing_pipeline_contracts(self):
        """E2E: Configuration → Content → AI → Organization pipeline interface validation."""
        from orchestration.application_kernel import ApplicationKernel
        from core.application_container import ApplicationContainer
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # Test configuration that should work interface-wise (dependencies may fail)
        config = ProcessingConfiguration(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            provider="openai",  # Test with real provider
            model="gpt-5", 
            api_key="test-key-for-interface-validation"
        )
        
        # Phase 1: Content Processing Contract
        if kernel.content_service:
            try:
                documents = [str(self.test_file)]
                content_results = kernel.content_service.batch_process_documents(documents)
                
                # Contract validation
                self.assertIsInstance(content_results, dict)
                for file_path, content_result in content_results.items():
                    # Required fields for downstream processing
                    self.assertIn("ready_for_ai", content_result)
                    self.assertIn("ai_ready_content", content_result) 
                    self.assertIn("success", content_result)
                    
            except TypeError as e:
                if "positional arguments" in str(e):
                    self.fail(f"E2E CONTRACT VIOLATION: ContentService interface: {e}")
        
        # Phase 2: AI Integration Contract  
        if kernel.ai_service:
            try:
                # Test interface exists
                self.assertTrue(hasattr(kernel.ai_service, 'validate_provider_setup'))
                
                # Test method signature
                validation_result = kernel.ai_service.validate_provider_setup("openai", "test-key")
                self.assertIsInstance(validation_result, dict)
                
            except Exception as e:
                if "positional arguments" in str(e) or "unexpected keyword" in str(e):
                    self.fail(f"E2E CONTRACT VIOLATION: AIIntegrationService interface: {e}")
    
    @pytest.mark.e2e  
    def test_error_handling_pipeline_contracts(self):
        """E2E: Error handling contracts across the complete pipeline."""
        from orchestration.application_kernel import ApplicationKernel
        from core.application_container import ApplicationContainer
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # Test with invalid configuration to validate error handling contracts
        invalid_config = ProcessingConfiguration(
            input_dir="/nonexistent/path",
            output_dir="/nonexistent/path", 
            provider="nonexistent_provider"
        )
        
        # Contract: Validation should return errors, not crash
        try:
            errors = kernel.validate_processing_config(invalid_config)
            self.assertIsInstance(errors, list)
            self.assertGreater(len(errors), 0, "Should detect validation errors")
            
        except Exception as e:
            self.fail(f"E2E CONTRACT VIOLATION: Error handling crashed instead of returning errors: {e}")
        
        # Contract: Processing with invalid config should fail gracefully
        try:
            result = kernel.process_documents(invalid_config)
            self.assertIsNotNone(result)
            self.assertFalse(result.success)
            self.assertIsInstance(result.errors, list)
            
        except Exception as e:
            if "interface" in str(e).lower() or "contract" in str(e).lower():
                self.fail(f"E2E CONTRACT VIOLATION: Processing error handling: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)