"""
Content Tamer AI - Intelligent Document Organization System

Originally based on sort-rename-move-pdf by munir-abbasi
(https://github.com/munir-abbasi/sort-rename-move-pdf)
Substantially modified and extended for multi-format content processing
and AI-powered document intelligence.

Licensed under MIT License - see LICENSE file for details.
"""

import sys

from core.application import organize_content
from core.cli_parser import (
    _print_capabilities,
    list_available_models,
    parse_arguments,
    restore_api_key,
    setup_api_key,
    setup_environment_and_args,
)
from core.directory_manager import (
    DEFAULT_DATA_DIR,
    DEFAULT_INPUT_DIR,
    DEFAULT_PROCESSED_DIR,
    DEFAULT_PROCESSING_DIR,
    DEFAULT_UNPROCESSED_DIR,
    ensure_default_directories,
    get_api_details,
    setup_directories,
)
from core.file_processor import (
    get_filename_from_ai,
    get_new_filename_with_retry,
    get_new_filename_with_retry_enhanced,
    pdfs_to_text_string,
    process_file,
    process_file_enhanced,
)

# Public API - only main function is exported
__all__ = ["main"]


def main() -> int:
    """Main function to parse arguments and run intelligent document organization."""
    try:
        args = setup_environment_and_args()

        # Setup API key and directories
        original_env, api_key_set = setup_api_key(args)

        try:
            # Setup display options with auto-detection
            display_options = {
                "verbose": args.verbose,
                "quiet": args.quiet,
                "no_color": False,  # Auto-detect in verbose mode, always False for rich UI
                "show_stats": True,  # Always show stats
            }

            input_dir, renamed_dir, unprocessed_dir = setup_directories(args)

            # Print capabilities in verbose mode
            if args.verbose:
                _print_capabilities(args.ocr_lang)

            # Start the main content organization task with enhanced display
            success = organize_content(
                input_dir,
                unprocessed_dir,
                renamed_dir,
                args.provider,
                args.model,
                reset_progress=args.reset_progress,
                ocr_lang=args.ocr_lang,
                display_options=display_options,
            )

            if not success:
                if not args.quiet:
                    print("Content organization failed.")
                return 1
            else:
                if not args.quiet:
                    print("Content organization completed successfully.")
                return 0
        finally:
            # Restore the original API key environment variable if it was changed.
            restore_api_key(api_key_set, original_env)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        return 130  # Standard exit code for a process stopped with Ctrl+C.
    except (ValueError, ImportError) as e:
        print(f"\nConfiguration error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"\nFile not found: {e}")
        return 1
    except PermissionError as e:
        print(f"\nPermission error: {e}")
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
