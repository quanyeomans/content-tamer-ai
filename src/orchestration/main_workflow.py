"""
Content Tamer AI - Application Orchestration

Main application logic coordinating all components for document processing.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from core.application_container import ApplicationContainer
from shared.infrastructure.directory_manager import (
    DEFAULT_PROCESSED_DIR,
    DEFAULT_PROCESSING_DIR,
    get_api_details,
)

try:
    from .workflow_processor import process_file_enhanced
except ImportError:
    from workflow_processor import process_file_enhanced

# Import utils with Rich display system
try:
    from shared.display.rich_display_manager import RichDisplayManager as DisplayManager
    from shared.display.rich_display_manager import RichDisplayOptions as DisplayOptions
    from shared.infrastructure.error_handling import create_retry_handler
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from shared.display.rich_display_manager import RichDisplayManager as DisplayManager
    from shared.display.rich_display_manager import RichDisplayOptions as DisplayOptions
    from shared.infrastructure.error_handling import create_retry_handler


# Create fallback implementations for missing modules
class AIProviderFactory:
    @staticmethod
    def get_default_model(provider: str) -> str:  # pylint: disable=unused-argument
        return "default"

    @staticmethod
    def create(provider: str, model: str, api_key: str) -> Any:  # pylint: disable=unused-argument
        return None


class ContentProcessorFactory:
    def __init__(self, ocr_lang: str = "eng"):
        pass

    def get_processor(self, file_path: str) -> Any:  # pylint: disable=unused-argument
        return None

    def get_supported_extensions(self) -> List[str]:
        return []


class FileOrganizer:
    def __init__(self):
        self.progress_tracker = MockProgressTracker()

    def create_directories(self, *args: Any) -> None:
        pass

    def run_post_processing_organization(
        self, *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:  # pylint: disable=unused-argument
        return {"success": False, "reason": "Not implemented"}


class MockProgressTracker:
    def load_progress(self, *args: Any) -> set:  # pylint: disable=unused-argument
        return set()


def _setup_display_manager(
    display_options: Optional[dict], container: Optional[Any] = None
) -> DisplayManager:
    """Initialize display system with options using new architecture."""
    # Application container import handled via TYPE_CHECKING
    pass

    display_opts = display_options or {}

    # Use provided container or create new one (supports test injection)
    if container is None:
        container = ApplicationContainer()

    options = DisplayOptions(
        verbose=display_opts.get("verbose", False),
        quiet=display_opts.get("quiet", False),
        no_color=display_opts.get("no_color", False),
        show_stats=display_opts.get("show_stats", True),
    )

    return container.create_display_manager(options)


def _setup_ai_client(
    provider: str, model: Optional[str], display_manager: DisplayManager
) -> Tuple[Optional[Any], Optional[str]]:
    """Setup and validate AI client."""
    try:
        if model is None:
            model = AIProviderFactory.get_default_model(provider)
        api_key = get_api_details(provider, model or "default")
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
    processable_files: List[str],
    processed_files: set,
    input_dir: str,
    unprocessed_dir: str,
    renamed_dir: str,
    progress_file: str,
    ocr_lang: str,
    ai_client: Any,
    organizer: Any,
    display_manager: DisplayManager,
    session_retry_handler: Any,
) -> Tuple[bool, int, int, List[Dict[str, str]]]:
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
                                unprocessed_path = os.path.join(unprocessed_dir, filename)
                                organizer.file_manager.safe_move(input_path, unprocessed_path)
                        except OSError:
                            pass  # Will be noted in error summary

                        ctx.fail_file(filename, "Processing failed")
                        failed_count += 1
                        error_details.append({"filename": filename, "error": "Processing failed"})
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


def _validate_and_setup_directories(
    input_dir: str, unprocessed_dir: str, renamed_dir: str, display_manager
) -> Tuple[bool, str, str, str]:
    """Validate directories and setup paths securely."""
    # Security validation for paths
    try:
        from shared.infrastructure.security import PathValidator, SecurityError
    except ImportError:
        import sys

        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from shared.infrastructure.security import PathValidator, SecurityError

    try:
        # Validate all directory paths for security
        safe_input_dir = PathValidator.validate_directory(input_dir)
        safe_unprocessed_dir = PathValidator.validate_directory(unprocessed_dir)
        safe_renamed_dir = PathValidator.validate_directory(renamed_dir)

        return True, safe_input_dir, safe_unprocessed_dir, safe_renamed_dir

    except SecurityError as e:
        display_manager.critical(f"Security error in directory paths: {e}")
        return False, input_dir, unprocessed_dir, renamed_dir


def _check_input_directory(input_dir: str, display_manager) -> bool:
    """Check if input directory exists."""
    if not os.path.exists(input_dir):
        display_manager.critical(f"Input folder '{input_dir}' does not exist.")
        return False
    return True


def _setup_processing_environment(
    provider: str,
    model: Optional[str],
    ocr_lang: str,
    display_manager,
    unprocessed_dir: str,
    renamed_dir: str,
) -> Tuple[
    Optional[Any], Optional[str], Optional[FileOrganizer], Optional[ContentProcessorFactory]
]:
    """Setup AI client, organizer, and content processor."""
    # Setup AI client
    ai_client, model = _setup_ai_client(provider, model, display_manager)
    if ai_client is None:
        return None, None, None, None

    # Initialize file organizer
    organizer = FileOrganizer()
    organizer.create_directories(unprocessed_dir, renamed_dir)

    # Get content processor factory
    content_factory = ContentProcessorFactory(ocr_lang)

    return ai_client, model, organizer, content_factory


def _handle_no_files(input_dir: str, supported_extensions: list, display_manager) -> bool:
    """Handle case when no processable files are found."""
    display_manager.warning(f"No processable files found in {input_dir}")
    display_manager.info(f"Supported extensions: {', '.join(supported_extensions)}")
    return True


def _determine_progress_file_path(renamed_dir: str) -> str:
    """Determine appropriate path for progress file."""
    # Use .processing directory for progress file if using defaults, otherwise use renamed_dir
    if renamed_dir == DEFAULT_PROCESSED_DIR:
        return os.path.join(DEFAULT_PROCESSING_DIR, ".progress")
    else:
        return os.path.join(renamed_dir, ".progress")


def _display_completion_summary(
    display_manager,
    total_files: int,
    progress_stats,
    successful_count: int,
    failed_count: int,
    session_retry_handler,
    error_details: list,
) -> None:
    """Display completion statistics and error summary."""
    # Show retry/recovery summary if there were any recoverable errors
    retry_summary = session_retry_handler.format_session_summary()
    if retry_summary:
        display_manager.info(retry_summary)

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


def _prompt_organization_workflow(
    processable_files: List[str], display_manager: DisplayManager, quiet_mode: bool = False
) -> Tuple[bool, int]:
    """
    Prompt user for organization workflow choice in quick start mode.
    Returns (enable_organization, ml_level).
    """
    if quiet_mode:
        # In quiet mode, don't prompt - use defaults (organization disabled)
        return False, 2

    file_count = len(processable_files)

    # Check feature flags to see if organization should be offered
    try:
        from shared.infrastructure.feature_flags import get_feature_manager

        feature_manager = get_feature_manager()

        # Check if organization is available for this context
        if not feature_manager.is_organization_enabled(file_count):
            return False, 2

        # Check if guided navigation should be shown
        if not feature_manager.should_show_guided_navigation(file_count):
            return False, 2

        # Get available ML levels for the prompt
        available_ml_levels = feature_manager.get_available_ml_levels()
        if not available_ml_levels:
            return False, 2

    except ImportError:
        # Fallback without feature flags - use original logic
        if file_count <= 1:
            return False, 2
        available_ml_levels = [1, 2, 3]

    display_manager.info("🗂️  Document Organization Options")
    display_manager.info(
        f"   Found {file_count} files to process. Would you like to organize them?"
    )
    display_manager.info("")
    display_manager.info("   Organization can automatically sort your processed files into:")
    display_manager.info("   • Logical folder structures based on content type")
    display_manager.info("   • Date-based organization for chronological documents")
    display_manager.info("   • Business categories (invoices, contracts, reports, etc.)")
    display_manager.info("")

    # Build dynamic options based on available ML levels
    options = ["Skip organization (default) - Just rename files"]
    option_mapping = {1: (False, 2)}  # Option 1 always disables organization

    for level in available_ml_levels:
        if level == 1:
            options.append("Basic organization - Fast rule-based sorting")
            option_mapping[len(options)] = (True, 1)
        elif level == 2:
            options.append("Smart organization - ML-enhanced categorization (recommended)")
            option_mapping[len(options)] = (True, 2)
        elif level == 3:
            options.append("Advanced organization - Temporal intelligence with insights")
            option_mapping[len(options)] = (True, 3)

    # Display available options
    display_manager.info("   Options:")
    for i, option in enumerate(options, 1):
        display_manager.info(f"     {i}. {option}")
    display_manager.info("")

    max_option = len(options)

    while True:
        try:
            choice = input(f"   Choose option [1-{max_option}, default=1]: ").strip()

            if choice == "" or choice == "1":
                display_manager.info("   ✅ Organization disabled - files will only be renamed")
                return False, 2

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= max_option:
                    enable_org, ml_level = option_mapping[choice_num]

                    if enable_org:
                        level_names = {1: "basic", 2: "smart", 3: "advanced"}
                        level_name = level_names.get(ml_level, f"level {ml_level}")
                        display_manager.info(f"   ✅ Using {level_name} organization")
                    else:
                        display_manager.info(
                            "   ✅ Organization disabled - files will only be renamed"
                        )

                    return enable_org, ml_level
                else:
                    display_manager.warning(f"   Please enter a number between 1 and {max_option}")
            except ValueError:
                display_manager.warning(f"   Please enter a number between 1 and {max_option}")

        except (KeyboardInterrupt, EOFError):
            display_manager.info("   Using default: organization disabled")
            return False, 2


def organize_content(
    input_dir: str,
    unprocessed_dir: str,
    renamed_dir: str,
    provider: str = "openai",
    model: Optional[str] = None,
    reset_progress: bool = False,
    ocr_lang: str = "eng",
    display_options: Optional[dict] = None,
    enable_post_processing: bool = False,
    ml_enhancement_level: int = 2,
    container: Optional[Any] = None,
    quiet_mode: bool = False,
) -> bool:
    """
    Organize and intelligently rename documents using AI analysis.

    Processes any content type - PDFs, images, screenshots - and generates
    meaningful, descriptive filenames based on document content.
    """
    # Initialize display system (with optional test container injection)
    display_manager = _setup_display_manager(display_options, container)

    # Validate directories and setup paths
    success, input_dir, unprocessed_dir, renamed_dir = _validate_and_setup_directories(
        input_dir, unprocessed_dir, renamed_dir, display_manager
    )
    if not success:
        return False

    # Check input directory exists
    if not _check_input_directory(input_dir, display_manager):
        return False

    # Setup processing environment
    ai_client, model, organizer, content_factory = _setup_processing_environment(
        provider, model, ocr_lang, display_manager, unprocessed_dir, renamed_dir
    )
    if ai_client is None:
        return False

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

    # Find processable files
    supported_extensions = content_factory.get_supported_extensions() if content_factory else []
    processable_files = _find_processable_files(input_dir, content_factory)

    total_files = len(processable_files)
    if total_files == 0:
        return _handle_no_files(input_dir, supported_extensions, display_manager)

    # Apply guided navigation if organization settings not explicitly set via CLI
    quiet_mode = display_options.get("quiet", False) if display_options else False

    # If enable_post_processing is the default False and no explicit CLI override,
    # show guided navigation prompts for multi-file batches
    if not enable_post_processing and total_files > 1:
        enable_post_processing, ml_enhancement_level = _prompt_organization_workflow(
            processable_files, display_manager, quiet_mode
        )

    # Setup progress tracking
    progress_file = _determine_progress_file_path(renamed_dir)
    processed_files = (
        organizer.progress_tracker.load_progress(progress_file, input_dir, reset_progress)
        if organizer
        else set()
    )

    # Initialize retry handler and process files
    session_retry_handler = create_retry_handler(max_attempts=3)
    success, successful_count, failed_count, error_details = _process_files_batch(
        processable_files,
        processed_files,
        input_dir,
        unprocessed_dir,
        renamed_dir,
        progress_file,
        ocr_lang,
        ai_client or {},  # Ensure not None
        organizer,
        display_manager,
        session_retry_handler,
    )

    if not success:
        return False

    # Display completion summary
    progress_stats = (
        display_manager.progress.stats if hasattr(display_manager.progress, "stats") else None
    )
    _display_completion_summary(
        display_manager,
        total_files,
        progress_stats,
        successful_count,
        failed_count,
        session_retry_handler,
        error_details or [],
    )

    # Run post-processing organization if enabled and there were successful files
    if enable_post_processing and successful_count > 0:
        try:
            # Get list of processed files in the renamed directory
            processed_files = []
            if os.path.exists(renamed_dir):
                for filename in os.listdir(renamed_dir):
                    file_path = os.path.join(renamed_dir, filename)
                    if os.path.isfile(file_path):
                        processed_files.append(file_path)

            if processed_files:
                # Use organization context for better progress display
                with display_manager.organization_context(
                    len(processed_files), ml_enhancement_level
                ):
                    # Show initial progress
                    display_manager.show_organization_progress(
                        "analyzing", 0, len(processed_files), "Preparing documents"
                    )

                    # Run post-processing organization with ML level
                    if organizer:
                        organization_result = organizer.run_post_processing_organization(
                            processed_files,
                            renamed_dir,
                            enable_organization=True,
                            ml_enhancement_level=ml_enhancement_level,
                        )
                    else:
                        organization_result = {"success": False, "reason": "No organizer available"}

                    if organization_result.get("success", False):
                        if organization_result.get("organization_applied", False):
                            # Show successful organization results using enhanced display
                            display_manager.show_organization_results(organization_result)
                        else:
                            reason = organization_result.get("reason", "Unknown")
                            display_manager.info(
                                f"ℹ️  Post-processing organization skipped: {reason}"
                            )
                    else:
                        error_msg = organization_result.get("reason", "Unknown error")
                        error_details = {
                            "error_type": organization_result.get("error_type", "unknown"),
                            "is_recoverable": organization_result.get("is_recoverable", False),
                            "retry_recommended": organization_result.get(
                                "retry_recommended", False
                            ),
                            "context": organization_result.get("context", ""),
                        }
                        display_manager.show_organization_error(error_msg, error_details)
            else:
                display_manager.info("ℹ️  No processed files found for post-processing organization")

        except Exception as e:
            display_manager.show_organization_error(
                f"Unexpected error: {e}", {"error_type": type(e).__name__}
            )
            # Don't fail the entire workflow due to post-processing issues

    return True
