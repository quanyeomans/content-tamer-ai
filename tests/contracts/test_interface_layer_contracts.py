#!/usr/bin/env python3
"""
Interface Layer Contract Tests

Tests the contracts between user-facing interfaces (CLI, Library API)
and the ApplicationKernel. These contracts ensure that user interactions
work correctly with the underlying processing system.

Focus: Configuration → Processing → Results workflow contracts
"""

import os
import sys
import tempfile
import unittest

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestConfigurationContracts(unittest.TestCase):
    """Contract tests for configuration interfaces."""
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_configuration_manager_processing_configuration_contract(self):
        """CONTRACT: ConfigurationManager → ProcessingConfiguration compatibility."""
        from interfaces.programmatic.configuration_manager import ConfigurationManager, ProcessingConfiguration
        
        manager = ConfigurationManager()
        
        # CONTRACT: load_configuration must return ProcessingConfiguration
        config = manager.load_configuration()
        self.assertIsInstance(config, ProcessingConfiguration)
        
        # CONTRACT: Required fields must be present
        required_fields = ["input_dir", "output_dir", "provider"]
        for field in required_fields:
            self.assertTrue(hasattr(config, field),
                           f"CONTRACT: ProcessingConfiguration must have '{field}' attribute")
        
        # CONTRACT: save_configuration must accept ProcessingConfiguration
        try:
            # Test with temporary config to avoid affecting real config
            temp_config = ProcessingConfiguration(
                input_dir="test",
                output_dir="test", 
                provider="local"
            )
            # Don't actually save, just test interface
            import inspect
            sig = inspect.signature(manager.save_configuration)
            params = list(sig.parameters.keys())
            self.assertIn("config", params,
                         "CONTRACT: save_configuration must accept 'config' parameter")
            
        except Exception as e:
            self.fail(f"CONTRACT VIOLATION: Configuration interface error: {e}")
    
    @pytest.mark.contract
    @pytest.mark.critical  
    def test_interactive_cli_application_kernel_contract(self):
        """CONTRACT: InteractiveCLI → ApplicationKernel interface compatibility."""
        from interfaces.human.interactive_cli import InteractiveCLI
        from orchestration.application_kernel import ApplicationKernel
        from core.application_container import ApplicationContainer
        
        cli = InteractiveCLI()
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # CONTRACT: CLI must be able to create compatible configuration
        # Test the interface without actually running interactive setup
        self.assertTrue(hasattr(cli, 'run_interactive_setup'),
                       "CONTRACT: InteractiveCLI must have run_interactive_setup method")
        
        # CONTRACT: ApplicationKernel must accept configuration from CLI
        self.assertTrue(hasattr(kernel, 'process_documents'),
                       "CONTRACT: ApplicationKernel must have process_documents method")
        self.assertTrue(hasattr(kernel, 'validate_processing_config'),
                       "CONTRACT: ApplicationKernel must have validate_processing_config method")
    
    @pytest.mark.contract
    def test_library_interface_contracts(self):
        """CONTRACT: Library interface must provide expected API."""
        from interfaces.programmatic.library_interface import ContentTamerAPI
        
        api = ContentTamerAPI()
        
        # CONTRACT: Must provide expected methods for programmatic use
        required_methods = ["process_documents", "validate_provider_api_key"]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(api, method_name),
                           f"CONTRACT: ContentTamerAPI must have '{method_name}' method")


class TestUserWorkflowContracts(unittest.TestCase):
    """Contract tests for complete user workflow interfaces."""
    
    @pytest.mark.contract
    @pytest.mark.critical
    def test_configuration_wizard_application_kernel_contract(self):
        """CONTRACT: Configuration wizard output → ApplicationKernel input compatibility."""
        from interfaces.human.configuration_wizard import ExpertConfigurationWizard
        from interfaces.human.rich_console_manager import RichConsoleManager
        from orchestration.application_kernel import ApplicationKernel  
        from core.application_container import ApplicationContainer
        
        # Test interface compatibility without running full wizard
        console = RichConsoleManager()
        wizard = ExpertConfigurationWizard(console)
        container = ApplicationContainer()
        kernel = ApplicationKernel(container)
        
        # CONTRACT: Wizard must create config compatible with kernel
        self.assertTrue(hasattr(wizard, 'config_manager'),
                       "CONTRACT: Wizard must have config_manager")
        self.assertTrue(hasattr(kernel, 'process_documents'),
                       "CONTRACT: Kernel must accept config for processing")
        
        # CONTRACT: Configuration flow must be end-to-end compatible
        config = wizard.config_manager.load_configuration()
        errors = kernel.validate_processing_config(config)
        
        # Should return validation errors (list), not crash with interface error
        self.assertIsInstance(errors, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)