"""
Safe File Manager

Consolidated file operations with proper locking, retry logic, and security.
Extracted from file_organizer.py, directory_manager.py, and other scattered file operations.
"""

import os
import platform
import shutil
import time
import tempfile
from typing import TextIO, Optional, Union, Dict, Any, TYPE_CHECKING
import logging

# Cross-platform file locking imports with proper type safety
if TYPE_CHECKING:
    import fcntl
    import msvcrt
else:
    if platform.system() == "Windows":
        import msvcrt
        fcntl = None
    else:
        import fcntl
        msvcrt = None


class FileLockManager:
    """Cross-platform file locking utilities."""

    @staticmethod
    def lock_file(file_obj: Union[TextIO, Any]) -> None:
        """Acquire exclusive file lock (cross-platform)."""
        # Type safety check for file locking
        if not hasattr(file_obj, 'fileno'):
            # If object doesn't support locking, log warning but don't fail
            logging.getLogger(__name__).warning(
                f"Cannot lock object of type {type(file_obj)} - no fileno() method"
            )
            return

        try:
            fileno = file_obj.fileno()
        except (AttributeError, OSError, ValueError) as e:
            logging.getLogger(__name__).warning(f"Cannot get file descriptor for locking: {e}")
            return

        if platform.system() == "Windows":
            if msvcrt is not None:
                msvcrt.locking(fileno, msvcrt.LK_LOCK, 1)
        else:
            if fcntl is not None:
                fcntl.flock(fileno, fcntl.LOCK_EX)  # type: ignore[attr-defined]

    @staticmethod
    def unlock_file(file_obj: TextIO) -> None:
        """Release file lock (cross-platform)."""
        if not hasattr(file_obj, 'fileno'):
            return  # Can't unlock what wasn't locked

        if platform.system() == "Windows":
            if msvcrt is not None:
                msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            if fcntl is not None:
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


class AtomicFileOperations:
    """Atomic file operations with rollback capability."""

    def __init__(self):
        """Initialize atomic file operations."""
        self.logger = logging.getLogger(__name__)

    def atomic_write(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """Write content to file atomically.

        Args:
            file_path: Target file path
            content: Content to write
            encoding: File encoding

        Returns:
            True if write was successful
        """
        # Initialize temp_path in outer scope for proper exception handling
        temp_path = f"{file_path}.tmp.{os.getpid()}"

        try:
            # Write to temporary file first
            with open(temp_path, 'w', encoding=encoding) as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk

            # Atomic move to final location
            if platform.system() == "Windows":
                # Windows requires removing target first
                if os.path.exists(file_path):
                    os.remove(file_path)
                shutil.move(temp_path, file_path)
            else:
                # Unix systems support atomic replace
                os.replace(temp_path, file_path)

            self.logger.debug("Atomically wrote file: {file_path}")
            return True

        except Exception as e:
            # Clean up temporary file (temp_path is now properly scoped)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

            self.logger.error("Atomic write failed for {file_path}: {e}")
            return False

    def atomic_move(self, src_path: str, dst_path: str, attempts: int = 3, delay: float = 0.75) -> bool:
        """Move file atomically with retry logic.

        Args:
            src_path: Source file path
            dst_path: Destination file path
            attempts: Number of retry attempts
            delay: Delay between retries

        Returns:
            True if move was successful
        """
        if not os.path.exists(src_path):
            self.logger.error("Source file does not exist: {src_path}")
            return False

        # Ensure destination directory exists
        dst_dir = os.path.dirname(dst_path)
        if dst_dir and not os.path.exists(dst_dir):
            try:
                os.makedirs(dst_dir, exist_ok=True)
            except Exception as e:
                self.logger.error("Cannot create destination directory {dst_dir}: {e}")
                return False

        last_err = None
        for attempt in range(attempts):
            try:
                # Handle filename conflicts
                actual_dst_path = self._resolve_filename_conflict(dst_path)

                # Try direct move first
                shutil.move(src_path, actual_dst_path)
                self.logger.debug("Successfully moved: {src_path} → {actual_dst_path}")
                return True

            except OSError as e:
                last_err = e
                self.logger.warning("Move attempt {attempt + 1} failed: {e}")

                if attempt < attempts - 1:  # Not last attempt
                    time.sleep(delay * (attempt + 1))
                    continue

        # Final attempt: copy then delete
        try:
            actual_dst_path = self._resolve_filename_conflict(dst_path)
            shutil.copy2(src_path, actual_dst_path)
            os.remove(src_path)
            self.logger.info("Fallback copy-delete successful: {src_path} → {actual_dst_path}")
            return True

        except Exception as e:
            self.logger.error("All move attempts failed. Last error: {last_err}, Fallback error: {e}")
            return False

    def _resolve_filename_conflict(self, file_path: str) -> str:
        """Resolve filename conflicts by appending counter."""
        if not os.path.exists(file_path):
            return file_path

        base_name, extension = os.path.splitext(file_path)
        counter = 1

        while os.path.exists(file_path):
            file_path = f"{base_name}_{counter}{extension}"
            counter += 1

            # Prevent infinite loop
            if counter > 1000:
                # Use timestamp as last resort
                timestamp = int(time.time())
                file_path = f"{base_name}_{timestamp}{extension}"
                break

        return file_path


class SafeFileManager:
    """Main safe file management service consolidating all file operations."""

    def __init__(self):
        """Initialize safe file manager."""
        self.logger = logging.getLogger(__name__)
        self.lock_manager = FileLockManager()
        self.atomic_ops = AtomicFileOperations()

        # Statistics tracking
        self._operation_stats = {
            "files_moved": 0,
            "files_copied": 0,
            "directories_created": 0,
            "operations_failed": 0
        }

    def safe_move(self, src: str, dst: str, attempts: int = 3, delay: float = 0.75) -> bool:
        """Safely move file with retry logic.

        Args:
            src: Source file path
            dst: Destination file path
            attempts: Number of retry attempts
            delay: Delay between retries

        Returns:
            True if successful
        """
        success = self.atomic_ops.atomic_move(src, dst, attempts, delay)

        if success:
            self._operation_stats["files_moved"] += 1
        else:
            self._operation_stats["operations_failed"] += 1

        return success

    def safe_copy(self, src: str, dst: str) -> bool:
        """Safely copy file to destination.

        Args:
            src: Source file path
            dst: Destination file path

        Returns:
            True if successful
        """
        try:
            # Ensure destination directory exists
            dst_dir = os.path.dirname(dst)
            if dst_dir and not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)

            # Handle filename conflicts
            actual_dst = self.atomic_ops._resolve_filename_conflict(dst)  # pylint: disable=protected-access

            # Copy with metadata preservation
            shutil.copy2(src, actual_dst)

            self._operation_stats["files_copied"] += 1
            self.logger.debug("Successfully copied: {src} → {actual_dst}")
            return True

        except Exception as e:
            self._operation_stats["operations_failed"] += 1
            self.logger.error("Copy failed: {src} → {dst}: {e}")
            return False

    def safe_create_directory(self, dir_path: str, mode: int = 0o755) -> bool:
        """Safely create directory with proper permissions.

        Args:
            dir_path: Directory path to create
            mode: Directory permissions

        Returns:
            True if successful
        """
        try:
            os.makedirs(dir_path, mode=mode, exist_ok=True)
            self._operation_stats["directories_created"] += 1
            self.logger.debug("Created directory: {dir_path}")
            return True

        except Exception as e:
            self._operation_stats["operations_failed"] += 1
            self.logger.error("Directory creation failed: {dir_path}: {e}")
            return False

    def safe_delete(self, file_path: str) -> bool:
        """Safely delete file.

        Args:
            file_path: File path to delete

        Returns:
            True if successful
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.debug("Deleted file: {file_path}")
            return True

        except Exception as e:
            self._operation_stats["operations_failed"] += 1
            self.logger.error("Delete failed: {file_path}: {e}")
            return False

    def create_temp_file(self, suffix: str = '', prefix: str = 'ct_', directory: Optional[str] = None) -> str:
        """Create temporary file safely.

        Args:
            suffix: File suffix
            prefix: File prefix
            directory: Directory for temp file

        Returns:
            Path to created temporary file
        """
        try:
            with tempfile.NamedTemporaryFile(
                mode='w+',
                suffix=suffix,
                prefix=prefix,
                dir=directory,
                delete=False
            ) as temp_file:
                temp_path = temp_file.name

            self.logger.debug("Created temporary file: {temp_path}")
            return temp_path

        except Exception as e:
            self.logger.error("Temporary file creation failed: {e}")
            raise RuntimeError(f"Cannot create temporary file: {e}") from e

    def validate_file_operation(self, operation: str, src: str, dst: Optional[str] = None) -> tuple:
        """Validate file operation before execution.

        Args:
            operation: Operation type ('move', 'copy', 'delete', 'create')
            src: Source path
            dst: Destination path (for move/copy)

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate source for most operations
            if operation in ['move', 'copy', 'delete']:
                if not os.path.exists(src):
                    return False, f"Source file does not exist: {src}"

                if not os.access(src, os.R_OK):
                    return False, f"No read permission for source: {src}"

            # Validate destination for move/copy
            if operation in ['move', 'copy'] and dst:
                dst_dir = os.path.dirname(dst)
                if dst_dir and not os.path.exists(dst_dir):
                    # Try to create directory
                    try:
                        os.makedirs(dst_dir, exist_ok=True)
                    except Exception as e:
                        return False, f"Cannot create destination directory: {e}"

                if dst_dir and not os.access(dst_dir, os.W_OK):
                    return False, f"No write permission for destination directory: {dst_dir}"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {e}"

    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get file operation statistics."""
        return {
            **self._operation_stats,
            "success_rate": self._calculate_success_rate(),
            "total_operations": sum(self._operation_stats.values())
        }

    def _calculate_success_rate(self) -> float:
        """Calculate success rate of operations."""
        total_ops = sum(self._operation_stats.values())
        if total_ops == 0:
            return 100.0

        failed_ops = self._operation_stats["operations_failed"]
        success_ops = total_ops - failed_ops

        return (success_ops / total_ops) * 100.0

    def reset_statistics(self) -> None:
        """Reset operation statistics."""
        for key in self._operation_stats:
            self._operation_stats[key] = 0


# Legacy compatibility - module-level instance cache
_file_manager_instance: Optional[SafeFileManager] = None

def get_file_manager() -> SafeFileManager:
    """Get global file manager instance (legacy compatibility)."""
    global _file_manager_instance  # pylint: disable=global-statement
    if _file_manager_instance is None:
        _file_manager_instance = SafeFileManager()
    return _file_manager_instance
