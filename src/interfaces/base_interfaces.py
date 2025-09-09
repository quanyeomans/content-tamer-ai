"""
Base Interface Contracts

Defines the contracts that all interface implementations must follow.
Ensures consistency across human, programmatic, and protocol interfaces.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Coroutine
from dataclasses import dataclass
from rich.console import Console


@dataclass
class ProcessingResult:
    """Result of document processing operation."""
    success: bool
    files_processed: int
    files_failed: int
    output_directory: str
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class HumanInterface(ABC):
    """Contract for all human-facing interfaces."""

    @abstractmethod
    def setup_console(self) -> Console:
        """Initialize Rich Console for human interaction."""
        pass

    @abstractmethod
    def show_progress(self, stage: str, current: int, total: int, detail: str = "") -> None:
        """Display human-friendly progress information."""
        pass

    @abstractmethod
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Show user-friendly error message with guidance."""
        pass

    @abstractmethod
    def prompt_user_choice(self, message: str, choices: List[str], default: Optional[str] = None) -> str:
        """Interactive user prompting with validation."""
        pass

    @abstractmethod
    def show_results(self, result: ProcessingResult) -> None:
        """Display processing results in human-friendly format."""
        pass


class ProgrammaticInterface(ABC):
    """Contract for automation and scripting interfaces."""

    @abstractmethod
    def process_documents(self, config: Dict[str, Any]) -> ProcessingResult:
        """Headless document processing with structured result."""
        pass

    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration returning list of errors."""
        pass

    @abstractmethod
    def get_progress_status(self) -> Dict[str, Any]:
        """Return machine-readable progress information."""
        pass

    @abstractmethod
    def get_supported_providers(self) -> List[str]:
        """Get list of supported AI providers."""
        pass

    @abstractmethod
    def get_supported_models(self, provider: str) -> List[str]:
        """Get supported models for a provider."""
        pass


class ProtocolInterface(ABC):
    """Contract for protocol-based interfaces (MCP, REST, etc.)."""

    @abstractmethod
    def initialize_protocol(self, config: Dict[str, Any]) -> bool:
        """Initialize the protocol handler."""
        pass

    @abstractmethod
    def handle_request(self, request: Dict[str, Any]) -> Union[Dict[str, Any], Coroutine[Any, Any, Dict[str, Any]]]:
        """Handle protocol-specific request (can be sync or async)."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return protocol capabilities description."""
        pass
