#!/usr/bin/env python3
"""Debug the specific processing pipeline failure."""

import os
import sys
import traceback

# Set environment
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxN6QsA"
)
os.environ["NO_COLOR"] = "1"

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def debug_exact_failure():
    """Debug the exact point where processing fails."""
    try:
        print("=== DEBUGGING EXACT PROCESSING FAILURE ===")

        # Use existing test file
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        test_file = os.path.join(
            current_dir, "data", "input", "nrma-home-pds-nrmahompds-rev2-0923.pdf"
        )

        if not os.path.exists(test_file):
            print(f"Test file not found: {test_file}")
            return False

        print(f"Using test file: {test_file}")

        # Import and setup components exactly like the main app
        from core.application import (
            _setup_ai_client,
            _setup_display_manager,
            _find_processable_files,
        )
        from content_processors import ContentProcessorFactory
        from file_organizer import FileOrganizer

        input_dir = os.path.join(current_dir, "data", "input")
        unprocessed_dir = os.path.join(current_dir, "data", "processed", "unprocessed")
        renamed_dir = os.path.join(current_dir, "data", "processed")

        # Setup components like main app does
        print("Setting up display manager...")
        display_options = {"no_color": True, "verbose": True, "show_stats": True}
        display_manager = _setup_display_manager(display_options)

        print("Setting up AI client...")
        ai_client, model = _setup_ai_client("openai", "gpt-5-mini", display_manager)
        print(f"AI client setup: {ai_client is not None}, model: {model}")

        print("Setting up content factory...")
        content_factory = ContentProcessorFactory()

        print("Setting up file organizer...")
        organizer = FileOrganizer()

        print("Finding processable files...")
        processable_files = _find_processable_files(input_dir, content_factory)
        print(f"Processable files: {processable_files}")

        if not processable_files:
            print("No processable files found!")
            return False

        # Test processing the first file step by step
        filename = processable_files[0]
        full_path = os.path.join(input_dir, filename)
        print(f"\nTesting file: {filename}")
        print(f"Full path: {full_path}")
        print(f"File exists: {os.path.exists(full_path)}")

        # Test the actual process_file call that the main app uses
        from core.application import _process_files_batch
        from utils.error_handling import create_retry_handler

        print("Testing batch processing...")
        retry_handler = create_retry_handler(max_attempts=3)

        # Mock progress tracker
        class MockProgressTracker:
            def load_progress(self, *args):
                return set()

        organizer.progress_tracker = MockProgressTracker()

        # Test the exact same call that fails in main app
        success, successful_count, failed_count, error_details = _process_files_batch(
            processable_files,
            input_dir,
            unprocessed_dir,
            renamed_dir,
            ai_client,
            content_factory,
            organizer,
            display_manager,
            retry_handler,
            ocr_lang="eng",
        )

        print(f"Batch processing result:")
        print(f"  Success: {success}")
        print(f"  Successful: {successful_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Error details: {error_details}")

        return success

    except Exception as e:
        print(f"Debug failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    debug_exact_failure()
