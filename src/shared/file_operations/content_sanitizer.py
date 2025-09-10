"""
Content Sanitizer

Input validation and content sanitization for safe processing.
Prevents injection attacks and validates content integrity.
"""

import html
import logging
import os
import re

# Some typing imports not used - keeping for future type hints
from typing import Any, Dict, List, Optional  # pylint: disable=unused-import


class ContentSanitizer:
    """Content sanitization and validation utilities."""

    def __init__(self):
        """Initialize content sanitizer."""
        self.logger = logging.getLogger(__name__)

        # Maximum content lengths for safety
        self.max_content_size = 50 * 1024 * 1024  # 50MB
        self.max_filename_length = 255

        # Patterns to detect and remove
        self.dangerous_patterns = [
            r"<script.*?>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript URLs
            r"data:.*base64,",  # Data URLs
            r"on\w+\s*=",  # Event handlers (onclick, etc.)
            r"expression\s*\(",  # CSS expressions
            r"@import\s+",  # CSS imports
            r"\\x[0-9a-fA-F]{2}",  # Hex encoded characters
            r"%[0-9a-fA-F]{2}",  # URL encoded characters
        ]

        # Suspicious content indicators
        self.suspicious_indicators = [
            r"eval\s*\(",  # Code evaluation
            r"exec\s*\(",  # Code execution
            r"document\.",  # DOM manipulation
            r"window\.",  # Browser window access
            r"location\.",  # URL manipulation
            r"cookie",  # Cookie access
            r"localStorage",  # Storage access
            r"sessionStorage",  # Session storage
        ]

    def sanitize_content_for_ai(self, content: str) -> str:
        """Sanitize content for safe AI processing.

        Args:
            content: Raw content to sanitize

        Returns:
            Sanitized content safe for AI processing
        """
        if not content:
            return ""

        try:
            # Check size limits
            if len(content) > self.max_content_size:
                self.logger.warning(
                    "Content too large (%d bytes), truncating to %d",
                    len(content),
                    self.max_content_size,
                )
                content = content[: self.max_content_size]

            # Remove dangerous patterns
            sanitized = content
            for pattern in self.dangerous_patterns:
                sanitized = re.sub(pattern, "[REMOVED]", sanitized, flags=re.IGNORECASE | re.DOTALL)

            # Log if suspicious patterns detected
            self._log_suspicious_content(sanitized)

            # Normalize whitespace and encoding
            sanitized = self._normalize_content(sanitized)

            return sanitized

        except Exception as e:
            self.logger.error("Content sanitization failed: %s", e)
            # Return safe fallback
            return "[Content sanitization failed - using safe fallback]"

    def validate_extracted_content(self, content: str, file_path: str) -> str:
        """Validate and sanitize extracted content.

        Args:
            content: Extracted content to validate
            file_path: Source file path for logging context

        Returns:
            Validated and sanitized content
        """
        if not content:
            return content

        try:
            # Check for obvious extraction errors
            if content.startswith("Error:"):
                return content  # Pass through error messages

            # Basic content validation
            if len(content.strip()) < 3:
                return content  # Very short content is probably valid

            # Sanitize for safety
            sanitized = self.sanitize_content_for_ai(content)

            # Log content quality metrics
            self._log_content_quality(sanitized, file_path)

            return sanitized

        except Exception as e:
            self.logger.error("Content validation failed for %s: %s", file_path, e)
            return f"[Content validation failed: {e}]"

    def sanitize_filename_input(self, filename: str) -> str:
        """Sanitize filename from user input.

        Args:
            filename: User-provided filename

        Returns:
            Sanitized filename safe for filesystem
        """
        if not filename:
            return "unnamed_file"

        try:
            # HTML decode if needed
            sanitized = html.unescape(filename)

            # Remove dangerous characters
            sanitized = re.sub(r'[<>:"|?*\\/]', "_", sanitized)

            # Remove control characters
            sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

            # Limit length
            if len(sanitized) > self.max_filename_length:
                name, ext = os.path.splitext(sanitized)
                max_name_len = self.max_filename_length - len(ext)
                sanitized = name[:max_name_len] + ext

            # Ensure not empty
            if not sanitized.strip():
                sanitized = "sanitized_filename"

            return sanitized

        except Exception as e:
            self.logger.error("Filename sanitization failed: %s", e)
            return "safe_filename"

    def _log_suspicious_content(self, content: str) -> None:
        """Log if suspicious patterns are detected in content."""
        try:
            for pattern in self.suspicious_indicators:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.logger.warning(
                        "Suspicious content pattern detected: %s (matches: %d)",
                        pattern,
                        len(matches),
                    )

        except Exception as e:
            self.logger.error("Suspicious content detection failed: %s", e)

    def _normalize_content(self, content: str) -> str:
        """Normalize content formatting and encoding."""
        try:
            # Normalize line endings
            normalized = content.replace("\r\n", "\n").replace("\r", "\n")

            # Collapse excessive whitespace
            normalized = re.sub(r"\n\s*\n\s*\n", "\n\n", normalized)  # Max 2 consecutive newlines
            normalized = re.sub(r"[ \t]+", " ", normalized)  # Multiple spaces to single space

            # Ensure UTF-8 compatibility
            normalized = normalized.encode("utf-8", errors="replace").decode("utf-8")

            return normalized

        except Exception as e:
            self.logger.error("Content normalization failed: %s", e)
            return content  # Return original if normalization fails

    def _log_content_quality(self, content: str, file_path: str) -> None:
        """Log content quality metrics for monitoring."""
        try:
            quality_metrics = {
                "length": len(content),
                "lines": content.count("\n"),
                "words": len(content.split()),
                "file_path": os.path.basename(file_path),
            }

            self.logger.debug("Content quality: %s", quality_metrics)

        except Exception as e:
            self.logger.error("Content quality logging failed: %s", e)


class SecurityError(Exception):
    """Exception raised when security validation fails."""

    pass


# Convenience functions
def sanitize_content_for_ai(content: str) -> str:
    """Sanitize content for AI processing using default sanitizer."""
    sanitizer = ContentSanitizer()
    return sanitizer.sanitize_content_for_ai(content)


def validate_extracted_content(content: str, file_path: str) -> str:
    """Validate extracted content using default sanitizer."""
    sanitizer = ContentSanitizer()
    return sanitizer.validate_extracted_content(content, file_path)


def sanitize_filename_input(filename: str) -> str:
    """Sanitize filename input using default sanitizer."""
    sanitizer = ContentSanitizer()
    return sanitizer.sanitize_filename_input(filename)
