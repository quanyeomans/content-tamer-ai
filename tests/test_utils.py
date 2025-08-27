"""
Tests for utility functions (text processing, etc.)
"""

import os
import sys
import unittest

# Add src directory to path
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from utils.text_utils import truncate_content_to_token_limit


class TestTextUtils(unittest.TestCase):
    """Test text processing utilities."""

    def test_truncate_content_to_token_limit(self):
        """Test that content is truncated correctly based on token count."""
        # Short text should remain unchanged
        short_text = "This is a short text that is well within the token limit."
        self.assertEqual(truncate_content_to_token_limit(short_text, 1000), short_text)

        # Long text should be truncated
        long_text = "word " * 10000
        truncated = truncate_content_to_token_limit(long_text, 100)
        self.assertLess(len(truncated), len(long_text))

        # Verify token count is within limit
        from utils.text_utils import ENCODING

        token_count = len(ENCODING.encode(truncated))
        self.assertLessEqual(token_count, 100)

    def test_truncate_empty_content(self):
        """Test truncation with empty or None content."""
        self.assertEqual(truncate_content_to_token_limit("", 100), "")
        self.assertEqual(truncate_content_to_token_limit("   ", 100), "   ")


if __name__ == "__main__":
    unittest.main()
