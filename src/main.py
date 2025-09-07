"""
Content Tamer AI - Intelligent Document Organization System

Originally based on sort-rename-move-pdf by munir-abbasi
(https://github.com/munir-abbasi/sort-rename-move-pdf)
Substantially modified and extended for multi-format content processing
and AI-powered document intelligence.

Licensed under MIT License - see LICENSE file for details.
"""

import sys

# Handle both package and direct execution imports
try:
    from core.application import organize_content
    from core.cli_parser import (
        _print_capabilities,
        restore_api_key,
        setup_api_key,
        setup_environment_and_args,
    )
    from core.directory_manager import setup_directories
except ImportError:
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from core.application import organize_content
    from core.cli_parser import (
        _print_capabilities,
        restore_api_key,
        setup_api_key,
        setup_environment_and_args,
    )
    from core.directory_manager import setup_directories

# Public API - only main function is exported
__all__ = ["main"]


def _validate_organization_settings(enable_post_processing: bool, ml_enhancement_level: int, quiet: bool):
    """Validate organization settings against feature flags."""
    if not enable_post_processing:
        return enable_post_processing, ml_enhancement_level

    try:
        from utils.feature_flags import get_feature_manager
        feature_manager = get_feature_manager()

        # Check if organization is available
        if not feature_manager.is_organization_enabled():
            if not quiet:
                print("⚠️  Organization features are currently disabled via feature flags")
            return False, ml_enhancement_level

        # Validate ML level against feature flags
        validated_ml_level = feature_manager.validate_ml_level(ml_enhancement_level)
        if validated_ml_level != ml_enhancement_level and not quiet:
            print(f"ℹ️  Adjusted ML level to {validated_ml_level} (closest available level)")

        return enable_post_processing, validated_ml_level

    except ImportError:
        # Feature flags not available, continue with original values
        return enable_post_processing, ml_enhancement_level


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

            # Determine organization settings from CLI arguments with feature flag validation
            # Note: If neither --organize nor --no-organize specified, guided navigation will handle it
            enable_post_processing = getattr(args, 'organize', False)
            ml_enhancement_level = getattr(args, 'ml_level', 2)

            # Force disable if --no-organize was specified
            if getattr(args, 'no_organize', False):
                enable_post_processing = False

            # Validate settings against feature flags
            enable_post_processing, ml_enhancement_level = _validate_organization_settings(
                enable_post_processing, ml_enhancement_level, args.quiet
            )

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
                enable_post_processing=enable_post_processing,
                ml_enhancement_level=ml_enhancement_level,
            )

            if not success:
                if not args.quiet:
                    print("Content organization failed.")
                return 1

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
