"""
File organization and management utilities.

Original PDF processing logic inspired by sort-rename-move-pdf
by munir-abbasi. Substantially modified and extended to handle
multiple content types with AI-powered analysis and organization.

This module handles file operations, progress tracking, and provides
the foundation for future domain-based organization features.
"""

import datetime as dt
import os
import platform
import re
import shutil
import time
import unicodedata
from typing import Any, Dict, List, Optional, Set, TextIO, Union

# Cross-platform file locking imports
if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl


class FileManager:
    """Cross-platform file operations with locking and retry logic."""

    @staticmethod
    def lock_file(file_obj: TextIO) -> None:
        """Acquire exclusive file lock (cross-platform)."""
        if platform.system() == "Windows":
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)

    @staticmethod
    def unlock_file(file_obj: TextIO) -> None:
        """Release file lock (cross-platform)."""
        if platform.system() == "Windows":
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def safe_move(src: str, dst: str, attempts: int = 3, delay: float = 0.75) -> None:
        """Robust file move with retry logic and copy-delete fallback."""
        last_err = None
        for i in range(attempts):
            try:
                shutil.move(src, dst)
                return
            except OSError as e:
                last_err = e
                time.sleep(delay * (i + 1))
        # Fallback: copy then delete if move fails
        shutil.copy2(src, dst)
        try:
            os.remove(src)
        except OSError as e:
            # Raise the current error, or the last error if current is None
            raise (e if e is not None else (last_err or OSError("Unknown file operation error")))


class ProgressTracker:
    """Progress tracking for resumable batch processing."""

    @staticmethod
    def load_progress(progress_file: str, input_dir: str, reset_progress: bool = False) -> Set[str]:
        """Load processed files list with optional reset."""
        if reset_progress and os.path.exists(progress_file):
            try:
                os.remove(progress_file)
                print("Resetting progress: existing .progress file removed.")
            except OSError as e:
                print(f"Warning: Could not delete progress file: {e}")

        processed_files = set()
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    processed_files = {line.strip() for line in f}
                # Only skip files that have been moved out of input folder
                processed_files = {
                    name
                    for name in processed_files
                    if not os.path.exists(os.path.join(input_dir, name))
                }
            except (IOError, OSError) as e:
                print(f"Warning: Could not read progress file: {e}")
        return processed_files

    @staticmethod
    def record_progress(
        progress_file_obj: TextIO, filename: str, file_manager: FileManager
    ) -> None:
        """Thread-safe progress recording with file locking."""
        try:
            # Try file locking first
            file_manager.lock_file(progress_file_obj)
            progress_file_obj.write(f"{filename}\n")
            progress_file_obj.flush()
            file_manager.unlock_file(progress_file_obj)
        except (OSError, ValueError):
            # If locking fails, try without locking (for tests and edge cases)
            try:
                progress_file_obj.write(f"{filename}\n")
                progress_file_obj.flush()
            except (OSError, ValueError):
                # If all progress recording fails, just continue - don't break processing
                pass


class FilenameHandler:
    """Filename validation, sanitization, and collision resolution."""

    @staticmethod
    def validate_and_trim_filename(initial_filename: str) -> str:
        """Clean filename for cross-platform filesystem compatibility."""
        if not initial_filename or initial_filename.isspace():
            timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            return f"empty_file_{timestamp}"

        # Unicode normalization to ASCII
        normalized = (
            unicodedata.normalize("NFKD", initial_filename)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        # Keep only alphanumeric and underscores
        cleaned_filename = re.sub(r"[^a-zA-Z0-9_]", "", normalized)

        if not cleaned_filename:
            timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            return f"invalid_name_{timestamp}"

        return cleaned_filename[:160]  # Limit length for filesystem compatibility

    @staticmethod
    def handle_duplicate_filename(filename: str, folder: str, extension: str = ".pdf") -> str:
        """Resolve filename collisions by appending numeric suffix."""
        base_filename = filename
        counter = 1
        while os.path.exists(os.path.join(folder, f"{filename}{extension}")):
            filename = f"{base_filename}_{counter}"
            counter += 1
        return filename


class FileOrganizer:
    """File organization with extensible domain-based categorization support."""

    def __init__(self) -> None:
        self.file_manager = FileManager()
        self.progress_tracker = ProgressTracker()
        self.filename_handler = FilenameHandler()

    def create_directories(self, *directories: str) -> None:
        """Ensures all specified directories exist."""
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def move_file_to_category(
        self,
        src_path: str,
        filename: str,
        category_dir: str,
        new_name: str,
        file_extension: str = ".pdf",
    ) -> str:
        """Move file to category with collision-safe naming."""
        final_name = self.filename_handler.handle_duplicate_filename(
            new_name, category_dir, file_extension
        )

        # Auto-detect extension if default doesn't match source
        if file_extension == ".pdf" and not src_path.lower().endswith(".pdf"):
            file_extension = os.path.splitext(src_path)[1]

        dest_path = os.path.join(category_dir, final_name + file_extension)
        self.file_manager.safe_move(src_path, dest_path)
        return final_name

    def get_file_stats(self, directory: str) -> Dict[str, Union[int, Dict[str, int]]]:
        """Get file statistics by type for directory analysis."""
        if not os.path.exists(directory):
            return {"total": 0, "by_extension": {}}

        stats: Dict[str, Union[int, Dict[str, int]]] = {"total": 0, "by_extension": {}}
        by_ext: Dict[str, int] = {}

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                stats["total"] = int(stats["total"]) + 1  # type: ignore
                ext = os.path.splitext(filename)[1].lower()
                by_ext[ext] = by_ext.get(ext, 0) + 1

        stats["by_extension"] = by_ext
        return stats

    # Future domain organization features

    def organize_by_content_type(self, files: List[str], base_dir: str) -> Dict[str, List[str]]:
        """Organize files by content type (placeholder for AI-powered categorization)."""
        # Future: AI analysis for document types (invoices, contracts, reports, etc.)

        organization_map = {"documents": [], "images": [], "other": []}

        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".pdf", ".doc", ".docx", ".txt"]:
                organization_map["documents"].append(file_path)
            elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
                organization_map["images"].append(file_path)
            else:
                organization_map["other"].append(file_path)

        return organization_map

    def organize_by_date_pattern(self, files: List[str], base_dir: str) -> Dict[str, List[str]]:
        """Organize files by temporal patterns (placeholder for date extraction)."""
        # Future: Extract dates from content/filenames for chronological organization

        current_year = dt.datetime.now().year
        organization_map = {
            f"{current_year}": files,  # Simple fallback for now
        }

        return organization_map

    def create_domain_folders(self, base_dir: str, domains: List[str]) -> Dict[str, str]:
        """Create domain-specific folder structure."""
        domain_paths = {}
        for domain in domains:
            domain_path = os.path.join(base_dir, domain)
            os.makedirs(domain_path, exist_ok=True)
            domain_paths[domain] = domain_path
        return domain_paths

    def suggest_organization_structure(self, files: List[str]) -> Dict[str, Any]:
        """AI-powered organization suggestions (placeholder for content analysis)."""
        # Future: Analyze content patterns to suggest optimal folder structures
        return {
            "suggested_structure": {
                "by_type": ["Documents", "Images", "Spreadsheets"],
                "by_date": ["2024", "2023", "Archive"],
                "by_content": ["Financial", "Personal", "Work"],
            },
            "confidence": 0.8,
            "reasoning": "Based on file types and content analysis",
        }

    def run_post_processing_organization(
        self, 
        processed_files: List[str], 
        target_folder: str, 
        enable_organization: bool = True
    ) -> Dict[str, Any]:
        """
        Run post-processing document organization using Phase 1 balanced architecture.
        
        Args:
            processed_files: List of file paths that have been processed
            target_folder: Target directory for organization
            enable_organization: Feature flag to enable/disable organization
            
        Returns:
            Dictionary with organization results and status
        """
        if not enable_organization:
            return {
                "success": True,
                "organization_applied": False,
                "reason": "Organization disabled via feature flag"
            }
        
        try:
            # Import Phase 1 organization engine
            from organization.organization_engine import BasicOrganizationEngine
            
            # Initialize organization engine
            engine = BasicOrganizationEngine(target_folder)
            
            # Prepare document info for organization
            processed_docs = []
            for file_path in processed_files:
                if os.path.exists(file_path):
                    # Extract document info
                    doc_info = {
                        "filename": os.path.basename(file_path),
                        "path": file_path,
                        "content": self._extract_file_content_for_organization(file_path)
                    }
                    processed_docs.append(doc_info)
            
            if not processed_docs:
                return {
                    "success": True,
                    "organization_applied": False,
                    "reason": "No valid documents found for organization"
                }
            
            # Run organization
            organization_result = engine.organize_documents(processed_docs)
            
            if organization_result.get("success", False):
                return {
                    "success": True,
                    "organization_applied": True,
                    "organization_result": organization_result,
                    "documents_organized": len(processed_docs)
                }
            else:
                return {
                    "success": False,
                    "organization_applied": False,
                    "reason": "Organization engine failed",
                    "error": organization_result.get("error", "Unknown error")
                }
                
        except ImportError as e:
            # Graceful degradation - organization components not available
            return {
                "success": True,
                "organization_applied": False,
                "reason": f"Organization components not available: {e}"
            }
        except Exception as e:
            # Log error but don't fail the entire workflow
            import logging
            logging.warning(f"Post-processing organization failed: {e}")
            return {
                "success": False,
                "organization_applied": False,
                "reason": "Unexpected error during organization",
                "error": str(e)
            }
    
    def _extract_file_content_for_organization(self, file_path: str) -> str:
        """
        Extract content from processed files for organization analysis.
        
        This method reuses OCR content when possible to avoid reprocessing.
        """
        try:
            # For text files, read content directly
            if file_path.lower().endswith(('.txt', '.md')):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # For other file types, we would typically reuse OCR content
            # For Phase 1, we'll use filename and basic file info
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Generate basic content description for classification
            return f"Document: {filename}, Size: {file_size} bytes"
            
        except (IOError, UnicodeDecodeError, OSError):
            # Fallback to filename only
            return os.path.basename(file_path)
