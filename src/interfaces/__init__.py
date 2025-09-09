"""
Interface Layer - Clean separation of user interaction patterns.

Provides persona-driven interfaces for:
- Human users (interactive CLI, Rich UI)
- Automation users (headless operation, structured output)
- Integration users (protocols, APIs)

This layer maintains the separation between user interaction patterns and business logic,
enabling clean support for multiple user personas without coupling.
"""

from .base_interfaces import HumanInterface, ProgrammaticInterface

__all__ = ['HumanInterface', 'ProgrammaticInterface']
