"""
Programmatic Interfaces - Headless Operation Support

Provides automation-friendly interfaces including:
- Pure CLI argument parsing
- Library interface for Python integration
- Configuration management without UI dependencies
- Structured output formats
"""

from .cli_arguments import PureCLIParser, ParsedArguments
from .library_interface import ContentTamerAPI
from .configuration_manager import ConfigurationManager

__all__ = ['PureCLIParser', 'ParsedArguments', 'ContentTamerAPI', 'ConfigurationManager']