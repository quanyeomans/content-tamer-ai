"""
Content Tamer AI - File Processing Pipeline

Handles the core file processing logic including content extraction,
AI-powered filename generation, and error handling with retry logic.
"""

import datetime as dt
import os
import time
from typing import Any, Optional, Tuple

try:
    from utils.error_handling import create_retry_handler, RetryHandler
except ImportError:
    # For when running as package
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.error_handling import create_retry_handler, RetryHandler


# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2

# Error log location
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DOCUMENTS_DIR = os.path.join(PROJECT_ROOT, "documents")
DEFAULT_PROCESSING_DIR = os.path.join(DEFAULT_DOCUMENTS_DIR, ".processing")
ERROR_LOG_FILE = os.path.join(DEFAULT_PROCESSING_DIR, "errors.log")


def _extract_file_content(input_path: str, ocr_lang: str, display_context) -> tuple:
    """Extract content from file using appropriate processor."""
    display_context.set_status("extracting_content")
    
    # Import here to avoid circular imports
    try:
        from content_processors import ContentProcessorFactory
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from content_processors import ContentProcessorFactory
        
    content_factory = ContentProcessorFactory(ocr_lang)
    processor = content_factory.get_processor(input_path)
    if not processor:
        raise ValueError(f"Unsupported file type: {input_path}")

    text, img_b64 = processor.extract_content(input_path)

    # If the extractor returned an error message, treat it as an unprocessable file.
    if text.startswith("Error"):
        raise ValueError(text)

    return text, img_b64


def _generate_filename(
    text: str, img_b64: str, ai_client, organizer, display_context
) -> str:
    """Generate appropriate filename based on content."""
    display_context.set_status("generating_filename")

    # If the file is empty (no text or image), give it a generic name.
    if not text and not img_b64:
        display_context.show_warning("File appears to be empty")
        timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
        return f"empty_file_{timestamp}"

    # Get a new filename from the AI, with retries in case of network issues.
    new_file_name = get_new_filename_with_retry_enhanced(
        ai_client, text, img_b64, display_context
    )
    return organizer.filename_handler.validate_and_trim_filename(new_file_name)


def _move_file_only(
    input_path: str,
    filename: str,
    renamed_folder: str,
    new_file_name: str,
    organizer,
    display_context,
) -> str:
    """Move file to renamed folder (progress recording handled separately)."""
    display_context.set_status("moving_file")
    file_extension = os.path.splitext(input_path)[1]
    final_file_name = organizer.move_file_to_category(
        input_path, filename, renamed_folder, new_file_name, file_extension
    )
    return final_file_name


def _move_and_record_file(
    input_path: str,
    filename: str,
    renamed_folder: str,
    new_file_name: str,
    organizer,
    progress_f,
    display_context,
) -> str:
    """Move file to renamed folder and record progress (legacy function)."""
    final_file_name = _move_file_only(
        input_path, filename, renamed_folder, new_file_name, organizer, display_context
    )

    # Record that this file has been processed.
    organizer.progress_tracker.record_progress(
        progress_f, filename, organizer.file_manager
    )

    return final_file_name


def _handle_processing_error_no_progress(
    error: Exception,
    filename: str,
    input_path: str,
    unprocessed_folder: str,
    organizer,
    display_context,
) -> tuple:
    """Handle processing errors by moving to unprocessed folder (progress recording handled separately)."""
    error_msg = f"Error processing {filename}: {str(error)}"
    display_context.show_error(error_msg)

    try:
        if os.path.exists(input_path):
            unprocessed_path = os.path.join(unprocessed_folder, filename)
            organizer.file_manager.safe_move(input_path, unprocessed_path)
            display_context.show_warning("Moved to unprocessed folder")
    except OSError as move_error:
        display_context.show_error(f"Failed to move file: {str(move_error)}")

    return False, None


def _handle_processing_error(
    error: Exception,
    filename: str,
    input_path: str,
    unprocessed_folder: str,
    organizer,
    progress_f,
    display_context,
) -> tuple:
    """Handle processing errors by moving to unprocessed folder (legacy function)."""
    success, result = _handle_processing_error_no_progress(
        error, filename, input_path, unprocessed_folder, organizer, display_context
    )

    # Record progress
    organizer.progress_tracker.record_progress(
        progress_f, filename, organizer.file_manager
    )

    return success, result


def _handle_runtime_error(error: RuntimeError, filename: str, display_context) -> tuple:
    """Handle runtime errors by logging."""
    error_msg = f"Unexpected error with file {filename}: {str(error)}"
    display_context.show_error(error_msg)

    try:
        with open(ERROR_LOG_FILE, mode="a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\\n")
    except (IOError, OSError) as log_error:
        display_context.show_warning(f"Could not write to error log: {str(log_error)}")

    return False, None


def process_file_enhanced_core(
    input_path: str,
    filename: str,
    unprocessed_folder: str,
    renamed_folder: str,
    progress_f: Any,
    ocr_lang: str,
    ai_client: Any,
    organizer: Any,
    display_context: Any,
) -> Tuple[bool, Optional[str]]:
    """Core file processing logic (called by retry wrapper)."""
    success = False
    result = None
    
    try:
        if not os.path.isfile(input_path):
            display_context.show_error(f"File not found: {input_path}")
            success, result = False, None
        else:
            # Extract content
            text, img_b64 = _extract_file_content(input_path, ocr_lang, display_context)

            # Generate filename
            new_file_name = _generate_filename(
                text, img_b64, ai_client, organizer, display_context
            )

            # Move file (without recording progress)
            final_file_name = _move_file_only(
                input_path,
                filename,
                renamed_folder,
                new_file_name,
                organizer,
                display_context,
            )

            success, result = True, final_file_name

    except (ValueError, OSError, FileNotFoundError) as e:
        success, result = _handle_processing_error_no_progress(
            e,
            filename,
            input_path,
            unprocessed_folder,
            organizer,
            display_context,
        )

    except RuntimeError as e:
        success, result = _handle_runtime_error(e, filename, display_context)
    
    finally:
        # Record progress once at the end, regardless of success/failure
        organizer.progress_tracker.record_progress(
            progress_f, filename, organizer.file_manager
        )
    
    return success, result


def process_file_with_retry(
    input_path: str,
    filename: str,
    unprocessed_folder: str,
    renamed_folder: str,
    progress_f: Any,
    ocr_lang: str,
    ai_client: Any,
    organizer: Any,
    display_context: Any,
    retry_handler: RetryHandler,
) -> Tuple[bool, Optional[str]]:
    """Process a file with intelligent retry logic for recoverable errors."""

    def _process_operation():
        """Inner function that performs the actual file processing."""
        return process_file_enhanced_core(
            input_path=input_path,
            filename=filename,
            unprocessed_folder=unprocessed_folder,
            renamed_folder=renamed_folder,
            progress_f=progress_f,
            ocr_lang=ocr_lang,
            ai_client=ai_client,
            organizer=organizer,
            display_context=display_context,
        )

    # Use the retry handler to execute the operation
    success, result, error_classification = retry_handler.execute_with_retry(
        operation=_process_operation, display_context=display_context, filename=filename
    )

    return success, result


def process_file_enhanced(
    input_path: str,
    filename: str,
    unprocessed_folder: str,
    renamed_folder: str,
    progress_f: Any,
    ocr_lang: str,
    ai_client: Any,
    organizer: Any,
    display_context: Any,
    retry_handler: Optional[RetryHandler] = None,
) -> Tuple[bool, Optional[str]]:
    """Enhanced file processing with intelligent retry logic."""
    # Create retry handler if not provided
    if retry_handler is None:
        retry_handler = create_retry_handler(max_attempts=3)

    return process_file_with_retry(
        input_path=input_path,
        filename=filename,
        unprocessed_folder=unprocessed_folder,
        renamed_folder=renamed_folder,
        progress_f=progress_f,
        ocr_lang=ocr_lang,
        ai_client=ai_client,
        organizer=organizer,
        display_context=display_context,
        retry_handler=retry_handler,
    )


def get_new_filename_with_retry_enhanced(
    ai_client: Any,
    pdf_content: str,
    image_b64: Optional[str] = None,
    display_context=None,
    max_attempts: int = MAX_RETRIES,
) -> str:
    """
    Get a new filename from the AI, with enhanced retry logic and display integration.
    """
    timeout_count = 0

    for attempt in range(max_attempts):
        try:
            return get_filename_from_ai(ai_client, pdf_content, image_b64)
        except RuntimeError as e:
            error_str = str(e).lower()
            is_timeout = any(
                t in error_str
                for t in ["timeout", "timed out", "connection", "network"]
            )

            if is_timeout:
                timeout_count += 1
                wait_time = RETRY_DELAY * (2**timeout_count)  # Exponential backoff
                if display_context:
                    display_context.show_warning(
                        f"API timeout/network error. Retrying in {wait_time} seconds..."
                    )
            else:
                if display_context:
                    display_context.show_warning(f"AI API error: {str(e)}")

            if attempt < max_attempts - 1:  # Don't wait after the last attempt
                if display_context:
                    display_context.set_status("retrying")
                time.sleep(wait_time if is_timeout else RETRY_DELAY)

    # If all retries failed, return a timestamped fallback name
    if display_context:
        display_context.show_warning(
            f"AI filename generation failed after {max_attempts} attempts. Using fallback naming."
        )
    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"failed_ai_generation_{timestamp}"


def get_new_filename_with_retry(
    ai_client: Any,
    pdf_content: str,
    image_b64: Optional[str] = None,
    max_attempts: int = MAX_RETRIES,
    max_retries: int = None,  # Backward compatibility
) -> str:
    """
    Get a new filename from the AI, with retries for network timeouts.
    Legacy function for backward compatibility with original fallback naming.
    """
    # Handle backward compatibility for max_retries parameter
    if max_retries is not None:
        max_attempts = max_retries
    
    # Legacy implementation with original error handling and fallback names
    for attempt in range(max_attempts):
        try:
            return ai_client.generate_filename(pdf_content, image_b64)
        except Exception as e:
            error_msg = str(e).lower()
            if attempt == max_attempts - 1:  # Last attempt
                # Return legacy fallback names based on error type
                timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
                if "timeout" in error_msg or "network" in error_msg:
                    return f"network_error_{timestamp}"
                else:
                    return f"untitled_document_{timestamp}"
            
            # Sleep before retry (except on last attempt)
            time.sleep(2 ** attempt)  # Exponential backoff
    
    # Fallback (should not reach here)
    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"untitled_document_{timestamp}"


def get_filename_from_ai(
    ai_client: Any, pdf_content: str, image_b64: Optional[str] = None
) -> str:
    """Generate filename using AI client."""
    if ai_client is None:
        raise RuntimeError("AI client not initialized. Call organize_content first.")
    return ai_client.generate_filename(pdf_content, image_b64)


def process_file(
    input_path: str,
    filename: str,
    unprocessed_folder: str,
    renamed_folder: str,
    pbar: Any,
    progress_f: Any,
    ocr_lang: str,
    ai_client: Any,
    organizer: Any,
) -> bool:
    """
    Legacy file processing function for backward compatibility.
    Processes a single file: extracts content, gets a new name, and moves the file.
    """
    try:
        if not os.path.isfile(input_path):
            return False

        # Extract content using appropriate processor
        try:
            from content_processors import ContentProcessorFactory
        except ImportError:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from content_processors import ContentProcessorFactory
            
        content_factory = ContentProcessorFactory(ocr_lang)
        processor = content_factory.get_processor(input_path)
        if not processor:
            raise ValueError(f"Unsupported file type: {input_path}")

        text, img_b64 = processor.extract_content(input_path)

        # If the extractor returned an error message, treat it as an unprocessable file.
        if text.startswith("Error"):
            raise ValueError(text)

        # If the PDF is empty (no text or image), give it a generic name.
        if not text and not img_b64:
            timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"empty_file_{timestamp}"
        else:
            # Get a new filename from the AI, with retries in case of network issues.
            new_file_name = get_new_filename_with_retry(ai_client, text, img_b64)
            new_file_name = organizer.filename_handler.validate_and_trim_filename(
                new_file_name
            )

        # Move the file to the renamed folder with proper extension handling
        file_extension = os.path.splitext(input_path)[1]
        new_file_name = organizer.move_file_to_category(
            input_path, filename, renamed_folder, new_file_name, file_extension
        )
        pbar.set_postfix({"Status": "Renamed", "New Name": new_file_name})

        # Record that this file has been processed.
        organizer.progress_tracker.record_progress(
            progress_f, filename, organizer.file_manager
        )
        return True

    except (ValueError, OSError, FileNotFoundError) as e:
        error_msg = f"Error with file {filename}: {str(e)}"
        print(f"\\n{error_msg}")
        try:
            if os.path.exists(input_path):
                unprocessed_path = os.path.join(unprocessed_folder, filename)
                organizer.file_manager.safe_move(input_path, unprocessed_path)
                pbar.set_postfix(
                    {"Status": "Unprocessed", "Moved to": unprocessed_folder}
                )
            else:
                pbar.set_postfix({"Status": "Error", "Message": "File not found"})

            # Progress recording is already handled in success path above
        except OSError as move_error:
            pbar.set_postfix({"Status": "Error", "Message": str(move_error)})
        
        # Record progress once for error case
        organizer.progress_tracker.record_progress(
            progress_f, filename, organizer.file_manager
        )
        return False
    except RuntimeError as e:
        error_msg = f"Unexpected error with file {filename}: {str(e)}"
        print(f"\\n{error_msg}")
        try:
            with open(ERROR_LOG_FILE, mode="a", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\\n")
        except (IOError, OSError) as log_error:
            print(f"Warning: Could not write to error log: {str(log_error)}")
        pbar.set_postfix({"Status": "Error", "Message": "Unexpected error"})
        return False

    pbar.update(1)
    return True


def pdfs_to_text_string(filepath: str, max_pages: Optional[int] = None) -> str:
    """
    Legacy function for extracting text, kept for compatibility.
    """
    try:
        from content_processors import PDFProcessor
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from content_processors import PDFProcessor
    processor = PDFProcessor()
    if processor.can_process(filepath):
        text, _ = processor.extract_content(filepath)
        return text
    return ""