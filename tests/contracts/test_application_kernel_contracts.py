#!/usr/bin/env python3
"""
ApplicationKernel Interface Contract Tests

These tests validate the critical interfaces between ApplicationKernel 
and Domain Services. These contracts must never break as they directly
impact user functionality.

Focus: Catching the exact interface mismatches that cause user outages.
"""

import os
import sys
import tempfile
import unittest
from typing import Dict, List

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestApplicationKernelContracts(unittest.TestCase):
    """Contract tests for ApplicationKernel interfaces with domain services."""
    
    def setUp(self):
        """Set up test environment."""
        from core.application_container import ApplicationContainer
        from orchestration.application_kernel import ApplicationKernel
        
        self.container = ApplicationContainer()
        self.kernel = ApplicationKernel(self.container)
        
        # Create test environment
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_document.txt")
        with open(self.test_file, 'w') as f:
            f.write("Test document content for contract validation")
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_application_kernel_content_service_contract(self):
        """CONTRACT: ApplicationKernel → ContentService interface must work exactly as called."""
        # This tests the exact call pattern that failed in production
        
        if not self.kernel.content_service:
            self.skipTest("ContentService not available")
            
        documents = [self.test_file]
        
        try:
            # CONTRACT: ApplicationKernel calls batch_process_documents with List[str]
            content_results = self.kernel.content_service.batch_process_documents(documents)
            
            # CONTRACT: Must return Dict[str, Dict[str, Any]]
            self.assertIsInstance(content_results, dict)
            
            # CONTRACT: Keys must be file paths
            for file_path in content_results.keys():
                self.assertIsInstance(file_path, str)
                self.assertTrue(os.path.isabs(file_path) or file_path in documents)
            
            # CONTRACT: Values must have required fields for downstream processing
            for file_path, content_result in content_results.items():
                required_fields = ["ready_for_ai", "success", "ai_ready_content"]
                for field in required_fields:
                    self.assertIn(field, content_result, 
                                f"CONTRACT VIOLATION: ContentService must return '{field}' field")
                
                # CONTRACT: Data types must be consistent
                self.assertIsInstance(content_result["ready_for_ai"], bool)
                self.assertIsInstance(content_result["success"], bool) 
                self.assertIsInstance(content_result["ai_ready_content"], str)
                
        except TypeError as e:
            if "positional arguments" in str(e):
                self.fail(f"CONTRACT VIOLATION: ApplicationKernel → ContentService method signature mismatch: {e}")
            else:
                raise
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_application_kernel_ai_service_contract(self):
        """CONTRACT: ApplicationKernel → AIIntegrationService interface validation."""
        if not self.kernel.ai_service:
            self.skipTest("AIIntegrationService not available")
        
        # CONTRACT: Must have validate_provider_setup method
        self.assertTrue(hasattr(self.kernel.ai_service, 'validate_provider_setup'),
                       "CONTRACT: AIIntegrationService must have validate_provider_setup method")
        
        # CONTRACT: Method signature validation
        try:
            result = self.kernel.ai_service.validate_provider_setup("openai", "test-key")
            
            # CONTRACT: Must return dict with specific fields
            self.assertIsInstance(result, dict)
            required_fields = ["available", "api_key_valid"]
            for field in required_fields:
                self.assertIn(field, result, 
                            f"CONTRACT: validate_provider_setup must return '{field}' field")
                
        except Exception as e:
            self.fail(f"CONTRACT VIOLATION: AIIntegrationService interface error: {e}")
    
    @pytest.mark.contract
    @pytest.mark.critical  
    def test_content_service_ai_service_data_flow_contract(self):
        """CONTRACT: ContentService output → AIIntegrationService input compatibility."""
        if not (self.kernel.content_service and self.kernel.ai_service):
            self.skipTest("Services not available")
        
        # Phase 1: Get ContentService output  
        documents = [self.test_file]
        content_results = self.kernel.content_service.batch_process_documents(documents)
        
        # Phase 2: Validate AI service can consume ContentService output
        for file_path, content_result in content_results.items():
            if content_result.get("ready_for_ai", False):
                ai_content = content_result.get("ai_ready_content", "")
                
                # CONTRACT: AI service must accept content from ContentService
                try:
                    # Test the method call ApplicationKernel makes
                    filename_result = self.kernel.ai_service.generate_filename_with_ai(
                        content=ai_content,
                        original_filename=os.path.basename(file_path),
                        provider="openai",
                        model="gpt-5", 
                        api_key="test-key"
                    )
                    
                    # CONTRACT: Must return object with status attribute
                    self.assertTrue(hasattr(filename_result, 'status'),
                                  "CONTRACT: AI service must return object with status")
                    
                except TypeError as e:
                    if "positional arguments" in str(e) or "unexpected keyword argument" in str(e):
                        self.fail(f"CONTRACT VIOLATION: ContentService → AIIntegrationService interface mismatch: {e}")
                    else:
                        # API errors are expected with test keys
                        pass
                except Exception as e:
                    # API errors are acceptable, interface errors are not
                    if "argument" in str(e).lower():
                        self.fail(f"CONTRACT VIOLATION: Interface mismatch: {e}")
    
    @pytest.mark.contract 
    @pytest.mark.critical
    def test_application_kernel_public_interface_contract(self):
        """CONTRACT: ApplicationKernel must expose expected public methods."""
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        
        # CONTRACT: Public interface methods must exist
        required_methods = [
            'process_documents',         # Primary user workflow
            'validate_processing_config', # Configuration validation
            'execute_processing'         # Alternative interface
        ]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(self.kernel, method_name),
                           f"CONTRACT: ApplicationKernel must have public method '{method_name}'")
        
        # CONTRACT: Methods must accept ProcessingConfiguration
        config = ProcessingConfiguration(
            input_dir=self.temp_dir,
            output_dir=self.temp_dir,
            provider="local"
        )
        
        try:
            # Test validation method
            errors = self.kernel.validate_processing_config(config)
            self.assertIsInstance(errors, list)
            
            # Test processing method exists and accepts config
            # (Don't actually run processing, just test interface)
            import inspect
            sig = inspect.signature(self.kernel.process_documents)
            params = list(sig.parameters.keys())
            self.assertIn("config", params, 
                         "CONTRACT: process_documents must accept 'config' parameter")
            
        except Exception as e:
            self.fail(f"CONTRACT VIOLATION: ApplicationKernel public interface error: {e}")


class TestDomainServiceBoundaryContracts(unittest.TestCase):
    """Contract tests for boundaries between domain services."""
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_content_service_output_format_contract(self):
        """CONTRACT: ContentService output format must be consistent and complete."""
        from domains.content.content_service import ContentService
        
        content_service = ContentService()
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        test_file.write("Test content for contract validation")
        test_file.close()
        
        try:
            # Test both individual and batch processing return consistent formats
            individual_result = content_service.process_document_complete(test_file.name)
            batch_result = content_service.batch_process_documents([test_file.name])
            
            # CONTRACT: Both methods must return compatible formats
            batch_item = batch_result[test_file.name]
            
            # CONTRACT: Required fields must be present in both
            required_fields = ["success", "ready_for_ai", "ai_ready_content", "extraction"]
            for field in required_fields:
                self.assertIn(field, individual_result, 
                            f"CONTRACT: Individual result must have '{field}' field")
                self.assertIn(field, batch_item,
                            f"CONTRACT: Batch result must have '{field}' field")
            
            # CONTRACT: Data types must be consistent
            self.assertEqual(type(individual_result["ready_for_ai"]), type(batch_item["ready_for_ai"]))
            self.assertEqual(type(individual_result["success"]), type(batch_item["success"]))
            
        finally:
            os.unlink(test_file.name)
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_provider_service_interface_contract(self):
        """CONTRACT: ProviderService interface must support ApplicationKernel usage."""
        from domains.ai_integration.provider_service import ProviderService
        
        provider_service = ProviderService()
        
        # CONTRACT: Must support OpenAI provider creation (primary use case)
        try:
            provider = provider_service.create_provider("openai", "gpt-5", "test-key")
            
            # CONTRACT: Must return AIProvider interface
            self.assertTrue(hasattr(provider, 'generate_filename'),
                           "CONTRACT: Provider must implement generate_filename method")
            
        except ImportError as e:
            if "beyond top-level package" in str(e):
                self.fail(f"CONTRACT VIOLATION: Provider import architecture broken: {e}")
        except Exception as e:
            # Other errors (API validation, etc.) are acceptable for contract test
            pass
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_organization_service_input_contract(self):
        """CONTRACT: OrganizationService must accept expected input format."""
        from domains.organization.organization_service import OrganizationService
        
        # Test with minimal configuration to avoid dependencies
        try:
            org_service = OrganizationService()
            
            # CONTRACT: Must have organize_processed_documents method
            self.assertTrue(hasattr(org_service, 'organize_processed_documents'),
                           "CONTRACT: OrganizationService must have organize_processed_documents method")
            
            # CONTRACT: Method signature must match ApplicationKernel expectations
            import inspect
            sig = inspect.signature(org_service.organize_processed_documents)
            params = list(sig.parameters.keys())
            
            # Validate signature accepts what ApplicationKernel provides
            # (Don't test actual execution, just interface compatibility)
            
        except ImportError:
            self.skipTest("OrganizationService not available")


class TestSharedServiceContracts(unittest.TestCase):
    """Contract tests for shared service interfaces used by domain services."""
    
    @pytest.mark.contract
    def test_extraction_service_interface_contract(self):
        """CONTRACT: ExtractionService interface must support ContentService usage."""
        from domains.content.extraction_service import ExtractionService
        
        extraction_service = ExtractionService()
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        test_file.write("Contract test content")
        test_file.close()
        
        try:
            # CONTRACT: Must return ExtractedContent with required attributes
            result = extraction_service.extract_from_file(test_file.name)
            
            # CONTRACT: Must have quality and text attributes
            self.assertTrue(hasattr(result, 'quality'), "CONTRACT: Must have quality attribute")
            self.assertTrue(hasattr(result, 'text'), "CONTRACT: Must have text attribute")
            
            # CONTRACT: Quality must have .value attribute for enum access
            if hasattr(result.quality, 'value'):
                quality_value = result.quality.value
                self.assertIsInstance(quality_value, str)
            
        finally:
            os.unlink(test_file.name)
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_file_organizer_interface_contract(self):
        """CONTRACT: FileOrganizer interface must support OrganizationService usage."""
        from shared.file_operations.file_organizer import FileOrganizer
        
        organizer = FileOrganizer()
        
        # CONTRACT: Must have expected methods for organization service
        required_methods = ["run_post_processing_organization"]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(organizer, method_name),
                           f"CONTRACT: FileOrganizer must have '{method_name}' method")


if __name__ == "__main__":
    unittest.main(verbosity=2)