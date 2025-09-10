"""
Content Tamer AI - Core Application Modules

This package contains the core business logic components:
- cli_parser: Command line argument parsing and validation
- file_processor: File processing pipeline and AI coordination
- directory_manager: Directory setup and management
- application: Main application orchestration logic
"""

# Import the main application container components
from .application_container import (
    ApplicationContainer,
    create_application_container,
    create_test_container,
    get_global_container,
    reset_global_container,
    set_global_container,
)

__all__ = [
    "ApplicationContainer",
    "create_application_container",
    "create_test_container",
    "get_global_container",
    "set_global_container",
    "reset_global_container",
]
