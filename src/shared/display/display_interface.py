"""
Display Interface Definition

Defines the common interface that all display managers must implement.
This ensures consistent behavior across different display implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.progress import Progress


class IDisplayManager(ABC):
    """Abstract base class defining the display manager interface."""
    
    @property
    @abstractmethod
    def console(self) -> Console:
        """Get the Rich Console instance."""
        pass
    
    # Status and messaging methods
    @abstractmethod
    def info(self, message: str, context: Optional[str] = None) -> None:
        """Display info message."""
        pass
    
    @abstractmethod
    def success(self, message: str, context: Optional[str] = None) -> None:
        """Display success message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, context: Optional[str] = None) -> None:
        """Display warning message."""
        pass
    
    @abstractmethod
    def error(
        self, message: str, context: Optional[str] = None, suggestions: Optional[List[str]] = None
    ) -> None:
        """Display error message with optional suggestions."""
        pass
    
    @abstractmethod
    def show_status(self, message: str, status: str = "info") -> None:
        """Show status message with appropriate styling."""
        pass
    
    @abstractmethod
    def show_loading(self, message: str) -> None:
        """Show loading message."""
        pass
    
    # Panel and display methods
    @abstractmethod
    def show_panel(self, title: str, content: str, style: str = "blue") -> None:
        """Display content in a panel."""
        pass
    
    @abstractmethod
    def show_table(
        self, title: str, headers: List[str], rows: List[List[str]], style: str = "blue"
    ) -> None:
        """Display data in a table."""
        pass
    
    @abstractmethod
    def show_section_header(self, title: str, description: Optional[str] = None) -> None:
        """Display section header with optional description."""
        pass
    
    @abstractmethod
    def show_configuration_table(
        self, config: Dict[str, Any], title: str = "Configuration"
    ) -> None:
        """Display configuration in a formatted table."""
        pass
    
    # Progress methods
    @abstractmethod
    def create_progress_display(self, description: str = "Processing") -> Progress:
        """Create a progress display."""
        pass
    
    @abstractmethod
    def start_progress(self, description: str = "Processing") -> str:
        """Start progress display and return progress ID."""
        pass
    
    @abstractmethod
    def update_progress(
        self, progress_id: str, current: int, total: int, description: Optional[str] = None
    ) -> None:
        """Update progress display."""
        pass
    
    @abstractmethod
    def finish_progress(self, progress_id: str) -> None:
        """Finish progress display."""
        pass
    
    # Interactive methods (for human interface)
    def prompt_choice(self, message: str, choices: list, default: Optional[str] = None) -> str:
        """Interactive choice prompt."""
        raise NotImplementedError("Interactive prompts only available in human interface")
    
    def prompt_confirm(self, message: str, default: bool = True) -> bool:
        """Interactive confirmation prompt."""
        raise NotImplementedError("Interactive prompts only available in human interface")
    
    def prompt_text(self, message: str, default: Optional[str] = None) -> str:
        """Interactive text input prompt."""
        raise NotImplementedError("Interactive prompts only available in human interface")
    
    # Utility methods
    @abstractmethod
    def clear_screen(self) -> None:
        """Clear the display screen."""
        pass
    
    @abstractmethod
    def print_separator(self, char: str = "─") -> None:
        """Print separator line."""
        pass
    
    # Special panels for specific use cases
    def show_welcome_panel(self) -> None:
        """Show welcome panel (optional for non-human interfaces)."""
        pass
    
    def show_info_panel(self, title: str, content: str, style: str = "info") -> None:
        """Display informational panel."""
        # Default implementation using show_panel
        self.show_panel(title, content, style)
    
    def show_error_panel(self, title: str, error: str, suggestions: Optional[list] = None) -> None:
        """Display error panel with optional suggestions."""
        # Default implementation using error method
        self.error(error, context=title, suggestions=suggestions)
    
    def show_success_panel(
        self, title: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Display success panel with optional details."""
        # Default implementation
        content = message
        if details:
            content += "\n\nDetails:"
            for key, value in details.items():
                content += f"\n• {key}: {value}"
        self.show_panel(title, content, "green")
    
    def show_processing_summary(self, results: Dict[str, Any]) -> None:
        """Show processing summary in appropriate format."""
        # Default implementation
        if results.get("success"):
            self.success(f"Processed {results.get('files_processed', 0)} files successfully")
            if results.get("output_directory"):
                self.info(f"Output directory: {results['output_directory']}")
            
            warnings = results.get("warnings", [])
            for warning in warnings:
                self.warning(warning)
        else:
            errors = results.get("errors", [])
            self.error("Processing failed", suggestions=errors[:3])
    
    def get_terminal_size(self) -> tuple:
        """Get terminal dimensions (width, height)."""
        if hasattr(self.console, 'size'):
            size = self.console.size
            return (size.width, size.height)
        return (80, 24)  # Default size
    
    def is_terminal_capable(self) -> bool:
        """Check if terminal supports Rich features."""
        if hasattr(self.console, 'is_terminal'):
            return self.console.is_terminal
        return False
    
    def get_display_capabilities(self) -> Dict[str, Any]:
        """Get display system capabilities."""
        return {
            "console_available": self.console is not None,
            "rich_features": self.is_terminal_capable(),
            "progress_available": True,
            "color_support": True
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle error display with user-friendly messaging."""
        # Default implementation
        error_message = str(error)
        suggestions = []
        
        if context and "api_key" in str(error).lower():
            suggestions.extend([
                "Verify your API key is correct and active",
                "Set your API key as an environment variable",
                "Check if the AI provider service is available"
            ])
        
        self.error(error_message, suggestions=suggestions if suggestions else None)