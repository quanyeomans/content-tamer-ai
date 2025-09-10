#!/usr/bin/env python3
"""
OpenAI GPT-5 API Compatibility Tests

Tests that OpenAI provider uses correct API parameters for GPT-5 models.
Prevents regression of max_tokens vs max_completion_tokens parameter issues.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))


class TestOpenAIGPT5Compatibility(unittest.TestCase):
    """Test OpenAI provider compatibility with GPT-5 API requirements."""
    
    def test_gpt5_uses_max_completion_tokens_not_max_tokens(self):
        """REGRESSION TEST: GPT-5 must use max_completion_tokens parameter, not max_tokens."""
        from domains.ai_integration.providers.openai_provider import OpenAIProvider
        
        # This test should PASS - GPT-5 should use correct parameters
        provider = OpenAIProvider("test-key", "gpt-5")
        
        with patch('domains.ai_integration.providers.openai_provider.OpenAI') as MockOpenAI:
            mock_client = Mock()
            MockOpenAI.return_value = mock_client
            
            # Mock successful response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "test_filename"
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test filename generation
            try:
                result = provider.generate_filename("Test content", "test.pdf")
                
                # Verify the API was called with correct parameters
                call_args = mock_client.chat.completions.create.call_args
                call_kwargs = call_args.kwargs if call_args else {}
                
                # CRITICAL: Must use max_completion_tokens, NOT max_tokens for GPT-5
                self.assertNotIn("max_tokens", call_kwargs, 
                                "REGRESSION: OpenAI provider must not use 'max_tokens' with GPT-5")
                self.assertIn("max_completion_tokens", call_kwargs,
                             "REGRESSION: OpenAI provider must use 'max_completion_tokens' with GPT-5")
                
            except Exception as e:
                self.fail(f"OpenAI GPT-5 API call failed: {e}")
    
    def test_legacy_models_can_still_use_max_tokens(self):
        """Test that legacy models (gpt-4, gpt-3.5-turbo) can still use max_tokens if needed."""
        from domains.ai_integration.providers.openai_provider import OpenAIProvider
        
        # Legacy models might still support max_tokens
        provider = OpenAIProvider("test-key", "gpt-4")
        
        with patch('domains.ai_integration.providers.openai_provider.OpenAI') as MockOpenAI:
            mock_client = Mock()
            MockOpenAI.return_value = mock_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "test_filename"
            mock_client.chat.completions.create.return_value = mock_response
            
            try:
                result = provider.generate_filename("Test content", "test.pdf")
                
                # For legacy models, either parameter should be acceptable
                call_args = mock_client.chat.completions.create.call_args
                call_kwargs = call_args.kwargs if call_args else {}
                
                # Should have some token limit parameter
                has_token_limit = "max_tokens" in call_kwargs or "max_completion_tokens" in call_kwargs
                self.assertTrue(has_token_limit, "Must specify some token limit parameter")
                
            except Exception as e:
                self.fail(f"Legacy model API call failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)