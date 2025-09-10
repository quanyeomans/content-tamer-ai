"""
Content Tamer AI - Path Management Utilities

Centralized path calculation and directory management to eliminate duplication.
"""

import os
from typing import Tuple

# Calculate PROJECT_ROOT once - shared across all modules
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Default directory structure
DEFAULT_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
DEFAULT_INPUT_DIR = os.path.join(DEFAULT_DATA_DIR, "input")
DEFAULT_PROCESSED_DIR = os.path.join(DEFAULT_DATA_DIR, "processed")
DEFAULT_PROCESSING_DIR = os.path.join(DEFAULT_DATA_DIR, ".processing")
DEFAULT_UNPROCESSED_DIR = os.path.join(DEFAULT_PROCESSED_DIR, "unprocessed")


def get_project_root() -> str:
    """
    Get the project root directory.

    Returns:
        Absolute path to the project root directory
    """
    return _PROJECT_ROOT


def get_default_directories() -> Tuple[str, str, str, str, str]:
    """
    Get all default directory paths.

    Returns:
        Tuple of (data_dir, input_dir, processed_dir, processing_dir, unprocessed_dir)
    """
    return (
        DEFAULT_DATA_DIR,
        DEFAULT_INPUT_DIR,
        DEFAULT_PROCESSED_DIR,
        DEFAULT_PROCESSING_DIR,
        DEFAULT_UNPROCESSED_DIR,
    )


def get_data_directories() -> Tuple[str, str, str]:
    """
    Get the main data processing directories.

    Returns:
        Tuple of (input_dir, processed_dir, unprocessed_dir)
    """
    return (DEFAULT_INPUT_DIR, DEFAULT_PROCESSED_DIR, DEFAULT_UNPROCESSED_DIR)
