#!/usr/bin/env python3
"""Test the fixed OpenAI provider."""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def test_fixed_provider():
    """Test the fixed OpenAI provider with both gpt-4o-mini and gpt-5-mini."""
    try:
        from ai_providers import AIProviderFactory

        api_key = "sk-proj-**********************************************************************************************************QsA"
        test_content = "NRMA home insurance policy certificate document"

        print("=== TESTING FIXED OPENAI PROVIDER ===")

        # Test with gpt-4o-mini (should work)
        print("\nTesting gpt-4o-mini:")
        try:
            client = AIProviderFactory.create("openai", "gpt-4o-mini", api_key)
            filename = client.generate_filename(test_content)
            print(f"  Generated: {filename}")
            print("  gpt-4o-mini works!")
        except Exception as e:
            print(f"  gpt-4o-mini failed: {e}")

        # Test with gpt-5-mini (the one causing issues)
        print("\nTesting gpt-5-mini:")
        try:
            client = AIProviderFactory.create("openai", "gpt-5-mini", api_key)
            filename = client.generate_filename(test_content)
            print(f"  Generated: {filename}")
            print("  gpt-5-mini works!")
        except Exception as e:
            print(f"  gpt-5-mini failed: {e}")

        return True

    except Exception as e:
        print(f"Test setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_fixed_provider()
