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

from .safe_file_manager import SafeFileManager
from .path_validator import PathValidator
from .content_sanitizer import ContentSanitizer

__all__ = ['SafeFileManager', 'PathValidator', 'ContentSanitizer']
