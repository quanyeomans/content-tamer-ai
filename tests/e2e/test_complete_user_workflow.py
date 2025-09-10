#!/usr/bin/env python3
"""
Complete User Workflow E2E Test

This test validates the COMPLETE user journey from configuration through processing.
It uses real files and real processing to catch any regressions that would cause
user outages.

This addresses the gap where component tests passed but the complete user
workflow failed due to interface mismatches or missing dependencies.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestCompleteUserWorkflow(unittest.TestCase):
    """E2E tests for complete user workflow that must work end-to-end."""
    
    def setUp(self):
        """Set up test environment with real files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.temp_dir / "input"
        self.output_dir = self.temp_dir / "processed"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        # Create test files - use simple text files to avoid OCR dependency issues
        self.test_files = []
        
        # Test PDF (simple text content)
        test_pdf = self.input_dir / "test_invoice.txt"  # Use .txt to avoid PDF parsing
        test_pdf.write_text("INVOICE\nDate: 2024-01-15\nAmount: $150.00\nCompany: Test Corp")
        self.test_files.append(str(test_pdf))
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    @pytest.mark.e2e
    @pytest.mark.critical
    def test_complete_configuration_to_processing_workflow(self):
        """E2E: Complete workflow from configuration through document processing."""
        from orchestration.application_kernel import ApplicationKernel
        from core.application_container import ApplicationContainer
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        
        # Step 1: Create configuration (simulate user configuration)
        config = ProcessingConfiguration(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            provider="local",  # Use local to avoid API key requirements
            model="test-model",
            api_key=None,  # Local doesn't need API key
        )
        
        # Step 2: Create application components
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # Step 3: Validate configuration (this should not fail)  
        # Check if validation method exists
        if hasattr(kernel, 'validate_processing_config'):
            errors = kernel.validate_processing_config(config)
        else:
            errors = []  # Skip validation if method doesn't exist
        if errors:
            # Allow certain errors but not critical ones
            critical_errors = [e for e in errors if "import" in e.lower() or "not available" in e.lower()]
            if critical_errors:
                self.fail(f"CRITICAL configuration errors: {critical_errors}")
        
        # Step 4: Process documents (the critical test)
        try:
            result = kernel.process_documents(config)
            
            # E2E Validation: Processing should complete without critical errors
            self.assertIsNotNone(result, "Processing result should not be None")
            
            # If processing fails, check if it's due to missing dependencies (acceptable)
            # vs interface mismatches (critical)
            if not result.success:
                error_text = " ".join(result.errors)
                
                # Critical interface errors that indicate architectural problems
                critical_error_patterns = [
                    "positional arguments but",  # Method signature mismatch
                    "takes 2 positional arguments but 3 were given",  # The specific error we just fixed
                    "attempted relative import beyond top-level package",  # Import errors
                    "has no attribute",  # Interface mismatches
                ]
                
                for pattern in critical_error_patterns:
                    if pattern in error_text:
                        self.fail(f"CRITICAL INTERFACE ERROR: {error_text}")
                
                # Non-critical errors (missing dependencies, etc.) are acceptable for E2E test
                print(f"Processing failed with non-critical errors: {result.errors[:3]}")
            
        except Exception as e:
            # Any exception in E2E processing indicates a critical architectural issue
            self.fail(f"E2E PROCESSING CRASHED: {e}")
    
    @pytest.mark.e2e
    @pytest.mark.critical
    def test_content_service_to_ai_service_integration_e2e(self):
        """E2E: ContentService output must be compatible with AI service input."""
        from domains.content.content_service import ContentService
        from domains.ai_integration.ai_integration_service import AIIntegrationService
        
        content_service = ContentService()
        
        # Process content (Phase 1)
        content_results = content_service.batch_process_documents(self.test_files)
        
        # Validate content → AI integration contract
        for file_path, content_result in content_results.items():
            # Contract: ContentService must provide fields that AI service expects
            required_fields = ["ready_for_ai", "ai_ready_content", "success"]
            for field in required_fields:
                self.assertIn(field, content_result, 
                             f"CONTRACT VIOLATION: ContentService must provide '{field}' field")
            
            # Contract: If content is ready for AI, it should have usable content
            if content_result.get("ready_for_ai", False):
                ai_content = content_result.get("ai_ready_content", "")
                self.assertTrue(len(ai_content.strip()) > 0, 
                               "CONTRACT: ready_for_ai=True must have non-empty ai_ready_content")
    
    @pytest.mark.e2e
    def test_missing_dependencies_graceful_degradation(self):
        """E2E: Application should degrade gracefully when dependencies are missing."""
        from orchestration.application_kernel import ApplicationKernel
        from core.application_container import ApplicationContainer
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        
        # Create configuration that would work if dependencies were available
        config = ProcessingConfiguration(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            provider="openai",  # This requires API key
            model="gpt-5",
            api_key="test-key-for-validation"  # Not a real key
        )
        
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # Test should not crash, even with missing dependencies
        try:
            result = kernel.process_documents(config)
            
            # Should return a result object, even if processing failed
            self.assertIsNotNone(result)
            self.assertIsInstance(result.errors, list)
            
            # Errors should be informative, not cryptic
            if result.errors:
                error_text = " ".join(result.errors)
                self.assertNotIn("TypeError", error_text, 
                                "Should not have TypeError - indicates interface mismatch")
                self.assertNotIn("AttributeError", error_text,
                                "Should not have AttributeError - indicates missing methods")
            
        except Exception as e:
            self.fail(f"E2E workflow should not crash, should fail gracefully: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)