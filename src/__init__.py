"""
Content Tamer AI - Intelligent Document Organization

Transform digital chaos into organized, searchable assets.
AI-powered content analysis and filename generation for any document type.
"""

__version__ = "2.0.0"
__author__ = "Content Tamer AI Project"

# Import main functions for easy access
from .main import list_available_models, organize_content

__all__ = ["organize_content", "list_available_models"]
