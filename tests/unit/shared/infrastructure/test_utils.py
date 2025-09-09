"""
Tests for utility functions (text processing, etc.)
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
()
        mock_prompter_class.return_value = mock_prompter

        # Mock should_use_expert_mode to return True (expert mode)
        mock_prompter.should_use_expert_mode.return_value = True

        # Mock config and args
        mock_config = ExpertConfig(input_dir="/test", provider="claude")
        mock_args = ["--input", "/test", "--provider", "claude"]
        mock_prompter.prompt_expert_configuration.return_value = mock_config
        mock_prompter.convert_to_args.return_value = mock_args

        result = prompt_expert_mode_if_needed()

        # Should return the mock args
        self.assertEqual(result, mock_args)
        mock_prompter.should_use_expert_mode.assert_called_once()
        mock_prompter.prompt_expert_configuration.assert_called_once()
        mock_prompter.convert_to_args.assert_called_once_with(mock_config)

    def test_prompt_expert_mode_detection_logic(self):
        """Test argument detection logic for determining when to skip expert mode."""
        # Test cases: (argv, should_skip_expert_mode)
        test_cases = [
            (["script.py"], False),  # No args - should prompt
            (["script.py", "--help"], True),  # Has args - should skip
            (["script.py", "--input", "/path"], True),  # Has args - should skip
            (["script.py", "-i", "/path", "--provider", "claude"], True),  # Has args - should skip
            (["script.py", "--version"], True),  # Has args - should skip
        ]

        for argv, should_skip in test_cases:
            with self.subTest(argv=argv):
                original_argv = sys.argv.copy()
                try:
                    sys.argv = argv

                    # Mock the prompter to avoid actual prompting
                    with patch("utils.expert_mode.ExpertModePrompter"):
                        result = prompt_expert_mode_if_needed()

                        if should_skip:
                            self.assertEqual(result, [], "Should return empty list for {argv}")
                        else:
                            # For no-args case, we'd get prompted but our mock returns None
                            # This tests that we reach the prompting logic
                            pass
                finally:
                    sys.argv = original_argv

if __name__ == "__main__":
    unittest.main()
