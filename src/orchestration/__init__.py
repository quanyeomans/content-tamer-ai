"""
Orchestration Layer

Application-level orchestration and workflow management.
Coordinates domain services to implement complete user workflows.

Components:
- ApplicationKernel: Main application coordination
- WorkflowEngine: Pipeline orchestration and execution
- SessionManager: State persistence and resume capability
"""

try:
    from .application_kernel import ApplicationKernel
    __all__ = ["ApplicationKernel"]
except ImportError:
    # If ApplicationKernel can't be imported, don't expose it
    __all__ = []
    ApplicationKernel = None
