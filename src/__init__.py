"""
Content Tamer AI - Intelligent Document Organization

Originally based on sort-rename-move-pdf by munir-abbasi
(https://github.com/munir-abbasi/sort-rename-move-pdf)
Substantially modified and extended for multi-format content processing
and AI-powered document intelligence.

Transform digital chaos into organized, searchable assets.
AI-powered content analysis and filename generation for any document type.

Licensed under MIT License - see LICENSE file for details.
"""

__version__ = "2.0.0"
__author__ = "Content Tamer AI Project"

# Import main functions for easy access
from .main import organize_content

__all__ = ["organize_content"]
