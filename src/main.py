"""
Document processing and organization system with AI-powered filename generation.
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
from typing import Any, List, Optional, Tuple, Union

import requests
from openai import APIError, OpenAI
from tqdm import tqdm


def _print_capabilities(ocr_lang: str) -> None:
    """Prints the status of optional dependencies."""
    try:
        from .content_processors import (
            HAVE_PYMUPDF,
            HAVE_TESSERACT,
            OCR_PAGES,
            OCR_ZOOM,
        )
    except ImportError:
        from content_processors import HAVE_PYMUPDF, HAVE_TESSERACT, OCR_PAGES, OCR_ZOOM
    pymupdf_status = "yes" if HAVE_PYMUPDF else "no"
    tesseract_status = "yes" if HAVE_TESSERACT else "no"
    print(
        f"OCR deps -> PyMuPDF: {pymupdf_status}, Tesseract: {tesseract_status}; "
        f"OCR_LANG={ocr_lang}, OCR_PAGES={OCR_PAGES}, OCR_ZOOM={OCR_ZOOM}"
    )


# Import modules - handle both package and direct execution
try:
    # Package import (when run as module)
    from .ai_providers import AI_PROVIDERS, DEFAULT_MODELS, AIProviderFactory
    from .content_processors import ContentProcessorFactory
    from .file_organizer import FilenameHandler, FileOrganizer, ProgressTracker
    from .utils.text_utils import truncate_content_to_token_limit
    from .utils.display_manager import DisplayManager, DisplayOptions
except ImportError:
    # Direct import (when run as script)
    from ai_providers import AI_PROVIDERS, DEFAULT_MODELS, AIProviderFactory
    from content_processors import ContentProcessorFactory
    from file_organizer import FilenameHandler, FileOrganizer, ProgressTracker
    from utils.text_utils import truncate_content_to_token_limit
    from utils.display_manager import DisplayManager, DisplayOptions


# -----------------------------
# Global constants
# -----------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2

# Default folder structure - go up one level from src/ to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DOCUMENTS_DIR = os.path.join(PROJECT_ROOT, "documents")
DEFAULT_INPUT_DIR = os.path.join(DEFAULT_DOCUMENTS_DIR, "input")
DEFAULT_PROCESSED_DIR = os.path.join(DEFAULT_DOCUMENTS_DIR, "processed")
DEFAULT_UNPROCESSED_DIR = os.path.join(DEFAULT_PROCESSED_DIR, "unprocessed")
DEFAULT_PROCESSING_DIR = os.path.join(DEFAULT_DOCUMENTS_DIR, ".processing")

ERROR_LOG_FILE = os.path.join(DEFAULT_PROCESSING_DIR, "errors.log")


# This tells Tesseract which language to look for in the document.
OCR_LANG = "eng"

# This will hold the AI client instance once it's initialized.
AI_CLIENT = None


# -----------------------------
# Core Logic and File Operations
# -----------------------------
def ensure_default_directories() -> tuple[str, str, str]:
    """Creates the default directory structure if it doesn't exist."""
    directories = [
        DEFAULT_DOCUMENTS_DIR,
        DEFAULT_INPUT_DIR,
        DEFAULT_PROCESSED_DIR,
        DEFAULT_UNPROCESSED_DIR,
        DEFAULT_PROCESSING_DIR,
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    return DEFAULT_INPUT_DIR, DEFAULT_PROCESSED_DIR, DEFAULT_UNPROCESSED_DIR


def get_api_details(provider: str, model: str) -> str:
    """Gets the API key from environment variables or prompts the user for it."""
    if provider not in AI_PROVIDERS:
        available_providers = ", ".join(AI_PROVIDERS.keys())
        raise ValueError(
            f"Unsupported provider '{provider}'. Available providers: {available_providers}"
        )

    env_var_name = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    if not api_key:
        api_key = input(f"Please enter your {provider.capitalize()} API key: ").strip()
        if not api_key:
            raise ValueError(f"{provider.capitalize()} API key is required.")

    if model not in AI_PROVIDERS.get(provider, []):
        available_models = ", ".join(
            AI_PROVIDERS.get(provider, ["No models available"])
        )
        raise ValueError(
            f"Invalid model '{model}' for provider '{provider}'. Available models: {available_models}"
        )

    return api_key


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
    display_opts = display_options or {}
    display_manager = DisplayManager(DisplayOptions(
        verbose=display_opts.get('verbose', False),
        quiet=display_opts.get('quiet', False),
        no_color=display_opts.get('no_color', False),
        show_stats=display_opts.get('show_stats', True)
    ))
    
    # Validate input directory
    if not os.path.exists(input_dir):
        display_manager.critical(f"Input folder '{input_dir}' does not exist.")
        return False

    # Setup AI client
    try:
        if model is None:
            model = AIProviderFactory.get_default_model(provider)
        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)
        
        display_manager.info(f"Using {provider} provider with model {model}")
    except (ValueError, ImportError) as e:
        display_manager.critical(f"Error setting up AI client: {e}")
        return False

    # Initialize file organizer
    organizer = FileOrganizer()
    organizer.create_directories(unprocessed_dir, renamed_dir)

    # Show startup information
    display_manager.show_startup_info({
        "directories": {
            "input": input_dir,
            "processed": renamed_dir,
            "unprocessed": unprocessed_dir
        }
    })

    # Get content processor factory to check supported file types
    content_factory = ContentProcessorFactory(ocr_lang)
    supported_extensions = content_factory.get_supported_extensions()

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

    # Enhanced processing with display manager
    try:
        with open(progress_file, "a", encoding="utf-8") as progress_f:
            with display_manager.processing_context(
                total_files=total_files, 
                description="Processing Files"
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
                    )
                    
                    if success and new_filename:
                        ctx.complete_file(filename, new_filename)
                    elif not success:
                        ctx.fail_file(filename, "Processing failed")
                    else:
                        ctx.complete_file(filename, "processed")

    except KeyboardInterrupt:
        display_manager.warning("Process interrupted by user. Progress has been saved.")
        return True  # Not a failure - user choice
    except IOError as e:
        display_manager.critical(f"Error writing to progress file: {e}")
        return False

    # Show completion statistics
    display_manager.show_completion_stats({
        "total_files": total_files,
        "successful": total_files,  # Will be updated with actual stats in future enhancement
    })
    
    return True



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
    """Processes a single file: extracts content, gets a new name, and moves the file."""
    try:
        if not os.path.isfile(input_path):
            pass

        # Extract content using appropriate processor
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

    except (ValueError, OSError, FileNotFoundError) as e:
        error_msg = f"Error with file {filename}: {str(e)}"
        print(f"\n{error_msg}")
        try:
            if os.path.exists(input_path):
                unprocessed_path = os.path.join(unprocessed_folder, filename)
                organizer.file_manager.safe_move(input_path, unprocessed_path)
                pbar.set_postfix(
                    {"Status": "Unprocessed", "Moved to": unprocessed_folder}
                )
            else:
                pbar.set_postfix({"Status": "Error", "Message": "File not found"})

            organizer.progress_tracker.record_progress(
                progress_f, filename, organizer.file_manager
            )
        except OSError as move_error:
            pbar.set_postfix({"Status": "Error", "Message": str(move_error)})
    except RuntimeError as e:
        error_msg = f"Unexpected error with file {filename}: {str(e)}"
        print(f"\n{error_msg}")
        try:
            with open(ERROR_LOG_FILE, mode="a", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\n")
        except (IOError, OSError) as log_error:
            print(f"Warning: Could not write to error log: {str(log_error)}")
        pbar.set_postfix({"Status": "Error", "Message": "Unexpected error"})

    pbar.update(1)


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
) -> Tuple[bool, Optional[str]]:
    """Enhanced file processing with integrated display updates."""
    try:
        if not os.path.isfile(input_path):
            display_context.show_error(f"File not found: {input_path}")
            return False, None

        # Extract content using appropriate processor
        display_context.set_status("extracting_content")
        content_factory = ContentProcessorFactory(ocr_lang)
        processor = content_factory.get_processor(input_path)
        if not processor:
            raise ValueError(f"Unsupported file type: {input_path}")

        text, img_b64 = processor.extract_content(input_path)

        # If the extractor returned an error message, treat it as an unprocessable file.
        if text.startswith("Error"):
            raise ValueError(text)

        # If the file is empty (no text or image), give it a generic name.
        if not text and not img_b64:
            display_context.show_warning("File appears to be empty")
            display_context.set_status("generating_filename")
            timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"empty_file_{timestamp}"
        else:
            # Get a new filename from the AI, with retries in case of network issues.
            display_context.set_status("generating_filename")
            new_file_name = get_new_filename_with_retry_enhanced(
                ai_client, text, img_b64, display_context
            )
            new_file_name = organizer.filename_handler.validate_and_trim_filename(
                new_file_name
            )

        # Move the file to the renamed folder with proper extension handling
        display_context.set_status("moving_file")
        file_extension = os.path.splitext(input_path)[1]
        final_file_name = organizer.move_file_to_category(
            input_path, filename, renamed_folder, new_file_name, file_extension
        )

        # Record that this file has been processed.
        organizer.progress_tracker.record_progress(
            progress_f, filename, organizer.file_manager
        )

        return True, final_file_name

    except (ValueError, OSError, FileNotFoundError) as e:
        error_msg = f"Error processing {filename}: {str(e)}"
        display_context.show_error(error_msg)
        
        try:
            if os.path.exists(input_path):
                unprocessed_path = os.path.join(unprocessed_folder, filename)
                organizer.file_manager.safe_move(input_path, unprocessed_path)
                display_context.show_warning(f"Moved to unprocessed folder")
            
            organizer.progress_tracker.record_progress(
                progress_f, filename, organizer.file_manager
            )
        except OSError as move_error:
            display_context.show_error(f"Failed to move file: {str(move_error)}")

        return False, None
        
    except RuntimeError as e:
        error_msg = f"Unexpected error with file {filename}: {str(e)}"
        display_context.show_error(error_msg)
        
        try:
            with open(ERROR_LOG_FILE, mode="a", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\n")
        except (IOError, OSError) as log_error:
            display_context.show_warning(f"Could not write to error log: {str(log_error)}")

        return False, None


def get_new_filename_with_retry_enhanced(
    ai_client: Any,
    pdf_content: str,
    image_b64: Optional[str] = None,
    display_context: Any = None,
    max_retries: int = MAX_RETRIES,
) -> str:
    """Enhanced filename retry with display integration."""
    timeout_count = 0
    for attempt in range(max_retries):
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
                wait_time = RETRY_DELAY * (attempt + 1)  # Linear backoff
                if display_context:
                    display_context.show_warning(
                        f"API error: {str(e)}. Retrying in {wait_time} seconds..."
                    )

            time.sleep(wait_time)

            if attempt == max_retries - 1:
                if display_context:
                    display_context.show_error(
                        f"Failed to get filename from API after {max_retries} attempts"
                    )
                timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                if timeout_count > 0:
                    return f"network_error_{timestamp}"
                else:
                    return f"untitled_document_{timestamp}"


def get_new_filename_with_retry(
    ai_client: Any,
    pdf_content: str,
    image_b64: Optional[str] = None,
    max_retries: int = MAX_RETRIES,
) -> str:
    """Calls the AI to get a filename, and retries if it fails."""
    timeout_count = 0
    for attempt in range(max_retries):
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
                wait_time = RETRY_DELAY * (
                    2**timeout_count
                )  # Use exponential backoff for network issues.
                print(
                    f"\nAPI timeout/network error: {str(e)}. Retrying in {wait_time} seconds..."
                )
            else:
                wait_time = RETRY_DELAY * (
                    attempt + 1
                )  # Use linear backoff for other errors.
                print(f"\nAPI error: {str(e)}. Retrying in {wait_time} seconds...")

            time.sleep(wait_time)

            if attempt == max_retries - 1:
                print(
                    f"\nFailed to get filename from API after {max_retries} attempts."
                )
                timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                if timeout_count > 0:
                    return f"network_error_{timestamp}"
                else:
                    return f"untitled_document_{timestamp}"


def get_filename_from_ai(
    ai_client: Any, pdf_content: str, image_b64: Optional[str] = None
) -> str:
    if ai_client is None:
        raise RuntimeError(
            "AI client not initialized. Call organize_content first."
        )
    return ai_client.generate_filename(pdf_content, image_b64)


def pdfs_to_text_string(filepath: str, max_pages: Optional[int] = None) -> str:
    """A legacy function for extracting text, kept for compatibility."""
    try:
        from .content_processors import PDFProcessor
    except ImportError:
        from content_processors import PDFProcessor
    processor = PDFProcessor()
    if processor.can_process(filepath):
        text, _ = processor.extract_content(filepath)
        return text
    return ""


def list_available_models() -> None:
    """Prints a list of all AI models supported by the script, grouped by provider."""
    print("Available AI models by provider:")
    for provider, models in AIProviderFactory.list_providers().items():
        print(f"\n{provider.capitalize()}:")
        for model in models:
            print(f"  - {model}")


def parse_arguments():
    """Sets up and parses the command-line arguments that the script accepts."""
    parser = argparse.ArgumentParser(
        description="Content Tamer AI - Organize documents with intelligent AI-powered filename generation",
        epilog="""
Examples:
  # Process documents using defaults (documents/input -> documents/processed)
  content-tamer-ai

  # Use specific AI provider and model
  content-tamer-ai -p openai -m gpt-4o

  # Use custom folders for organization
  content-tamer-ai -i ./my-documents -r ./organized -u ./needs-review

  # List all available AI models
  content-tamer-ai --list-models
""",
    )
    parser.add_argument(
        "--input",
        "-i",
        help=f"Input folder containing documents to organize (PDFs, images, screenshots) (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--unprocessed",
        "-u",
        help=f"Folder for files that could not be processed (default: {DEFAULT_UNPROCESSED_DIR})",
    )
    parser.add_argument(
        "--renamed",
        "-r",
        help=f"Folder for organized documents with AI-generated names (default: {DEFAULT_PROCESSED_DIR})",
    )
    parser.add_argument(
        "--provider",
        "-p",
        help=f"AI provider (options: {', '.join(AI_PROVIDERS.keys())})",
        default="openai",
        choices=AI_PROVIDERS.keys(),
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Model to use for the selected provider (run with --list-models to see options)",
    )
    parser.add_argument("--api-key", "-k", help="API key for the selected provider")
    parser.add_argument(
        "--list-models",
        "-l",
        action="store_true",
        help="List all available models by provider and exit",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="Tesseract OCR language hint (e.g., 'eng', 'eng+ind')",
    )
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Ignore and delete existing .progress file before run",
    )
    
    # Display options
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output (progress bar only, suppress info and success messages)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Detailed logging output (show debug messages and additional info)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output (useful for CI/CD or when output is redirected)",
    )
    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="Disable statistics display in progress bar",
    )
    
    return parser.parse_args()


def main() -> int:
    """Main function to parse arguments and run intelligent document organization."""
    try:
        # This block runs when the script is executed directly from the command line.
        args = parse_arguments()
        # Set the OCR language from the command-line argument.
        if not args.quiet:
            _print_capabilities(args.ocr_lang)

        # If the user just wants to see the available models, print them and exit.
        if args.list_models:
            list_available_models()
            sys.exit(0)

        # Temporarily set the API key from the command line if provided.
        original_env = None
        api_key_set = False

        try:
            # Setup display options
            display_options = {
                'verbose': args.verbose,
                'quiet': args.quiet,
                'no_color': args.no_color,
                'show_stats': not args.no_stats,
            }
            
            if args.api_key:
                env_var = f"{args.provider.upper()}_API_KEY"
                original_env = (env_var, os.environ.get(env_var))
                os.environ[env_var] = args.api_key
                api_key_set = True
                # Use enhanced display for API key message
                if not args.quiet:
                    print(f"Using provided {args.provider.capitalize()} API key")

            # Get the folder paths from the arguments, or use defaults
            if args.input or args.renamed or args.unprocessed:
                # User specified custom paths
                input_dir = args.input or input("Enter the input folder path: ")
                renamed_dir = args.renamed or input(
                    "Enter the renamed PDFs folder path: "
                )
                unprocessed_dir = args.unprocessed or input(
                    "Enter the unprocessed files folder path: "
                )
            else:
                # Use default directory structure
                if not args.quiet:
                    print("Using default directory structure:")
                input_dir, renamed_dir, unprocessed_dir = ensure_default_directories()
                if not args.quiet:
                    print(f"  Input: {input_dir}")
                    print(f"  Processed: {renamed_dir}")
                    print(f"  Unprocessed: {unprocessed_dir}")

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
            if api_key_set and original_env:
                try:
                    env_var, original_value = original_env
                    if original_value is None:
                        os.environ.pop(env_var, None)
                    else:
                        os.environ[env_var] = original_value
                except (KeyError, TypeError):
                    print("Warning: Could not restore original API key environment.")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        return 130  # Standard exit code for a process stopped with Ctrl+C.
    except (ValueError, ImportError) as e:
        print(f"\nConfiguration error: {e}")
        return 1
    except Exception as e:
        print(f"\nCritical error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
