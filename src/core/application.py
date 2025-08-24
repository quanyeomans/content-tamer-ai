"""
Content Tamer AI - Application Orchestration

Main application logic coordinating all components for document processing.
"""

import os
from typing import Optional

from .directory_manager import get_api_details, DEFAULT_PROCESSED_DIR, DEFAULT_PROCESSING_DIR
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
) -> bool:
    """Process batch of files with error handling."""
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

                    if success and new_filename:
                        ctx.complete_file(filename, new_filename)
                    elif not success:
                        ctx.fail_file(filename, "Processing failed")
                    else:
                        ctx.complete_file(filename, "processed")
        return True
    except KeyboardInterrupt:
        display_manager.warning("Process interrupted by user. Progress has been saved.")
        return True  # Not a failure - user choice
    except IOError as e:
        display_manager.critical(f"Error writing to progress file: {e}")
        return False


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

    # Validate input directory
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
    success = _process_files_batch(
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

    # Show completion statistics
    display_manager.show_completion_stats(
        {
            "total_files": total_files,
            "successful": total_files,  # Will be updated with actual stats in future enhancement
            "recoverable_errors": session_retry_handler.get_stats().recoverable_errors_encountered,
            "successful_retries": session_retry_handler.get_stats().successful_retries,
        }
    )

    return True