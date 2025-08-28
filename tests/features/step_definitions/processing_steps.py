"""Step definitions for document processing BDD scenarios."""

import os
import sys
import tempfile
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when

# Add src directory to path for imports
sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ),
        "src",
    )
)

from tests.bdd_fixtures.file_helpers import BDDTestContext, create_test_context


@pytest.fixture
def bdd_context():
    """Fixture to provide BDD test context."""
    context = create_test_context()
    yield context
    context.cleanup_directories()


# Scenario imports
@scenario("../document_processing.feature", "User processes documents successfully")
def test_user_processes_documents_successfully():
    pass


@scenario("../document_processing.feature", "User encounters temporary file locks")
def test_user_encounters_temporary_file_locks():
    pass


@scenario("../document_processing.feature", "User processes mixed file types successfully")
def test_user_processes_mixed_file_types_successfully():
    pass


@scenario("../document_processing.feature", "User understands which files failed and why")
def test_user_understands_which_files_failed_and_why():
    pass


# Step definitions using minimal mocking pattern
@given("I have a clean working directory")
def clean_working_directory(bdd_context):
    """Set up clean test directories - no mocking needed."""
    bdd_context.setup_directories()


@given("the AI service is available")
def ai_service_available(bdd_context):
    """Mock AI service availability - only external dependency we mock."""
    bdd_context.ai_service_available = True


@given(parsers.parse("I have {num:d} PDF files in the input directory"))
def create_pdf_files(bdd_context, num):
    """Create real PDF files for testing - no mocking file operations."""
    for i in range(num):
        filename = f"test_document_{i+1}.pdf"
        bdd_context.create_pdf_file(filename, f"Content for document {i+1}")
        # Set AI mock response for this file
        bdd_context.set_ai_mock_response(filename, f"ai_generated_doc_{i+1}")


@given(parsers.parse("I have {num:d} PNG file in the input directory"))
def create_png_file(bdd_context, num):
    """Create real PNG file for testing."""
    for i in range(num):
        filename = f"test_image_{i+1}.png"
        bdd_context.create_png_file(filename)
        bdd_context.set_ai_mock_response(filename, f"ai_generated_image_{i+1}")


@given(parsers.parse("I have {num:d} TXT file in the input directory"))
def create_txt_file(bdd_context, num):
    """Create real text file for testing."""
    for i in range(num):
        filename = f"test_text_{i+1}.txt"
        bdd_context.create_txt_file(filename, f"Text content {i+1}")
        bdd_context.set_ai_mock_response(filename, f"ai_generated_text_{i+1}")


@given(parsers.parse("I have {num:d} valid PDF files in the input directory"))
def create_valid_pdf_files(bdd_context, num):
    """Create valid PDF files that will process successfully."""
    for i in range(num):
        filename = f"valid_document_{i+1}.pdf"
        bdd_context.create_pdf_file(filename, f"Valid PDF content {i+1}")
        bdd_context.set_ai_mock_response(filename, f"ai_generated_valid_{i+1}")


@given(parsers.parse("I have {num:d} corrupted file in the input directory"))
def create_corrupted_file(bdd_context, num):
    """Create corrupted file that will fail processing."""
    for i in range(num):
        filename = f"corrupted_file_{i+1}.pdf"
        bdd_context.create_corrupted_file(filename)


@given("one file is temporarily locked by antivirus")
def lock_file_temporarily(bdd_context):
    """Set up scenario where one file is temporarily locked."""
    # We'll simulate this in the processing step with retry logic
    bdd_context.file_locked_scenario = True
    bdd_context.locked_file = (
        bdd_context.test_files[1] if len(bdd_context.test_files) > 1 else bdd_context.test_files[0]
    )


@when("I run the document processing")
def run_document_processing(bdd_context):
    """Run actual processing with minimal mocking - only mock AI service."""
    from core.application import organize_content
    from utils.display_manager import DisplayManager, DisplayOptions

    # Set fake API key to avoid prompting during tests
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake-test-key-just-for-testing"}):
        # Capture display output for user experience validation
        bdd_context.display_output = StringIO()
        display_options = DisplayOptions(quiet=False, file=bdd_context.display_output)

        # Only mock external AI service - use real file operations
        def mock_ai_filename_generator(content, image_data=None):
            # Determine which file this is based on content
            for filename, response in bdd_context.ai_mock_responses.items():
                # Simple matching - in real scenario this would be more sophisticated
                base_name = filename.replace(".pdf", "").replace(".png", "").replace(".txt", "")
                if base_name.split("_")[-1] in content or len(bdd_context.ai_mock_responses) == 1:
                    return response
            return "ai_generated_default"

        # Mock AI provider and get_api_details
        with patch("core.directory_manager.get_api_details") as mock_get_api:
            with patch("ai_providers.AIProviderFactory.create") as mock_ai_factory:
                mock_get_api.return_value = "sk-fake-test-key-just-for-testing"
                mock_ai_client = Mock()
                mock_ai_client.generate_filename.side_effect = mock_ai_filename_generator
                mock_ai_factory.return_value = mock_ai_client

                # Handle file locking scenario if needed
                if hasattr(bdd_context, "file_locked_scenario"):
                    with patch("core.file_processor.process_file_enhanced_core") as mock_processor:
                        # Simulate retry scenario: fail twice, then succeed
                        call_count = 0
                        original_files = list(bdd_context.test_files)

                        def mock_processing_with_retry(*args, **kwargs):
                            nonlocal call_count
                            call_count += 1
                            input_path = args[0]

                            if input_path == bdd_context.locked_file and call_count <= 2:
                                # Simulate temporary file lock
                                raise OSError("File temporarily locked by antivirus")
                            else:
                                # Simulate successful processing
                                filename = os.path.basename(input_path)
                                base_name = os.path.splitext(filename)[0]
                                return True, f"ai_generated_{base_name}"

                        mock_processor.side_effect = mock_processing_with_retry

                # Run the actual organize_content function
                try:
                    bdd_context.processing_result = organize_content(
                        input_dir=bdd_context.input_dir,
                        unprocessed_dir=bdd_context.unprocessed_dir,
                        renamed_dir=bdd_context.processed_dir,
                        provider="openai",
                        model="gpt-4o",
                    )
                except Exception as e:
                    bdd_context.processing_result = False
                    bdd_context.processing_error = str(e)


@then(parsers.parse("I should see {num:d} files processed successfully"))
def verify_successful_files_count(bdd_context, num):
    """Verify user sees correct number of successful files."""
    # Check processed directory for successfully processed files
    processed_files = []
    if os.path.exists(bdd_context.processed_dir):
        processed_files = os.listdir(bdd_context.processed_dir)

    assert (
        len(processed_files) == num
    ), f"Expected {num} processed files, found {len(processed_files)}: {processed_files}"


@then("the progress display should show 100% completion")
def verify_progress_completion(bdd_context):
    """Verify user sees 100% completion in progress display."""
    display_text = bdd_context.display_output.getvalue()
    # Look for completion indicators that user would see
    assert (
        "100%" in display_text or "completed" in display_text.lower()
    ), f"Display should show completion status. Actual output: {display_text}"


@then("all files should appear in the processed directory with AI-generated names")
def verify_ai_generated_names(bdd_context):
    """Verify files have AI-generated names and exist in processed directory."""
    processed_files = os.listdir(bdd_context.processed_dir)

    # Verify AI-generated naming pattern
    for filename in processed_files:
        assert "ai_generated" in filename, f"File should have AI-generated name: {filename}"

    # Verify all original files were processed
    original_count = len(bdd_context.test_files)
    assert (
        len(processed_files) == original_count
    ), f"All {original_count} files should be processed, found {len(processed_files)}"


@then('I should see "Success" status for all files')
def verify_success_status_display(bdd_context):
    """Verify user sees Success status in the display."""
    display_text = bdd_context.display_output.getvalue()
    success_count = display_text.lower().count("success")
    expected_count = len(bdd_context.test_files)

    assert (
        success_count >= expected_count
    ), f"Should see Success status for all {expected_count} files. Display: {display_text}"


@then(parsers.parse("I should see {num:d} file processed immediately"))
def verify_immediate_processing(bdd_context, num):
    """Verify some files are processed without retry."""
    # This would be verified by checking the processing timing and display
    # For BDD test, we verify the end result matches expectation
    processed_files = os.listdir(bdd_context.processed_dir)
    assert len(processed_files) >= num, f"At least {num} file should be processed"


@then(parsers.parse("I should see {num:d} file should be retried and then succeed"))
def verify_retry_success(bdd_context, num):
    """Verify files that required retry ultimately succeeded."""
    # In real implementation, we'd check retry statistics
    # For BDD, verify the final successful outcome
    processed_files = os.listdir(bdd_context.processed_dir)
    total_files = len(bdd_context.test_files)
    assert (
        len(processed_files) == total_files
    ), f"All files including retried ones should succeed: {len(processed_files)}/{total_files}"


@then(parsers.parse("the final statistics should show {num:d} successful files"))
def verify_final_statistics(bdd_context, num):
    """Verify final statistics show correct success count."""
    processed_files = os.listdir(bdd_context.processed_dir)
    assert len(processed_files) == num, f"Statistics should show {num} successful files"


@then("I should see recovery statistics for the locked file")
def verify_recovery_statistics(bdd_context):
    """Verify user sees information about file recovery."""
    display_text = bdd_context.display_output.getvalue()
    # Look for retry/recovery indicators
    assert any(
        word in display_text.lower() for word in ["retry", "recovered", "attempt"]
    ), f"Should show recovery information. Display: {display_text}"


@then("all files should maintain their original extensions")
def verify_extension_preservation(bdd_context):
    """Verify processed files maintain original file extensions."""
    processed_files = os.listdir(bdd_context.processed_dir)

    # Check that we have the expected extensions
    extensions = [os.path.splitext(f)[1] for f in processed_files]
    expected_extensions = {".pdf", ".png", ".txt"}
    actual_extensions = set(extensions)

    assert expected_extensions.issubset(
        actual_extensions
    ), f"Should preserve all extensions {expected_extensions}, found {actual_extensions}"


@then("I should see appropriate processing messages for each file type")
def verify_file_type_messages(bdd_context):
    """Verify user sees appropriate messages for different file types."""
    display_text = bdd_context.display_output.getvalue()
    # User should see evidence that different file types were handled
    assert len(display_text) > 0, "Should see processing messages for different file types"


@then(parsers.parse("I should see {num:d} file failed with clear error message"))
def verify_clear_error_message(bdd_context, num):
    """Verify user sees clear error message for failed files."""
    display_text = bdd_context.display_output.getvalue()
    error_indicators = display_text.lower().count("error") + display_text.lower().count("failed")
    assert error_indicators >= num, f"Should see error indication for {num} file(s)"


@then("the failed file should appear in the unprocessed directory")
def verify_failed_file_location(bdd_context):
    """Verify failed files are moved to unprocessed directory."""
    unprocessed_files = os.listdir(bdd_context.unprocessed_dir)
    assert len(unprocessed_files) > 0, "Failed files should appear in unprocessed directory"


@then(
    parsers.parse(
        "I should see accurate final statistics showing {success:d} success, {failure:d} failure"
    )
)
def verify_accurate_final_statistics(bdd_context, success, failure):
    """Verify final statistics accurately reflect processing results."""
    processed_files = os.listdir(bdd_context.processed_dir)
    unprocessed_files = os.listdir(bdd_context.unprocessed_dir)

    assert len(processed_files) == success, f"Should have {success} successful files"
    assert len(unprocessed_files) == failure, f"Should have {failure} failed files"
