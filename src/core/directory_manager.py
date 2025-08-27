"""
Content Tamer AI - Directory Management

Handles directory setup, validation, and default structure creation.
"""

import os
import re
from typing import Tuple

# Directory structure constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DEFAULT_INPUT_DIR = os.path.join(DEFAULT_DATA_DIR, "input")
DEFAULT_PROCESSED_DIR = os.path.join(DEFAULT_DATA_DIR, "processed")
DEFAULT_UNPROCESSED_DIR = os.path.join(DEFAULT_PROCESSED_DIR, "unprocessed")
DEFAULT_PROCESSING_DIR = os.path.join(DEFAULT_DATA_DIR, ".processing")

# Error log location
ERROR_LOG_FILE = os.path.join(DEFAULT_PROCESSING_DIR, "errors.log")


def ensure_default_directories() -> Tuple[str, str, str]:
    """Creates the default directory structure if it doesn't exist."""
    directories = [
        DEFAULT_DATA_DIR,
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
    """
    Gets the API key from environment variables or prompts the user securely.
    
    Args:
        provider: AI provider name (openai, claude, etc.)
        model: Model name to validate
        
    Returns:
        Validated API key
        
    Raises:
        ValueError: If provider/model invalid or API key invalid
    """
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
        # Use regular input with immediate feedback
        print(f"\nAPI Key Input:")
        print(f"• Type or paste your API key (you'll see it as you type)")
        print(f"• {provider.capitalize()} keys start with '{'sk-ant-' if provider == 'claude' else 'sk-'}' and are typically 40-60 characters")
        print(f"• You can set {provider.upper()}_API_KEY environment variable to skip this step")
        print(f"• Your key will be validated and cleared from display after entry")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    print(f"\nAttempt {attempt + 1} of {max_attempts}")
                
                api_key = input(
                    f"\nEnter your {provider.capitalize()} API key: "
                ).strip()
                
                # Clean up common paste issues
                if api_key:
                    # Remove all whitespace, newlines, and common paste artifacts
                    api_key = ''.join(api_key.split())
                    # Remove common quotes that might get copied
                    api_key = api_key.strip('"\'`')
                
                # Provide user feedback about the input received
                if api_key:
                    # Show partial key for user verification (first 10, last 4 characters)
                    if len(api_key) >= 14:
                        partial_display = f"{api_key[:10]}{'*' * max(0, len(api_key) - 14)}{api_key[-4:]}"
                    else:
                        partial_display = f"{api_key[:min(6, len(api_key))]}{'*' * max(0, len(api_key) - 6)}"
                    
                    print(f"[OK] Received API key: {partial_display} ({len(api_key)} characters)")
                    if len(api_key) < 20:
                        print(f"[WARNING] Key seems short for {provider.capitalize()} (got {len(api_key)} chars, expected 40+)")
                    
                    # Try validation
                    try:
                        validated_key = _validate_api_key(api_key, provider)
                        print("[OK] API key format validated successfully")
                        
                        # Clear the screen to remove visible API key
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"[OK] {provider.capitalize()} API key accepted and secured.")
                        
                        return validated_key
                    except ValueError as e:
                        print(f"[ERROR] Validation failed: {e}")
                        if attempt < max_attempts - 1:
                            print("Please try again...")
                            continue
                        else:
                            raise
                else:
                    print("[ERROR] No input received")
                    if attempt < max_attempts - 1:
                        print("Please try again...")
                        continue
                    else:
                        raise ValueError(f"{provider.capitalize()} API key is required.")
                        
            except (KeyboardInterrupt, EOFError):
                raise ValueError("API key entry cancelled by user.")
        
        # If we get here, all attempts failed
        raise ValueError(f"Failed to get valid API key after {max_attempts} attempts.")

    # For API keys from environment variables, still validate
    return _validate_api_key(api_key, provider)


def _validate_api_key(api_key: str, provider: str) -> str:
    """
    Validate API key format and security.
    
    Args:
        api_key: API key to validate
        provider: Provider name for validation rules
        
    Returns:
        Validated API key
        
    Raises:
        ValueError: If API key is invalid or insecure
    """
    # Basic security checks
    if len(api_key) < 10:
        raise ValueError(
            f"{provider.capitalize()} API key appears to be too short ({len(api_key)} characters). "
            f"Expected format: OpenAI keys start with 'sk-' and are ~51 characters long. "
            f"Please check your paste was successful and try again."
        )
    
    if len(api_key) > 512:
        raise ValueError(f"{provider.capitalize()} API key appears to be too long ({len(api_key)} characters).")
    
    # Check for obviously fake or test keys
    test_patterns = [
        r'^(test|fake|dummy|placeholder)',
        r'^(sk-)?1{10,}',  # All 1s
        r'^(sk-)?0{10,}',  # All 0s
        r'password|secret|key|token',  # Contains obvious words
    ]
    
    for pattern in test_patterns:
        if re.match(pattern, api_key, re.IGNORECASE):
            raise ValueError(
                f"API key appears to be a placeholder or test value. Please use a real {provider.capitalize()} API key."
            )
    
    # Provider-specific validation
    if provider == "openai":
        if not api_key.startswith('sk-'):
            raise ValueError("OpenAI API keys must start with 'sk-'")
        if len(api_key) < 20:
            raise ValueError("OpenAI API key format appears invalid")
    
    elif provider == "claude":
        if not api_key.startswith('sk-ant-'):
            raise ValueError("Claude API keys must start with 'sk-ant-'")
        if len(api_key) < 20:
            raise ValueError("Claude API key format appears invalid")
    
    # Check for suspicious characters that might indicate injection attempts
    # Allow common API key characters: letters, numbers, hyphens, underscores, dots, plus signs
    if not re.match(r'^[a-zA-Z0-9\-_.+]+$', api_key):
        # Show what characters were found for debugging
        invalid_chars = set(re.findall(r'[^a-zA-Z0-9\-_.+]', api_key))
        raise ValueError(f"API key contains invalid characters: {sorted(invalid_chars)}")
    
    return api_key