"""
Tests for Phase 3 message system enhancements including progressive disclosure,
priority handling, and advanced filtering.
"""

import os
import sys
import time
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from utils.message_handler import (
    DisclosureMode,
    DisplayLocation,
    MessageConfig,
    MessageHandler,
    MessageLevel,
    MessagePriority,
)


class TestProgressiveDisclosure(unittest.TestCase):
    """Test progressive disclosure modes and their behavior."""

    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()

    def test_minimal_mode_configuration(self):
        """Test minimal disclosure mode settings."""
        config = MessageConfig(disclosure_mode=DisclosureMode.MINIMAL)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Minimal mode should show only critical errors
        self.assertFalse(handler.config.show_debug)
        self.assertFalse(handler.config.show_info)
        self.assertFalse(handler.config.show_success)
        self.assertFalse(handler.config.show_warnings)
        self.assertTrue(handler.config.show_errors)
        self.assertEqual(handler.config.min_priority, MessagePriority.CRITICAL)

    def test_standard_mode_configuration(self):
        """Test standard disclosure mode settings."""
        config = MessageConfig(disclosure_mode=DisclosureMode.STANDARD)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Standard mode should show most messages except debug
        self.assertFalse(handler.config.show_debug)
        self.assertTrue(handler.config.show_info)
        self.assertTrue(handler.config.show_success)
        self.assertTrue(handler.config.show_warnings)
        self.assertTrue(handler.config.show_errors)
        self.assertEqual(handler.config.min_priority, MessagePriority.NORMAL)

    def test_detailed_mode_configuration(self):
        """Test detailed disclosure mode settings."""
        config = MessageConfig(disclosure_mode=DisclosureMode.DETAILED)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Detailed mode should show all except debug
        self.assertFalse(handler.config.show_debug)
        self.assertTrue(handler.config.show_info)
        self.assertTrue(handler.config.show_success)
        self.assertTrue(handler.config.show_warnings)
        self.assertTrue(handler.config.show_errors)
        self.assertEqual(handler.config.min_priority, MessagePriority.LOW)

    def test_debug_mode_configuration(self):
        """Test debug disclosure mode settings."""
        config = MessageConfig(disclosure_mode=DisclosureMode.DEBUG)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Debug mode should show everything
        self.assertTrue(handler.config.show_debug)
        self.assertTrue(handler.config.show_info)
        self.assertTrue(handler.config.show_success)
        self.assertTrue(handler.config.show_warnings)
        self.assertTrue(handler.config.show_errors)
        self.assertEqual(handler.config.min_priority, MessagePriority.LOW)

    def test_runtime_disclosure_mode_change(self):
        """Test changing disclosure mode at runtime."""
        handler = MessageHandler(no_color=True, file=self.output)

        # Start with standard mode
        self.assertEqual(handler.config.disclosure_mode, DisclosureMode.STANDARD)
        self.assertTrue(handler.config.show_info)

        # Change to minimal mode
        handler.set_disclosure_mode(DisclosureMode.MINIMAL)
        self.assertEqual(handler.config.disclosure_mode, DisclosureMode.MINIMAL)
        self.assertFalse(handler.config.show_info)

        # Change to debug mode
        handler.set_disclosure_mode(DisclosureMode.DEBUG)
        self.assertEqual(handler.config.disclosure_mode, DisclosureMode.DEBUG)
        self.assertTrue(handler.config.show_debug)


class TestMessagePriorityHandling(unittest.TestCase):
    """Test message priority filtering and handling."""

    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()

    def test_priority_filtering_minimal_mode(self):
        """Test that minimal mode only shows critical priority messages."""
        config = MessageConfig(disclosure_mode=DisclosureMode.MINIMAL)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Low priority message should be filtered out
        handler.info("Low priority info", priority=MessagePriority.LOW)
        handler.warning("Normal priority warning", priority=MessagePriority.NORMAL)
        handler.error("High priority error", priority=MessagePriority.HIGH)
        handler.critical("Critical error")

        output = self.output.getvalue()
        # Only critical should appear
        self.assertNotIn("Low priority info", output)
        self.assertNotIn("Normal priority warning", output)
        self.assertNotIn("High priority error", output)
        self.assertIn("Critical error", output)

    def test_priority_filtering_standard_mode(self):
        """Test that standard mode shows normal and higher priority messages."""
        config = MessageConfig(disclosure_mode=DisclosureMode.STANDARD)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        handler.info("Low priority info", priority=MessagePriority.LOW)
        handler.info("Normal priority info", priority=MessagePriority.NORMAL)
        handler.warning("High priority warning", priority=MessagePriority.HIGH)

        output = self.output.getvalue()
        # Low priority should be filtered, others should appear
        self.assertNotIn("Low priority info", output)
        self.assertIn("Normal priority info", output)
        self.assertIn("High priority warning", output)

    def test_critical_messages_always_display(self):
        """Test that critical messages always display regardless of settings."""
        config = MessageConfig(
            disclosure_mode=DisclosureMode.MINIMAL,
            show_errors=False,  # Even with errors disabled
        )
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        handler.critical("This should always show")

        output = self.output.getvalue()
        self.assertIn("This should always show", output)


class TestMessageGroupingAndSuppression(unittest.TestCase):
    """Test message grouping and suppression functionality."""

    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()

    def test_similar_message_grouping(self):
        """Test that similar messages are grouped together."""
        config = MessageConfig(group_similar_messages=True, max_similar_messages=2)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Send similar messages
        handler.warning("API timeout occurred")
        handler.warning("API timeout occurred")  # Second occurrence - should show
        handler.warning("API timeout occurred")  # Third - should be suppressed
        handler.warning("API timeout occurred")  # Fourth - should be suppressed

        output = self.output.getvalue()
        # Should see the original and a grouped message, not individual instances
        self.assertEqual(
            output.count("API timeout occurred"), 2
        )  # Original + grouped message
        self.assertIn("similar messages", output)

    def test_suppressed_message_tracking(self):
        """Test that suppressed messages are tracked correctly."""
        config = MessageConfig(group_similar_messages=True, max_similar_messages=1)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Send messages that will be suppressed
        handler.info("Repeated message")
        handler.info("Repeated message")  # Should be suppressed
        handler.info("Repeated message")  # Should be suppressed

        # Check suppressed messages
        suppressed = handler.get_suppressed_messages()
        self.assertEqual(len(suppressed), 2)
        self.assertEqual(suppressed[0]["message"], "Repeated message")

    def test_message_grouping_can_be_disabled(self):
        """Test that message grouping can be disabled."""
        handler = MessageHandler(no_color=True, file=self.output)
        handler.set_message_grouping(enabled=False)

        # Send many similar messages
        for i in range(5):
            handler.warning("Same warning message")

        output = self.output.getvalue()
        # All messages should appear since grouping is disabled
        self.assertEqual(output.count("Same warning message"), 5)


class TestEnhancedMessageFormatting(unittest.TestCase):
    """Test enhanced message formatting features."""

    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()

    def test_timestamp_formatting(self):
        """Test timestamp addition to messages."""
        config = MessageConfig(show_timestamps=True)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        handler.info("Message with timestamp")

        output = self.output.getvalue()
        # Should contain timestamp format [HH:MM:SS]
        self.assertRegex(output, r"\[\d{2}:\d{2}:\d{2}\]")
        self.assertIn("Message with timestamp", output)

    def test_context_hints(self):
        """Test context hint addition to messages."""
        config = MessageConfig(show_context_hints=True)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        handler.error("Processing failed", context="file.pdf")

        output = self.output.getvalue()
        self.assertIn("Processing failed", output)
        self.assertIn("(file.pdf)", output)

    def test_priority_indicators_in_debug_mode(self):
        """Test that priority indicators show in debug mode."""
        config = MessageConfig(disclosure_mode=DisclosureMode.DEBUG)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        handler.warning("High priority warning", priority=MessagePriority.HIGH)
        handler.critical("Critical error")

        output = self.output.getvalue()
        self.assertIn("[HIGH]", output)
        self.assertIn("[CRITICAL]", output)


class TestSessionStatisticsAndReporting(unittest.TestCase):
    """Test session statistics and reporting functionality."""

    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()

    def test_session_statistics_tracking(self):
        """Test that session statistics are tracked correctly."""
        config = MessageConfig(disclosure_mode=DisclosureMode.DEBUG)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        handler.debug("Debug message")
        handler.info("Info message")
        handler.success("Success message")
        handler.warning("Warning message")
        handler.error("Error message")
        handler.critical("Critical message")

        stats = handler.get_session_statistics()

        self.assertEqual(stats["message_counts"]["debug"], 1)
        self.assertEqual(stats["message_counts"]["info"], 1)
        self.assertEqual(stats["message_counts"]["success"], 1)
        self.assertEqual(stats["message_counts"]["warning"], 1)
        self.assertEqual(stats["message_counts"]["error"], 1)
        self.assertEqual(stats["message_counts"]["critical"], 1)
        self.assertEqual(stats["total_messages"], 6)

    def test_enhanced_session_summary(self):
        """Test enhanced session summary display."""
        handler = MessageHandler(no_color=True, file=self.output)

        # Generate some messages
        handler.warning("Test warning")
        handler.error("Test error")
        handler.critical("Critical issue")

        # Clear output and show summary
        self.output.seek(0)
        self.output.truncate(0)
        handler.show_summary()

        summary_output = self.output.getvalue()
        self.assertIn("1 warnings", summary_output)
        self.assertIn("1 errors", summary_output)
        self.assertIn("1 critical errors", summary_output)

    def test_detailed_statistics_in_debug_mode(self):
        """Test detailed statistics in debug mode."""
        config = MessageConfig(disclosure_mode=DisclosureMode.DEBUG)
        handler = MessageHandler(config=config, no_color=True, file=self.output)

        handler.info("Info message")
        handler.warning("Warning message")

        # Clear output and show summary
        self.output.seek(0)
        self.output.truncate(0)
        handler.show_summary()

        summary_output = self.output.getvalue()
        self.assertIn("Detailed session statistics", summary_output)
        self.assertIn("Disclosure mode: debug", summary_output)


class TestAdvancedMessageFiltering(unittest.TestCase):
    """Test advanced message filtering and history management."""

    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()
        config = MessageConfig(disclosure_mode=DisclosureMode.DEBUG)
        self.handler = MessageHandler(config=config, no_color=True, file=self.output)

        # Add some test messages
        self.handler.debug("Debug message", context="test")
        self.handler.info("Info message", context="process")
        self.handler.warning("Warning message", priority=MessagePriority.HIGH)
        self.handler.error("Error message", context="test")

    def test_filter_by_message_level(self):
        """Test filtering messages by level."""
        warnings = self.handler.get_filtered_messages(level_filter=MessageLevel.WARNING)

        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["message"], "Warning message")

    def test_filter_by_priority(self):
        """Test filtering messages by priority."""
        high_priority = self.handler.get_filtered_messages(
            priority_filter=MessagePriority.HIGH
        )

        # Both warning and error should have HIGH priority
        self.assertEqual(len(high_priority), 2)
        messages = [msg["message"] for msg in high_priority]
        self.assertIn("Warning message", messages)
        self.assertIn("Error message", messages)

    def test_filter_by_context(self):
        """Test filtering messages by context."""
        test_context = self.handler.get_filtered_messages(context_filter="test")

        self.assertEqual(len(test_context), 2)  # Debug and error messages
        contexts = [msg.get("context") for msg in test_context]
        self.assertTrue(all("test" in (ctx or "") for ctx in contexts))

    def test_filter_by_time_range(self):
        """Test filtering messages by time range."""
        current_time = time.time()
        past_time = current_time - 3600  # 1 hour ago
        future_time = current_time + 3600  # 1 hour from now

        # All messages should be in this range
        recent_messages = self.handler.get_filtered_messages(
            time_range=(past_time, future_time)
        )

        self.assertEqual(len(recent_messages), 4)  # All test messages

    def test_combined_filtering(self):
        """Test combining multiple filters."""
        filtered = self.handler.get_filtered_messages(
            level_filter=MessageLevel.ERROR, context_filter="test"
        )

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["message"], "Error message")

    def test_message_history_clearing(self):
        """Test clearing message history and statistics."""
        # Verify we have messages
        self.assertEqual(len(self.handler.message_history), 4)

        # Clear history
        self.handler.clear_message_history()

        # Verify everything is cleared
        self.assertEqual(len(self.handler.message_history), 0)
        self.assertEqual(len(self.handler.suppressed_messages), 0)
        self.assertEqual(len(self.handler.message_counts), 0)
        self.assertEqual(sum(self.handler.session_stats.values()), 0)

    def test_message_log_export(self):
        """Test exporting message log data."""
        log_data = self.handler.export_message_log(include_suppressed=True)

        self.assertIn("session_stats", log_data)
        self.assertIn("disclosure_mode", log_data)
        self.assertIn("message_history", log_data)
        self.assertIn("message_patterns", log_data)
        self.assertIn("suppressed_messages", log_data)

        # Check that message history is included
        self.assertEqual(len(log_data["message_history"]), 4)


class TestBackwardCompatibilityPhase3(unittest.TestCase):
    """Test that Phase 3 enhancements maintain backward compatibility."""

    def setUp(self):
        """Set up test environment."""
        self.output = StringIO()

    def test_old_message_methods_still_work(self):
        """Test that old message method signatures still work."""
        handler = MessageHandler(no_color=True, file=self.output)

        # Test old-style method calls without new parameters
        handler.debug("Old debug call")
        handler.info("Old info call")
        handler.success("Old success call")
        handler.warning("Old warning call")
        handler.error("Old error call")
        handler.critical("Old critical call")

        # Should not crash and should produce output
        output = self.output.getvalue()
        self.assertGreater(len(output), 0)

    def test_default_configuration_unchanged(self):
        """Test that default configuration is backward compatible."""
        handler = MessageHandler(no_color=True, file=self.output)

        # Default should be standard mode
        self.assertEqual(handler.config.disclosure_mode, DisclosureMode.STANDARD)

        # Should show standard message types by default
        self.assertTrue(handler.config.show_info)
        self.assertTrue(handler.config.show_success)
        self.assertTrue(handler.config.show_warnings)
        self.assertTrue(handler.config.show_errors)

    def test_simple_message_handler_compatibility(self):
        """Test that SimpleMessageHandler still works as expected."""
        from utils.message_handler import SimpleMessageHandler

        simple_handler = SimpleMessageHandler(file=self.output)

        # Should have all expected methods
        self.assertTrue(hasattr(simple_handler, "info"))
        self.assertTrue(hasattr(simple_handler, "warning"))
        self.assertTrue(hasattr(simple_handler, "error"))
        self.assertTrue(hasattr(simple_handler, "critical"))

        # Methods should work without crashing
        simple_handler.info("Test info")
        simple_handler.warning("Test warning")

        output = self.output.getvalue()
        self.assertIn("Test info", output)
        self.assertIn("Test warning", output)


if __name__ == "__main__":
    unittest.main()
