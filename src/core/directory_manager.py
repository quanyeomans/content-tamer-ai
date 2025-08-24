"""
Content Tamer AI - Directory Management

Handles directory setup, validation, and default structure creation.
"""

import os
from typing import Tuple

# Directory structure constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DOCUMENTS_DIR = os.path.join(PROJECT_ROOT, "documents")
DEFAULT_INPUT_DIR = os.path.join(DEFAULT_DOCUMENTS_DIR, "input")
DEFAULT_PROCESSED_DIR = os.path.join(DEFAULT_DOCUMENTS_DIR, "processed")
DEFAULT_UNPROCESSED_DIR = os.path.join(DEFAULT_PROCESSED_DIR, "unprocessed")
DEFAULT_PROCESSING_DIR = os.path.join(DEFAULT_DOCUMENTS_DIR, ".processing")

# Error log location
ERROR_LOG_FILE = os.path.join(DEFAULT_PROCESSING_DIR, "errors.log")


def ensure_default_directories() -> Tuple[str, str, str]:
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


def setup_directories(args) -> Tuple[str, str, str]:
    """Setup input/output directories from arguments or defaults."""
    # Get the folder paths from the arguments, or use defaults
    if args.input or args.renamed or args.unprocessed:
        # User specified custom paths
        input_dir = args.input or input("Enter the input folder path: ")
        renamed_dir = args.renamed or input("Enter the renamed PDFs folder path: ")
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

    return input_dir, renamed_dir, unprocessed_dir


def get_api_details(provider: str, model: str) -> str:
    """Gets the API key from environment variables or prompts the user for it."""
    # Import here to avoid circular imports
    try:
        from ai_providers import AI_PROVIDERS
    except ImportError:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from ai_providers import AI_PROVIDERS
        
    if provider not in AI_PROVIDERS:
        available_providers = ", ".join(AI_PROVIDERS.keys())
        raise ValueError(
            f"Unsupported provider '{provider}'. Available providers: {available_providers}"
        )
    
    # Validate model for the given provider
    if model not in AI_PROVIDERS[provider]:
        available_models = ", ".join(AI_PROVIDERS[provider])
        raise ValueError(
            f"Invalid model '{model}' for provider '{provider}'. Available models: {available_models}"
        )

    env_var_name = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    if not api_key:
        api_key = input(f"Please enter your {provider.capitalize()} API key: ").strip()
        if not api_key:
            raise ValueError(f"{provider.capitalize()} API key is required.")

    # Basic validation - allow test keys to be shorter
    if len(api_key) < 5:
        raise ValueError(f"{provider.capitalize()} API key appears to be too short.")

    return api_key