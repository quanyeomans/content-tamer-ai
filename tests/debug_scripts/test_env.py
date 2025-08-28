#!/usr/bin/env python3
"""Test environment variable detection."""

import os
import sys

# Set API key directly in Python
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)
os.environ["PYTHONUTF8"] = "1"
os.environ["NO_COLOR"] = "1"

sys.path.insert(0, "src")

# Test environment variable detection
print("Environment variables:")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
if "OPENAI_API_KEY" in os.environ:
    key = os.environ["OPENAI_API_KEY"]
    print(f"OPENAI_API_KEY length: {len(key)}")
    print(f"OPENAI_API_KEY starts with: {key[:8]}...")

print(f"PYTHONUTF8: {os.environ.get('PYTHONUTF8')}")
print(f"NO_COLOR: {os.environ.get('NO_COLOR')}")

# Test API key detection function
try:
    from core.directory_manager import get_api_details

    print("\nTesting get_api_details...")
    api_key = get_api_details("openai", "gpt-5-mini")
    print(f"[OK] API key retrieved successfully: {api_key[:8]}...{api_key[-8:]}")
except Exception as e:
    print(f"[ERROR] Error in get_api_details: {e}")
    import traceback

    traceback.print_exc()
