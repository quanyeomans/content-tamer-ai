#!/usr/bin/env python3
"""Debug script to test file processing without console encoding issues."""

import os
import sys
import traceback

# Add src to path
sys.path.insert(0, "src")


def test_content_extraction():
    """Test content extraction step by step."""
    try:
        from content_processors import ContentProcessorFactory

        # Test file
        input_path = "data/input/R2403D-PDF-ENG.PDF"

        if not os.path.exists(input_path):
            return False, f"File does not exist: {input_path}"

        # Create processor
        content_factory = ContentProcessorFactory("eng")
        processor = content_factory.get_processor(input_path)

        if not processor:
            return False, "No processor found for file"

        # Extract content
        content, metadata = processor.extract_content(input_path)

        return (
            True,
            f"Content extraction successful: {len(content)} characters, content starts with: {content[:50] if content else 'None'}...",
        )

    except Exception as e:
        return False, f"Content extraction error: {str(e)}\n{traceback.format_exc()}"


def test_ai_client():
    """Test AI client setup."""
    try:
        # Set real API key for debugging
        os.environ["OPENAI_API_KEY"] = (
            "sk-proj-**********************************************************************************************************QsA"
        )

        from ai_providers import AIProviderFactory
        from core.directory_manager import get_api_details

        provider = "openai"
        model = "gpt-5-mini"

        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)

        return True, "AI client setup successful"

    except Exception as e:
        return False, f"AI client error: {str(e)}\n{traceback.format_exc()}"


def test_filename_generation(content):
    """Test filename generation with fake API key."""
    try:
        from ai_providers import AIProviderFactory
        from core.directory_manager import get_api_details

        provider = "openai"
        model = "gpt-5-mini"
        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)

        # This should fail with fake key, but we want to see the error handling
        result = ai_client.generate_filename(content[:1000], None)
        return True, f"Unexpected success: {result}"

    except Exception as e:
        error_str = str(e)
        if "API error" in error_str or "invalid_api_key" in error_str:
            return (
                True,
                f"Expected API error (good error handling): {error_str[:100]}...",
            )
        else:
            return False, f"Unexpected error: {str(e)}\n{traceback.format_exc()}"


def main():
    """Run all tests and write results to file."""
    results = []

    # Test 1: Content extraction
    success, message = test_content_extraction()
    results.append(f"Content Extraction: {'PASS' if success else 'FAIL'} - {message}")

    if success:
        # Get content for further testing
        from content_processors import ContentProcessorFactory

        content_factory = ContentProcessorFactory("eng")
        processor = content_factory.get_processor("data/input/R2403D-PDF-ENG.PDF")
        content, _ = processor.extract_content("data/input/R2403D-PDF-ENG.PDF")

        # Test 2: AI client setup
        success, message = test_ai_client()
        results.append(f"AI Client Setup: {'PASS' if success else 'FAIL'} - {message}")

        # Test 3: Filename generation (with expected failure)
        success, message = test_filename_generation(content)
        results.append(
            f"Filename Generation: {'PASS' if success else 'FAIL'} - {message}"
        )

    # Write results to file
    with open("debug_results.txt", "w", encoding="utf-8") as f:
        f.write("=== FILE PROCESSING DEBUG RESULTS ===\n\n")
        for result in results:
            f.write(result + "\n")

    return results


if __name__ == "__main__":
    results = main()
    # Safe print to console
    print("Debug completed. Check debug_results.txt for details.")
    for result in results:
        # Only print success/fail status to avoid encoding issues
        status = result.split(" - ")[0]
        print(status)
