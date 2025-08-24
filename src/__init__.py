"""
AI-Powered Document Organization System

Intelligent document processing with AI-generated filenames.
Supports PDFs, images, and screenshots with multi-provider AI integration.
"""

__version__ = "2.0.0"
__author__ = "AI-Powered Document Organization Project"

# Import main functions for easy access
from .main import list_available_models, sort_and_rename_pdfs

__all__ = ["sort_and_rename_pdfs", "list_available_models"]
