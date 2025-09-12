"""
Smart Emoji Usage Handler

Provides platform-aware emoji rendering with ASCII fallbacks for consistent
display across different terminal capabilities and platforms.
"""

from typing import Dict

from rich.console import Console


class SmartEmojiHandler:
    """Handles smart emoji usage with platform detection and fallbacks."""

    # Emoji to ASCII mappings
    EMOJI_FALLBACKS: Dict[str, str] = {
        # Status indicators
        "ℹ️": "[INFO]",
        "✅": "[OK]",
        "⚠️": "[WARN]",
        "❌": "[ERROR]",
        "🚨": "[CRIT]",
        # Progress indicators
        "⚙️": "[PROC]",
        "⏭️": "[SKIP]",
        "♻️": "[RECOV]",
        "⏱️": "[TIME]",
        # Feature indicators
        "🗂️": "[ORG]",
        "🎯": ">>",
        "📋": "[LIST]",
        "🔍": "[DEBUG]",
        # UI feedback
        "🎉": "[SUCCESS]",
        "📁": "[FILES]",
        "📂": "[FOLDER]",
        "🛑": "[STOP]",
        "💥": "[ERROR]",
        # Generic markers
        ">>": ">>",  # Already ASCII
        "<<": "<<",  # Already ASCII
    }

    def __init__(self, console: Console):
        """Initialize with console instance for capability detection.

        Args:
            console: Rich Console instance for capability detection
        """
        self.console = console
        self._supports_unicode = self._detect_unicode_support()

    def _detect_unicode_support(self) -> bool:
        """Detect if console supports Unicode emoji display.

        Uses Rich console properties and platform detection to determine
        if emoji should be displayed or ASCII fallbacks used.

        Returns:
            bool: True if emoji should be used, False for ASCII fallbacks
        """
        # Check Rich console encoding capability
        if hasattr(self.console, "options") and hasattr(self.console.options, "encoding"):
            encoding = self.console.options.encoding
            if encoding and "utf-8" in encoding.lower():
                return True

        # Fallback: check if console has legacy_windows property
        if hasattr(self.console, "legacy_windows") and self.console.legacy_windows:
            return False

        # Conservative fallback to ASCII
        return False

    def format_with_emoji(self, emoji: str, text: str, style: str = "") -> str:
        """Format text with emoji or ASCII fallback.

        Args:
            emoji: Emoji character to use
            text: Text content to display
            style: Rich style string for formatting

        Returns:
            str: Formatted string with emoji or ASCII fallback
        """
        if self._supports_unicode:
            icon = emoji
        else:
            icon = self.EMOJI_FALLBACKS.get(emoji, emoji)

        if style:
            return f"[{style}]{icon} {text}[/{style}]"
        return f"{icon} {text}"

    def get_icon(self, emoji: str) -> str:
        """Get appropriate icon (emoji or ASCII) for display.

        Args:
            emoji: Emoji character

        Returns:
            str: Emoji or ASCII fallback
        """
        if self._supports_unicode:
            return emoji
        return self.EMOJI_FALLBACKS.get(emoji, emoji)

    def get(self, emoji: str) -> str:
        """Convenience alias for get_icon.

        Args:
            emoji: Emoji character

        Returns:
            str: Emoji or ASCII fallback
        """
        return self.get_icon(emoji)

    def supports_unicode(self) -> bool:
        """Check if Unicode/emoji is supported.

        Returns:
            bool: True if emoji should be used
        """
        return self._supports_unicode


def create_emoji_handler(console: Console) -> SmartEmojiHandler:
    """Create SmartEmojiHandler instance.

    Args:
        console: Rich Console instance

    Returns:
        SmartEmojiHandler: Configured emoji handler
    """
    return SmartEmojiHandler(console)
