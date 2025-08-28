#!/usr/bin/env python3
"""Debug processing error in detail."""

import os
import sys
import traceback

# Set environment
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)
os.environ["NO_COLOR"] = "1"

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def debug_single_file_processing():
    """Debug processing a single file with detailed error catching."""
    try:
        from core.file_processor import process_file_enhanced
        from ai_providers import AIProviderFactory
        from content_processors import ContentProcessorFactory
        from file_organizer import FileOrganizer
        from utils.display_manager import DisplayManager, DisplayOptions

        # Setup components
        input_file = "R2403D-PDF-ENG.PDF"
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        input_path = os.path.join(current_dir, "data", "input", input_file)

        if not os.path.exists(input_path):
            print(f"File not found: {input_path}")
            return False

        print(f"Processing: {input_path}")

        # Create AI client
        api_key = os.environ.get("OPENAI_API_KEY")
        ai_client = AIProviderFactory.create("openai", "gpt-5-mini", api_key)
        print("AI client created successfully")

        # Create content processor
        content_factory = ContentProcessorFactory()
        processor = content_factory.get_processor(input_path)
        print(f"Content processor: {type(processor).__name__}")

        # Create file organizer
        organizer = FileOrganizer()
        print("File organizer created")

        # Create display manager
        display_options = DisplayOptions(no_color=True, verbose=True)
        display = DisplayManager(display_options)
        print("Display manager created")

        # Test content extraction
        print("Testing content extraction...")
        text, img_b64 = processor.extract_content(input_path)
        print(f"Extracted text length: {len(text) if text else 0}")
        print(f"Extracted image: {'Yes' if img_b64 else 'No'}")

        # Test AI filename generation
        print("Testing AI filename generation...")
        try:
            ai_filename = ai_client.generate_filename(text, img_b64)
            print(f"AI generated filename: {ai_filename}")
        except Exception as e:
            print(f"AI filename generation failed: {e}")
            traceback.print_exc()
            return False

        # Test full processing
        print("Testing full processing...")
        success, result_filename = process_file_enhanced(
            input_path=input_path,
            ai_client=ai_client,
            content_factory=content_factory,
            organizer=organizer,
            display_context=display,
            ocr_lang="eng",
        )

        print(f"Processing success: {success}")
        print(f"Result filename: {result_filename}")

        return success

    except Exception as e:
        print(f"Debug failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== DEBUG SINGLE FILE PROCESSING ===")
    debug_single_file_processing()
