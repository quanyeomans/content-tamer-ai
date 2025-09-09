"""
Content Tamer AI - Directory Management

Handles directory setup, validation, and default structure creation.
"""

import os
import re
import subprocess
import sys
from typing import Tuple

# Import centralized path management
from .path_utilities import get_default_directories, get_project_root

# Use centralized directory structure constants
PROJECT_ROOT = get_project_root()
(
    DEFAULT_DATA_DIR,
    DEFAULT_INPUT_DIR,
    DEFAULT_PROCESSED_DIR,
    DEFAULT_PROCESSING_DIR,
    DEFAULT_UNPROCESSED_DIR,
) = get_default_directories()

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
            try:
                from interfaces.human.rich_console_manager import RichConsoleManager
                console = RichConsoleManager().console
                console.print("📂 [cyan]Using default directory structure:[/cyan]")
            except ImportError:
                print("Using default directory structure:")
        
        input_dir, renamed_dir, unprocessed_dir = ensure_default_directories()
        
        if not args.quiet:
            try:
                from interfaces.human.rich_console_manager import RichConsoleManager
                console = RichConsoleManager().console
                console.print(f"   📥 [blue]Input:[/blue] [white]{input_dir}[/white]")
                console.print(f"   📤 [green]Processed:[/green] [white]{renamed_dir}[/white]")
                console.print(f"   📋 [yellow]Unprocessed:[/yellow] [white]{unprocessed_dir}[/white]")
            except ImportError:
                print(f"  Input: {input_dir}")
                print(f"  Processed: {renamed_dir}")
                print(f"  Unprocessed: {unprocessed_dir}")

    return input_dir, renamed_dir, unprocessed_dir


def _validate_provider_and_model(provider: str, model: str) -> None:
    """Validate provider and model combination."""
    # Import here to avoid circular imports
    try:
        from ...domains.ai_integration.provider_service import ProviderConfiguration
        AI_PROVIDERS = ProviderConfiguration.AI_PROVIDERS
    except ImportError:
        # Fallback for testing or standalone usage
        AI_PROVIDERS = {}

    if provider not in AI_PROVIDERS:
        available_providers = ", ".join(AI_PROVIDERS.keys())
        raise ValueError(
            f"Unsupported provider '{provider}'. Available providers: {available_providers}"
        )

    if model not in AI_PROVIDERS[provider]:
        available_models = ", ".join(AI_PROVIDERS[provider])
        raise ValueError(
            f"Invalid model '{model}' for provider '{provider}'. Available models: {available_models}"
        )


def _display_api_key_instructions(provider: str) -> None:
    """Display instructions for API key input using Rich Console."""
    try:
        from interfaces.human.rich_console_manager import RichConsoleManager
        console = RichConsoleManager().console
        
        console.print()
        console.print("🔑 [bold blue]API Key Input[/bold blue]")
        console.print("• [white]Type or paste your API key (you'll see it as you type)[/white]")
        
        key_format = 'sk-ant-' if provider == 'claude' else 'sk-'
        console.print(f"• [cyan]{provider.capitalize()} keys start with[/cyan] [yellow]'{key_format}'[/yellow] [white]and are typically 40-60 characters[/white]")
        
        console.print(f"• [white]You can set[/white] [green]{provider.upper()}_API_KEY[/green] [white]environment variable to skip this step[/white]")
        console.print("• [white]Your key will be validated and cleared from display after entry[/white]")
        
    except ImportError:
        # Fallback if Rich not available
        print("\nAPI Key Input:")
        print("• Type or paste your API key (you'll see it as you type)")
        print(f"• {provider.capitalize()} keys start with '{'sk-ant-' if provider == 'claude' else 'sk-'}' and are typically 40-60 characters")
        print(f"• You can set {provider.upper()}_API_KEY environment variable to skip this step")
        print("• Your key will be validated and cleared from display after entry")


def _clean_and_validate_input(api_key: str, provider: str) -> str:
    """Clean API key input and provide user feedback."""
    if not api_key:
        return api_key

    # Remove all whitespace, newlines, and common paste artifacts
    api_key = "".join(api_key.split())
    # Remove common quotes that might get copied
    api_key = api_key.strip("\"'`")

    # Show partial key for user verification
    if len(api_key) >= 14:
        partial_display = (
            f"{api_key[:10]}{'*' * max(0, len(api_key) - 14)}{api_key[-4:]}"
        )
    else:
        partial_display = (
            f"{api_key[:min(6, len(api_key))]}{'*' * max(0, len(api_key) - 6)}"
        )

    try:
        from interfaces.human.rich_console_manager import RichConsoleManager
        console = RichConsoleManager().console
        console.print(f"✅ [green]Received API key:[/green] [white]{partial_display}[/white] [dim]({len(api_key)} characters)[/dim]")
        
        if len(api_key) < 20:
            console.print(f"⚠️  [yellow]Key seems short for {provider.capitalize()}[/yellow] [white](got {len(api_key)} chars, expected 40+)[/white]")
    except ImportError:
        print(f"[OK] Received API key: {partial_display} ({len(api_key)} characters)")
        if len(api_key) < 20:
            print(f"[WARNING] Key seems short for {provider.capitalize()} (got {len(api_key)} chars, expected 40+)")

    return api_key


def _prompt_for_api_key(provider: str) -> str:
    """Prompt user for API key with retry logic."""
    _display_api_key_instructions(provider)

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                print(f"\nAttempt {attempt + 1} of {max_attempts}")

            api_key = input(f"\nEnter your {provider.capitalize()} API key: ").strip()
            api_key = _clean_and_validate_input(api_key, provider)

            if api_key:
                try:
                    validated_key = _validate_api_key(api_key, provider)
                    try:
                        from interfaces.human.rich_console_manager import RichConsoleManager
                        console = RichConsoleManager().console
                        console.print("✅ [green]API key format validated successfully[/green]")
                        _clear_screen_secure()
                        console.print(f"🔐 [green]{provider.capitalize()} API key accepted and secured[/green]")
                    except ImportError:
                        print("[OK] API key format validated successfully")
                        _clear_screen_secure()
                        print(f"[OK] {provider.capitalize()} API key accepted and secured.")

                    return validated_key
                except ValueError as e:
                    try:
                        from interfaces.human.rich_console_manager import RichConsoleManager
                        console = RichConsoleManager().console
                        console.print(f"❌ [red]Validation failed:[/red] [white]{e}[/white]")
                        if attempt < max_attempts - 1:
                            console.print("💭 [cyan]Please try again...[/cyan]")
                    except ImportError:
                        print(f"[ERROR] Validation failed: {e}")
                        if attempt < max_attempts - 1:
                            print("Please try again...")
                        continue
                    else:
                        raise
            else:
                try:
                    from interfaces.human.rich_console_manager import RichConsoleManager
                    console = RichConsoleManager().console
                    console.print("❌ [red]No input received[/red]")
                    if attempt < max_attempts - 1:
                        console.print("💭 [cyan]Please try again...[/cyan]")
                except ImportError:
                    print("[ERROR] No input received")
                    if attempt < max_attempts - 1:
                        print("Please try again...")
                    continue
                else:
                    raise ValueError(f"{provider.capitalize()} API key is required.")

        except (KeyboardInterrupt, EOFError):
            raise ValueError("API key entry cancelled by user.")

    raise ValueError(f"Failed to get valid API key after {max_attempts} attempts.")


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
    _validate_provider_and_model(provider, model)

    env_var_name = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)

    if not api_key:
        return _prompt_for_api_key(provider)
    else:
        # Clean environment variable value (remove whitespace, quotes)
        api_key = _clean_and_validate_input(api_key, provider)

        # Check if after cleaning the key is empty
        if not api_key:
            return _prompt_for_api_key(provider)
        # For API keys from environment variables, still validate
        return _validate_api_key(api_key, provider)


def _detect_api_key_provider(api_key: str) -> str:
    """
    Detect which provider an API key belongs to based on its format.

    Args:
        api_key: API key to analyze

    Returns:
        Provider name or "unknown"
    """
    if api_key.startswith("sk-ant-"):
        return "claude"
    elif api_key.startswith("sk-proj-"):
        return "openai"
    elif api_key.startswith("sk-") and len(api_key) > 20:
        return "openai"  # Catch both old and new OpenAI formats
    elif api_key.startswith("AIza"):
        return "gemini"
    elif len(api_key) == 32 and api_key.isalnum():
        return "deepseek"
    else:
        return "unknown"


def _perform_basic_security_checks(api_key: str, provider: str) -> None:
    """Perform basic length and security checks on API key."""
    if len(api_key) < 10:
        raise ValueError(
            f"{provider.capitalize()} API key appears to be too short ({len(api_key)} characters). "
            f"Expected format: OpenAI keys start with 'sk-' and are ~51 characters long. "
            f"Please check your paste was successful and try again."
        )

    if len(api_key) > 512:
        raise ValueError(
            f"{provider.capitalize()} API key appears to be too long ({len(api_key)} characters)."
        )

    # Check for obviously fake or test keys
    test_patterns = [
        r"^(test|fake|dummy|placeholder)",
        r"^(sk-)?1{10,}",  # All 1s
        r"^(sk-)?0{10,}",  # All 0s
        r"password|secret|key|token",  # Contains obvious words
    ]

    for pattern in test_patterns:
        if re.match(pattern, api_key, re.IGNORECASE):
            raise ValueError(
                f"API key appears to be a placeholder or test value. Please use a real {provider.capitalize()} API key."
            )


def _check_provider_mismatch(
    api_key: str, provider: str, detected_provider: str
) -> None:
    """Check for provider mismatch and provide helpful error."""
    if detected_provider == "unknown" or detected_provider == provider:
        return

    provider_formats = {
        "openai": "sk-proj-... or sk-... (51+ characters)",
        "claude": "sk-ant-... (104 characters)",
        "gemini": "AIza... (Google Cloud API key)",
        "deepseek": "32-character alphanumeric string",
    }

    current_format = provider_formats.get(detected_provider, "unknown format")
    expected_format = provider_formats.get(provider, "unknown format")

    raise ValueError(
        f"API key mismatch detected!\n"
        f"  • You provided a {detected_provider.upper()} API key ({current_format})\n"
        f"  • But the application is configured for {provider.upper()} ({expected_format})\n"
        f"  • Either use --provider {detected_provider} or provide a {provider.upper()} API key\n"
        f"  • To switch providers, run: python src/main.py --provider {detected_provider} --model <model_name>"
    )


def _validate_provider_specific_format(
    api_key: str, provider: str, detected_provider: str
) -> None:
    """Validate provider-specific API key format requirements."""
    if provider == "openai":
        if not api_key.startswith("sk-"):
            provider_hint = (
                detected_provider.upper()
                if detected_provider != "unknown"
                else "different provider"
            )
            raise ValueError(
                f"OpenAI API keys must start with 'sk-'. "
                f"Your key starts with '{api_key[:10]}...' which looks like a {provider_hint} key."
            )
        if len(api_key) < 20:
            raise ValueError("OpenAI API key format appears invalid")

    elif provider == "claude":
        if not api_key.startswith("sk-ant-"):
            provider_hint = (
                detected_provider.upper()
                if detected_provider != "unknown"
                else "different provider"
            )
            raise ValueError(
                f"Claude API keys must start with 'sk-ant-'. "
                f"Your key starts with '{api_key[:10]}...' which looks like a {provider_hint} key."
            )
        if len(api_key) < 50:
            raise ValueError("Claude API key format appears invalid (too short)")

    elif provider == "gemini":
        if not api_key.startswith("AIza"):
            provider_hint = (
                detected_provider.upper()
                if detected_provider != "unknown"
                else "different provider"
            )
            raise ValueError(
                f"Google Gemini API keys must start with 'AIza'. "
                f"Your key starts with '{api_key[:10]}...' which looks like a {provider_hint} key."
            )
        if len(api_key) < 35:
            raise ValueError("Google Gemini API key format appears invalid")

    elif provider == "deepseek":
        if not (len(api_key) == 32 and api_key.isalnum()):
            provider_hint = (
                detected_provider.upper()
                if detected_provider != "unknown"
                else "different provider"
            )
            raise ValueError(
                f"DeepSeek API keys should be 32-character alphanumeric strings. "
                f"Your key is {len(api_key)} characters and looks like a {provider_hint} key."
            )


def _check_for_suspicious_characters(api_key: str) -> None:
    """Check for suspicious characters that might indicate injection attempts."""
    # Allow common API key characters: letters, numbers, hyphens, underscores, dots, plus signs
    if not re.match(r"^[a-zA-Z0-9\-_.+]+$", api_key):
        # Show what characters were found for debugging
        invalid_chars = set(re.findall(r"[^a-zA-Z0-9\-_.+]", api_key))
        raise ValueError(
            f"API key contains invalid characters: {sorted(invalid_chars)}"
        )


def _validate_api_key(api_key: str, provider: str) -> str:
    """
    Validate API key format and security with enhanced provider detection.

    Args:
        api_key: API key to validate
        provider: Expected provider name for validation

    Returns:
        Validated API key

    Raises:
        ValueError: If API key is invalid, insecure, or mismatched
    """
    _perform_basic_security_checks(api_key, provider)

    detected_provider = _detect_api_key_provider(api_key)
    _check_provider_mismatch(api_key, provider, detected_provider)
    _validate_provider_specific_format(api_key, provider, detected_provider)
    _check_for_suspicious_characters(api_key)

    return api_key


def _clear_screen_secure():
    """
    Securely clear the terminal screen using Rich Console.
    
    Rich handles terminal capabilities and clearing automatically.
    """
    try:
        from interfaces.human.rich_console_manager import RichConsoleManager
        console = RichConsoleManager().console
        console.clear()
    except ImportError:
        # Fallback to manual ANSI sequences if Rich not available
        try:
            if sys.platform.startswith("win"):
                # Windows: Use ANSI escape sequence (works in modern Windows Terminal)
                print("\033[2J\033[H", end="")
            else:
                # Unix/Linux/macOS: Use subprocess with shell=False for security
                subprocess.run(
                    ["clear"], shell=False, check=False, capture_output=True, timeout=1
                )
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback: Print newlines to simulate screen clear if commands fail
            print("\n" * 50)
