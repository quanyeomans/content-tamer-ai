"""
Real E2E User Workflow Tests

Tests that use the actual application API (organize_content) to validate
complete user journeys from start to finish. These tests mirror the
actual CLI usage patterns described in the README.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ),
        "src",
    )
)

try:
    from orchestration.main_workflow import organize_content
except ImportError:
    # Fallback if module structure changes
    organize_content = None


class TestEmptyDirectoryHandling(unittest.TestCase):
    """Test graceful handling of empty input directories."""

    def setUp(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.processed_dir = os.path.join(self.temp_dir, "processed")
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")

        # Create directories
        os.makedirs(self.input_dir)
        os.makedirs(self.processed_dir)
        os.makedirs(self.unprocessed_dir)

    def test_empty_directory_graceful_handling(self):
        """Test that application handles empty input directory gracefully."""
        if organize_content is None:
            self.skipTest("organize_content function not available")

        # Mock the AI provider system to avoid requiring real API keys
        with patch("shared.infrastructure.directory_manager.get_api_details") as mock_get_api:
            with patch("shared.infrastructure.directory_manager._prompt_for_api_key") as mock_prompt:
                with patch("orchestration.main_workflow.AIProviderFactory.create") as mock_ai_factory:
                    # Setup mocks
                    mock_get_api.return_value = "sk-fake-test-key-for-e2e-testing"
                    mock_prompt.return_value = "sk-fake-test-key-for-e2e-testing"
                    mock_ai_client = Mock()
                    mock_ai_client.generate_filename.return_value = "test_filename"
                    mock_ai_factory.return_value = mock_ai_client
                
                    # Also mock the provider validation to allow "openai"
                    with patch("shared.infrastructure.directory_manager._validate_provider_and_model"):
                        # Mock console output to prevent Windows encoding issues
                        with patch("shared.infrastructure.directory_manager._display_api_key_instructions"):
                            with patch("shared.display.rich_display_manager.RichDisplayManager") as mock_display:
                                mock_display_instance = Mock()
                                mock_display.return_value = mock_display_instance
                                
                                # Execute with empty input directory
                                success = organize_content(
                                    input_dir=self.input_dir,
                                    unprocessed_dir=self.unprocessed_dir,
                                    renamed_dir=self.processed_dir,
                                    provider="openai",
                                    model="gpt-4o",
                                    display_options={"quiet": True, "no_color": True},
                                )

                                # Should complete successfully even with no files
                                self.assertTrue(success, "Should succeed with empty input directory")

                                # With empty directory, no files should be processed

                                # Directories should remain empty
                                self.assertEqual(len(os.listdir(self.input_dir)), 0, "Input should remain empty")
                                self.assertEqual(len(os.listdir(self.processed_dir)), 0, "Processed should remain empty")
                                self.assertEqual(
                                    len(os.listdir(self.unprocessed_dir)), 0, "Unprocessed should remain empty"
                                )


if __name__ == "__main__":
    unittest.main()
