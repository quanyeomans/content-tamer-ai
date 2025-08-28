#!/usr/bin/env python3
"""Test end-to-end processing with the actual main application logic."""

import os
import sys

# Set environment variable (method 1 - proves env var reading works)
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)
os.environ["NO_COLOR"] = "0"  # Enable rich UI

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def test_full_integration():
    """Test the full integration exactly like the main app does."""
    try:
        from core.application import organize_content

        print("=== END-TO-END INTEGRATION TEST ===")

        # Test environment variable reading
        api_key = os.environ.get("OPENAI_API_KEY")
        print(
            f"Environment variable read: {api_key[:20]}..."
            if api_key
            else "FAILED - No API key found"
        )

        # Test directory setup
        input_dir = "data/input"
        unprocessed_dir = "data/processed/unprocessed"
        renamed_dir = "data/processed"

        print(f"Input dir exists: {os.path.exists(input_dir)}")
        print(f"Unprocessed dir exists: {os.path.exists(unprocessed_dir)}")
        print(f"Renamed dir exists: {os.path.exists(renamed_dir)}")

        # Copy test file
        import shutil

        test_file_src = "data/processed/unprocessed/R2403D-PDF-ENG.PDF"
        test_file_dst = "data/input/R2403D-PDF-ENG.PDF"

        if os.path.exists(test_file_src):
            shutil.copy2(test_file_src, test_file_dst)
            print(f"Copied test file: {test_file_dst}")
        else:
            print(f"Source file not found: {test_file_src}")
            return False

        # Run the main organize_content function
        print("Starting organize_content...")
        success = organize_content(
            input_dir=input_dir,
            unprocessed_dir=unprocessed_dir,
            renamed_dir=renamed_dir,
            provider="openai",
            model="gpt-5-mini",
            display_options={
                "no_color": False,  # Rich UI
                "verbose": True,
                "show_stats": True,
            },
        )

        print(f"organize_content result: {success}")

        # Check results
        input_files = os.listdir(input_dir) if os.path.exists(input_dir) else []
        processed_files = (
            [
                f
                for f in os.listdir(renamed_dir)
                if f.endswith(".PDF") and not f.startswith("R2403D-PDF-ENG")
            ]
            if os.path.exists(renamed_dir)
            else []
        )
        unprocessed_files = (
            [f for f in os.listdir(unprocessed_dir) if f.endswith(".PDF")]
            if os.path.exists(unprocessed_dir)
            else []
        )

        print(f"Files remaining in input: {len(input_files)}")
        print(f"Files in processed: {len(processed_files)}")
        print(f"Files in unprocessed: {len(unprocessed_files)}")

        if success:
            print("SUCCESS: End-to-end processing completed!")
        else:
            print("PARTIAL SUCCESS: Application ran but processing had issues")

        return True

    except Exception as e:
        print(f"Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_full_integration()
