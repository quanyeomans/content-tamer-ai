#!/usr/bin/env python3
"""Debug the _move_file_only function specifically."""

import os
import sys
import traceback

# Set environment variables
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxN6QsA"
)

sys.path.insert(0, "src")


def test_move_file_only():
    """Test the _move_file_only function directly."""
    try:
        from core.file_processor import _move_file_only
        from file_organizer import FileOrganizer
        from ai_providers import AIProviderFactory
        from core.directory_manager import get_api_details

        # Test setup
        input_path = "data/input/R2403D-PDF-ENG.PDF"
        filename = "R2403D-PDF-ENG.PDF"
        renamed_folder = "data/processed"

        if not os.path.exists(input_path):
            print("ERROR: Test file missing!")
            return False

        # Setup components
        provider = "openai"
        model = "gpt-5-mini"
        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)
        organizer = FileOrganizer()

        # Generate filename like the real process would
        from content_processors import ContentProcessorFactory

        content_factory = ContentProcessorFactory("eng")
        processor = content_factory.get_processor(input_path)
        text, img_b64 = processor.extract_content(input_path)
        new_filename = ai_client.generate_filename(text[:2000], img_b64)

        print(f"Generated filename: '{new_filename}'")

        # Mock display context
        class MockDisplayContext:
            def set_status(self, status, **kwargs):
                print(f"Status: {status} {kwargs}")

            def show_warning(self, msg, **kwargs):
                print(f"Warning: {msg} {kwargs}")

            def show_error(self, msg, **kwargs):
                print(f"Error: {msg} {kwargs}")

        mock_context = MockDisplayContext()

        # Create test file copy
        test_file = input_path.replace(".PDF", "_movetest.PDF")
        import shutil

        shutil.copy2(input_path, test_file)

        print(f"\\nTesting _move_file_only...")
        print(f"Source: {test_file}")
        print(f"Target folder: {renamed_folder}")
        print(f"New name: {new_filename}")

        # Test the actual function
        result = _move_file_only(
            test_file,
            os.path.basename(test_file),
            renamed_folder,
            new_filename,
            organizer,
            mock_context,
        )

        print(f"\\nResult: '{result}'")

        # Check if file was moved and find where it went
        expected_path_no_ext = os.path.join(
            renamed_folder, result if result else "UNKNOWN"
        )
        expected_path_with_ext = expected_path_no_ext + ".PDF"

        print(f"Expected path (no ext): {expected_path_no_ext}")
        print(f"Expected path (with ext): {expected_path_with_ext}")
        print(f"File exists (no ext): {os.path.exists(expected_path_no_ext)}")
        print(f"File exists (with ext): {os.path.exists(expected_path_with_ext)}")
        print(f"Original test file still exists: {os.path.exists(test_file)}")

        # List files in processed directory to see what's there
        if os.path.exists(renamed_folder):
            files = os.listdir(renamed_folder)
            print(f"Files in {renamed_folder}: {files}")
            # Look for files containing our generated name
            matching_files = [f for f in files if "Talent_Management_Freelancers" in f]
            print(f"Matching files: {matching_files}")

        return result is not None

    except Exception as e:
        print(f"_move_file_only test failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_move_file_only()
    print(f"\\n=== TEST {'PASSED' if success else 'FAILED'} ===")
