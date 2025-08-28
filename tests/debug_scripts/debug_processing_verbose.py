#!/usr/bin/env python3
"""Debug script to test processing with detailed error output."""

import os
import sys
import logging

# Set environment variables
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)
os.environ["NO_COLOR"] = "0"  # Enable colors
os.environ["PYTHONIOENCODING"] = "utf-8"

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def debug_processing():
    """Debug the processing with detailed error output."""
    try:
        from core.application import organize_content

        input_dir = "data/input"
        unprocessed_dir = "data/processed/unprocessed"
        renamed_dir = "data/processed"

        print(f"Input directory: {input_dir}")
        print(
            f"Files in input: {os.listdir(input_dir) if os.path.exists(input_dir) else 'Directory not found'}"
        )

        # Try with detailed logging
        success = organize_content(
            input_dir=input_dir,
            unprocessed_dir=unprocessed_dir,
            renamed_dir=renamed_dir,
            provider="openai",
            model="gpt-5-mini",
            display_options={
                "no_color": False,  # Enable Rich UI
                "verbose": True,
                "show_stats": True,
            },
        )

        print(f"Processing result: {success}")
        return success

    except Exception as e:
        print(f"Debug processing failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== DEBUG PROCESSING TEST ===")
    debug_processing()
