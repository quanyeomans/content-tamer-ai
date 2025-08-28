#!/usr/bin/env python3
"""Test the correct OpenAI API format that should work."""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def test_correct_openai_format():
    """Test with the standard chat completions API."""
    try:
        from openai import OpenAI
        from ai_providers import get_system_prompt

        api_key = "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxN6QsA"

        client = OpenAI(api_key=api_key)

        # Test content (like what the app would process)
        test_content = (
            "This is a test PDF document about NRMA home insurance policy certificate."
        )

        print("=== TESTING CORRECT CHAT COMPLETIONS API ===")
        print(f"Content: {test_content}")

        # Use the same system prompt as the app
        system_prompt = get_system_prompt("openai")
        print(f"System prompt: {system_prompt[:100]}...")

        # Test with standard chat completions (what works)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Known working model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": test_content},
            ],
            max_tokens=50,
            timeout=30,
        )

        filename = response.choices[0].message.content.strip()
        print(f"Generated filename: {filename}")

        print("Standard chat completions API works!")

        # Now test if gpt-5-mini exists
        print("\n=== TESTING gpt-5-mini MODEL ===")
        try:
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": test_content},
                ],
                max_tokens=50,
                timeout=30,
            )
            filename = response.choices[0].message.content.strip()
            print(f"gpt-5-mini filename: {filename}")
            print("gpt-5-mini model works with chat completions!")
        except Exception as e:
            print(f"gpt-5-mini failed: {e}")
            print("Model may not exist or need different API")

        return True

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_correct_openai_format()
