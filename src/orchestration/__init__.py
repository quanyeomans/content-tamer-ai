"""
Orchestration Layer

Application-level orchestration and workflow management.
Coordinates domain services to implement complete user workflows.

Components:
- ApplicationKernel: Main application coordination
- WorkflowEngine: Pipeline orchestration and execution
- SessionManager: State persistence and resume capability
"""

from .application_kernel import ApplicationKernel

__all__ = ["ApplicationKernel"]
