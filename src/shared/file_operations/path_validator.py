"""
Path Validator

Security-focused path validation and sanitization.
Prevents directory traversal and validates cross-platform paths.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional, Tuple


class PathValidator:
    """Cross-platform path validation with security focus."""

    def __init__(self):
        """Initialize path validator."""
        self.logger = logging.getLogger(__name__)

        # Security patterns to detect
        self.suspicious_patterns = [
            r"\.\.[\\/]",  # Directory traversal
            r"[\\/]\.\.[\\\/]",  # Directory traversal variations
            r"^\.\.[\\/]",  # Leading directory traversal
            r"[\\/]\.\.[\\/]\.\.",  # Multiple directory traversal
            r"%2e%2e",  # URL encoded directory traversal
            r"%252e%252e",  # Double URL encoded
            r"\x00",  # Null byte injection
            r"%00",  # URL encoded null byte
        ]

        # Platform-specific forbidden paths
        if os.name == "nt":  # Windows
            self.forbidden_paths = [
                r"^[A-Za-z]:\\Windows\\",
                r"^[A-Za-z]:\\Program Files\\",
                r"^[A-Za-z]:\\Users\\[^\\]+\\AppData\\",
                r"\\System32\\",
                r"\\SysWOW64\\",
            ]
        else:  # Unix-like
            self.forbidden_paths = [
                r"^/etc/",
                r"^/proc/",
                r"^/sys/",
                r"^/dev/",
                r"^/root/",
                r"^/usr/bin/",
                r"^/usr/sbin/",
            ]

    def validate_file_path(
        self, file_path: str, base_directory: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Validate file path for security and accessibility.

        Args:
            file_path: File path to validate
            base_directory: Optional base directory to restrict access to

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic validation
            if not file_path or not isinstance(file_path, str):
                return False, "File path must be a non-empty string"

            # Check for suspicious patterns
            if self._contains_suspicious_patterns(file_path):
                return False, f"Suspicious path patterns detected in: {file_path}"

            # Check for forbidden system paths
            if self._is_forbidden_system_path(file_path):
                return False, f"Access to system path not allowed: {file_path}"

            # Resolve path and check bounds
            try:
                resolved_path = Path(file_path).resolve()

                # Check base directory bounds if specified
                if base_directory:
                    base_path = Path(base_directory).resolve()
                    try:
                        resolved_path.relative_to(base_path)
                    except ValueError:
                        return False, f"Path outside allowed base directory: {file_path}"

            except (OSError, ValueError) as e:
                return False, f"Invalid path resolution: {e}"

            return True, ""

        except Exception as e:
            self.logger.error(f"Path validation error: {e}")
            return False, f"Path validation failed: {e}"

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for all platforms
        """
        if not filename:
            return "unnamed_file"

        # Remove or replace problematic characters
        # Windows forbidden characters: < > : " | ? * \ /
        sanitized = re.sub(r'[<>:"|?*\\/]', "_", filename)

        # Remove control characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

        # Handle Windows reserved names
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        name_without_ext = os.path.splitext(sanitized)[0].upper()
        if name_without_ext in reserved_names:
            sanitized = f"file_{sanitized}"

        # Limit length (255 chars is filesystem limit)
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            max_name_len = 255 - len(ext)
            sanitized = name[:max_name_len] + ext

        # Ensure not empty after sanitization
        if not sanitized.strip():
            sanitized = "sanitized_file"

        return sanitized

    def _contains_suspicious_patterns(self, path: str) -> bool:
        """Check for suspicious patterns in path."""
        path_str = str(path).replace("\\", "/")  # Normalize separators

        for pattern in self.suspicious_patterns:
            if re.search(pattern, path_str, re.IGNORECASE):
                return True

        return False

    def _is_forbidden_system_path(self, path: str) -> bool:
        """Check if path accesses forbidden system directories."""
        path_str = str(path)

        for pattern in self.forbidden_paths:
            if re.search(pattern, path_str, re.IGNORECASE):
                return True

        return False

    def validate_directory_path(
        self, dir_path: str, must_exist: bool = False, must_be_writable: bool = False
    ) -> Tuple[bool, str]:
        """Validate directory path with specific requirements.

        Args:
            dir_path: Directory path to validate
            must_exist: Whether directory must already exist
            must_be_writable: Whether directory must be writable

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic path validation
        is_valid, error = self.validate_file_path(dir_path)
        if not is_valid:
            return False, error

        try:
            path_obj = Path(dir_path)

            # Check existence requirement
            if must_exist and not path_obj.exists():
                return False, f"Directory does not exist: {dir_path}"

            if path_obj.exists() and not path_obj.is_dir():
                return False, f"Path exists but is not a directory: {dir_path}"

            # Check writability requirement
            if must_be_writable:
                if path_obj.exists():
                    if not os.access(path_obj, os.W_OK):
                        return False, f"Directory is not writable: {dir_path}"
                else:
                    # Try to create parent directory to test writability
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        if not os.access(path_obj, os.W_OK):
                            return False, f"Directory cannot be made writable: {dir_path}"
                    except Exception as e:
                        return False, f"Cannot create/access directory: {e}"

            return True, ""

        except Exception as e:
            return False, f"Directory validation error: {e}"


# Convenience functions
def validate_file_path(file_path: str, base_directory: Optional[str] = None) -> Tuple[bool, str]:
    """Validate file path using default validator."""
    validator = PathValidator()
    return validator.validate_file_path(file_path, base_directory)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename using default validator."""
    validator = PathValidator()
    return validator.sanitize_filename(filename)
