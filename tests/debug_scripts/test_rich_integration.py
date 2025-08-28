#!/usr/bin/env python3
"""Test Rich integration to ensure it resolves encoding issues."""

import os
import sys
import traceback

# Set environment variables first
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)
os.environ["PYTHONUTF8"] = "1"
os.environ["NO_COLOR"] = "0"  # Enable colors to test Rich
os.environ["PYTHONIOENCODING"] = "utf-8"

sys.path.insert(0, "src")


def test_rich_display():
    """Test Rich display components."""
    try:
        from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions

        print("=== TESTING RICH DISPLAY SYSTEM ===")

        # Create Rich display manager
        display_options = RichDisplayOptions(
            verbose=True,
            quiet=False,
            no_color=False,  # Enable colors for testing
            show_stats=True,
        )

        display = RichDisplayManager(display_options)

        # Test header
        display.print_header("CONTENT TAMER AI", "Rich UI Integration Test")

        # Test various message types
        display.debug("This is a debug message with Unicode ✓")
        display.info("This is an info message with emoji 🎯")
        display.success("This is a success message with celebration 🎉")
        display.warning("This is a warning message ⚠️")
        display.error("This is an error message ❌")

        # Test capabilities display
        ocr_deps = {"PyMuPDF": True, "Tesseract": True}
        ocr_settings = {"OCR_LANG": "eng", "OCR_PAGES": 4, "OCR_ZOOM": 3.5}
        display.print_capabilities(ocr_deps, ocr_settings)

        # Test provider setup
        display.print_provider_setup("openai", "gpt-5-mini")

        # Test directory info
        directories = {
            "Input": "C:\\Users\\danie\\Programming\\content-tamer-ai\\data\\input",
            "Processed": "C:\\Users\\danie\\Programming\\content-tamer-ai\\data\\processed",
            "Unprocessed": "C:\\Users\\danie\\Programming\\content-tamer-ai\\data\\processed\\unprocessed",
        }
        display.print_directory_info(directories)

        return True, "Rich display system working perfectly! ✨"

    except Exception as e:
        return False, f"Rich display error: {e}\\n{traceback.format_exc()}"


def test_rich_progress():
    """Test Rich progress display."""
    try:
        import time
        from utils.rich_progress_display import RichProgressDisplay

        print("\\n=== TESTING RICH PROGRESS DISPLAY ===")

        # Create Rich progress display
        progress = RichProgressDisplay(no_color=False, show_stats=True)

        # Test progress with multiple files
        test_files = [
            "document1.pdf",
            "screenshot_with_unicode_✓.png",
            "file_with_émojis_🎯.pdf",
            "another_document.pdf",
        ]

        with progress.processing_context(
            len(test_files), "Testing Rich Progress"
        ) as ctx:
            for i, filename in enumerate(test_files):
                ctx.start_file(filename)
                time.sleep(0.1)  # Simulate processing

                ctx.set_status("extracting_content")
                time.sleep(0.1)

                ctx.set_status("generating_filename")
                time.sleep(0.1)

                if i == 1:  # Simulate warning on second file
                    ctx.warn_file(filename, "Unicode character detected")
                elif i == 2:  # Simulate error on third file
                    ctx.fail_file(filename, "Processing failed")
                    continue
                else:
                    ctx.complete_file(filename, f"processed_{filename}")

        return True, "Rich progress display working beautifully! 🌈"

    except Exception as e:
        return False, f"Rich progress error: {e}\\n{traceback.format_exc()}"


def test_full_pipeline_with_rich():
    """Test full pipeline with Rich integration."""
    try:
        from core.application import organize_content

        print("\\n=== TESTING FULL PIPELINE WITH RICH ===")

        # Test parameters
        input_dir = "data/input"
        unprocessed_dir = "data/processed/unprocessed"
        renamed_dir = "data/processed"
        provider = "openai"
        model = "gpt-5-mini"

        # Check if test file exists
        test_file = os.path.join(input_dir, "R2403D-PDF-ENG.PDF")
        if not os.path.exists(test_file):
            return False, f"Test file does not exist: {test_file}"

        print(f"Test file exists: {test_file}")
        print("Running organize_content with Rich display...")

        success = organize_content(
            input_dir=input_dir,
            unprocessed_dir=unprocessed_dir,
            renamed_dir=renamed_dir,
            provider=provider,
            model=model,
            display_options={"no_color": False, "verbose": True},  # Enable Rich colors
        )

        return (
            success,
            f"Pipeline completed {'successfully' if success else 'with errors'}",
        )

    except Exception as e:
        return False, f"Pipeline error: {e}\\n{traceback.format_exc()}"


def main():
    """Run all Rich integration tests."""
    tests = [
        ("Rich Display System", test_rich_display),
        ("Rich Progress Display", test_rich_progress),
        ("Full Pipeline with Rich", test_full_pipeline_with_rich),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\\n{'='*60}")
        print(f"Running: {test_name}")
        print("=" * 60)

        try:
            success, message = test_func()
            status = "[PASS]" if success else "[FAIL]"
            results.append((test_name, success, message))
            print(f"\\n{status}: {message}")
        except Exception as e:
            results.append((test_name, False, f"Exception: {e}"))
            print(f"\\n[EXCEPTION]: {e}")

    # Final summary
    print(f"\\n{'='*60}")
    print("RICH INTEGRATION TEST SUMMARY")
    print("=" * 60)

    for test_name, success, message in results:
        status_icon = "[PASS]" if success else "[FAIL]"
        print(f"{status_icon} {test_name}: {message[:100]}...")

    total_tests = len(results)
    passed_tests = sum(1 for _, success, _ in results if success)

    print(f"\\nResults: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("[SUCCESS] ALL TESTS PASSED! Rich integration successful!")
        return True
    else:
        print("[WARNING] Some tests failed. Rich integration needs attention.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
