"""
Content Tamer AI - Application Orchestration

Main application logic coordinating all components for document processing.
"""

import os
from typing import Optional, Set

from .directory_manager import (
    get_api_details,
    DEFAULT_PROCESSED_DIR,
    DEFAULT_PROCESSING_DIR,
)
from .file_processor import process_file_enhanced

# Import utils with fallback
try:
    from utils.error_handling import create_retry_handler
    from utils.display_manager import DisplayManager, DisplayOptions
except ImportError:
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.error_handling import create_retry_handler
    from utils.display_manager import DisplayManager, DisplayOptions


# Import modules - handle both package and direct execution
try:
    from ai_providers import AIProviderFactory
    from content_processors import ContentProcessorFactory
    from file_organizer import FileOrganizer
except ImportError:
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ai_providers import AIProviderFactory
    from content_processors import ContentProcessorFactory
    from file_organizer import FileOrganizer


def _setup_display_manager(display_options: Optional[dict]) -> DisplayManager:
    """Initialize display system with options."""
    display_opts = display_options or {}
    return DisplayManager(
        DisplayOptions(
            verbose=display_opts.get("verbose", False),
            quiet=display_opts.get("quiet", False),
            no_color=display_opts.get("no_color", False),
            show_stats=display_opts.get("show_stats", True),
        )
    )


def _setup_ai_client(
    provider: str, model: Optional[str], display_manager: DisplayManager
):
    """Setup and validate AI client."""
    try:
        if model is None:
            model = AIProviderFactory.get_default_model(provider)
        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)

        display_manager.info(f"Using {provider} provider with model {model}")
        return ai_client, model
    except (ValueError, ImportError) as e:
        display_manager.critical(f"Error setting up AI client: {e}")
        return None, None


def _find_processable_files(input_dir: str, content_factory) -> list:
    """Find files that can be processed in input directory."""
    processable_files = []
    for f in os.listdir(input_dir):
        # Skip hidden or system files
        if f.startswith(".") or f.startswith("._"):
            continue

        full_path = os.path.join(input_dir, f)
        if not os.path.isfile(full_path):
            continue

        # Check if we can process this file type
        if content_factory.get_processor(full_path) is not None:
            processable_files.append(f)

    return processable_files


def _process_files_batch(
    processable_files: list,
    processed_files: set,
    input_dir: str,
    unprocessed_dir: str,
    renamed_dir: str,
    progress_file: str,
    ocr_lang: str,
    ai_client,
    organizer,
    display_manager,
    session_retry_handler,
) -> tuple[bool, int, int, list]:
    """Process batch of files with error handling. Returns (success, successful_count, failed_count, error_details)."""
    successful_count = 0
    failed_count = 0
    error_details = []

    try:
        with open(progress_file, "a", encoding="utf-8") as progress_f:
            with display_manager.processing_context(
                total_files=len(processable_files), description="Processing Files"
            ) as ctx:
                for filename in processable_files:
                    if filename in processed_files:
                        ctx.skip_file(filename)
                        continue

                    input_path = os.path.normpath(os.path.join(input_dir, filename))
                    if not os.path.exists(input_path):
                        ctx.show_warning(f"File {filename} no longer exists, skipping")
                        ctx.skip_file(filename)
                        continue

                    # Start processing the file
                    ctx.start_file(filename)

                    success, new_filename = process_file_enhanced(
                        input_path,
                        filename,
                        unprocessed_dir,
                        renamed_dir,
                        progress_f,
                        ocr_lang,
                        ai_client,
                        organizer,
                        ctx,
                        retry_handler=session_retry_handler,
                    )

                    if success:
                        # File was processed successfully
                        display_name = new_filename if new_filename else "processed"
                        ctx.complete_file(filename, display_name)
                        successful_count += 1
                    else:
                        # File processing failed after all retries
                        # Move file to unprocessed folder
                        try:
                            if os.path.exists(input_path):
                                unprocessed_path = os.path.join(
                                    unprocessed_dir, filename
                                )
                                organizer.file_manager.safe_move(
                                    input_path, unprocessed_path
                                )
                        except OSError:
                            pass  # Will be noted in error summary

                        ctx.fail_file(filename, "Processing failed")
                        failed_count += 1
                        error_details.append(
                            {"filename": filename, "error": "Processing failed"}
                        )
        return True, successful_count, failed_count, error_details
    except KeyboardInterrupt:
        display_manager.warning("Process interrupted by user. Progress has been saved.")
        return (
            True,
            successful_count,
            failed_count,
            error_details,
        )  # Not a failure - user choice
    except IOError as e:
        display_manager.critical(f"Error writing to progress file: {e}")
        return False, successful_count, failed_count, error_details


def organize_content(
    input_dir: str,
    unprocessed_dir: str,
    renamed_dir: str,
    provider: str = "openai",
    model: Optional[str] = None,
    reset_progress: bool = False,
    ocr_lang: str = "eng",
    display_options: Optional[dict] = None,
) -> bool:
    """
    Organize and intelligently rename documents using AI analysis.

    Processes any content type - PDFs, images, screenshots - and generates
    meaningful, descriptive filenames based on document content.
    """
    # Initialize display system
    display_manager = _setup_display_manager(display_options)

    # Security validation for paths
    try:
        from utils.security import PathValidator, SecurityError
    except ImportError:
        import sys

        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from utils.security import PathValidator, SecurityError

    try:
        # Validate all directory paths for security
        safe_input_dir = PathValidator.validate_directory(input_dir)
        safe_unprocessed_dir = PathValidator.validate_directory(unprocessed_dir)
        safe_renamed_dir = PathValidator.validate_directory(renamed_dir)

        # Create allowed base directories set for file validation
        allowed_dirs = {safe_input_dir, safe_unprocessed_dir, safe_renamed_dir}

        # Update paths to use validated versions
        input_dir, unprocessed_dir, renamed_dir = (
            safe_input_dir,
            safe_unprocessed_dir,
            safe_renamed_dir,
        )

    except SecurityError as e:
        display_manager.critical(f"Security error in directory paths: {e}")
        return False

    # Validate input directory exists
    if not os.path.exists(input_dir):
        display_manager.critical(f"Input folder '{input_dir}' does not exist.")
        return False

    # Setup AI client
    ai_client, model = _setup_ai_client(provider, model, display_manager)
    if ai_client is None:
        return False

    # Initialize file organizer
    organizer = FileOrganizer()
    organizer.create_directories(unprocessed_dir, renamed_dir)

    # Show startup information
    display_manager.show_startup_info(
        {
            "directories": {
                "input": input_dir,
                "processed": renamed_dir,
                "unprocessed": unprocessed_dir,
            }
        }
    )

    # Get content processor factory and find processable files
    content_factory = ContentProcessorFactory(ocr_lang)
    supported_extensions = content_factory.get_supported_extensions()
    processable_files = _find_processable_files(input_dir, content_factory)

    total_files = len(processable_files)
    if total_files == 0:
        display_manager.warning(f"No processable files found in {input_dir}")
        display_manager.info(f"Supported extensions: {', '.join(supported_extensions)}")
        return True

    # Use .processing directory for progress file if using defaults, otherwise use renamed_dir
    if renamed_dir == DEFAULT_PROCESSED_DIR:
        progress_file = os.path.join(DEFAULT_PROCESSING_DIR, ".progress")
    else:
        progress_file = os.path.join(renamed_dir, ".progress")
    processed_files = organizer.progress_tracker.load_progress(
        progress_file, input_dir, reset_progress
    )

    # Initialize session-level retry handler for statistics
    session_retry_handler = create_retry_handler(max_attempts=3)

    # Process files batch
    success, successful_count, failed_count, error_details = _process_files_batch(
        processable_files,
        processed_files,
        input_dir,
        unprocessed_dir,
        renamed_dir,
        progress_file,
        ocr_lang,
        ai_client,
        organizer,
        display_manager,
        session_retry_handler,
    )

    if not success:
        return False

    # Show retry/recovery summary if there were any recoverable errors
    retry_summary = session_retry_handler.format_session_summary()
    if retry_summary:
        display_manager.info(retry_summary)

    # Use progress stats as source of truth for final summary 
    progress_stats = display_manager.progress.stats if hasattr(display_manager.progress, 'stats') else None
    
    # Show completion statistics with actual counts from progress tracking
    if progress_stats:
        display_manager.show_completion_stats(
            {
                "total_files": total_files,
                "successful": progress_stats.succeeded,
                "errors": progress_stats.failed,
                "warnings": progress_stats.warnings,
                "recoverable_errors": session_retry_handler.get_stats().files_with_recoverable_issues,
                "successful_retries": session_retry_handler.get_stats().successful_retries,
            }
        )
    else:
        # Fallback to loop counters if progress stats unavailable
        display_manager.show_completion_stats(
            {
                "total_files": total_files,
                "successful": successful_count,
                "errors": failed_count,
                "warnings": 0,
                "recoverable_errors": session_retry_handler.get_stats().files_with_recoverable_issues,
                "successful_retries": session_retry_handler.get_stats().successful_retries,
            }
        )

    # Show detailed error summary if there were failures
    if error_details:
        display_manager.info("📋 Detailed Error Summary:")
        for error in error_details:
            display_manager.error(f"❌ {error['filename']}: {error['error']}")

    return True
