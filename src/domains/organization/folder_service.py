"""
Folder Service

Directory operations and folder structure management.
Handles safe file operations and intelligent folder organization.
"""

import logging
import os
import re
import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .clustering_service import ClassificationResult


class FolderStructureType(Enum):
    """Types of folder organization structures."""

    TIME_FIRST = "time_first"  # 2025/category/
    CATEGORY_FIRST = "category_first"  # category/2025/
    FLAT_TIME = "flat_time"  # 2025_month_category/
    FLAT_CATEGORY = "flat_category"  # category_files/


class FiscalYearType(Enum):
    """Fiscal year types."""

    CALENDAR = "calendar"  # Jan-Dec
    FY_JULY = "fy_july"  # Jul-Jun
    FY_APRIL = "fy_april"  # Apr-Mar
    FY_SEPTEMBER = "fy_sep"  # Sep-Aug


@dataclass
class FolderStructure:
    """Definition of folder organization structure."""

    structure_type: FolderStructureType
    fiscal_year_type: FiscalYearType
    time_granularity: str  # "year" or "month"
    base_path: str
    categories: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FileOperation:
    """Represents a file operation to be performed."""

    source_path: str
    target_path: str
    operation_type: str  # "move", "copy", "create_dir"
    category: str
    confidence: float
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FolderAnalyzer:
    """Analyzes existing folder structures to detect patterns."""

    def __init__(self):
        """Initialize folder analyzer."""
        self.logger = logging.getLogger(__name__)

    def analyze_existing_structure(self, target_path: str) -> Optional[FolderStructure]:
        """Analyze existing folder structure to detect organization pattern.

        Args:
            target_path: Path to analyze for existing patterns

        Returns:
            FolderStructure if pattern detected, None otherwise
        """
        try:
            if not os.path.exists(target_path):
                return None

            # Get subdirectories
            subdirs = [
                d
                for d in os.listdir(target_path)
                if os.path.isdir(os.path.join(target_path, d)) and not d.startswith(".")
            ]

            if not subdirs:
                return None

            # Detect structure patterns
            structure_type = self._detect_structure_type(subdirs)
            fiscal_year_type = self._detect_fiscal_year_type(subdirs)
            time_granularity = self._detect_time_granularity(subdirs)
            categories = self._extract_categories(subdirs, structure_type)

            return FolderStructure(
                structure_type=structure_type,
                fiscal_year_type=fiscal_year_type,
                time_granularity=time_granularity,
                base_path=target_path,
                categories=categories,
                metadata={
                    "detected_subdirs": subdirs,
                    "analysis_confidence": self._calculate_pattern_confidence(
                        subdirs, structure_type
                    ),
                },
            )

        except Exception as e:
            self.logger.error("Existing structure analysis failed: %s", e)
            return None

    def _detect_structure_type(self, subdirs: List[str]) -> FolderStructureType:
        """Detect whether structure is time-first or category-first."""
        # Count year-like directories (4 digits starting with 19 or 20)
        year_dirs = [d for d in subdirs if re.match(r"^(19|20)\d{2}$", d)]

        # Count likely category directories
        category_indicators = [
            "financial",
            "legal",
            "personal",
            "business",
            "medical",
            "tax",
            "bills",
            "receipts",
            "contracts",
            "statements",
            "documents",
        ]
        category_dirs = [
            d for d in subdirs if any(indicator in d.lower() for indicator in category_indicators)
        ]

        if len(year_dirs) > len(category_dirs):
            return FolderStructureType.TIME_FIRST
        if len(category_dirs) > len(year_dirs):
            return FolderStructureType.CATEGORY_FIRST
            # Default to category-first if uncertain
            return FolderStructureType.CATEGORY_FIRST

    def _detect_fiscal_year_type(self, subdirs: List[str]) -> FiscalYearType:
        """Detect fiscal year type from existing folders."""
        # Look for fiscal year patterns in folder names
        fy_patterns = [
            (r"fy.*july|july.*fy", FiscalYearType.FY_JULY),
            (r"fy.*april|april.*fy", FiscalYearType.FY_APRIL),
            (r"fy.*sep|sep.*fy", FiscalYearType.FY_SEPTEMBER),
        ]

        for pattern, fy_type in fy_patterns:
            if any(re.search(pattern, d.lower()) for d in subdirs):
                return fy_type

        # Default to calendar year
        return FiscalYearType.CALENDAR

    def _detect_time_granularity(self, subdirs: List[str]) -> str:
        """Detect if using year or month-level time granularity."""
        # Look for month patterns
        month_patterns = [
            r"\d{4}[-_]\d{1,2}",  # YYYY-MM or YYYY_MM
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",  # Month names
            r"(january|february|march|april|may|june|july|august|september|october|november|december)",
        ]

        month_dirs = sum(
            1 for d in subdirs if any(re.search(pattern, d.lower()) for pattern in month_patterns)
        )

        return "month" if month_dirs > 0 else "year"

    def _extract_categories(
        self, subdirs: List[str], structure_type: FolderStructureType
    ) -> List[str]:
        """Extract category names from subdirectories."""
        if structure_type == FolderStructureType.TIME_FIRST:
            # Categories would be in subdirectories of time folders
            # For now, return common categories as we'd need to scan deeper
            return []
        # Filter out time-based directories to get categories
        year_pattern = r"^(19|20)\d{2}$"
        categories = [d for d in subdirs if not re.match(year_pattern, d)]
        return categories

    def _calculate_pattern_confidence(
        self, subdirs: List[str], detected_type: FolderStructureType
    ) -> float:
        """Calculate confidence in detected pattern."""
        if not subdirs:
            return 0.0

        pattern_indicators = 0
        total_dirs = len(subdirs)

        if detected_type == FolderStructureType.TIME_FIRST:
            # Count year-like directories
            year_dirs = sum(1 for d in subdirs if re.match(r"^(19|20)\d{2}$", d))
            pattern_indicators = year_dirs
        else:
            # Count category-like directories
            category_indicators = [
                "financial",
                "legal",
                "personal",
                "business",
                "medical",
                "bills",
                "receipts",
                "contracts",
                "statements",
            ]
            category_dirs = sum(
                1
                for d in subdirs
                if any(indicator in d.lower() for indicator in category_indicators)
            )
            pattern_indicators = category_dirs

        return min(1.0, pattern_indicators / total_dirs)


class FolderService:
    """Main folder management service."""

    def __init__(self):
        """Initialize folder service."""
        self.logger = logging.getLogger(__name__)
        self.analyzer = FolderAnalyzer()

    def create_folder_structure(
        self,
        target_path: str,
        classifications: Dict[str, ClassificationResult],
        existing_structure: Optional[FolderStructure] = None,
    ) -> Tuple[FolderStructure, List[FileOperation]]:
        """Create optimal folder structure based on classifications.

        Args:
            target_path: Base path for organization
            classifications: Document classification results
            existing_structure: Existing structure to extend (optional)

        Returns:
            Tuple of (folder_structure, file_operations)
        """
        try:
            # Analyze existing structure if not provided
            if existing_structure is None:
                existing_structure = self.analyzer.analyze_existing_structure(target_path)

            # Determine optimal structure
            optimal_structure = self._determine_optimal_structure(
                target_path, classifications, existing_structure
            )

            # Plan file operations
            file_operations = self._plan_file_operations(classifications, optimal_structure)

            return optimal_structure, file_operations

        except Exception as e:
            self.logger.error("Folder structure creation failed: %s", e)
            raise RuntimeError(f"Failed to create folder structure: {e}") from e

    def _determine_optimal_structure(
        self,
        target_path: str,
        classifications: Dict[str, ClassificationResult],
        existing_structure: Optional[FolderStructure],
    ) -> FolderStructure:
        """Determine optimal folder structure."""
        # If existing structure exists and is reasonable, extend it
        if existing_structure and self._is_structure_reasonable(existing_structure):
            return self._extend_existing_structure(existing_structure, classifications)

        # Create new structure based on document analysis
        return self._create_new_structure(target_path, classifications)

    def _is_structure_reasonable(self, structure: FolderStructure) -> bool:
        """Check if existing structure is reasonable to extend."""
        # Check confidence in pattern detection
        confidence = structure.metadata.get("analysis_confidence", 0)
        if confidence < 0.3:
            return False

        # Check if categories are reasonable
        if len(structure.categories) > 20:  # Too many categories
            return False

        return True

    def _extend_existing_structure(
        self, existing_structure: FolderStructure, classifications: Dict[str, ClassificationResult]
    ) -> FolderStructure:
        """Extend existing folder structure with new categories."""
        # Extract new categories from classifications
        classified_categories = set(result.category for result in classifications.values())
        new_categories = classified_categories - set(existing_structure.categories)

        extended_categories = existing_structure.categories + list(new_categories)

        return FolderStructure(
            structure_type=existing_structure.structure_type,
            fiscal_year_type=existing_structure.fiscal_year_type,
            time_granularity=existing_structure.time_granularity,
            base_path=existing_structure.base_path,
            categories=extended_categories,
            metadata={
                **existing_structure.metadata,
                "extended": True,
                "new_categories": list(new_categories),
                "extension_count": len(new_categories),
            },
        )

    def _create_new_structure(
        self, target_path: str, classifications: Dict[str, ClassificationResult]
    ) -> FolderStructure:
        """Create new folder structure from scratch."""
        # Extract categories from classifications
        categories = list(set(result.category for result in classifications.values()))

        # Determine structure type based on content
        structure_type = self._choose_structure_type(classifications)

        # Choose time granularity based on document volume
        time_granularity = self._choose_time_granularity(classifications)

        return FolderStructure(
            structure_type=structure_type,
            fiscal_year_type=FiscalYearType.CALENDAR,  # Default to calendar
            time_granularity=time_granularity,
            base_path=target_path,
            categories=categories,
            metadata={
                "created_new": True,
                "document_count": len(classifications),
                "unique_categories": len(categories),
            },
        )

    def _choose_structure_type(
        self, classifications: Dict[str, ClassificationResult]
    ) -> FolderStructureType:
        """Choose structure type based on document characteristics."""
        # If documents have strong category patterns, use category-first
        strong_categories = sum(
            1 for result in classifications.values() if result.confidence >= 0.8
        )

        # If most documents have strong categories, use category-first
        if strong_categories / len(classifications) >= 0.6:
            return FolderStructureType.CATEGORY_FIRST
            return FolderStructureType.TIME_FIRST

    def _choose_time_granularity(self, classifications: Dict[str, ClassificationResult]) -> str:
        """Choose time granularity based on document volume."""
        # Simple heuristic: if more than 50 documents, use monthly granularity
        return "month" if len(classifications) > 50 else "year"

    def _plan_file_operations(
        self, classifications: Dict[str, ClassificationResult], structure: FolderStructure
    ) -> List[FileOperation]:
        """Plan file operations needed for organization."""
        operations = []

        # Group files by category
        files_by_category = self._group_files_by_category(classifications)

        for category, files in files_by_category.items():
            try:
                # Create directory operation if needed
                category_path = self._get_category_path(category, structure)
                if not os.path.exists(category_path):
                    operations.append(
                        FileOperation(
                            source_path="",
                            target_path=category_path,
                            operation_type="create_dir",
                            category=category,
                            confidence=1.0,
                            metadata={"directory_creation": True},
                        )
                    )

                # Plan file move operations
                for file_path, result in files:
                    target_file_path = os.path.join(category_path, os.path.basename(file_path))

                    operations.append(
                        FileOperation(
                            source_path=file_path,
                            target_path=target_file_path,
                            operation_type="move",
                            category=category,
                            confidence=result.confidence,
                            metadata={
                                "classification_method": result.method.value if result.method else "unknown",
                                "original_category": result.category,
                                "reasoning": result.reasoning,
                            },
                        )
                    )

            except Exception as e:
                self.logger.error("Failed to plan operations for category %s: %s", category, e)

        return operations

    def _group_files_by_category(
        self, classifications: Dict[str, ClassificationResult]
    ) -> Dict[str, List[Tuple[str, ClassificationResult]]]:
        """Group files by their classified categories."""
        files_by_category = {}

        for file_path, result in classifications.items():
            category = result.category
            if category not in files_by_category:
                files_by_category[category] = []
            files_by_category[category].append((file_path, result))

        return files_by_category

    def _get_category_path(self, category: str, structure: FolderStructure) -> str:
        """Get full path for a category based on folder structure."""
        if structure.structure_type == FolderStructureType.CATEGORY_FIRST:
            if structure.time_granularity == "year":
                return os.path.join(structure.base_path, category)
            # Would include time component - simplified for now
            return os.path.join(structure.base_path, category)
        # TIME_FIRST - Would include time component - simplified for now
        return os.path.join(structure.base_path, "2025", category)  # Placeholder

    def execute_file_operations(self, operations: List[FileOperation]) -> Dict[str, Any]:
        """Execute planned file operations safely.

        Args:
            operations: List of file operations to execute

        Returns:
            Dictionary with execution results
        """
        results = {
            "total_operations": len(operations),
            "successful_operations": 0,
            "failed_operations": 0,
            "created_directories": 0,
            "moved_files": 0,
            "errors": [],
        }

        for operation in operations:
            try:
                if operation.operation_type == "create_dir":
                    self._safe_create_directory(operation.target_path)
                    results["created_directories"] += 1

                elif operation.operation_type == "move":
                    self._safe_move_file(operation.source_path, operation.target_path)
                    results["moved_files"] += 1

                elif operation.operation_type == "copy":
                    self._safe_copy_file(operation.source_path, operation.target_path)
                    # Note: copy operations would increment a copy counter if we tracked them

                results["successful_operations"] += 1

            except Exception as e:
                error_msg = f"Operation failed for {operation.source_path}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
                results["failed_operations"] += 1

        # Log summary
        success_rate = (results["successful_operations"] / results["total_operations"]) * 100
        self.logger.info("File operations complete: %.1f%% success rate", success_rate)

        return results

    def _safe_create_directory(self, dir_path: str) -> None:
        """Safely create directory with proper permissions."""
        try:
            os.makedirs(dir_path, mode=0o755, exist_ok=True)
            self.logger.debug("Created directory: %s", dir_path)
        except Exception as e:
            raise RuntimeError(f"Failed to create directory {dir_path}: {e}") from e

    def _safe_move_file(self, source_path: str, target_path: str) -> None:
        """Safely move file with conflict resolution."""
        try:
            # Check if target already exists
            if os.path.exists(target_path):
                target_path = self._resolve_filename_conflict(target_path)

            # Ensure target directory exists
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                self._safe_create_directory(target_dir)

            # Move file atomically
            shutil.move(source_path, target_path)
            self.logger.debug("Moved file: %s → %s", source_path, target_path)

        except Exception as e:
            raise RuntimeError(f"Failed to move {source_path} to {target_path}: {e}") from e

    def _safe_copy_file(self, source_path: str, target_path: str) -> None:
        """Safely copy file with conflict resolution."""
        try:
            # Check if target already exists
            if os.path.exists(target_path):
                target_path = self._resolve_filename_conflict(target_path)

            # Ensure target directory exists
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                self._safe_create_directory(target_dir)

            # Copy file
            shutil.copy2(source_path, target_path)  # copy2 preserves metadata
            self.logger.debug("Copied file: %s → %s", source_path, target_path)

        except Exception as e:
            raise RuntimeError(f"Failed to copy {source_path} to {target_path}: {e}") from e

    def _resolve_filename_conflict(self, target_path: str) -> str:
        """Resolve filename conflicts by appending counter."""
        base_name, extension = os.path.splitext(target_path)
        counter = 1

        while os.path.exists(target_path):
            target_path = f"{base_name}_{counter}{extension}"
            counter += 1

            # Prevent infinite loop
            if counter > 1000:
                raise RuntimeError(f"Could not resolve filename conflict for {base_name}")

        return target_path

    def validate_folder_structure(self, structure: FolderStructure) -> Dict[str, Any]:
        """Validate proposed folder structure.

        Args:
            structure: Folder structure to validate

        Returns:
            Validation results with any issues found
        """
        issues = []
        warnings = []

        # Check base path
        if not os.path.exists(structure.base_path):
            try:
                os.makedirs(structure.base_path, exist_ok=True)
                warnings.append(f"Created base directory: {structure.base_path}")
            except Exception as e:
                issues.append(f"Cannot create base directory: {e}")

        if not os.access(structure.base_path, os.W_OK):
            issues.append(f"No write permission to base directory: {structure.base_path}")

        # Check category names
        invalid_categories = []
        for category in structure.categories:
            if not self._is_valid_folder_name(category):
                invalid_categories.append(category)

        if invalid_categories:
            issues.append(f"Invalid category names: {invalid_categories}")

        # Check for reasonable number of categories
        if len(structure.categories) > 25:
            warnings.append(
                f"Large number of categories ({len(structure.categories)}) may create cluttered structure"
            )

        # Check for very small categories (would need file count data)
        # This would require additional context about file distribution

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "structure_type": structure.structure_type.value if structure.structure_type else "unknown",
            "total_categories": len(structure.categories),
            "base_path": structure.base_path,
        }

    def _is_valid_folder_name(self, name: str) -> bool:
        """Check if folder name is valid for filesystem."""
        if not name or len(name) > 255:
            return False

        # Check for invalid characters
        invalid_chars = r'[<>:"|?*\\/]'
        if re.search(invalid_chars, name):
            return False

        # Check for reserved names (Windows)
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]
        if name.upper() in reserved_names:
            return False

        return True

    def get_folder_statistics(self, target_path: str) -> Dict[str, Any]:
        """Get statistics about folder organization.

        Args:
            target_path: Path to analyze

        Returns:
            Dictionary with folder statistics
        """
        try:
            if not os.path.exists(target_path):
                return {"exists": False}

            # Count files and directories
            total_files = 0
            total_dirs = 0
            files_by_extension = {}

            for root, dirs, files in os.walk(target_path):
                total_dirs += len(dirs)
                total_files += len(files)

                for file in files:
                    if not file.startswith("."):  # Skip hidden files
                        ext = os.path.splitext(file)[1].lower()
                        files_by_extension[ext] = files_by_extension.get(ext, 0) + 1

            # Analyze structure depth
            max_depth = 0
            for root, dirs, files in os.walk(target_path):
                depth = root[len(target_path) :].count(os.sep)
                max_depth = max(max_depth, depth)

            return {
                "exists": True,
                "total_files": total_files,
                "total_directories": total_dirs,
                "max_depth": max_depth,
                "file_types": files_by_extension,
                "structure_detected": self.analyzer.analyze_existing_structure(target_path)
                is not None,
            }

        except Exception as e:
            self.logger.error("Folder statistics failed: %s", e)
            return {"exists": True, "error": str(e)}

    def validate_file_operation(
        self, operation_type: str, source_path: str, target_path: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate a file operation before execution.

        Args:
            operation_type: Type of operation ("move", "copy", "create_dir")
            source_path: Source file path
            target_path: Target file path

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate operation type
            valid_operations = ["move", "copy", "create_dir"]
            if operation_type not in valid_operations:
                return False, f"Invalid operation type: {operation_type}"

            # For create_dir, only validate target path
            if operation_type == "create_dir":
                if not target_path:
                    return False, "Target path required for directory creation"
                return True, None

            # Validate source path exists for move/copy operations
            if not os.path.exists(source_path):
                return False, f"Source path does not exist: {source_path}"

            # Validate target path is reasonable
            if not target_path:
                return False, "Target path cannot be empty"

            # Check if target directory exists and is writable
            target_dir = os.path.dirname(target_path)
            if target_dir and not os.path.exists(target_dir):
                # Check if we can create the target directory
                try:
                    os.makedirs(target_dir, exist_ok=True)
                except Exception as e:
                    return False, f"Cannot create target directory: {e}"

            # Check write permissions
            if not os.access(target_dir or ".", os.W_OK):
                return False, f"No write permission to target directory: {target_dir}"

            # Check for cross-device moves on Windows
            if operation_type == "move":
                source_drive = os.path.splitdrive(source_path)[0]
                target_drive = os.path.splitdrive(target_path)[0]
                if source_drive != target_drive:
                    # Cross-device move might require copy+delete
                    pass  # This is handled by shutil.move()

            return True, None

        except Exception as e:
            return False, f"Validation failed: {e}"
