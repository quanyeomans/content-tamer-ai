"""
Integration Contracts: End-to-End Workflow Agreements
=====================================================

CONTRACT AGREEMENTS TESTED:
1. File processing workflow maintains component interface agreements
2. Success/failure determination contracts across processing pipeline
3. Display manager integration contracts with processing results
4. Directory management contracts with file operations
5. Error handling contracts across component boundaries

Migrated to use pytest tmp_path fixtures for proper cleanup and race condition elimination.
"""

import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src directory to path
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"
    )
)

from orchestration.main_workflow import _process_files_batch
from orchestration.workflow_processor import process_file_enhanced_core
from shared.display.rich_display_manager import RichDisplayManager, RichDisplayOptions
from shared.infrastructure.directory_manager import ensure_default_directories
from tests.utils.rich_test_utils import RichTestCase
from tests.utils.pytest_file_utils import create_processing_directories


class TestIntegrationContracts(unittest.TestCase, RichTestCase):
    """Contracts for end-to-end workflow component integration."""

    def setUp(self):
        """Set up test environment with temporary directories."""
        RichTestCase.setUp(self)
        # tmp_path will be injected by pytest fixture

    def tearDown(self):
        """Clean up test environment."""
        # No manual cleanup needed - pytest tmp_path handles it
        RichTestCase.tearDown(self)

    @pytest.mark.usefixtures("tmp_path")
    def test_file_processing_workflow_success_contract(self, tmp_path):
        """CONTRACT: File processing workflow produces predictable success results."""
        # Set up test environment with tmp_path
        directories = create_processing_directories(tmp_path)
        
        # Create test PDF file
        test_file = directories["input"] / "test_document.pd"
        test_file.write_bytes(b"%PDF-1.4\ntest content\n%EOF")

        # Create display manager for contract testing
        display_options = RichDisplayOptions(
            verbose=False,
            quiet=True,
            no_color=True,
            show_stats=False,
            file=self.test_console.file,
            width=80,
        )
        display_manager = self.test_container.create_display_manager(display_options)

        # Mock dependencies with contract-compliant responses
        with patch("orchestration.workflow_processor._extract_file_content") as mock_extract, \
             patch("orchestration.workflow_processor._generate_filename") as mock_filename, \
             patch("orchestration.workflow_processor._move_file_only") as mock_move:

            # Set up contract-compliant mock responses
            mock_extract.return_value = ("Sample document text content", None)
            mock_filename.return_value = "sample_document_text_content"
            mock_move.return_value = "sample_document_text_content.pdf"

            # Execute workflow contract
            success, result = process_file_enhanced_core(
                input_path=str(test_file),
                filename="test_document.pd",
                unprocessed_folder=str(directories["unprocessed"]),
                renamed_folder=str(directories["processed"]),
                progress_f=MagicMock(),
                ocr_lang="eng",
                ai_client=Mock(),
                organizer=Mock(),
                display_context=Mock()
            )

            # Assert contract compliance
            self.assertTrue(success, "Success contract: Workflow must return True for successful processing")
            self.assertIsInstance(result, str, "Result contract: Success result must be string filename")
            self.assertTrue(result.endswith(".pdf"), "Filename contract: Result must maintain file extension")

            # Assert Rich I/O contract compliance
            self.assert_no_rich_io_errors()

    @pytest.mark.usefixtures("tmp_path")
    def test_file_processing_workflow_failure_contract(self, tmp_path):
        """CONTRACT: File processing workflow handles failures with predictable error responses."""
        # Set up test environment with tmp_path
        directories = create_processing_directories(tmp_path)
        
        # Create test file that will fail processing
        test_file = directories["input"] / "corrupted_document.pd"
        test_file.write_text("Not a valid PDF file")

        # Mock extraction failure to test error contract
        with patch("orchestration.workflow_processor._extract_file_content") as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed - corrupted file")

            # Execute workflow failure contract
            success, result = process_file_enhanced_core(
                input_path=str(test_file),
                filename="corrupted_document.pd",
                unprocessed_folder=str(directories["unprocessed"]),
                renamed_folder=str(directories["processed"]),
                progress_f=MagicMock(),
                ocr_lang="eng",
                ai_client=Mock(),
                organizer=Mock(),
                display_context=Mock()
            )

            # Assert failure contract compliance
            self.assertFalse(success, "Failure contract: Workflow must return False for failed processing")
            self.assertIsNone(result, "Error contract: Failed processing must return None result")

    @pytest.mark.usefixtures("tmp_path")
    def test_display_manager_contract_with_processing_results(self, tmp_path):
        """CONTRACT: Display manager integrates correctly with processing workflow results."""
        # Set up test environment with tmp_path
        directories = create_processing_directories(tmp_path)

        # Create test files for display contract testing
        test_files = []
        for i in range(3):
            test_file = directories["input"] / f"document_{i}.pd"
            test_file.write_bytes(b"%PDF-1.4\ntest content\n%EOF")
            test_files.append(str(test_file))

        # Create display manager with contract specifications
        display_options = RichDisplayOptions(
            verbose=True,
            quiet=False,
            no_color=True,
            show_stats=True,
            file=self.test_console.file,
            width=80,
        )
        display_manager = self.test_container.create_display_manager(display_options)

        # Mock processing workflow for display contract testing
        with patch("orchestration.main_workflow._process_files_batch") as mock_batch:
            mock_batch.return_value = (3, 0, 0)  # 3 success, 0 failed, 0 retry

            # Execute display manager contract
            try:
                success_count, failed_count, retry_count = _process_files_batch(
                    test_files,
                    str(directories["processed"]),
                    str(directories["unprocessed"]),
                    Mock(),  # AI client
                    Mock(),  # Organizer
                    display_manager,
                    "eng"  # OCR language
                )

                # Assert display manager contract compliance
                self.assertEqual(success_count, 3, "Display contract: Must report correct success count")
                self.assertEqual(failed_count, 0, "Display contract: Must report correct failure count")
                self.assertEqual(retry_count, 0, "Display contract: Must report correct retry count")

                # Assert Rich display contract compliance
                self.assert_no_rich_io_errors()
                
            except Exception as e:
                self.fail(f"Display manager contract violation: {str(e)}")

    @pytest.mark.usefixtures("tmp_path")
    def test_directory_management_contract_with_file_operations(self, tmp_path):
        """CONTRACT: Directory management maintains file operation contracts."""
        # Test directory contract compliance
        directories = create_processing_directories(tmp_path)

        # Assert directory contract compliance
        required_dirs = ["input", "output", "processed", "unprocessed", "temp"]
        for dir_key in required_dirs:
            self.assertIn(dir_key, directories, f"Directory contract: {dir_key} must be created")
            self.assertTrue(directories[dir_key].exists(), f"Directory contract: {dir_key} must exist")
            self.assertTrue(directories[dir_key].is_dir(), f"Directory contract: {dir_key} must be directory")

        # Test file operations contract
        test_file_path = directories["input"] / "contract_test.pd"
        test_file_path.write_text("Contract test content")

        # Assert file operations contract compliance
        self.assertTrue(test_file_path.exists(), "File contract: Created files must exist")
        self.assertEqual(
            test_file_path.read_text(), 
            "Contract test content", 
            "File contract: File content must be preserved"
        )

        # Test move operation contract
        target_path = directories["processed"] / "contract_test.pd"
        test_file_path.rename(target_path)

        # Assert move contract compliance
        self.assertFalse(test_file_path.exists(), "Move contract: Source file must not exist after move")
        self.assertTrue(target_path.exists(), "Move contract: Target file must exist after move")
        self.assertEqual(
            target_path.read_text(), 
            "Contract test content", 
            "Move contract: File content must be preserved during move"
        )

    @pytest.mark.usefixtures("tmp_path")
    def test_error_handling_contracts_across_component_boundaries(self, tmp_path):
        """CONTRACT: Error handling maintains consistent contracts across component boundaries."""
        # Set up test environment with tmp_path
        directories = create_processing_directories(tmp_path)

        # Create scenarios that test error boundary contracts
        error_scenarios = [
            ("missing_file", "nonexistent.pd", FileNotFoundError),
            ("empty_file", "empty.pd", Exception),
            ("locked_file", "locked.pd", PermissionError),
        ]

        for scenario_name, filename, expected_error_type in error_scenarios:
            with self.subTest(scenario=scenario_name):
                if scenario_name == "empty_file":
                    # Create empty file for testing
                    test_file = directories["input"] / filename
                    test_file.write_text("")
                    file_path = str(test_file)
                elif scenario_name == "locked_file":
                    # Create file for locking test
                    test_file = directories["input"] / filename
                    test_file.write_text("locked content")
                    file_path = str(test_file)
                else:
                    # Missing file scenario
                    file_path = str(directories["input"] / filename)

                # Mock component to raise expected error
                with patch("orchestration.workflow_processor._extract_file_content") as mock_extract:
                    mock_extract.side_effect = expected_error_type(f"Simulated {scenario_name} error")

                    # Execute error handling contract
                    success, result = process_file_enhanced_core(
                        input_path=file_path,
                        filename=filename,
                        unprocessed_folder=str(directories["unprocessed"]),
                        renamed_folder=str(directories["processed"]),
                        progress_f=MagicMock(),
                        ocr_lang="eng",
                        ai_client=Mock(),
                        organizer=Mock(),
                        display_context=Mock()
                    )

                    # Assert error handling contract compliance
                    self.assertFalse(
                        success, 
                        f"Error contract ({scenario_name}): Must return False for {expected_error_type.__name__}"
                    )
                    self.assertIsNone(
                        result, 
                        f"Error contract ({scenario_name}): Must return None for {expected_error_type.__name__}"
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)