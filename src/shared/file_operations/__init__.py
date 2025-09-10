"""
File Operations - Consolidated Safe File Management

Unified file operations eliminating duplication across:
- file_organizer.py (FileManager class)
- directory_manager.py (directory operations)
- Various file handling scattered across modules

Provides:
- Atomic file operations with proper locking
- Cross-platform path validation and security
- Content sanitization and validation
"""

from .content_sanitizer import ContentSanitizer
from .path_validator import PathValidator
from .safe_file_manager import SafeFileManager

__all__ = ["SafeFileManager", "PathValidator", "ContentSanitizer"]
