"""
Hierarchical message handling for CLI applications.

Provides structured message display with proper visual hierarchy,
respecting user preferences for verbosity and quiet modes.
"""

import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, TextIO, Tuple

from .cli_display import ColorFormatter, Colors, MessageLevel


class DisplayLocation(Enum):
    """Where messages should be displayed relative to progress."""

    ABOVE_PROGRESS = "above"
    BELOW_PROGRESS = "below"
    REPLACE_PROGRESS = "replace"
    INLINE = "inline"


class MessagePriority(Enum):
    """Message priority levels for filtering and display."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class DisclosureMode(Enum):
    """Progressive disclosure modes for different user experiences."""

    MINIMAL = "minimal"  # Only critical errors and final results
    STANDARD = "standard"  # Errors, warnings, and key status updates
    DETAILED = "detailed"  # All messages except debug
    DEBUG = "debug"  # Everything including debug messages


@dataclass
class MessageConfig:
    """Enhanced configuration for message display behavior."""

    show_debug: bool = False
    show_info: bool = True
    show_success: bool = True
    show_warnings: bool = True
    show_errors: bool = True
    quiet_mode: bool = False
    verbose_mode: bool = False
    max_message_history: int = 100

    # Phase 3 enhancements
    disclosure_mode: DisclosureMode = DisclosureMode.STANDARD
    min_priority: MessagePriority = MessagePriority.NORMAL
    show_timestamps: bool = False
    group_similar_messages: bool = True
    max_similar_messages: int = 3
    show_context_hints: bool = True
    enable_message_filtering: bool = True


class MessageHandler:
    """Enhanced hierarchical message display with progressive disclosure."""

    def __init__(
        self,
        config: Optional[MessageConfig] = None,
        no_color: bool = False,
        file: Optional[TextIO] = None,
    ):
        self.config = config or MessageConfig()
        self.formatter = ColorFormatter(no_color=no_color)
        self.file = file or sys.stdout
        self.message_history: List[Dict[str, Any]] = []
        self._progress_active = False

        # Phase 3 enhancements
        self.message_counts: Dict[str, int] = {}  # Track similar messages
        self.suppressed_messages: List[Dict[str, Any]] = []
        self.session_stats = {
            "debug": 0,
            "info": 0,
            "success": 0,
            "warning": 0,
            "error": 0,
            "critical": 0,
        }
        self._apply_disclosure_mode()

    def _apply_disclosure_mode(self) -> None:
        """Apply progressive disclosure settings based on mode."""
        mode = self.config.disclosure_mode

        if mode == DisclosureMode.MINIMAL:
            self.config.show_debug = False
            self.config.show_info = False
            self.config.show_success = False
            self.config.show_warnings = False
            self.config.show_errors = True
            self.config.min_priority = MessagePriority.CRITICAL

        elif mode == DisclosureMode.STANDARD:
            self.config.show_debug = False
            self.config.show_info = True
            self.config.show_success = True
            self.config.show_warnings = True
            self.config.show_errors = True
            self.config.min_priority = MessagePriority.NORMAL

        elif mode == DisclosureMode.DETAILED:
            self.config.show_debug = False
            self.config.show_info = True
            self.config.show_success = True
            self.config.show_warnings = True
            self.config.show_errors = True
            self.config.min_priority = MessagePriority.LOW

        elif mode == DisclosureMode.DEBUG:
            self.config.show_debug = True
            self.config.show_info = True
            self.config.show_success = True
            self.config.show_warnings = True
            self.config.show_errors = True
            self.config.min_priority = MessagePriority.LOW

    def set_disclosure_mode(self, mode: DisclosureMode) -> None:
        """Change disclosure mode at runtime."""
        self.config.disclosure_mode = mode
        self._apply_disclosure_mode()

    def configure(
        self, quiet: bool = False, verbose: bool = False, no_color: bool = False
    ) -> None:
        """Update configuration settings."""
        if quiet:
            self.config.quiet_mode = True
            self.config.show_info = False
            self.config.show_success = False
            self.config.show_debug = False

        if verbose:
            self.config.verbose_mode = True
            self.config.show_debug = True
            self.config.show_info = True

        if no_color:
            self.formatter = ColorFormatter(no_color=True)

    def set_progress_active(self, active: bool) -> None:
        """Notify handler whether progress display is currently active."""
        self._progress_active = active

    def debug(
        self,
        message: str,
        location: DisplayLocation = DisplayLocation.BELOW_PROGRESS,
        priority: MessagePriority = MessagePriority.LOW,
        context: Optional[str] = None,
    ) -> None:
        """Enhanced debug message with priority and context."""
        if self.config.show_debug and self._should_display_message(
            MessageLevel.DEBUG, priority
        ):
            self._display_message_enhanced(
                message, MessageLevel.DEBUG, location, priority, context
            )

    def info(
        self,
        message: str,
        location: DisplayLocation = DisplayLocation.BELOW_PROGRESS,
        priority: MessagePriority = MessagePriority.NORMAL,
        context: Optional[str] = None,
    ) -> None:
        """Enhanced info message with priority and context."""
        if (
            self.config.show_info
            and not self.config.quiet_mode
            and self._should_display_message(MessageLevel.INFO, priority)
        ):
            self._display_message_enhanced(
                message, MessageLevel.INFO, location, priority, context
            )

    def success(
        self,
        message: str,
        location: DisplayLocation = DisplayLocation.BELOW_PROGRESS,
        brief: bool = True,
        priority: MessagePriority = MessagePriority.NORMAL,
        context: Optional[str] = None,
    ) -> None:
        """Enhanced success message with priority and context."""
        if (
            self.config.show_success
            and not self.config.quiet_mode
            and self._should_display_message(MessageLevel.SUCCESS, priority)
        ):
            self._display_message_enhanced(
                message, MessageLevel.SUCCESS, location, priority, context
            )

    def warning(
        self,
        message: str,
        location: DisplayLocation = DisplayLocation.BELOW_PROGRESS,
        priority: MessagePriority = MessagePriority.HIGH,
        context: Optional[str] = None,
    ) -> None:
        """Enhanced warning message with priority and context."""
        if self.config.show_warnings and self._should_display_message(
            MessageLevel.WARNING, priority
        ):
            self._display_message_enhanced(
                message, MessageLevel.WARNING, location, priority, context
            )

    def error(
        self,
        message: str,
        location: DisplayLocation = DisplayLocation.BELOW_PROGRESS,
        priority: MessagePriority = MessagePriority.HIGH,
        context: Optional[str] = None,
    ) -> None:
        """Enhanced error message with priority and context."""
        if self.config.show_errors and self._should_display_message(
            MessageLevel.ERROR, priority
        ):
            self._display_message_enhanced(
                message, MessageLevel.ERROR, location, priority, context
            )

    def critical(
        self,
        message: str,
        location: DisplayLocation = DisplayLocation.REPLACE_PROGRESS,
        context: Optional[str] = None,
    ) -> None:
        """Enhanced critical error message (always shown)."""
        # Critical messages always display regardless of settings
        self._display_message_enhanced(
            message, MessageLevel.CRITICAL, location, MessagePriority.CRITICAL, context
        )

    def _should_display_message(
        self, level: MessageLevel, priority: MessagePriority
    ) -> bool:
        """Determine if message should be displayed based on priority and disclosure mode."""
        # Critical messages always display
        if level == MessageLevel.CRITICAL:
            return True

        # Check minimum priority threshold
        if priority.value < self.config.min_priority.value:
            return False

        return True

    def _get_message_key(self, message: str) -> str:
        """Generate key for grouping similar messages."""
        # Simple grouping based on first few words and message type indicators
        words = message.lower().split()[:3]
        return " ".join(words)

    def _display_message_enhanced(
        self,
        message: str,
        level: MessageLevel,
        location: DisplayLocation,
        priority: MessagePriority,
        context: Optional[str] = None,
    ) -> None:
        """Enhanced message display with grouping and filtering."""
        # Update session statistics
        level_name = level.value
        if level_name in self.session_stats:
            self.session_stats[level_name] += 1

        # Check for message grouping
        if self.config.group_similar_messages and level != MessageLevel.CRITICAL:
            message_key = self._get_message_key(message)
            count = self.message_counts.get(message_key, 0) + 1
            self.message_counts[message_key] = count

            # Suppress if we've seen this message too many times
            if count > self.config.max_similar_messages:
                self.suppressed_messages.append(
                    {
                        "message": message,
                        "level": level,
                        "timestamp": time.time(),
                        "priority": priority,
                        "context": context,
                    }
                )
                return
            elif count == self.config.max_similar_messages:
                # Show grouping message
                grouped_msg = f"{message} (and {count - 1} similar messages)"
                message = grouped_msg

        # Format message with enhancements
        formatted_message = self._format_enhanced_message(
            message, level, priority, context
        )
        timestamp = time.time()

        # Store in history
        self.message_history.append(
            {
                "message": message,
                "level": level,
                "timestamp": timestamp,
                "formatted": formatted_message,
                "priority": priority,
                "context": context,
            }
        )

        # Trim history if needed
        if len(self.message_history) > self.config.max_message_history:
            self.message_history = self.message_history[
                -self.config.max_message_history :
            ]

        # Display the message
        self._render_message(formatted_message, location)

    def _format_enhanced_message(
        self,
        message: str,
        level: MessageLevel,
        priority: MessagePriority,
        context: Optional[str] = None,
    ) -> str:
        """Format message with enhanced features."""
        base_message = self.formatter.format_message(message, level)

        # Add timestamp if enabled
        if self.config.show_timestamps:
            timestamp = time.strftime("%H:%M:%S")
            base_message = f"[{timestamp}] {base_message}"

        # Add context hint if available and enabled
        if context and self.config.show_context_hints:
            context_hint = self.formatter.colorize(f" ({context})", "dim")
            base_message = f"{base_message}{context_hint}"

        # Add priority indicator for high priority messages
        if priority == MessagePriority.CRITICAL:
            priority_indicator = self.formatter.colorize(
                " [CRITICAL]", "bright_red", bold=True
            )
            base_message = f"{base_message}{priority_indicator}"
        elif (
            priority == MessagePriority.HIGH
            and self.config.disclosure_mode == DisclosureMode.DEBUG
        ):
            priority_indicator = self.formatter.colorize(" [HIGH]", "bright_yellow")
            base_message = f"{base_message}{priority_indicator}"

        return base_message

    def _render_message(
        self, formatted_message: str, location: DisplayLocation
    ) -> None:
        """Render message to output based on location."""
        # Handle display based on location and progress state
        if location == DisplayLocation.REPLACE_PROGRESS and self._progress_active:
            # Clear progress line and show message
            self._clear_progress_line()
            self.file.write(f"{formatted_message}\n")
            self.file.flush()
        elif location == DisplayLocation.ABOVE_PROGRESS and self._progress_active:
            # Move up, show message, then restore progress
            if not self.formatter.no_color:
                self.file.write(
                    f"\r{Colors.CURSOR_UP}{formatted_message}\n{Colors.CURSOR_DOWN}"
                )
            else:
                self.file.write(f"\n{formatted_message}")
            self.file.flush()
        elif location == DisplayLocation.BELOW_PROGRESS:
            # Show message below current progress
            if self._progress_active:
                # Move to new line after progress, show message, no extra newline
                self.file.write(f"\n{formatted_message}")
            else:
                self.file.write(f"\n{formatted_message}\n")
            self.file.flush()
        else:  # INLINE or default
            self.file.write(f"{formatted_message}\n")
            self.file.flush()

    def _display_message(
        self, message: str, level: MessageLevel, location: DisplayLocation
    ) -> None:
        """Internal method to handle message display logic."""
        formatted_message = self.formatter.format_message(message, level)
        timestamp = time.time()

        # Store in history
        self.message_history.append(
            {
                "message": message,
                "level": level,
                "timestamp": timestamp,
                "formatted": formatted_message,
            }
        )

        # Trim history if needed
        if len(self.message_history) > self.config.max_message_history:
            self.message_history = self.message_history[
                -self.config.max_message_history :
            ]

        # Handle display based on location and progress state
        if location == DisplayLocation.REPLACE_PROGRESS and self._progress_active:
            # Clear progress line and show message
            self._clear_progress_line()
            self.file.write(f"{formatted_message}\n")
            self.file.flush()
        elif location == DisplayLocation.ABOVE_PROGRESS and self._progress_active:
            # Move up, show message, then restore progress
            if not self.formatter.no_color:
                self.file.write(
                    f"\r{Colors.CURSOR_UP}{formatted_message}\n{Colors.CURSOR_DOWN}"
                )
            else:
                self.file.write(f"\n{formatted_message}")
            self.file.flush()
        elif location == DisplayLocation.BELOW_PROGRESS:
            # Show message below current progress
            if self._progress_active:
                # Move to new line after progress, show message, no extra newline
                self.file.write(f"\n{formatted_message}")
            else:
                self.file.write(f"\n{formatted_message}\n")
            self.file.flush()
        else:  # INLINE or default
            self.file.write(f"{formatted_message}\n")
            self.file.flush()

    def _clear_progress_line(self) -> None:
        """Clear the current progress line and stats line."""
        if not self.formatter.no_color:
            # Clear current line and potential stats line below
            self.file.write(f"\r{Colors.CLEAR_LINE}")
            # Also clear the line below (stats line) and return cursor
            self.file.write(f"\n{Colors.CLEAR_LINE}\r{Colors.CURSOR_UP}")
        else:
            self.file.write("\r" + " " * 80 + "\r")

    def show_summary(self) -> None:
        """Enhanced session summary with statistics and suppressed messages."""
        if self.config.quiet_mode:
            return

        # Show main summary
        summary_parts = []

        # Use session_stats for accurate counts
        if self.session_stats["warning"] > 0:
            summary_parts.append(
                self.formatter.colorize(
                    f"{self.session_stats['warning']} warnings", "bright_yellow"
                )
            )

        if self.session_stats["error"] > 0:
            summary_parts.append(
                self.formatter.colorize(
                    f"{self.session_stats['error']} errors", "bright_red"
                )
            )

        if self.session_stats["critical"] > 0:
            summary_parts.append(
                self.formatter.colorize(
                    f"{self.session_stats['critical']} critical errors",
                    "bright_red",
                    bold=True,
                )
            )

        # Show suppressed message count if any
        if (
            self.suppressed_messages
            and self.config.disclosure_mode != DisclosureMode.MINIMAL
        ):
            suppressed_count = len(self.suppressed_messages)
            summary_parts.append(
                self.formatter.colorize(
                    f"{suppressed_count} similar messages suppressed", "dim"
                )
            )

        if summary_parts:
            self.file.write(f"\nSession summary: {' • '.join(summary_parts)}\n")
            self.file.flush()

        # Show detailed stats in debug mode
        if self.config.disclosure_mode == DisclosureMode.DEBUG:
            self._show_detailed_stats()

    def _show_detailed_stats(self) -> None:
        """Show detailed session statistics."""
        self.file.write("\nDetailed session statistics:\n")

        for level, count in self.session_stats.items():
            if count > 0:
                level_display = level.capitalize()
                color_map = {
                    "debug": "dim",
                    "info": "blue",
                    "success": "bright_green",
                    "warning": "bright_yellow",
                    "error": "bright_red",
                    "critical": "bright_red",
                }
                color = color_map.get(level, "white")
                formatted_stat = self.formatter.colorize(
                    f"  {level_display}: {count}", color
                )
                self.file.write(f"{formatted_stat}\n")

        # Show disclosure mode
        mode_display = self.formatter.colorize(
            f"  Disclosure mode: {self.config.disclosure_mode.value}", "cyan"
        )
        self.file.write(f"{mode_display}\n")

        # Show most frequent message types
        if self.message_counts:
            self.file.write("\nMost frequent message patterns:\n")
            sorted_patterns = sorted(
                self.message_counts.items(), key=lambda x: x[1], reverse=True
            )[:3]
            for pattern, count in sorted_patterns:
                if count > 1:
                    pattern_display = self.formatter.colorize(
                        f'  "{pattern}...": {count} times', "dim"
                    )
                    self.file.write(f"{pattern_display}\n")

        self.file.flush()

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        return {
            "message_counts": self.session_stats.copy(),
            "total_messages": sum(self.session_stats.values()),
            "suppressed_count": len(self.suppressed_messages),
            "disclosure_mode": self.config.disclosure_mode.value,
            "message_patterns": self.message_counts.copy(),
            "history_size": len(self.message_history),
        }

    def get_recent_messages(
        self, count: int = 10, level_filter: Optional[MessageLevel] = None
    ) -> List[Dict[str, Any]]:
        """Get recent messages, optionally filtered by level."""
        messages = self.message_history

        if level_filter:
            messages = [msg for msg in messages if msg["level"] == level_filter]

        return messages[-count:] if count > 0 else messages

    def get_filtered_messages(
        self,
        level_filter: Optional[MessageLevel] = None,
        priority_filter: Optional[MessagePriority] = None,
        time_range: Optional[Tuple[float, float]] = None,
        context_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages with advanced filtering options."""
        messages = self.message_history.copy()

        # Filter by level
        if level_filter:
            messages = [msg for msg in messages if msg.get("level") == level_filter]

        # Filter by priority
        if priority_filter:
            messages = [
                msg for msg in messages if msg.get("priority") == priority_filter
            ]

        # Filter by time range (start_time, end_time)
        if time_range:
            start_time, end_time = time_range
            messages = [
                msg
                for msg in messages
                if start_time <= msg.get("timestamp", 0) <= end_time
            ]

        # Filter by context
        if context_filter:
            messages = [
                msg
                for msg in messages
                if context_filter.lower() in (msg.get("context", "") or "").lower()
            ]

        return messages

    def get_suppressed_messages(
        self, level_filter: Optional[MessageLevel] = None
    ) -> List[Dict[str, Any]]:
        """Get messages that were suppressed due to grouping."""
        messages = self.suppressed_messages.copy()

        if level_filter:
            messages = [msg for msg in messages if msg.get("level") == level_filter]

        return messages

    def clear_message_history(self) -> None:
        """Clear message history and reset statistics."""
        self.message_history.clear()
        self.suppressed_messages.clear()
        self.message_counts.clear()
        self.session_stats = {
            "debug": 0,
            "info": 0,
            "success": 0,
            "warning": 0,
            "error": 0,
            "critical": 0,
        }

    def export_message_log(
        self, include_suppressed: bool = False
    ) -> List[Dict[str, Any]]:
        """Export complete message log for analysis or debugging."""
        log_data = {
            "session_stats": self.session_stats.copy(),
            "disclosure_mode": self.config.disclosure_mode.value,
            "message_history": self.message_history.copy(),
            "message_patterns": self.message_counts.copy(),
        }

        if include_suppressed:
            log_data["suppressed_messages"] = self.suppressed_messages.copy()

        return log_data

    def set_message_grouping(self, enabled: bool, max_similar: int = 3) -> None:
        """Configure message grouping behavior."""
        self.config.group_similar_messages = enabled
        self.config.max_similar_messages = max_similar

        # Clear existing counts if disabling
        if not enabled:
            self.message_counts.clear()

    def replay_suppressed_messages(
        self, level_filter: Optional[MessageLevel] = None
    ) -> None:
        """Replay suppressed messages (useful for debugging)."""
        suppressed = self.get_suppressed_messages(level_filter)

        if not suppressed:
            self.info("No suppressed messages to replay")
            return

        self.info(f"Replaying {len(suppressed)} suppressed messages:")

        for msg in suppressed:
            # Temporarily disable grouping to show all messages
            original_grouping = self.config.group_similar_messages
            self.config.group_similar_messages = False

            try:
                # Re-display the message
                formatted = self._format_enhanced_message(
                    msg["message"],
                    msg["level"],
                    msg.get("priority", MessagePriority.NORMAL),
                    msg.get("context"),
                )
                replay_formatted = (
                    self.formatter.colorize("[REPLAY] ", "dim") + formatted
                )
                self._render_message(replay_formatted, DisplayLocation.BELOW_PROGRESS)

            finally:
                self.config.group_similar_messages = original_grouping

    @contextmanager
    def temporary_quiet(self):
        """Temporarily suppress non-critical messages."""
        original_config = MessageConfig(
            show_debug=self.config.show_debug,
            show_info=self.config.show_info,
            show_success=self.config.show_success,
            show_warnings=self.config.show_warnings,
            quiet_mode=self.config.quiet_mode,
        )

        # Temporarily enable quiet mode
        self.config.show_debug = False
        self.config.show_info = False
        self.config.show_success = False
        self.config.show_warnings = False
        self.config.quiet_mode = True

        try:
            yield self
        finally:
            # Restore original configuration
            self.config.show_debug = original_config.show_debug
            self.config.show_info = original_config.show_info
            self.config.show_success = original_config.show_success
            self.config.show_warnings = original_config.show_warnings
            self.config.quiet_mode = original_config.quiet_mode

    @contextmanager
    def capture_messages(self):
        """Capture messages instead of displaying them immediately."""
        captured_messages = []
        original_display = self._display_message

        def capture_display(
            message: str, level: MessageLevel, location: DisplayLocation
        ) -> None:
            formatted = self.formatter.format_message(message, level)
            captured_messages.append(
                {
                    "message": message,
                    "level": level,
                    "location": location,
                    "formatted": formatted,
                    "timestamp": time.time(),
                }
            )

        self._display_message = capture_display

        try:
            yield captured_messages
        finally:
            self._display_message = original_display


class SimpleMessageHandler:
    """Simple fallback message handler for compatibility."""

    def __init__(self, file: Optional[TextIO] = None, **kwargs):
        self.file = file or sys.stdout

    def configure(self, **kwargs) -> None:
        pass

    def set_progress_active(self, active: bool) -> None:
        pass

    def debug(self, message: str, **kwargs) -> None:
        pass  # Debug messages not shown in simple mode

    def info(self, message: str, **kwargs) -> None:
        self.file.write(f"[INFO] {message}\n")
        self.file.flush()

    def success(self, message: str, **kwargs) -> None:
        self.file.write(f"[SUCCESS] {message}\n")
        self.file.flush()

    def warning(self, message: str, **kwargs) -> None:
        self.file.write(f"[WARNING] {message}\n")
        self.file.flush()

    def error(self, message: str, **kwargs) -> None:
        self.file.write(f"[ERROR] {message}\n")
        self.file.flush()

    def critical(self, message: str, **kwargs) -> None:
        self.file.write(f"[CRITICAL] {message}\n")
        self.file.flush()

    def show_summary(self) -> None:
        pass

    def get_recent_messages(self, **kwargs) -> List[Dict[str, Any]]:
        return []

    def temporary_quiet(self):
        return self

    def capture_messages(self):
        return self

    def __enter__(self):
        return []

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
