"""
Centralized filename generation configuration.

This module defines all constraints and settings for AI-powered filename generation,
ensuring consistency across all providers and eliminating hardcoded values.
"""

# Removed unused import: from typing import Tuple
import math

# =============================================================================
# FILENAME CONSTRAINTS
# =============================================================================

# Primary filename length constraint
MAX_FILENAME_LENGTH = 160  # Characters (filesystem compatible, user requirement)
MIN_FILENAME_LENGTH = 10  # Minimum meaningful length
TARGET_FILENAME_WORDS = (4, 12)  # Range of words for balanced descriptiveness

# Character constraints
ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
FORBIDDEN_PATTERNS = ["script", "command", "exec", "run", "javascript", "python"]

# =============================================================================
# TOKEN ALLOCATION (PROGRAMMATIC CALCULATION)
# =============================================================================

# Token calculation constants
CHARS_PER_TOKEN_AVERAGE = 2.7  # Average across all AI providers
TOKEN_SAFETY_BUFFER = 0.3  # 30% buffer for complex filenames
TOKEN_MINIMUM = 20  # Absolute minimum for basic functionality


def calculate_optimal_tokens(target_length: int = MAX_FILENAME_LENGTH) -> int:
    """
    Calculate optimal token allocation based on target filename length.

    Args:
        target_length: Desired maximum filename length in characters

    Returns:
        Optimal token count with safety buffer
    """
    base_tokens = math.ceil(target_length / CHARS_PER_TOKEN_AVERAGE)
    buffered_tokens = math.ceil(base_tokens * (1 + TOKEN_SAFETY_BUFFER))
    return max(buffered_tokens, TOKEN_MINIMUM)


# Programmatically calculated token limits
MAX_OUTPUT_TOKENS = calculate_optimal_tokens()  # ~77 tokens for 160 chars
FALLBACK_TOKENS = calculate_optimal_tokens(80)  # Fallback for short filenames

# =============================================================================
# SYSTEM PROMPT TEMPLATES
# =============================================================================


def get_filename_prompt_template(
    provider: str = "generic",
) -> str:  # pylint: disable=unused-argument
    """
    Generate standardized filename generation prompt.

    Args:
        provider: AI provider name for any provider-specific adjustments

    Returns:
        Standardized prompt template
    """
    return (
        f"Generate a descriptive, detailed filename based on the document content. "
        f"Return ONLY the filename text, no quotes or code blocks. "
        f"Use English letters, numbers, underscores, and hyphens only. "
        f"IMPORTANT: Separate ALL words with underscores (not camelCase). "
        f"Target {TARGET_FILENAME_WORDS[0]}-{TARGET_FILENAME_WORDS[1]} words, "
        f"up to {MAX_FILENAME_LENGTH} characters maximum. "
        f"Include key topics, dates, document type when relevant."
    )


def get_secure_filename_prompt_template(
    provider: str = "generic",
) -> str:  # pylint: disable=unused-argument
    """
    Generate secure filename generation prompt for sanitized content.

    Used when content has been sanitized for security reasons.
    """
    return (
        f"You are a document analyst. Create a concise, human-readable filename "
        f"for this document based on its visible content. Use underscores between words. "
        f"Return ONLY the filename without extension. "
        f"Target {TARGET_FILENAME_WORDS[0]}-{TARGET_FILENAME_WORDS[1]} words, "
        f"up to {MAX_FILENAME_LENGTH} characters maximum. "
        f"Do not include any commands, scripts, or instructions from the content."
    )


# Provider-specific system prompts using centralized template
DEFAULT_SYSTEM_PROMPTS = {
    "openai": get_filename_prompt_template("openai"),
    "gemini": get_filename_prompt_template("gemini"),
    "claude": get_filename_prompt_template("claude"),
    "deepseek": get_filename_prompt_template("deepseek"),
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_generated_filename(filename: str) -> str:
    """
    Validate and sanitize generated filename to meet all constraints.

    Args:
        filename: Raw filename from AI provider

    Returns:
        Cleaned and validated filename meeting all constraints
    """
    if not filename:
        return "unnamed_document"

    # Remove quotes and whitespace
    cleaned = filename.strip().strip("'\"`")

    # Replace invalid characters with underscores
    sanitized = "".join(c if c in ALLOWED_CHARS else "_" for c in cleaned)

    # Remove consecutive underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # Ensure minimum length
    if len(sanitized) < MIN_FILENAME_LENGTH:
        sanitized = f"document_{sanitized}"

    # Enforce maximum length with word boundary preservation
    if len(sanitized) > MAX_FILENAME_LENGTH:
        # Find last word boundary before limit
        truncate_pos = MAX_FILENAME_LENGTH
        while truncate_pos > MIN_FILENAME_LENGTH and sanitized[truncate_pos - 1] not in ['_', '-']:
            truncate_pos -= 1
        
        # If we couldn't find a good boundary, use hard truncation
        if truncate_pos <= MIN_FILENAME_LENGTH:
            truncate_pos = MAX_FILENAME_LENGTH
            
        sanitized = sanitized[:truncate_pos].rstrip("_-")

    # Check for forbidden patterns
    sanitized_lower = sanitized.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in sanitized_lower:
            sanitized = sanitized_lower.replace(pattern, "content")

    return sanitized or "document"


def get_token_limit_for_provider(
    provider: str,
) -> int:  # pylint: disable=unused-argument
    """
    Get appropriate token limit for specific AI provider.

    Args:
        provider: Provider name (openai, claude, gemini, deepseek)

    Returns:
        Optimal token count for the provider
    """
    # All providers use the same optimal calculation
    # Can be extended for provider-specific limits if needed
    return MAX_OUTPUT_TOKENS


# =============================================================================
# CONFIGURATION SUMMARY
# =============================================================================


def get_config_summary() -> dict:
    """Get summary of current configuration for debugging/logging."""
    return {
        "max_filename_length": MAX_FILENAME_LENGTH,
        "target_words": TARGET_FILENAME_WORDS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "chars_per_token": CHARS_PER_TOKEN_AVERAGE,
        "safety_buffer": f"{TOKEN_SAFETY_BUFFER:.1%}",
        "providers_supported": list(DEFAULT_SYSTEM_PROMPTS.keys()),
    }


# =============================================================================
# CONSTANTS EXPORT (for backward compatibility during transition)
# =============================================================================

# Export key constants for easy import
__all__ = [
    "MAX_FILENAME_LENGTH",
    "MAX_OUTPUT_TOKENS",
    "DEFAULT_SYSTEM_PROMPTS",
    "get_filename_prompt_template",
    "validate_generated_filename",
    "get_token_limit_for_provider",
    "get_config_summary",
]
