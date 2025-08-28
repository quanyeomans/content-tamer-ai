#!/usr/bin/env python3
"""Test the full processing pipeline with proper environment setup."""

import os
import sys

# Set environment variables first
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxN6QsA"
)
os.environ["PYTHONUTF8"] = "1"
os.environ["NO_COLOR"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

sys.path.insert(0, "src")


def test_full_pipeline():
    """Test the complete file processing pipeline."""
    try:
        from core.application import organize_content

        # Test parameters
        input_dir = "data/input"
        unprocessed_dir = "data/processed/unprocessed"
        renamed_dir = "data/processed"
        provider = "openai"
        model = "gpt-5-mini"

        print("=== FULL PIPELINE TEST ===")
        print(f"Input dir: {input_dir}")
        print(f"Unprocessed dir: {unprocessed_dir}")
        print(f"Renamed dir: {renamed_dir}")
        print(f"Provider: {provider}")
        print(f"Model: {model}")

        # Check if test file exists
        import os

        test_file = os.path.join(input_dir, "R2403D-PDF-ENG.PDF")
        if not os.path.exists(test_file):
            print(f"WARNING: Test file does not exist: {test_file}")
            return False
        else:
            print(f"Test file exists: {test_file}")

        # Run the organize_content function
        print("\nRunning organize_content...")

        success = organize_content(
            input_dir=input_dir,
            unprocessed_dir=unprocessed_dir,
            renamed_dir=renamed_dir,
            provider=provider,
            model=model,
            display_options={"no_color": True, "verbose": True},
        )

        print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
        return success

    except Exception as e:
        print(f"ERROR in full pipeline test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_pipeline()
    print(f"\n=== PIPELINE TEST {'PASSED' if success else 'FAILED'} ===")
