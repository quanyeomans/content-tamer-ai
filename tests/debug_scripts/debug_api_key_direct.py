#!/usr/bin/env python3
"""Test API key directly with OpenAI to identify the exact issue."""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def test_api_key_direct():
    """Test the API key directly with OpenAI client."""
    try:
        # Test 1: Direct OpenAI client
        print("=== TESTING API KEY DIRECTLY ===")

        api_key = "sk-proj-**********************************************************************************************************QsA"
        print(f"API key length: {len(api_key)}")
        print(f"API key starts with: {api_key[:20]}...")
        print(f"API key ends with: ...{api_key[-20:]}")

        # Test with direct OpenAI import
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        print("OpenAI client created successfully")

        # Test a simple API call
        print("Testing simple completion...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use a basic model
            messages=[
                {"role": "user", "content": "Say 'API key works' if you can read this."}
            ],
            max_tokens=10,
            timeout=30,
        )

        result = response.choices[0].message.content.strip()
        print(f"OpenAI response: {result}")

        if "API key works" in result or "works" in result.lower():
            print("✅ API key is working with OpenAI")
            return True
        else:
            print("❓ API key works but got unexpected response")
            return True

    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ai_provider():
    """Test our AI provider wrapper."""
    try:
        print("\n=== TESTING AI PROVIDER WRAPPER ===")

        api_key = "sk-proj-**********************************************************************************************************QsA"

        from ai_providers import AIProviderFactory

        # Test our provider factory
        client = AIProviderFactory.create(
            "openai", "gpt-4o-mini", api_key
        )  # Use gpt-4o-mini instead of gpt-5-mini
        print("AI provider created successfully")

        # Test filename generation
        test_text = "This is a test PDF document about insurance policies."

        print(f"Testing filename generation with text: {test_text[:50]}...")
        filename = client.generate_filename(test_text, None)
        print(f"Generated filename: {filename}")

        if filename and len(filename) > 0:
            print("✅ AI provider wrapper is working")
            return True
        else:
            print("❌ AI provider returned empty filename")
            return False

    except Exception as e:
        print(f"❌ AI provider test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing API key authentication issues...\n")

    direct_success = test_api_key_direct()
    provider_success = test_ai_provider()

    print(f"\n=== RESULTS ===")
    print(f"Direct OpenAI: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"AI Provider: {'✅ PASS' if provider_success else '❌ FAIL'}")

    if direct_success and provider_success:
        print("\n🎉 API key is working! Issue must be elsewhere.")
    elif direct_success and not provider_success:
        print("\n🔍 API key works directly, but AI provider wrapper has issues.")
    elif not direct_success:
        print("\n❌ API key authentication is failing.")
        print("Check if the key has sufficient credits or correct permissions.")
