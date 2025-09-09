"""
Display Services - Unified Rich UI Components

Consolidates display logic from multiple scattered managers and provides
comprehensive Rich UI components for all application interfaces.

Core Components:
- UnifiedDisplayManager: Primary display service for all Rich UI operations
- ConsoleManager: Singleton pattern for Rich Console management
- CLI Display: ANSI color support and terminal detection utilities
- Rich Components: Progress displays, message handlers, and UI managers

Migration from utils/:
- All display utilities now centralized in shared/display/
- Consistent Rich console patterns throughout
- Smart emoji usage with platform detection
- Standardized message formatting and error display
"""

# CLI and terminal utilities
from .cli_display import (
    ColorFormatter,
    Colors,
    MessageLevel,
    TerminalCapabilities,
    create_formatter,
    get_terminal_capabilities,
)
from .console_manager import ConsoleManager, create_test_console, get_application_console

# Rich UI components
from .display_manager import DisplayManager
from .emoji_handler import SmartEmojiHandler, create_emoji_handler
from .message_handler import MessageHandler
from .progress_display import ProgressDisplay
from .rich_cli_display import RichCLIDisplay
from .rich_display_manager import RichDisplayManager
from .rich_progress_display import RichProgressDisplay

# Core display services
from .unified_display_manager import UnifiedDisplayManager

__all__ = [
    # Core services
    "UnifiedDisplayManager",
    "ConsoleManager",
    "get_application_console",
    "create_test_console",
    "SmartEmojiHandler",
    "create_emoji_handler",
    # CLI utilities
    "MessageLevel",
    "Colors",
    "TerminalCapabilities",
    "ColorFormatter",
    "get_terminal_capabilities",
    "create_formatter",
    # Rich UI components
    "DisplayManager",
    "RichDisplayManager",
    "RichCLIDisplay",
    "RichProgressDisplay",
    "ProgressDisplay",
    "MessageHandler",
]
