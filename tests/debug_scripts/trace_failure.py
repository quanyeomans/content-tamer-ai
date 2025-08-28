#!/usr/bin/env python3
"""Trace through the main application to find exact failure point."""

import os
import sys

# Set environment
os.environ["OPENAI_API_KEY"] = (
    "sk-proj-**********************************************************************************************************QsA"
)
os.environ["NO_COLOR"] = "1"

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def trace_processing():
    """Add logging to core processing functions to see where failure occurs."""
    try:
        # Patch the process_file_enhanced function to add logging
        from core import file_processor

        # Backup original function
        original_process = file_processor.process_file_enhanced

        def logged_process_file_enhanced(*args, **kwargs):
            print(f"=== process_file_enhanced called ===")
            print(f"Args: {len(args)}")
            print(f"Kwargs: {list(kwargs.keys()) if kwargs else 'None'}")
            try:
                if args:
                    print(f"Input path: {args[0]}")
                    print(f"File exists: {os.path.exists(args[0])}")

                result = original_process(*args, **kwargs)
                print(f"process_file_enhanced result: {result}")
                return result
            except Exception as e:
                print(f"process_file_enhanced FAILED: {e}")
                import traceback

                traceback.print_exc()
                raise

        # Replace the function
        file_processor.process_file_enhanced = logged_process_file_enhanced

        # Now run the main application logic
        from core.application import organize_content

        print("=== TRACING MAIN APPLICATION ===")

        success = organize_content(
            input_dir="data/input",
            unprocessed_dir="data/processed/unprocessed",
            renamed_dir="data/processed",
            provider="openai",
            model="gpt-5-mini",
            display_options={"no_color": True, "verbose": True},
        )

        print(f"Final result: {success}")
        return success

    except Exception as e:
        print(f"Tracing failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    trace_processing()
