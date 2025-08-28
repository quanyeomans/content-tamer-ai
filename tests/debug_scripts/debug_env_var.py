#!/usr/bin/env python3
"""Debug environment variable reading."""

import os
import sys

# Set environment variable
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def test_env_var_reading():
    """Test environment variable reading."""
    print("=== ENVIRONMENT VARIABLE DEBUG ===")

    # Test direct environment variable access
    direct_key = os.environ.get("OPENAI_API_KEY")
    print(
        f"Direct os.environ.get('OPENAI_API_KEY'): {direct_key[:20]}..."
        if direct_key
        else "None"
    )

    # Test the directory manager function
    try:
        from core.directory_manager import get_api_details

        print("Testing get_api_details('openai', 'gpt-5-mini')...")
        api_key = get_api_details("openai", "gpt-5-mini")
        print(f"get_api_details returned: {api_key[:20]}..." if api_key else "None")

    except Exception as e:
        print(f"get_api_details failed: {e}")
        import traceback

        traceback.print_exc()

    # Test manual env var lookup like the function does
    env_var_name = f"{'openai'.upper()}_API_KEY"
    manual_key = os.environ.get(env_var_name)
    print(
        f"Manual lookup {env_var_name}: {manual_key[:20]}..." if manual_key else "None"
    )


if __name__ == "__main__":
    test_env_var_reading()
