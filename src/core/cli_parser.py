"""
Content Tamer AI - Command Line Interface Parser

Handles command line argument parsing, validation, and expert mode integration.
"""

import argparse
import os
import sys
from typing import Any

try:
    from utils.expert_mode import prompt_expert_mode_if_needed
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.expert_mode import prompt_expert_mode_if_needed


# Import AI providers for validation
try:
    from ai_providers import AI_PROVIDERS, AIProviderFactory
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ai_providers import AI_PROVIDERS, AIProviderFactory

# Default directories
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DEFAULT_INPUT_DIR = os.path.join(DEFAULT_DATA_DIR, "input")
DEFAULT_PROCESSED_DIR = os.path.join(DEFAULT_DATA_DIR, "processed")


def parse_arguments():
    """Sets up and parses the command-line arguments that the script accepts."""
    parser = argparse.ArgumentParser(
        description="Content Tamer AI - Organize documents with intelligent AI-powered filename generation",
        epilog="""
Examples:
  # Process documents using defaults (data/input -> data/processed)
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
    # Note: Unprocessed folder is now automatically created within processed folder
    # Keeping argument for backward compatibility but marking as advanced/deprecated
    parser.add_argument(
        "--unprocessed",
        "-u",
        help="[ADVANCED] Custom location for unprocessed files (default: auto-created within processed folder)",
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
        help="Self-contained mode: one-line stats output, no user prompts. Requires API key and folders as parameters.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Default mode with guided menus, auto-detecting unicode support for rich or basic UI",
    )

    return parser.parse_args()


def list_available_models() -> None:
    """Prints a list of all AI models supported by the script, grouped by provider."""
    print("Available AI models by provider:")
    for provider, models in AIProviderFactory.list_providers().items():
        print(f"\n{provider.capitalize()}:")
        for model in models:
            print(f"  - {model}")


def _print_capabilities(ocr_lang: str) -> None:
    """Prints the status of optional dependencies."""
    # Import needed constants locally to avoid redefinition issues
    try:
        from content_processors import HAVE_PYMUPDF as _HAVE_PYMUPDF
        from content_processors import HAVE_TESSERACT as _HAVE_TESSERACT
        from content_processors import OCR_PAGES as _OCR_PAGES
        from content_processors import OCR_ZOOM as _OCR_ZOOM
    except ImportError:
        import os
        import sys

        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from content_processors import HAVE_PYMUPDF as _HAVE_PYMUPDF
        from content_processors import HAVE_TESSERACT as _HAVE_TESSERACT
        from content_processors import OCR_PAGES as _OCR_PAGES
        from content_processors import OCR_ZOOM as _OCR_ZOOM
    pymupdf_status = "yes" if _HAVE_PYMUPDF else "no"
    tesseract_status = "yes" if _HAVE_TESSERACT else "no"
    print(
        f"OCR deps -> PyMuPDF: {pymupdf_status}, Tesseract: {tesseract_status}; "
        f"OCR_LANG={ocr_lang}, OCR_PAGES={_OCR_PAGES}, OCR_ZOOM={_OCR_ZOOM}"
    )


def setup_environment_and_args():
    """Setup expert mode and parse command line arguments."""
    # Handle expert mode prompting (only if no CLI args provided)
    expert_args = prompt_expert_mode_if_needed()
    if expert_args:
        # Modify sys.argv to include expert mode arguments
        sys.argv.extend(expert_args)

    # Parse arguments (including any expert mode additions)
    args = parse_arguments()

    # Set the OCR language from the command-line argument.
    if not args.quiet:
        _print_capabilities(args.ocr_lang)

    # If the user just wants to see the available models, print them and exit.
    if args.list_models:
        list_available_models()
        sys.exit(0)

    return args


def setup_api_key(args) -> tuple:
    """Setup API key from command line arguments."""
    original_env = None
    api_key_set = False

    if args.api_key:
        env_var = f"{args.provider.upper()}_API_KEY"
        original_env = (env_var, os.environ.get(env_var))
        os.environ[env_var] = args.api_key
        api_key_set = True
        # Use enhanced display for API key message
        if not args.quiet:
            print(f"Using provided {args.provider.capitalize()} API key")

    return original_env, api_key_set


def restore_api_key(api_key_set: bool, original_env: tuple) -> None:
    """Restore original API key environment variable."""
    if api_key_set and original_env:
        try:
            env_var, original_value = original_env
            if original_value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = original_value
        except (KeyError, TypeError):
            print("Warning: Could not restore original API key environment.")
