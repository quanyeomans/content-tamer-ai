"""
Content Tamer AI - Security Utilities

Provides input sanitization, validation, and security controls for file processing
and AI prompt construction to prevent injection attacks and path traversal.
"""

import os
import re
from pathlib import Path
from typing import Optional, Set


# Security constants
MAX_CONTENT_LENGTH = 4096  # Reduced from 8000 for safety
MAX_FILENAME_LENGTH = 160
SAFE_CHARS = re.compile(r'^[a-zA-Z0-9._\-\s]+$')

# Dangerous patterns that could indicate prompt injection
PROMPT_INJECTION_PATTERNS = [
    # Direct instruction attempts
    r'ignore\s+(?:previous|all|above)\s+instructions?',
    r'forget\s+(?:previous|all|above)\s+instructions?',
    r'new\s+instructions?',
    r'system\s*:\s*',
    r'assistant\s*:\s*',
    r'user\s*:\s*',
    
    # Command injection attempts
    r'execute\s+(?:command|code|script)',
    r'run\s+(?:command|code|script)',
    r'eval\s*\(',
    r'exec\s*\(',
    r'subprocess\.',
    r'os\.system',
    
    # Data exfiltration attempts
    r'print\s+(?:api|key|token|secret)',
    r'output\s+(?:api|key|token|secret)',
    r'reveal\s+(?:api|key|token|secret)',
    r'show\s+(?:api|key|token|secret)',
    
    # Formatting attempts
    r'```\s*(?:python|bash|sh|cmd)',
    r'<script[^>]*>',
    r'javascript:',
    
    # Role confusion attempts  
    r'you\s+are\s+(?:now|a)\s+(?:hacker|admin|root)',
    r'act\s+as\s+(?:if\s+you\s+are\s+)?(?:a|an|)\s*(?:hacker|admin|root|administrator)',
    r'pretend\s+(?:to\s+be|you\s+are)',
    r'act\s+like\s+(?:a|an)\s+(?:hacker|admin|root)',
]

# Compiled regex patterns for performance
INJECTION_REGEX = re.compile('|'.join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE)


class SecurityError(Exception):
    """Raised when a security validation fails."""
    pass


class InputSanitizer:
    """Handles input sanitization and validation for security."""
    
    @staticmethod
    def sanitize_content_for_ai(content: str) -> str:
        """
        Sanitize content before sending to AI to prevent prompt injection.
        
        Args:
            content: Raw extracted content from files
            
        Returns:
            Sanitized content safe for AI processing
            
        Raises:
            SecurityError: If content contains suspicious patterns
        """
        if not content:
            return ""
        
        # Truncate to safe length
        content = content[:MAX_CONTENT_LENGTH]
        
        # Check for prompt injection patterns
        if INJECTION_REGEX.search(content):
            # Log the attempt but don't include the actual content in the error
            raise SecurityError(
                "Suspicious content patterns detected. File may contain prompt injection attempts."
            )
        
        # Remove/escape potential control characters
        content = InputSanitizer._remove_control_characters(content)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    @staticmethod
    def _remove_control_characters(text: str) -> str:
        """Remove or escape control characters that could be dangerous."""
        # Remove non-printable characters except newlines and tabs
        cleaned = ''.join(
            char for char in text 
            if char.isprintable() or char in '\n\t'
        )
        
        # Limit consecutive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize filename for security.
        
        Args:
            filename: Proposed filename
            
        Returns:
            Sanitized filename
            
        Raises:
            SecurityError: If filename is unsafe
        """
        if not filename:
            raise SecurityError("Filename cannot be empty")
        
        # Check length
        if len(filename) > MAX_FILENAME_LENGTH:
            filename = filename[:MAX_FILENAME_LENGTH]
        
        # Check for dangerous characters
        if not SAFE_CHARS.match(filename):
            # Remove unsafe characters
            filename = re.sub(r'[^a-zA-Z0-9._\-\s]', '', filename)
        
        # Remove dangerous patterns
        dangerous_names = {'.', '..', 'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 
                          'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                          'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 
                          'LPT8', 'LPT9'}
        
        if filename.upper() in dangerous_names:
            raise SecurityError(f"Filename '{filename}' is reserved/dangerous")
        
        # Ensure it doesn't start/end with dangerous characters
        filename = filename.strip('. ')
        
        if not filename:
            raise SecurityError("Filename became empty after sanitization")
        
        return filename


class PathValidator:
    """Handles path validation and traversal protection."""
    
    @staticmethod
    def validate_file_path(file_path: str, base_dirs: Set[str]) -> str:
        """
        Validate file path to prevent directory traversal attacks.
        
        Args:
            file_path: Path to validate
            base_dirs: Set of allowed base directories
            
        Returns:
            Resolved absolute path if safe
            
        Raises:
            SecurityError: If path is unsafe or outside allowed directories
        """
        if not file_path:
            raise SecurityError("File path cannot be empty")
        
        try:
            # Resolve path to handle symlinks and relative components
            resolved_path = Path(file_path).resolve()
            abs_path = str(resolved_path)
            
            # Check if path is within any allowed base directory
            path_is_safe = False
            for base_dir in base_dirs:
                base_resolved = Path(base_dir).resolve()
                try:
                    # Check if file_path is within base_dir
                    resolved_path.relative_to(base_resolved)
                    path_is_safe = True
                    break
                except ValueError:
                    continue
            
            if not path_is_safe:
                raise SecurityError(
                    f"Path '{file_path}' is outside allowed directories"
                )
            
            return abs_path
            
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid file path: {e}") from e
    
    @staticmethod
    def validate_directory(dir_path: str) -> str:
        """
        Validate directory path for safety.
        
        Args:
            dir_path: Directory path to validate
            
        Returns:
            Absolute directory path
            
        Raises:
            SecurityError: If directory path is unsafe
        """
        try:
            resolved_dir = Path(dir_path).resolve()
            
            # Check for suspicious patterns
            path_str = str(resolved_dir)
            if '..' in path_str.split(os.sep):
                raise SecurityError("Directory path contains traversal attempts")
            
            return str(resolved_dir)
            
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid directory path: {e}") from e


class ContentValidator:
    """Validates content extracted from files."""
    
    @staticmethod
    def validate_extracted_content(content: str, source_file: str) -> str:
        """
        Validate content extracted from files before AI processing.
        
        Args:
            content: Extracted content
            source_file: Source file path for context
            
        Returns:
            Validated content
            
        Raises:
            SecurityError: If content appears malicious
        """
        if not content:
            return ""
        
        # Basic length check
        if len(content) > MAX_CONTENT_LENGTH * 2:  # Allow some overhead before truncation
            content = content[:MAX_CONTENT_LENGTH * 2]
        
        # Check for embedded scripts or commands
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        combined_pattern = re.compile('|'.join(script_patterns), re.IGNORECASE | re.DOTALL)
        if combined_pattern.search(content):
            raise SecurityError(
                f"File '{source_file}' contains potentially malicious embedded scripts"
            )
        
        return content


# Security configuration
SECURITY_CONFIG = {
    'max_content_length': MAX_CONTENT_LENGTH,
    'max_filename_length': MAX_FILENAME_LENGTH,
    'enable_injection_detection': True,
    'strict_path_validation': True,
}


def get_security_config() -> dict:
    """Get current security configuration."""
    return SECURITY_CONFIG.copy()


def update_security_config(**kwargs) -> None:
    """Update security configuration (for testing only)."""
    SECURITY_CONFIG.update(kwargs)