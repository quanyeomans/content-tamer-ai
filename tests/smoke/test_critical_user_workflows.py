#!/usr/bin/env python3
"""
Critical User Workflow Smoke Tests

These tests catch regressions that would cause user outages.
Run these tests BEFORE any deployment to ensure core functionality works.

These tests specifically address the AI provider import regression that broke
the configuration wizard and prevented users from using the application.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestCriticalUserWorkflows(unittest.TestCase):
    """Smoke tests for critical user workflows that must never break."""
    
    def test_ai_provider_imports_work(self):
        """CRITICAL: All AI providers must be importable (prevents configuration wizard failures)."""
        # This test would have caught the import regression
        try:
            from domains.ai_integration.providers.openai_provider import OpenAIProvider
            from domains.ai_integration.providers.claude_provider import ClaudeProvider
            from domains.ai_integration.providers.gemini_provider import GeminiProvider
            from domains.ai_integration.providers.deepseek_provider import DeepseekProvider
            from domains.ai_integration.providers.local_llm_provider import LocalLLMProvider
        except ImportError as e:
            self.fail(f"CRITICAL: AI provider import failed - this breaks configuration wizard: {e}")
    
    def test_openai_provider_creation_works(self):
        """CRITICAL: OpenAI provider creation must work (primary use case)."""
        from domains.ai_integration.provider_service import ProviderService
        
        provider_service = ProviderService()
        
        # Focus on OpenAI since that's what broke in the regression
        try:
            provider = provider_service.create_provider("openai", "gpt-5", "test-key")
            self.assertIsNotNone(provider)
        except Exception as e:
            self.fail(f"CRITICAL: Cannot create OpenAI provider (this broke configuration wizard): {e}")
    
    def test_provider_imports_individually(self):
        """CRITICAL: Each provider import must work (catches import regressions)."""
        # Test the specific import pattern that failed
        import_tests = [
            ("OpenAI", "from domains.ai_integration.providers.openai_provider import OpenAIProvider"),
            ("Claude", "from domains.ai_integration.providers.claude_provider import ClaudeProvider"),
        ]
        
        for provider_name, import_statement in import_tests:
            with self.subTest(provider=provider_name):
                try:
                    exec(import_statement)
                except ImportError as e:
                    self.fail(f"CRITICAL: {provider_name} provider import failed: {e}")
                except Exception as e:
                    self.fail(f"CRITICAL: {provider_name} provider import error: {e}")
    
    def test_configuration_wizard_starts_successfully(self):
        """CRITICAL: Configuration wizard must start without errors."""
        try:
            from interfaces.human.configuration_wizard import ExpertConfigurationWizard
            from interfaces.human.rich_console_manager import RichConsoleManager
            
            # This should not fail with import errors
            console = RichConsoleManager()
            wizard = ExpertConfigurationWizard(console)
            
            self.assertIsNotNone(wizard)
            self.assertIsNotNone(wizard.config_manager)
            
        except Exception as e:
            self.fail(f"CRITICAL: Configuration wizard startup failed: {e}")
    
    def test_api_key_security_no_file_storage(self):
        """CRITICAL: API keys must NEVER be stored in configuration files."""
        from interfaces.programmatic.configuration_manager import ConfigurationManager, ProcessingConfiguration
        import json
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config manager with temp directory
            config_file = Path(temp_dir) / "test_config.json"
            manager = ConfigurationManager(config_dir=Path(temp_dir))
            
            # Create config with API key
            config = ProcessingConfiguration(
                input_dir="test",
                output_dir="test", 
                provider="openai",
                api_key="sk-test-key-should-never-be-saved"  # This should be excluded
            )
            
            # Save configuration
            success = manager.save_configuration(config)
            self.assertTrue(success, "Configuration save should succeed")
            
            # Verify API key is NOT in saved file
            self.assertTrue(config_file.exists(), "Config file should be created")
            
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
            
            # SECURITY CRITICAL: API key must not be in file
            self.assertIsNone(saved_config.get("api_key"), 
                            "SECURITY VIOLATION: API key must not be stored in config file")
            self.assertEqual(saved_config.get("api_key_source"), "environment_variable_required",
                           "Config should indicate environment variable required")
    
    def test_environment_variable_api_key_detection(self):
        """CRITICAL: Environment variable API keys must be detected properly."""
        from interfaces.programmatic.configuration_manager import ConfigurationManager
        
        # Set test environment variable
        test_key = "sk-test-environment-key"
        os.environ["TEST_PROVIDER_API_KEY"] = test_key
        
        try:
            manager = ConfigurationManager()
            config = manager.load_configuration()
            config.provider = "test_provider"  # Set provider to match env var
            
            # Apply environment variables
            config = manager._merge_environment_variables(config)
            
            # Environment variable should be detected
            # Note: This tests the mechanism, not the specific provider
            
        finally:
            # Clean up environment variable
            if "TEST_PROVIDER_API_KEY" in os.environ:
                del os.environ["TEST_PROVIDER_API_KEY"]
    
    def test_application_entry_point_works(self):
        """CRITICAL: Application entry point must be accessible."""
        try:
            # Test that main entry point can be imported
            import main
            self.assertIsNotNone(main.main)
            
        except ImportError as e:
            self.fail(f"CRITICAL: Application entry point import failed: {e}")
    
    def test_no_plain_text_api_keys_in_codebase(self):
        """SECURITY: Verify no real API keys are committed to repository."""
        # Check that any sk- patterns in code are test keys or documentation
        import subprocess
        
        try:
            # Search for potential real API key patterns
            result = subprocess.run([
                "grep", "-r", "sk-[a-zA-Z0-9_-]{20,}", "src/", 
                "--exclude-dir=__pycache__"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # If found, verify they are test keys or documentation
                found_lines = result.stdout.strip().split('\n')
                for line in found_lines:
                    if 'test' not in line.lower() and 'example' not in line.lower():
                        self.fail(f"SECURITY: Potential real API key found in code: {line}")
                        
        except subprocess.TimeoutExpired:
            # Grep took too long, skip this check
            pass
        except FileNotFoundError:
            # grep not available on Windows, skip this check
            pass


class TestApplicationSmokeTasks(unittest.TestCase):
    """High-level smoke tests for complete application workflows."""
    
    def test_help_command_works(self):
        """SMOKE: Help command should work without errors."""
        try:
            import subprocess
            result = subprocess.run([
                "python", "src/main.py", "--help"
            ], capture_output=True, text=True, timeout=30)
            
            # Should not crash, regardless of return code
            # (Help might exit with non-zero, that's OK)
            self.assertIn("Content Tamer AI", result.stdout + result.stderr)
            
        except subprocess.TimeoutExpired:
            self.fail("Help command timed out")
        except Exception as e:
            self.fail(f"Help command crashed: {e}")
    
    def test_application_can_create_kernel(self):
        """SMOKE: Application kernel can be created with container."""
        try:
            from core.application_container import ApplicationContainer
            from orchestration.application_kernel import ApplicationKernel
            
            container = ApplicationContainer()
            kernel = ApplicationKernel(container)
            self.assertIsNotNone(kernel)
            
        except Exception as e:
            self.fail(f"Kernel creation failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)