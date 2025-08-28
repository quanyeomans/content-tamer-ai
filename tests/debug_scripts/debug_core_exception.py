#!/usr/bin/env python3
"""Debug the exact exception in process_file_enhanced_core."""

import os
import sys
import traceback

# Set environment variables
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)

sys.path.insert(0, "src")


def debug_core_exception():
    """Debug process_file_enhanced_core by manually calling each step."""
    try:
        from core.file_processor import (
            _extract_file_content,
            _generate_filename,
            _move_file_only,
        )
        from ai_providers import AIProviderFactory
        from content_processors import ContentProcessorFactory
        from file_organizer import FileOrganizer
        from core.directory_manager import get_api_details

        # Test setup
        input_path = "data/input/R2403D-PDF-ENG.PDF"
        filename = "R2403D-PDF-ENG.PDF"
        unprocessed_folder = "data/processed/unprocessed"
        renamed_folder = "data/processed"
        ocr_lang = "eng"

        if not os.path.exists(input_path):
            print("ERROR: Test file missing!")
            return False

        print("=== DEBUGGING process_file_enhanced_core STEP BY STEP ===")

        # Setup all components
        provider = "openai"
        model = "gpt-5-mini"
        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)
        organizer = FileOrganizer()

        # Mock display context that matches the real one
        class MockDisplayContext:
            def set_status(self, status, **kwargs):
                print(f"  Status: {status}")

            def show_warning(self, msg, **kwargs):
                print(f"  Warning: {msg}")

            def show_error(self, msg, **kwargs):
                print(f"  Error: {msg}")

        display_context = MockDisplayContext()

        # Create test file copy for this test
        test_file = input_path.replace(".PDF", "_coretest.PDF")
        import shutil

        shutil.copy2(input_path, test_file)

        print(f"Test file: {test_file}")
        print(f"Original file exists: {os.path.exists(input_path)}")

        # Now manually call each step from process_file_enhanced_core

        print("\\n1. Testing _extract_file_content...")
        try:
            text, img_b64 = _extract_file_content(test_file, ocr_lang, display_context)
            print(f"  [OK] Success: {len(text)} characters extracted")
        except Exception as e:
            print(f"  [FAIL] Failed: {e}")
            traceback.print_exc()
            return False

        print("\\n2. Testing _generate_filename...")
        try:
            new_file_name = _generate_filename(
                text, img_b64, ai_client, organizer, display_context, filename=filename
            )
            print(f"  [OK] Success: Generated '{new_file_name}'")
        except Exception as e:
            print(f"  [FAIL] Failed: {e}")
            traceback.print_exc()
            return False

        print("\\n3. Testing _move_file_only...")
        try:
            final_file_name = _move_file_only(
                test_file,
                filename,
                renamed_folder,
                new_file_name,
                organizer,
                display_context,
            )
            print(f"  [OK] Success: Moved to '{final_file_name}'")
        except Exception as e:
            print(f"  [FAIL] Failed: {e}")
            traceback.print_exc()
            return False

        print("\\n4. Now testing the ACTUAL process_file_enhanced_core...")

        # Create another test file
        test_file2 = input_path.replace(".PDF", "_coretest2.PDF")
        shutil.copy2(input_path, test_file2)

        # Create mock progress file
        progress_file_path = os.path.join(unprocessed_folder, ".progress_debug")
        os.makedirs(os.path.dirname(progress_file_path), exist_ok=True)

        try:
            from core.file_processor import process_file_enhanced_core

            with open(progress_file_path, "w", encoding="utf-8") as progress_f:
                print(f"  Calling process_file_enhanced_core with:")
                print(f"    input_path: {test_file2}")
                print(f"    filename: {filename}")
                print(f"    unprocessed_folder: {unprocessed_folder}")
                print(f"    renamed_folder: {renamed_folder}")
                print(f"    ocr_lang: {ocr_lang}")

                success, result = process_file_enhanced_core(
                    test_file2,
                    filename,
                    unprocessed_folder,
                    renamed_folder,
                    progress_f,
                    ocr_lang,
                    ai_client,
                    organizer,
                    display_context,
                )

                print(f"\\n  Result: success={success}, result='{result}'")
                print(f"  Test file still exists: {os.path.exists(test_file2)}")

                if not success:
                    print(f"\\n  CORE FUNCTION FAILED - this is where the issue is!")
                    # Check if file was moved to unprocessed
                    unprocessed_path = os.path.join(unprocessed_folder, filename)
                    print(
                        f"  File moved to unprocessed: {os.path.exists(unprocessed_path)}"
                    )

                return success

        except Exception as e:
            print(f"  [FAIL] process_file_enhanced_core exception: {e}")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"Setup error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = debug_core_exception()
    print(f"\\n=== CORE DEBUG {'SUCCESS' if success else 'FAILED'} ===")
