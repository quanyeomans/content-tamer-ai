"""
Enhanced error handling for file processing operations.

Provides smart error categorization, retry logic, and user-friendly messaging
for common filesystem issues like permission errors and file locks.
"""

import errno
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Tuple

# Import secure logging to prevent API key exposure
from .security import sanitize_log_message

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Categories of errors that can occur during file processing."""

    RECOVERABLE_PERMISSION = "recoverable_permission"  # Errno 13 - Permission denied
    FILE_LOCKED = "file_locked"  # Errno 32 - File in use
    SYNC_CONFLICT = "sync_conflict"  # OneDrive/Dropbox conflicts
    TEMPORARY_UNAVAILABLE = "temp_unavailable"  # Various temporary issues
    NETWORK_ISSUE = "network_issue"  # Network-related problems
    PERMANENT_ERROR = "permanent"  # Genuine failures
    UNSUPPORTED_FORMAT = "unsupported"  # File format issues

    # Organization-specific errors
    ORGANIZATION_ML_UNAVAILABLE = "org_ml_unavailable"  # ML dependencies missing
    ORGANIZATION_CONFIG_ERROR = "org_config_error"  # Configuration issues
    ORGANIZATION_INSUFFICIENT_DATA = "org_insufficient_data"  # Not enough data for organization
    ORGANIZATION_CLASSIFIER_ERROR = "org_classifier_error"  # Classification failures
    ORGANIZATION_FOLDER_ERROR = "org_folder_error"  # Folder creation/access issues


@dataclass
class ErrorClassification:
    """Details about a classified error."""

    error_type: ErrorType
    is_recoverable: bool
    suggested_wait_time: float
    user_message: str
    retry_recommended: bool


class ErrorClassifier:
    """Classifies exceptions into recoverable vs permanent errors."""

    @staticmethod
    def classify_error(exception: Exception) -> ErrorClassification:
        """Classify an exception and provide handling recommendations."""
        error_str = str(exception).lower()
        error_code = getattr(exception, "errno", None)

        # Permission denied errors (very common on Windows)
        if (
            error_code == errno.EACCES
            or "permission denied" in error_str
            or "errno 13" in error_str
        ):
            return ErrorClassification(
                error_type=ErrorType.RECOVERABLE_PERMISSION,
                is_recoverable=True,
                suggested_wait_time=2.0,
                user_message="File temporarily locked (likely antivirus scan or sync)",
                retry_recommended=True,
            )

        # File in use errors
        if (
            error_code == errno.EBUSY
            or "file is being used" in error_str
            or "errno 32" in error_str
            or "temporarily locked" in error_str
            or "file locked" in error_str
        ):
            return ErrorClassification(
                error_type=ErrorType.FILE_LOCKED,
                is_recoverable=True,
                suggested_wait_time=1.5,
                user_message="File in use by another application",
                retry_recommended=True,
            )

        # Sync software conflicts
        sync_indicators = ["onedrive", "dropbox", "sync", "cloud", "conflicted copy"]
        if any(indicator in error_str for indicator in sync_indicators):
            return ErrorClassification(
                error_type=ErrorType.SYNC_CONFLICT,
                is_recoverable=True,
                suggested_wait_time=3.0,
                user_message="Cloud sync conflict detected",
                retry_recommended=True,
            )

        # Network-related issues
        network_indicators = ["network", "timeout", "connection", "unreachable"]
        if any(indicator in error_str for indicator in network_indicators):
            return ErrorClassification(
                error_type=ErrorType.NETWORK_ISSUE,
                is_recoverable=True,
                suggested_wait_time=5.0,
                user_message="Network connectivity issue",
                retry_recommended=True,
            )

        # File format issues
        format_indicators = [
            "unsupported",
            "invalid format",
            "corrupted",
            "not a valid",
        ]
        if any(indicator in error_str for indicator in format_indicators):
            return ErrorClassification(
                error_type=ErrorType.UNSUPPORTED_FORMAT,
                is_recoverable=False,
                suggested_wait_time=0.0,
                user_message="Unsupported or corrupted file format",
                retry_recommended=False,
            )

        # Organization-specific error classification
        return ErrorClassifier._classify_organization_error(error_str, exception)

    @staticmethod
    def _classify_organization_error(
        error_str: str, exception: Exception
    ) -> ErrorClassification:  # pylint: disable=unused-argument
        """Classify organization-specific errors."""

        # ML/NLP dependencies missing
        ml_indicators = [
            "spacy",
            "sentence",
            "transformers",
            "sklearn",
            "nltk",
            "model",
            "no module named",
        ]
        if any(indicator in error_str for indicator in ml_indicators):
            return ErrorClassification(
                error_type=ErrorType.ORGANIZATION_ML_UNAVAILABLE,
                is_recoverable=False,
                suggested_wait_time=0.0,
                user_message="ML dependencies not available, falling back to basic organization",
                retry_recommended=False,
            )

        # Configuration errors
        config_indicators = [
            "configuration",
            "invalid config",
            "missing config",
            "preferences",
        ]
        if any(indicator in error_str for indicator in config_indicators):
            return ErrorClassification(
                error_type=ErrorType.ORGANIZATION_CONFIG_ERROR,
                is_recoverable=True,
                suggested_wait_time=1.0,
                user_message="Organization configuration issue, using defaults",
                retry_recommended=True,
            )

        # Insufficient data for organization
        data_indicators = [
            "no documents",
            "empty content",
            "insufficient data",
            "no valid documents",
        ]
        if any(indicator in error_str for indicator in data_indicators):
            return ErrorClassification(
                error_type=ErrorType.ORGANIZATION_INSUFFICIENT_DATA,
                is_recoverable=False,
                suggested_wait_time=0.0,
                user_message="Insufficient data for intelligent organization",
                retry_recommended=False,
            )

        # Classification failures
        classifier_indicators = [
            "classification",
            "categorization",
            "clustering",
            "similarity",
        ]
        if any(indicator in error_str for indicator in classifier_indicators):
            return ErrorClassification(
                error_type=ErrorType.ORGANIZATION_CLASSIFIER_ERROR,
                is_recoverable=True,
                suggested_wait_time=2.0,
                user_message="Classification temporarily failed, retrying with simpler approach",
                retry_recommended=True,
            )

        # Folder creation/access issues
        folder_indicators = [
            "mkdir",
            "folder",
            "directory",
            "makedirs",
            "cannot create",
        ]
        if any(indicator in error_str for indicator in folder_indicators):
            return ErrorClassification(
                error_type=ErrorType.ORGANIZATION_FOLDER_ERROR,
                is_recoverable=True,
                suggested_wait_time=1.0,
                user_message="Folder access issue, checking permissions",
                retry_recommended=True,
            )

        # Default to permanent error
        return ErrorClassification(
            error_type=ErrorType.PERMANENT_ERROR,
            is_recoverable=False,
            suggested_wait_time=0.0,
            user_message="Processing error",
            retry_recommended=False,
        )


@dataclass
class RetryStats:
    """Statistics about retry attempts and outcomes."""

    total_attempts: int = 0
    successful_retries: int = 0
    failed_retries: int = 0
    files_with_recoverable_issues: int = 0  # Unique files that had warnings
    permanent_errors: int = 0
    recoverable_errors_encountered: int = 0  # Total retry attempts across all files

    # Track which files have already been counted for warnings
    _files_with_warnings: Optional[set] = None

    def __post_init__(self):
        if self._files_with_warnings is None:
            self._files_with_warnings = set()

    def add_attempt(self, success: bool, was_retry: bool = False):
        """Record an attempt result."""
        self.total_attempts += 1
        if was_retry:
            if success:
                self.successful_retries += 1
            else:
                self.failed_retries += 1

    def add_recoverable_error(self, filename: Optional[str] = None):
        """Record a recoverable error encounter for a specific file."""
        # Always increment total retry attempts
        self.recoverable_errors_encountered += 1

        # Track unique files with recoverable issues
        if self._files_with_warnings is None:
            self._files_with_warnings = set()
        if filename and filename not in self._files_with_warnings:
            self.files_with_recoverable_issues += 1
            self._files_with_warnings.add(filename)

    def add_permanent_error(self):
        """Record a permanent error."""
        self.permanent_errors += 1


class RetryHandler:
    """Handles retry logic with exponential backoff and smart error reporting."""

    def __init__(self, max_attempts: int = 3, base_wait_time: float = 1.0):
        self.max_attempts = max_attempts
        self.base_wait_time = base_wait_time
        self.stats = RetryStats()

    def execute_with_retry(
        self, operation: Callable, display_context: Any, filename: str, *args, **kwargs
    ) -> Tuple[bool, Optional[Any], Optional[ErrorClassification]]:
        """
        Execute an operation with smart retry logic.

        Returns:
            (success, result, final_error_classification)
        """
        last_error_classification = None

        for attempt in range(self.max_attempts):
            try:
                # Attempt the operation
                result = operation(*args, **kwargs)

                # Success!
                if attempt > 0:
                    # This was a successful retry
                    self.stats.add_attempt(success=True, was_retry=True)
                    display_context.set_status("recovered")
                    display_context.show_info("✅ Successfully processed after retry")
                else:
                    # First attempt success
                    self.stats.add_attempt(success=True, was_retry=False)

                return True, result, None

            except Exception as e:
                # Classify the error
                error_classification = ErrorClassifier.classify_error(e)
                last_error_classification = error_classification

                # Log the attempt with sanitized error message
                sanitized_error = sanitize_log_message(str(e))
                logger.debug(f"Attempt {attempt + 1} failed for {filename}: {sanitized_error}")

                # Check if we should retry
                if (
                    error_classification.is_recoverable
                    and error_classification.retry_recommended
                    and attempt < self.max_attempts - 1
                ):

                    # This is a recoverable error, and we have attempts left
                    self.stats.add_recoverable_error(filename)

                    # Calculate wait time with exponential backoff
                    wait_time = error_classification.suggested_wait_time * (2**attempt)

                    # Show status update and user-friendly retry message
                    display_context.set_status("retrying")
                    display_context.show_info(
                        f"⏳ {error_classification.user_message}, retrying..."
                    )

                    # Wait before retry
                    time.sleep(wait_time)
                    continue

                else:
                    # Either not recoverable, or we've exhausted retries
                    if error_classification.is_recoverable:
                        # Recoverable error but exhausted retries
                        self.stats.add_attempt(success=False, was_retry=True)
                        display_context.set_status("failed")
                    else:
                        # Permanent error
                        self.stats.add_permanent_error()
                        display_context.set_status("failed")

                    return False, None, error_classification

        # Should never reach here, but just in case
        return False, None, last_error_classification

    def get_stats(self) -> RetryStats:
        """Get retry statistics."""
        return self.stats

    def format_session_summary(self) -> str:
        """Format a user-friendly session summary."""
        if self.stats.files_with_recoverable_issues == 0:
            return ""

        parts = []

        if self.stats.successful_retries > 0:
            parts.append(
                f"♻️ {self.stats.successful_retries} files recovered after temporary issues"
            )

        if self.stats.files_with_recoverable_issues > 0:
            parts.append(
                f"⚠️ {self.stats.files_with_recoverable_issues} files had temporary permission/lock issues "
                f"(typically caused by antivirus scans or cloud sync)"
            )

        return " • ".join(parts) if parts else ""


def create_retry_handler(max_attempts: int = 3) -> RetryHandler:
    """Factory function to create a configured retry handler."""
    return RetryHandler(max_attempts=max_attempts, base_wait_time=1.0)
