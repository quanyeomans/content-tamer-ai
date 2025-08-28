#!/usr/bin/env python3
"""Debug the exact step that fails in process_file_enhanced_core."""

import os
import sys

# Set environment
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def debug_core_steps():
    """Debug each step of process_file_enhanced_core."""
    try:
        # Import all needed components
        from core.file_processor import _extract_file_content, _generate_filename
        from ai_providers import AIProviderFactory
        from file_organizer import FileOrganizer
        from utils.display_manager import DisplayManager, DisplayOptions

        print("=== DEBUGGING CORE PROCESSING STEPS ===")

        # Use a test file from unprocessed (where failed files go)
        test_file = "data/processed/unprocessed/nrma-home-pds-nrmahompds-rev2-0923.pdf"
        if not os.path.exists(test_file):
            print(f"Test file not found: {test_file}")
            return False

        print(f"Testing file: {test_file}")

        # Setup components
        display_options = DisplayOptions(no_color=True, verbose=True)
        display_manager = DisplayManager(display_options)

        ai_client = AIProviderFactory.create(
            "openai", "gpt-5-mini", os.environ["OPENAI_API_KEY"]
        )
        organizer = FileOrganizer()

        print("Components initialized successfully")

        # Get proper processing context
        with display_manager.processing_context(
            total_files=1, description="Debug Test"
        ) as display_context:
            # Step 1: Extract content
            print("\n=== STEP 1: Content Extraction ===")
            try:
                text, img_b64 = _extract_file_content(test_file, "eng", display_context)
                print("Content extraction successful:")
                print(f"   Text length: {len(text) if text else 0}")
                print(f"   Has image: {'Yes' if img_b64 else 'No'}")
            except Exception as e:
                print(f"Content extraction FAILED: {e}")
                import traceback

                traceback.print_exc()
                return False

            # Step 2: Generate filename
            print("\n=== STEP 2: Filename Generation ===")
            try:
                new_filename = _generate_filename(
                    text,
                    img_b64,
                    ai_client,
                    organizer,
                    display_context,
                    filename="test.pdf",
                )
                print(f"Filename generation successful: {new_filename}")
            except Exception as e:
                print(f"Filename generation FAILED: {e}")
                import traceback

                traceback.print_exc()
                return False

            # Step 3: Test move operation (we'll skip actual move)
            print("\n=== STEP 3: File Move (simulated) ===")
            print("Would move file successfully (skipping actual move)")

            print("\nALL CORE STEPS SUCCESSFUL!")
            return True

    except Exception as e:
        print(f"Setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = debug_core_steps()
    print(f"\nOverall result: {'SUCCESS' if success else 'FAILED'}")
