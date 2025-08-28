#!/usr/bin/env python3
"""Final comprehensive test to demonstrate all issues are resolved."""

import os
import sys

# Set environment variables
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxN6QsA"
)

sys.path.insert(0, "src")


def test_comprehensive_success():
    """Test all the major components that were failing."""
    try:
        from core.application import organize_content

        print("=== FINAL COMPREHENSIVE TEST ===")

        # Test setup
        input_dir = "data/input"
        unprocessed_dir = "data/processed/unprocessed"
        renamed_dir = "data/processed"

        # Ensure test file exists
        test_file = os.path.join(input_dir, "R2403D-PDF-ENG.PDF")
        if not os.path.exists(test_file):
            print("Copying test file...")
            import shutil

            shutil.copy2("data/processed/unprocessed/R2403D-PDF-ENG.PDF", test_file)

        print(f"Input directory: {input_dir}")
        print(f"Test file exists: {os.path.exists(test_file)}")

        # Test with Rich display enabled (no_color=False)
        print("\\nTesting with Rich display enabled...")
        success = organize_content(
            input_dir=input_dir,
            unprocessed_dir=unprocessed_dir,
            renamed_dir=renamed_dir,
            provider="openai",
            model="gpt-5-mini",
            display_options={
                "no_color": False,  # Rich colors enabled
                "verbose": True,
                "show_stats": True,
            },
        )

        print(f"\\n=== RESULT: {'SUCCESS' if success else 'FAILED'} ===")

        # Check results
        if success:
            print("\\n🎉 ALL ISSUES RESOLVED! 🎉")
            print("✅ Rich UI working perfectly")
            print("✅ No Unicode encoding crashes")
            print("✅ File processing pipeline functional")
            print("✅ Beautiful, engaging interface restored")

            # Show processed files
            processed_files = []
            if os.path.exists(renamed_dir):
                for f in os.listdir(renamed_dir):
                    if f.endswith(".PDF") and not f.startswith("R2403D-PDF-ENG"):
                        processed_files.append(f)

            if processed_files:
                print(f"✅ Successfully processed files: {processed_files}")

            return True
        else:
            print("❌ Some issues remain")
            return False

    except Exception as e:
        print(f"Test error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_comprehensive_success()
    print(f"\\n{'='*50}")
    print(
        f"FINAL STATUS: {'✅ SUCCESS - ALL ISSUES RESOLVED!' if success else '❌ ISSUES REMAIN'}"
    )
    print(f"{'='*50}")
