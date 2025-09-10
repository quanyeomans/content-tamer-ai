#!/usr/bin/env python3
"""
Domain Service Interface Contract Tests

These tests validate the actual interfaces between domain services that
the application kernel uses. This catches signature mismatches and 
interface breaks that would cause processing failures.

This addresses the critical gap where ContentService.batch_process_documents()
signature mismatch was not caught by contract tests.
"""

import os
import sys
import unittest
from typing import Dict, List
from unittest.mock import Mock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestDomainServiceContracts(unittest.TestCase):
    """Contract tests for domain service interfaces used by application kernel."""
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_content_service_batch_process_documents_contract(self):
        """CONTRACT: ContentService.batch_process_documents must accept List[str] only."""
        from domains.content.content_service import ContentService
        
        content_service = ContentService()
        
        # Contract verification: Method signature must be (self, file_paths: List[str])
        test_files = ["file1.pdf", "file2.pdf"]
        
        try:
            # This is how ApplicationKernel calls it - must work
            result = content_service.batch_process_documents(test_files)
            
            # Contract: Must return Dict[str, Dict[str, Any]]
            self.assertIsInstance(result, dict)
            for file_path, file_result in result.items():
                self.assertIsInstance(file_path, str)
                self.assertIsInstance(file_result, dict)
                
        except TypeError as e:
            if "positional arguments" in str(e):
                self.fail(f"CONTRACT VIOLATION: ContentService.batch_process_documents signature mismatch: {e}")
            else:
                raise
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_ai_integration_service_interface_contract(self):
        """CONTRACT: AIIntegrationService interface must be compatible with ApplicationKernel."""
        try:
            from domains.ai_integration.ai_integration_service import AIIntegrationService
            from core.application_container import ApplicationContainer
            
            container = ApplicationContainer()
            ai_service = container.create_ai_integration_service()
            
            if ai_service:
                # Contract: Must have validate_provider_setup method
                self.assertTrue(hasattr(ai_service, 'validate_provider_setup'), 
                               "CONTRACT: AIIntegrationService must have validate_provider_setup method")
                
                # Contract: Method must accept (provider: str, api_key: str)
                try:
                    result = ai_service.validate_provider_setup("openai", "test-key")
                    self.assertIsInstance(result, dict)
                    self.assertIn("available", result)
                    self.assertIn("api_key_valid", result)
                except Exception as e:
                    self.fail(f"CONTRACT VIOLATION: validate_provider_setup interface mismatch: {e}")
            
        except ImportError:
            # AIIntegrationService may not be available in all environments
            self.skipTest("AIIntegrationService not available")
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_organization_service_interface_contract(self):
        """CONTRACT: OrganizationService interface must be compatible with ApplicationKernel."""
        try:
            from domains.organization.organization_service import OrganizationService
            from core.application_container import ApplicationContainer
            
            container = ApplicationContainer()
            org_service = container.create_organization_service("test_folder")
            
            if org_service:
                # Contract: Must have organize_processed_documents method
                self.assertTrue(hasattr(org_service, 'organize_processed_documents'), 
                               "CONTRACT: OrganizationService must have organize_processed_documents method")
                
                # Contract: Method signature validation
                import inspect
                sig = inspect.signature(org_service.organize_processed_documents)
                params = list(sig.parameters.keys())
                
                # Must accept processed_documents parameter
                self.assertIn("processed_documents", params, 
                             "CONTRACT: organize_processed_documents must accept processed_documents parameter")
            
        except ImportError:
            # OrganizationService may not be available in all environments
            self.skipTest("OrganizationService not available")
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_application_kernel_to_content_service_integration_contract(self):
        """CONTRACT: ApplicationKernel must be able to call ContentService methods correctly."""
        # This test simulates the exact call pattern that failed
        from orchestration.application_kernel import ApplicationKernel
        from core.application_container import ApplicationContainer
        from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # Simulate the exact processing call that failed
        documents = ["test1.pdf", "test2.pdf"]
        
        if kernel.content_service:
            try:
                # This is the exact call that was failing
                content_results = kernel.content_service.batch_process_documents(documents)
                
                # Contract: Must return dict mapping file paths to results
                self.assertIsInstance(content_results, dict)
                
            except TypeError as e:
                if "positional arguments" in str(e):
                    self.fail(f"CONTRACT VIOLATION: ApplicationKernel → ContentService interface mismatch: {e}")
                else:
                    # Other errors are expected (files don't exist, etc)
                    pass
        else:
            self.skipTest("ContentService not available in container")
    
    @pytest.mark.contract
    @pytest.mark.critical  
    def test_domain_service_container_integration_contracts(self):
        """CONTRACT: ApplicationContainer must provide expected domain services."""
        from core.application_container import ApplicationContainer
        
        container = ApplicationContainer()
        
        # Contract: Container must provide expected service creation methods
        expected_methods = [
            'create_content_service',
            'create_ai_integration_service', 
            'create_organization_service'
        ]
        
        for method_name in expected_methods:
            self.assertTrue(hasattr(container, method_name),
                           f"CONTRACT: ApplicationContainer must have {method_name} method")
    
    @pytest.mark.contract
    def test_provider_service_interface_contract(self):
        """CONTRACT: ProviderService interface must support all required operations."""
        from domains.ai_integration.provider_service import ProviderService
        
        provider_service = ProviderService()
        
        # Contract: Must have create_provider method
        self.assertTrue(hasattr(provider_service, 'create_provider'),
                       "CONTRACT: ProviderService must have create_provider method")
        
        # Contract: Must support OpenAI provider (primary use case)
        try:
            provider = provider_service.create_provider("openai", "gpt-5", "test-key")
            self.assertIsNotNone(provider)
        except ImportError as e:
            if "attempted relative import beyond top-level package" in str(e):
                self.fail(f"CONTRACT VIOLATION: Provider import architecture broken: {e}")
            else:
                # Other import errors are environment-related
                pass


if __name__ == "__main__":
    unittest.main(verbosity=2)