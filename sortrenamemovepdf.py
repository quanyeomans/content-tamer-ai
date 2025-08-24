"""
Document processing and organization system with AI-powered filename generation.
"""

import os
import time
import sys
import argparse
import json
import datetime as dt
from openai import OpenAI, APIError
from tqdm import tqdm
import requests
from typing import Any, Optional, List, Tuple


def _print_capabilities(ocr_lang: str):
    """Prints the status of optional dependencies."""
    from content_processors import HAVE_PYMUPDF, HAVE_TESSERACT, OCR_PAGES, OCR_ZOOM
    pymupdf_status = "yes" if HAVE_PYMUPDF else "no"
    tesseract_status = "yes" if HAVE_TESSERACT else "no"
    print(
        f"OCR deps -> PyMuPDF: {pymupdf_status}, Tesseract: {tesseract_status}; "
        f"OCR_LANG={ocr_lang}, OCR_PAGES={OCR_PAGES}, OCR_ZOOM={OCR_ZOOM}"
    )


# Import modules
from ai_providers import AIProviderFactory, AI_PROVIDERS, DEFAULT_MODELS
from content_processors import ContentProcessorFactory
from file_organizer import FileOrganizer, ProgressTracker, FilenameHandler
from utils.text_utils import truncate_content_to_token_limit


# -----------------------------
# Global constants
# -----------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2

ERROR_LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pdf_processing_errors.log"
)


# This tells Tesseract which language to look for in the document.
OCR_LANG = "eng"

# This will hold the AI client instance once it's initialized.
AI_CLIENT = None


# -----------------------------
# Core Logic and File Operations
# -----------------------------
def get_api_details(provider: str, model: str):
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


def sort_and_rename_pdfs(
    input_dir,
    corrupted_dir,
    renamed_dir,
    provider="openai",
    model=None,
    reset_progress: bool = False,
    ocr_lang: str = "eng",
):
    """The main function that orchestrates the PDF processing workflow."""
    if not os.path.exists(input_dir):
        print(f"Error: Input folder '{input_dir}' does not exist.")
        return False

    if model is None:
        model = AIProviderFactory.get_default_model(provider)

    try:
        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)
    except (ValueError, ImportError) as e:
        print(f"Error setting up AI client: {e}")
        return False

    # Initialize file organizer
    organizer = FileOrganizer()
    organizer.create_directories(corrupted_dir, renamed_dir)

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
        print(f"No processable files found in {input_dir}")
        print(f"Supported extensions: {', '.join(supported_extensions)}")
        return True

    progress_file = os.path.join(renamed_dir, ".progress")
    processed_files = organizer.progress_tracker.load_progress(progress_file, input_dir, reset_progress)

    try:
        with open(progress_file, "a", encoding="utf-8") as progress_f, tqdm(
            total=total_files, desc="Processing Files", unit="file"
        ) as pbar:
            for filename in processable_files:
                if filename in processed_files:
                    pbar.update(1)
                    continue

                input_path = os.path.normpath(os.path.join(input_dir, filename))
                if not os.path.exists(input_path):
                    print(f"\nWarning: File {filename} no longer exists, skipping.")
                    pbar.update(1)
                    continue

                process_file(
                    input_path,
                    filename,
                    corrupted_dir,
                    renamed_dir,
                    pbar,
                    progress_f,
                    ocr_lang,
                    ai_client,
                    organizer,
                )
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Progress has been saved.")
    except IOError as e:
        print(f"\nError writing to progress file: {e}")
        return False

    return True


def process_file(
    input_path,
    filename,
    corrupted_folder,
    renamed_folder,
    pbar,
    progress_f,
    ocr_lang: str,
    ai_client: Any,
    organizer: FileOrganizer,
):
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

        # If the extractor returned an error message, treat it as a corrupted file.
        if text.startswith("Error"):
            raise ValueError(text)

        # If the PDF is empty (no text or image), give it a generic name.
        if not text and not img_b64:
            timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"empty_file_{timestamp}"
        else:
            # Get a new filename from the AI, with retries in case of network issues.
            new_file_name = get_new_filename_with_retry(ai_client, text, img_b64)
            new_file_name = organizer.filename_handler.validate_and_trim_filename(new_file_name)

        # Move the file to the renamed folder with proper extension handling
        file_extension = os.path.splitext(input_path)[1]
        new_file_name = organizer.move_file_to_category(
            input_path, filename, renamed_folder, new_file_name, file_extension
        )
        pbar.set_postfix({"Status": "Renamed", "New Name": new_file_name})

        # Record that this file has been processed.
        organizer.progress_tracker.record_progress(progress_f, filename, organizer.file_manager)

    except (ValueError, OSError, FileNotFoundError) as e:
        error_msg = f"Error with file {filename}: {str(e)}"
        print(f"\n{error_msg}")
        try:
            if os.path.exists(input_path):
                corrupted_path = os.path.join(corrupted_folder, filename)
                organizer.file_manager.safe_move(input_path, corrupted_path)
                pbar.set_postfix({"Status": "Corrupted", "Moved to": corrupted_folder})
            else:
                pbar.set_postfix({"Status": "Error", "Message": "File not found"})

            organizer.progress_tracker.record_progress(progress_f, filename, organizer.file_manager)
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
            "AI client not initialized. Call sort_and_rename_pdfs first."
        )
    return ai_client.generate_filename(pdf_content, image_b64)


def pdfs_to_text_string(filepath: str, max_pages: Optional[int] = None) -> str:
    """A legacy function for extracting text, kept for compatibility."""
    from content_processors import PDFProcessor
    processor = PDFProcessor()
    if processor.can_process(filepath):
        text, _ = processor.extract_content(filepath)
        return text
    return ""


def list_available_models():
    """Prints a list of all AI models supported by the script, grouped by provider."""
    print("Available AI models by provider:")
    for provider, models in AIProviderFactory.list_providers().items():
        print(f"\n{provider.capitalize()}:")
        for model in models:
            print(f"  - {model}")


def parse_arguments():
    """Sets up and parses the command-line arguments that the script accepts."""
    parser = argparse.ArgumentParser(
        description="Sort and rename PDF files based on their content",
        epilog="""
Examples:
  # Use default OpenAI model
  python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed

  # Use GPT-4o
  python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-4o
  
  # Use Claude
  python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p claude -m claude-3-sonnet
  
  # List all available models
  python sortrenamemovepdf.py --list-models
""",
    )
    parser.add_argument("--input", "-i", help="Input folder containing PDF files")
    parser.add_argument("--corrupted", "-c", help="Folder for corrupted PDF files")
    parser.add_argument("--renamed", "-r", help="Folder for renamed PDF files")
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
    return parser.parse_args()

def main():
    """Main function to parse arguments and run the PDF processing."""
    try:
        # This block runs when the script is executed directly from the command line.
        args = parse_arguments()
        # Set the OCR language from the command-line argument.
        _print_capabilities(args.ocr_lang)

        # If the user just wants to see the available models, print them and exit.
        if args.list_models:
            list_available_models()
            sys.exit(0)

        # Temporarily set the API key from the command line if provided.
        original_env = None
        api_key_set = False

        try:
            if args.api_key:
                env_var = f"{args.provider.upper()}_API_KEY"
                original_env = (env_var, os.environ.get(env_var))
                os.environ[env_var] = args.api_key
                api_key_set = True
                print(f"Using provided {args.provider.capitalize()} API key")

            # Get the folder paths from the arguments, or ask the user if not provided.
            input_dir = args.input or input("Enter the input folder path: ")
            corrupted_dir = args.corrupted or input(
                "Enter the corrupted PDFs folder path: "
            )
            renamed_dir = args.renamed or input("Enter the renamed PDFs folder path: ")

            # Start the main PDF processing task.
            success = sort_and_rename_pdfs(
                input_dir,
                corrupted_dir,
                renamed_dir,
                args.provider,
                args.model,
                reset_progress=args.reset_progress,
                ocr_lang=args.ocr_lang,
            )

            if not success:
                print("PDF sorting and renaming failed.")
                return 1
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