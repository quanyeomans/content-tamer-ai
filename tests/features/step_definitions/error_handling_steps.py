"""Step definitions for error handling and user communication BDD scenarios."""

import os
import shutil
import sys
import tempfile
from io import StringIO
from unittest.mock import Mock

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

from utils.display_manager import DisplayManager, DisplayOptions
from utils.error_handling import create_retry_handler


@pytest.fixture
def error_context():
    """Context for error handling tests."""
    context = type("ErrorContext", (), {})()
    context.temp_dir = tempfile.mkdtemp()
    context.display_output = StringIO()
    context.display_options = DisplayOptions(quiet=False, file=context.display_output)
    context.display_manager = DisplayManager(context.display_options)
    yield context
    if os.path.exists(context.temp_dir):
        shutil.rmtree(context.temp_dir)


# Scenario imports
@scenario(
    "../error_handling.feature", "User sees clear feedback for file processing failures"
)
def test_user_sees_clear_feedback_for_file_processing_failures():
    pass


@scenario(
    "../error_handling.feature",
    "User sees recovery information when files succeed after retries",
)
def test_user_sees_recovery_information_when_files_succeed_after_retries():
    pass


@scenario(
    "../error_handling.feature",
    "User sees accurate progress statistics during mixed outcomes",
)
def test_user_sees_accurate_progress_statistics_during_mixed_outcomes():
    pass


# Step definitions focusing on user-observable behavior
@given("I have a clean test environment")
def clean_test_environment(error_context):
    """Set up clean test environment for error handling tests."""
    # Environment is already clean from fixture
    error_context.initial_success_count = (
        error_context.display_manager.progress.stats.success_count
    )
    error_context.initial_error_count = (
        error_context.display_manager.progress.stats.failed
    )


@when("I simulate a file processing failure")
def simulate_file_processing_failure(error_context):
    """Simulate a file that fails processing."""
    with error_context.display_manager.processing_context(
        total_files=1
    ) as display_context:
        # Simulate what happens when a file fails processing
        display_context.fail_file(
            "test_file.pdf", "Processing failed due to corruption"
        )
        error_context.processing_context = display_context


@when("I simulate a file that succeeds after retry attempts")
def simulate_retry_success(error_context):
    """Simulate file that succeeds after retries."""
    retry_handler = create_retry_handler(max_attempts=3)

    # Simulate operation that fails twice then succeeds
    call_count = 0

    def mock_operation():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise OSError("File temporarily locked by antivirus")
        return "successfully_processed_file.pdf"

    with error_context.display_manager.processing_context(
        total_files=1
    ) as display_context:
        # Execute retry operation
        success, result, error_classification = retry_handler.execute_with_retry(
            operation=mock_operation,
            display_context=display_context,
            filename="test_file.pdf",
        )

        # Complete the file based on retry result
        if success:
            display_context.complete_file("test_file.pdf", result)
        else:
            display_context.fail_file(
                "test_file.pdf", f"Failed after retries: {error_classification}"
            )

        error_context.retry_success = success
        error_context.retry_result = result
        error_context.call_count = call_count


@when("I simulate processing 3 successful files and 2 failed files")
def simulate_mixed_processing_outcomes(error_context):
    """Simulate batch processing with mixed outcomes."""
    with error_context.display_manager.processing_context(
        total_files=5
    ) as display_context:
        # Process 3 successful files
        display_context.complete_file("success1.pdf", "renamed_success1.pdf")
        display_context.complete_file("success2.pdf", "renamed_success2.pdf")
        display_context.complete_file("success3.pdf", "renamed_success3.pdf")

        # Process 2 failed files
        display_context.fail_file("failed1.pdf", "Corrupted file")
        display_context.fail_file("failed2.pdf", "Unsupported format")


@then("I should see clear error communication")
def verify_clear_error_communication(error_context):
    """Verify user sees clear error communication."""
    display_output = error_context.display_output.getvalue()

    # User should see error indication
    assert (
        "error" in display_output.lower() or "failed" in display_output.lower()
    ), f"Display should show error communication. Output: {display_output}"


@then("the error count should be incremented")
def verify_error_count_incremented(error_context):
    """Verify error count increased correctly."""
    final_error_count = error_context.display_manager.progress.stats.failed
    expected_error_count = error_context.initial_error_count + 1

    assert (
        final_error_count == expected_error_count
    ), f"Error count should be {expected_error_count}, got {final_error_count}"


@then("I should understand what went wrong")
def verify_error_understanding(error_context):
    """Verify user can understand what went wrong."""
    display_output = error_context.display_output.getvalue()

    # Look for error indicators that user can see
    error_indicators = ["failed", "error", "✗"]
    has_error_indicator = any(
        indicator in display_output.lower() for indicator in error_indicators
    )

    assert (
        has_error_indicator
    ), f"Should see clear error indicators. Output: {display_output}"


@then("I should see recovery success information")
def verify_recovery_success_information(error_context):
    """Verify user sees recovery success information."""
    # The file should have ultimately succeeded
    assert error_context.retry_success, "File should succeed after retries"
    assert error_context.call_count == 3, "Should have made 3 attempts"


@then("the final result should show success not failure")
def verify_final_result_shows_success(error_context):
    """Verify final result shows success for retried files."""
    final_success_count = error_context.display_manager.progress.stats.success_count
    final_error_count = error_context.display_manager.progress.stats.failed

    # Should show success, not failure, for files that eventually succeed
    assert (
        final_success_count == error_context.initial_success_count + 1
    ), "Retry success should increment success counter"
    assert (
        final_error_count == error_context.initial_error_count
    ), "Retry success should NOT increment error counter"


@then("I should see appropriate retry statistics")
def verify_retry_statistics(error_context):
    """Verify user sees appropriate retry statistics."""
    # The retry succeeded with the expected number of attempts
    assert (
        error_context.retry_result == "successfully_processed_file.pdf"
    ), "Should return successful result"


@then(parsers.parse("I should see {num:d} files marked as successful"))
def verify_successful_files_marked(error_context, num):
    """Verify correct number of files marked as successful."""
    success_count = error_context.display_manager.progress.stats.success_count
    expected_count = error_context.initial_success_count + num

    assert (
        success_count == expected_count
    ), f"Should have {expected_count} successful files, got {success_count}"


@then(parsers.parse("I should see {num:d} files marked as failed"))
def verify_failed_files_marked(error_context, num):
    """Verify correct number of files marked as failed."""
    error_count = error_context.display_manager.progress.stats.failed
    expected_count = error_context.initial_error_count + num

    assert (
        error_count == expected_count
    ), f"Should have {expected_count} failed files, got {error_count}"


@then(parsers.parse("the total count should equal {num:d} files processed"))
def verify_total_files_processed(error_context, num):
    """Verify total processed count matches expected."""
    total_processed = error_context.display_manager.progress.stats.completed

    # Note: completed should equal initial + newly processed
    expected_total = num  # Since we're processing exactly this many in this scenario
    assert (
        total_processed >= expected_total
    ), f"Should have processed at least {expected_total} files, got {total_processed}"


@then("the statistics should be mathematically consistent")
def verify_statistics_consistency(error_context):
    """Verify statistics are mathematically consistent."""
    success_count = error_context.display_manager.progress.stats.success_count
    error_count = error_context.display_manager.progress.stats.failed
    total_processed = error_context.display_manager.progress.stats.completed

    # Remove initial counts to focus on this test's processing
    test_success_count = success_count - error_context.initial_success_count
    test_error_count = error_count - error_context.initial_error_count

    # For this scenario: 3 success + 2 failed = 5 total
    assert test_success_count == 3, f"Should have 3 successes, got {test_success_count}"
    assert test_error_count == 2, f"Should have 2 errors, got {test_error_count}"
    assert (
        test_success_count + test_error_count == 5
    ), "Success + Error should equal total files processed in this test"
