"""
Organization Domain

Document clustering, folder management, and learning services.
Implements the progressive enhancement architecture from PRD_04.

Services:
- ClusteringService: Rule-based classification with ML refinement
- FolderService: Directory operations and structure management
- LearningService: State management and continuous improvement
- OrganizationService: Main orchestrating service
"""

from .clustering_service import ClusteringService
from .folder_service import FolderService
from .learning_service import LearningService
from .organization_service import OrganizationService

__all__ = ["ClusteringService", "FolderService", "LearningService", "OrganizationService"]
