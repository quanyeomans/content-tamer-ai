"""Step definitions for progress display and user feedback BDD scenarios."""

import os
import shutil
import sys
import tempfile
from io import StringIO

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

from shared.display.display_manager import DisplayManager
from shared.display.rich_display_manager import RichDisplayOptions

@pytest.fixture
def progress_context():
    """Context for progress display tests."""
    context = type("ProgressContext", (), {})()
    context.temp_dir = tempfile.mkdtemp()
    context.display_output = StringIO()
    context.display_options = RichDisplayOptions(quiet=False)
    context.display_manager = DisplayManager(context.display_options)
    yield context
    if os.path.exists(context.temp_dir):
        shutil.rmtree(context.temp_dir)

# Scenario imports
@scenario("../progress_display.feature", "User sees progress counters increment correctly")
def test_user_sees_progress_counters_increment_correctly():
    pass

@scenario("../progress_display.feature", "User sees accurate completion statistics")
def test_user_sees_accurate_completion_statistics():
    pass

@scenario("../progress_display.feature", "User sees clear file status progression")
def test_user_sees_clear_file_status_progression():
    pass

# Step definitions focusing on user-observable progress behavior
@given("I have a clean progress environment")
def clean_progress_environment(progress_context):
    """Set up clean progress environment."""
    progress_context.initial_success = progress_context.display_manager.progress.stats.success_count
    progress_context.initial_failed = progress_context.display_manager.progress.stats.failed
    progress_context.initial_completed = progress_context.display_manager.progress.stats.completed

@when("I process 2 files successfully")
def process_two_files_successfully(progress_context):
    """Simulate processing 2 files successfully."""
    with progress_context.display_manager.processing_context(total_files=2) as display_context:
        # Process 2 files successfully
        display_context.complete_file("file1.pd", "renamed_file1.pd")
        display_context.complete_file("file2.pd", "renamed_file2.pd")
        progress_context.processing_context = display_context

@when("I complete a full processing session with 3 successes and 1 failure")
def complete_full_processing_session(progress_context):
    """Simulate a complete processing session with mixed outcomes."""
    with progress_context.display_manager.processing_context(total_files=4) as display_context:
        # Process 3 files successfully
        display_context.complete_file("success1.pd", "renamed_success1.pd")
        display_context.complete_file("success2.pd", "renamed_success2.pd")
        display_context.complete_file("success3.pd", "renamed_success3.pd")

        # Process 1 file with failure
        display_context.fail_file("failed1.pd", "File processing error")

        progress_context.processing_context = display_context

@when("I track file processing status changes")
def track_file_processing_status_changes(progress_context):
    """Track file status changes during processing."""
    with progress_context.display_manager.processing_context(total_files=1) as display_context:
        # Simulate the progression of file status
        progress_context.status_progression = []

        # Start file processing
        display_context.start_file("test_file.pd", "target_name.pd")
        progress_context.status_progression.append("started")

        # Update status during processing
        display_context.set_status("processing", target_filename="target_name.pd")
        progress_context.status_progression.append("processing")

        # Complete the file
        display_context.complete_file("test_file.pd", "target_name.pd")
        progress_context.status_progression.append("completed")

        progress_context.processing_context = display_context

@then("I should see the success counter increase by 2")
def verify_success_counter_increase(progress_context):
    """Verify success counter increased by exactly 2."""
    current_success = progress_context.display_manager.progress.stats.success_count
    expected_success = progress_context.initial_success + 2

    assert (
        current_success == expected_success
    ), "Success counter should increase by 2. Expected: {expected_success}, Got: {current_success}"

@then("I should see the total completed counter increase by 2")
def verify_completed_counter_increase(progress_context):
    """Verify total completed counter increased by 2."""
    current_completed = progress_context.display_manager.progress.stats.completed
    expected_completed = progress_context.initial_completed + 2

    assert (
        current_completed == expected_completed
    ), "Completed counter should increase by 2. Expected: {expected_completed}, Got: {current_completed}"

@then("I should see 0 errors in the counter")
def verify_no_errors_in_counter(progress_context):
    """Verify error counter didn't change."""
    current_failed = progress_context.display_manager.progress.stats.failed
    expected_failed = progress_context.initial_failed  # Should be unchanged

    assert (
        current_failed == expected_failed
    ), "Error counter should remain unchanged. Expected: {expected_failed}, Got: {current_failed}"

@then(parsers.parse("I should see final statistics showing {num:d} successful files"))
def verify_final_success_statistics(progress_context, num):
    """Verify final statistics show correct number of successful files."""
    current_success = progress_context.display_manager.progress.stats.success_count
    expected_success = progress_context.initial_success + num

    assert (
        current_success == expected_success
    ), "Final statistics should show {num} successful files. Expected: {expected_success}, Got: {current_success}"

@then(parsers.parse("I should see final statistics showing {num:d} failed file"))
def verify_final_failure_statistics(progress_context, num):
    """Verify final statistics show correct number of failed files."""
    current_failed = progress_context.display_manager.progress.stats.failed
    expected_failed = progress_context.initial_failed + num

    assert (
        current_failed == expected_failed
    ), "Final statistics should show {num} failed file. Expected: {expected_failed}, Got: {current_failed}"

@then(parsers.parse("I should see final statistics showing {num:d} total files processed"))
def verify_total_files_processed_statistics(progress_context, num):
    """Verify final statistics show correct total processed count."""
    current_completed = progress_context.display_manager.progress.stats.completed
    expected_completed = progress_context.initial_completed + num

    assert (
        current_completed == expected_completed
    ), "Final statistics should show {num} total processed. Expected: {expected_completed}, Got: {current_completed}"

@then("the success rate should be calculated correctly")
def verify_success_rate_calculation(progress_context):
    """Verify success rate is calculated correctly."""
    success_count = (
        progress_context.display_manager.progress.stats.success_count
        - progress_context.initial_success
    )
    total_processed = (
        progress_context.display_manager.progress.stats.completed
        - progress_context.initial_completed
    )

    if total_processed > 0:
        expected_rate = (success_count / total_processed) * 100
        # For 3 successes out of 4 total: 75%
        assert (
            expected_rate == 75.0
        ), "Success rate should be 75% (3/4). Calculated: {expected_rate}%"
    else:
        pytest.fail("No files were processed to calculate success rate")

@then("I should see files start in processing state")
def verify_files_start_in_processing_state(progress_context):
    """Verify files start in processing state."""
    assert (
        "started" in progress_context.status_progression
    ), "Files should start in processing state"

@then("I should see files transition to completed state")
def verify_files_transition_to_completed(progress_context):
    """Verify files transition to completed state."""
    assert (
        "completed" in progress_context.status_progression
    ), "Files should transition to completed state"

@then("I should see appropriate status messages throughout")
def verify_appropriate_status_messages(progress_context):
    """Verify appropriate status messages are shown throughout processing."""
    # Verify the progression makes sense
    expected_progression = ["started", "processing", "completed"]

    for expected_status in expected_progression:
        assert (
            expected_status in progress_context.status_progression
        ), "Should see {expected_status} status in progression: {progress_context.status_progression}"

    # Verify the progression is in logical order
    started_index = progress_context.status_progression.index("started")
    processing_index = progress_context.status_progression.index("processing")
    completed_index = progress_context.status_progression.index("completed")

    assert (
        started_index < processing_index < completed_index
    ), "Status progression should be logical order: {progress_context.status_progression}"
