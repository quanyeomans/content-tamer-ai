#!/usr/bin/env python3
"""
Quick test to analyze optimal token settings for 160-character filenames.
"""
import os
import sys

from utils.text_utils import ENCODING

sys.path.append("src")


def analyze_filename_tokens():
    """Analyze token requirements for optimal filename generation."""

    # Test various filename lengths
    test_filenames = [
        # Short (current AI target)
        "meeting_notes_2024_quarterly_review",
        # Medium (good descriptive length)
        "quarterly_financial_review_meeting_notes_with_action_items_march_2024",
        # Long (near 160 character limit)
        "comprehensive_quarterly_financial_review_meeting_notes_including_budget_analysis_action_items_and_strategic_planning_discussion_march_2024_v2",
        # At 160 character limit
        "very_detailed_comprehensive_quarterly_financial_review_meeting_notes_including_detailed_budget_analysis_specific_action_items_strategic_planning_session",
    ]

    print("=== Filename Token Analysis ===")
    print("Target: 160 character filename limit\n")

    for i, filename in enumerate(test_filenames, 1):
        char_count = len(filename)
        token_count = len(ENCODING.encode(filename))

        print(f"Test {i}: {char_count} chars, {token_count} tokens")
        print(f"  '{filename}'")
        print(f"  Ratio: {char_count / token_count:.2f} chars/token")
        print()

    # Calculate optimal token allocation
    max_chars = 160
    avg_chars_per_token = 4.2  # Typical for English text
    optimal_tokens = int(max_chars / avg_chars_per_token * 1.2)  # 20% buffer

    print("=== Recommendations ===")
    print("Current AI output tokens: 60-64")
    print(f"Optimal AI output tokens: {optimal_tokens}")
    print("Current prompt instruction: '50 characters max'")
    print(f"Optimal prompt instruction: '{max_chars} characters max'")

    # Test content truncation limits
    print("\n=== Content Input Analysis ===")
    sample_content = "This is a sample document content. " * 1000  # ~34k chars
    current_limit = 15000
    token_count = len(ENCODING.encode(sample_content))

    print(f"Sample content: {len(sample_content)} chars, {token_count} tokens")
    print(f"Current input limit: {current_limit} tokens")
    print(f"Utilization: {(current_limit / token_count) * 100:.1f}% of sample content")


if __name__ == "__main__":
    analyze_filename_tokens()
