"""
End-to-End Multi-Provider Compatibility Tests

Tests for cross-provider compatibility, provider switching, and
comprehensive AI provider ecosystem validation.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from ai_providers import (
    AIProviderFactory, 
    OpenAIProvider, 
    ClaudeProvider, 
    GeminiProvider, 
    LocalLLMProvider
)
from core.file_processor import FileProcessor
from core.directory_manager import DirectoryManager
from utils.display_manager import DisplayManager


class TestE2EMultiProviderCompatibility(unittest.TestCase):
    """End-to-end multi-provider compatibility and switching tests."""
    
    def setUp(self):
        """Set up multi-provider test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, 'input')
        self.processed_dir = os.path.join(self.test_dir, 'processed')
        self.unprocessed_dir = os.path.join(self.test_dir, 'unprocessed')
        
        # Create directory structure
        os.makedirs(self.input_dir)
        os.makedirs(self.processed_dir)
        os.makedirs(self.unprocessed_dir)
        
        # Set up API keys for all providers
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890abcdef1234567890abcdef12345678'
        os.environ['CLAUDE_API_KEY'] = 'sk-ant-test1234567890abcdef1234567890abcdef'
        os.environ['GEMINI_API_KEY'] = 'AIzaSyTest1234567890abcdef1234567890abcdef'
        
        # Create test documents
        self.test_files = []
        for i in range(4):
            filename = f'multi_provider_test_{i+1}.pdf'
            filepath = os.path.join(self.input_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f'Multi-provider test document {i+1}\n' * 15)
            self.test_files.append(filename)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    @patch('ai_providers.ClaudeProvider.generate_filename')
    @patch('ai_providers.GeminiProvider.generate_filename')
    @patch('utils.model_manager.requests.Session')
    def test_all_providers_sequential_workflow(self, mock_session, mock_gemini, mock_claude, mock_openai):
        """
        E2E Test: All providers sequential processing workflow
        
        Tests each AI provider in sequence with same document types
        """
        # Mock provider responses with distinct naming patterns
        mock_openai.return_value = 'OpenAI_Generated_Analysis.pdf'
        mock_claude.return_value = 'Claude_Generated_Summary.pdf'  
        mock_gemini.return_value = 'Gemini_Generated_Report.pdf'
        
        # Mock Local LLM responses
        mock_response_local = MagicMock()
        mock_response_local.json.return_value = {
            "response": "LocalLLM_Generated_Document.pdf"
        }
        mock_response_local.raise_for_status.return_value = None
        
        mock_response_models = MagicMock()
        mock_response_models.json.return_value = {
            "models": [{"name": "gemma-2-2b:latest", "size": 1700000000}]
        }
        mock_response_models.raise_for_status.return_value = None
        
        mock_session.return_value.get.return_value = mock_response_models
        mock_session.return_value.post.return_value = mock_response_local
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        # Test each provider sequentially
        providers_to_test = [
            ('openai', 'gpt-4o-mini'),
            ('claude', 'claude-3-5-sonnet-20241022'),
            ('gemini', 'gemini-1.5-pro'),
            ('local', 'gemma-2-2b')
        ]
        
        results = {}
        
        for provider_name, model_name in providers_to_test:
            # Create fresh test file for each provider
            test_file = f'test_{provider_name}.pdf'
            test_path = os.path.join(self.input_dir, test_file)
            with open(test_path, 'w') as f:
                f.write(f'Test content for {provider_name} provider\n' * 20)
            
            # Process with current provider
            processor = FileProcessor(
                directory_manager=directory_manager,
                display_manager=display_manager,
                provider=provider_name,
                model=model_name
            )
            
            stats = processor.process_files()
            results[provider_name] = stats
            
            # Verify provider processed file successfully  
            self.assertEqual(stats['successful'], 1, 
                           f"{provider_name} should process 1 file successfully")
            self.assertEqual(stats['failed'], 0,
                           f"{provider_name} should have no failures")
        
        # Verify all providers worked
        self.assertEqual(len(results), 4, "Should test all 4 providers")
        
        # Verify different naming patterns were used
        processed_files = os.listdir(self.processed_dir)
        self.assertEqual(len(processed_files), 4, "Should have files from all providers")
        
        # Verify each provider's mock was called
        mock_openai.assert_called()
        mock_claude.assert_called()
        mock_gemini.assert_called()
        mock_session.return_value.post.assert_called()  # Local LLM
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    @patch('ai_providers.ClaudeProvider.generate_filename')
    def test_provider_switching_same_session(self, mock_claude, mock_openai):
        """
        E2E Test: Provider switching within same session
        
        Tests dynamically switching providers for different file types
        """
        mock_openai.return_value = 'OpenAI_Technical_Analysis.pdf'
        mock_claude.return_value = 'Claude_Creative_Summary.pdf'
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        # Create different types of test files
        technical_file = os.path.join(self.input_dir, 'technical_document.pdf')
        creative_file = os.path.join(self.input_dir, 'creative_document.pdf')
        
        with open(technical_file, 'w') as f:
            f.write('Technical analysis document with data and charts\n' * 20)
        
        with open(creative_file, 'w') as f:
            f.write('Creative writing document with narrative content\n' * 20)
        
        # Process technical file with OpenAI (good for technical content)
        processor_openai = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',
            model='gpt-4o-mini'
        )
        
        # Remove creative file temporarily  
        shutil.move(creative_file, creative_file + '.temp')
        
        stats_openai = processor_openai.process_files()
        
        # Restore creative file
        shutil.move(creative_file + '.temp', creative_file)
        
        # Process creative file with Claude (good for creative content)
        processor_claude = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='claude',
            model='claude-3-5-sonnet-20241022'
        )
        
        stats_claude = processor_claude.process_files()
        
        # Verify both processing sessions worked
        self.assertEqual(stats_openai['successful'], 1, "OpenAI should process technical file")
        self.assertEqual(stats_claude['successful'], 1, "Claude should process creative file")
        
        # Verify different providers were used appropriately
        mock_openai.assert_called()
        mock_claude.assert_called()
        
        # Verify processed files reflect provider specialization
        processed_files = os.listdir(self.processed_dir)
        self.assertEqual(len(processed_files), 2, "Should have files from both providers")
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    @patch('ai_providers.ClaudeProvider.generate_filename')
    @patch('ai_providers.GeminiProvider.generate_filename')
    def test_provider_fallback_workflow(self, mock_gemini, mock_claude, mock_openai):
        """
        E2E Test: Provider fallback workflow
        
        Tests automatic fallback when primary provider fails
        """
        # Configure primary provider to fail, secondary to succeed
        mock_openai.side_effect = [
            Exception("OpenAI API rate limit exceeded"),
            Exception("OpenAI service temporarily unavailable")
        ]
        
        mock_claude.return_value = 'Claude_Fallback_Analysis.pdf'
        mock_gemini.return_value = 'Gemini_Fallback_Summary.pdf'
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        # Create test files
        test_files = ['fallback_test_1.pdf', 'fallback_test_2.pdf']
        for filename in test_files:
            filepath = os.path.join(self.input_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f'Fallback test content for {filename}\n' * 20)
        
        # Attempt processing with OpenAI (will fail)
        processor_openai = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='openai',
            model='gpt-4o-mini',
            max_retries=2  # Allow retries but still fail
        )
        
        stats_openai = processor_openai.process_files()
        
        # OpenAI should fail all files
        self.assertEqual(stats_openai['successful'], 0, "OpenAI should fail all files")
        self.assertEqual(stats_openai['failed'], 2, "Should have 2 failed files")
        
        # Files should be moved to unprocessed for fallback
        unprocessed_files = os.listdir(self.unprocessed_dir)
        self.assertEqual(len(unprocessed_files), 2, "Failed files should be in unprocessed")
        
        # Move files back to input for fallback processing
        for filename in unprocessed_files:
            src = os.path.join(self.unprocessed_dir, filename)
            dst = os.path.join(self.input_dir, filename)
            shutil.move(src, dst)
        
        # Process with Claude as fallback
        processor_claude = FileProcessor(
            directory_manager=directory_manager,
            display_manager=display_manager,
            provider='claude',
            model='claude-3-5-sonnet-20241022'
        )
        
        stats_claude = processor_claude.process_files()
        
        # Claude should succeed as fallback
        self.assertEqual(stats_claude['successful'], 2, "Claude fallback should succeed")
        self.assertEqual(stats_claude['failed'], 0, "Claude fallback should have no failures")
        
        # Verify fallback processing completed
        processed_files = os.listdir(self.processed_dir)
        self.assertEqual(len(processed_files), 2, "Should have fallback processed files")
    
    def test_ai_provider_factory_all_providers(self):
        """
        E2E Test: AI Provider Factory with all providers
        
        Tests provider factory correctly creates all provider types
        """
        # Test OpenAI provider creation
        openai_provider = AIProviderFactory.create('openai', 'gpt-4o-mini')
        self.assertIsInstance(openai_provider, OpenAIProvider)
        self.assertEqual(openai_provider.model, 'gpt-4o-mini')
        
        # Test Claude provider creation
        claude_provider = AIProviderFactory.create('claude', 'claude-3-5-sonnet-20241022')
        self.assertIsInstance(claude_provider, ClaudeProvider)
        self.assertEqual(claude_provider.model, 'claude-3-5-sonnet-20241022')
        
        # Test Gemini provider creation
        gemini_provider = AIProviderFactory.create('gemini', 'gemini-1.5-pro')
        self.assertIsInstance(gemini_provider, GeminiProvider)
        self.assertEqual(gemini_provider.model, 'gemini-1.5-pro')
        
        # Test Local LLM provider creation
        local_provider = AIProviderFactory.create('local', 'gemma-2-2b')
        self.assertIsInstance(local_provider, LocalLLMProvider)
        self.assertEqual(local_provider.model_name, 'gemma-2-2b')
        
        # Test invalid provider
        with self.assertRaises(ValueError):
            AIProviderFactory.create('invalid_provider', 'model')
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    @patch('ai_providers.ClaudeProvider.generate_filename')
    def test_provider_model_compatibility(self, mock_claude, mock_openai):
        """
        E2E Test: Provider model compatibility
        
        Tests different models within same provider family
        """
        # Test different OpenAI models
        openai_models = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo']
        mock_openai.return_value = 'OpenAI_Model_Test.pdf'
        
        # Test different Claude models  
        claude_models = ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307']
        mock_claude.return_value = 'Claude_Model_Test.pdf'
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        # Test OpenAI models
        for model in openai_models:
            # Create test file for this model
            test_file = f'openai_{model.replace("-", "_")}_test.pdf'
            test_path = os.path.join(self.input_dir, test_file)
            with open(test_path, 'w') as f:
                f.write(f'Test content for OpenAI model {model}\n' * 15)
            
            # Process with specific model
            processor = FileProcessor(
                directory_manager=directory_manager,
                display_manager=display_manager,
                provider='openai',
                model=model
            )
            
            stats = processor.process_files()
            
            # Should process successfully with any supported model
            self.assertEqual(stats['successful'], 1, 
                           f"OpenAI model {model} should process successfully")
        
        # Test Claude models
        for model in claude_models:
            # Create test file for this model
            test_file = f'claude_{model.replace("-", "_")}_test.pdf'
            test_path = os.path.join(self.input_dir, test_file)
            with open(test_path, 'w') as f:
                f.write(f'Test content for Claude model {model}\n' * 15)
            
            # Process with specific model
            processor = FileProcessor(
                directory_manager=directory_manager,
                display_manager=display_manager,
                provider='claude',
                model=model
            )
            
            stats = processor.process_files()
            
            # Should process successfully with any supported model
            self.assertEqual(stats['successful'], 1,
                           f"Claude model {model} should process successfully")
        
        # Verify all models were tested
        processed_files = os.listdir(self.processed_dir)
        expected_files = len(openai_models) + len(claude_models)
        self.assertEqual(len(processed_files), expected_files, 
                        f"Should have {expected_files} processed files")
    
    @patch('ai_providers.OpenAIProvider.generate_filename')
    @patch('ai_providers.ClaudeProvider.generate_filename')  
    @patch('ai_providers.GeminiProvider.generate_filename')
    @patch('utils.model_manager.requests.Session')
    def test_provider_performance_comparison(self, mock_session, mock_gemini, mock_claude, mock_openai):
        """
        E2E Test: Provider performance comparison
        
        Tests relative performance characteristics of different providers
        """
        import time
        
        # Mock responses with different "processing times" 
        def slow_openai_response(*args, **kwargs):
            time.sleep(0.1)  # Simulate processing time
            return 'OpenAI_Slow_Processing.pdf'
        
        def fast_claude_response(*args, **kwargs):
            time.sleep(0.05)  # Faster processing
            return 'Claude_Fast_Processing.pdf'
        
        def medium_gemini_response(*args, **kwargs):
            time.sleep(0.075)  # Medium processing time
            return 'Gemini_Medium_Processing.pdf'
        
        mock_openai.side_effect = slow_openai_response
        mock_claude.side_effect = fast_claude_response
        mock_gemini.side_effect = medium_gemini_response
        
        # Mock Local LLM (should be slowest due to local processing)
        def slow_local_response(*args, **kwargs):
            time.sleep(0.15)
            response = MagicMock()
            response.json.return_value = {"response": "Local_Slow_Processing.pdf"}
            response.raise_for_status.return_value = None
            return response
        
        mock_response_models = MagicMock()
        mock_response_models.json.return_value = {
            "models": [{"name": "gemma-2-2b:latest", "size": 1700000000}]
        }
        mock_response_models.raise_for_status.return_value = None
        
        mock_session.return_value.get.return_value = mock_response_models
        mock_session.return_value.post.side_effect = slow_local_response
        
        directory_manager = DirectoryManager(
            input_folder=self.input_dir,
            processed_folder=self.processed_dir,
            unprocessed_folder=self.unprocessed_dir
        )
        
        display_manager = DisplayManager(quiet=True)
        
        # Test performance of each provider
        providers = [
            ('claude', 'claude-3-5-sonnet-20241022'),    # Should be fastest
            ('gemini', 'gemini-1.5-pro'),                # Should be medium
            ('openai', 'gpt-4o-mini'),                   # Should be slower
            ('local', 'gemma-2-2b')                      # Should be slowest
        ]
        
        performance_results = {}
        
        for provider_name, model_name in providers:
            # Create test file
            test_file = f'perf_test_{provider_name}.pdf'
            test_path = os.path.join(self.input_dir, test_file)
            with open(test_path, 'w') as f:
                f.write(f'Performance test content for {provider_name}\n' * 20)
            
            # Measure processing time
            start_time = time.time()
            
            processor = FileProcessor(
                directory_manager=directory_manager,
                display_manager=display_manager,
                provider=provider_name,
                model=model_name
            )
            
            stats = processor.process_files()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            performance_results[provider_name] = {
                'time': processing_time,
                'success': stats['successful'] == 1
            }
            
            # Verify successful processing
            self.assertTrue(performance_results[provider_name]['success'],
                          f"{provider_name} should process successfully")
        
        # Verify performance characteristics (rough order)
        claude_time = performance_results['claude']['time']
        gemini_time = performance_results['gemini']['time']
        openai_time = performance_results['openai']['time']
        local_time = performance_results['local']['time']
        
        # Claude should be fastest, Local should be slowest
        self.assertLess(claude_time, local_time, "Claude should be faster than Local LLM")
        self.assertLess(gemini_time, local_time, "Gemini should be faster than Local LLM")
        
        # All providers should complete in reasonable time
        for provider_name, result in performance_results.items():
            self.assertLess(result['time'], 1.0, 
                          f"{provider_name} should complete within 1 second")
    
    def test_provider_configuration_validation(self):
        """
        E2E Test: Provider configuration validation
        
        Tests provider configuration validation and error handling
        """
        # Test with missing API keys
        original_openai_key = os.environ.get('OPENAI_API_KEY')
        original_claude_key = os.environ.get('CLAUDE_API_KEY')
        
        try:
            # Remove API keys
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            if 'CLAUDE_API_KEY' in os.environ:
                del os.environ['CLAUDE_API_KEY']
            
            # Test OpenAI without API key
            with self.assertRaises(ValueError):
                AIProviderFactory.create('openai', 'gpt-4o-mini')
            
            # Test Claude without API key
            with self.assertRaises(ValueError):
                AIProviderFactory.create('claude', 'claude-3-5-sonnet-20241022')
            
            # Test Local LLM (should work without API key)
            local_provider = AIProviderFactory.create('local', 'gemma-2-2b')
            self.assertIsInstance(local_provider, LocalLLMProvider)
            
            # Test with invalid models
            os.environ['OPENAI_API_KEY'] = 'sk-test123'
            
            # Should accept valid models
            valid_provider = AIProviderFactory.create('openai', 'gpt-4o-mini')
            self.assertIsInstance(valid_provider, OpenAIProvider)
            
        finally:
            # Restore original API keys
            if original_openai_key:
                os.environ['OPENAI_API_KEY'] = original_openai_key
            if original_claude_key:
                os.environ['CLAUDE_API_KEY'] = original_claude_key


class TestE2EProviderEcosystem(unittest.TestCase):
    """Tests for the complete AI provider ecosystem integration."""
    
    def setUp(self):
        """Set up provider ecosystem test environment."""
        # Set up all API keys
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890abcdef1234567890abcdef12345678'
        os.environ['CLAUDE_API_KEY'] = 'sk-ant-test1234567890abcdef1234567890abcdef'
        os.environ['GEMINI_API_KEY'] = 'AIzaSyTest1234567890abcdef1234567890abcdef'
    
    def test_complete_provider_ecosystem(self):
        """
        E2E Test: Complete provider ecosystem validation
        
        Tests that all providers integrate correctly with the system
        """
        from ai_providers import AI_PROVIDERS
        
        # Verify all expected providers are available
        expected_providers = ['openai', 'claude', 'gemini', 'local']
        
        for provider_name in expected_providers:
            self.assertIn(provider_name, AI_PROVIDERS, 
                         f"Provider {provider_name} should be in AI_PROVIDERS")
            
            # Verify provider has models
            provider_models = AI_PROVIDERS[provider_name]
            self.assertIsInstance(provider_models, list, 
                                f"{provider_name} should have list of models")
            self.assertGreater(len(provider_models), 0, 
                             f"{provider_name} should have at least one model")
            
            # Test creating provider with first available model
            first_model = provider_models[0]
            
            if provider_name != 'local':  # Local doesn't need API key validation
                provider = AIProviderFactory.create(provider_name, first_model)
                self.assertIsNotNone(provider, 
                                   f"Should create {provider_name} provider")
    
    def test_provider_model_combinations(self):
        """
        E2E Test: All provider/model combinations
        
        Tests that all documented provider/model combinations work
        """
        from ai_providers import AI_PROVIDERS
        
        successful_combinations = []
        failed_combinations = []
        
        for provider_name, models in AI_PROVIDERS.items():
            for model in models:
                try:
                    if provider_name == 'local':
                        # Local LLM provider doesn't require API key
                        provider = AIProviderFactory.create(provider_name, model)
                        self.assertIsInstance(provider, LocalLLMProvider)
                        successful_combinations.append((provider_name, model))
                    else:
                        # Cloud providers require API keys
                        provider = AIProviderFactory.create(provider_name, model)
                        self.assertIsNotNone(provider)
                        successful_combinations.append((provider_name, model))
                        
                except Exception as e:
                    failed_combinations.append((provider_name, model, str(e)))
        
        # Report results
        self.assertGreater(len(successful_combinations), 0, 
                          "Should have successful provider/model combinations")
        
        # All combinations should work with proper API keys
        if failed_combinations:
            failure_details = '\n'.join([
                f"  {provider}/{model}: {error}" 
                for provider, model, error in failed_combinations
            ])
            self.fail(f"Failed provider/model combinations:\n{failure_details}")


if __name__ == '__main__':
    unittest.main(verbosity=2)