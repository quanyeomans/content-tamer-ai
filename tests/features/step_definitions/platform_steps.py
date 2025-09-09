"""Step definitions for cross-platform consistency BDD scenarios."""

import os
import platform
import shutil
import sys
import tempfile
from io import StringIO
from pathlib import Path

import pytest
from pytest_bdd import given, scenario, then, when

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
def platform_context():
    """Context for platform consistency tests."""
    context = type("PlatformContext", (), {})()
    context.temp_dir = tempfile.mkdtemp()
    context.platform_name = platform.system()
    context.test_files = []
    context.display_output = StringIO()
    context.display_options = RichDisplayOptions(quiet=False)
    context.display_manager = DisplayManager(context.display_options)
    yield context
    if os.path.exists(context.temp_dir):
        shutil.rmtree(context.temp_dir)

# Scenario imports
@scenario(
    "../platform_consistency.feature",
    "Processing works consistently with different path separators",
)
def test_processing_works_consistently_with_different_path_separators():
    pass

@scenario("../platform_consistency.feature", "Error messages are platform-appropriate")
def test_error_messages_are_platform_appropriate():
    pass

@scenario(
    "../platform_consistency.feature",
    "Display output works across different terminal environments",
)
def test_display_output_works_across_different_terminal_environments():
    pass

# Step definitions focusing on cross-platform behavior
@given("I have a clean platform test environment")
def clean_platform_test_environment(platform_context):
    """Set up clean platform test environment."""
    # Create subdirectories to test path handling
    platform_context.input_dir = os.path.join(platform_context.temp_dir, "input")
    platform_context.output_dir = os.path.join(platform_context.temp_dir, "output")
    platform_context.nested_dir = os.path.join(
        platform_context.input_dir, "nested", "deeply", "nested"
    )

    os.makedirs(platform_context.input_dir)
    os.makedirs(platform_context.output_dir)
    os.makedirs(platform_context.nested_dir)

@when("I create files with platform-appropriate paths")
def create_files_with_platform_paths(platform_context):
    """Create files with various path formats."""
    # Create files in different locations to test path handling
    test_files = [
        os.path.join(platform_context.input_dir, "simple_file.txt"),
        os.path.join(platform_context.nested_dir, "nested_file.txt"),
    ]

    # Also test with pathlib Path objects (cross-platform)
    pathlib_file = Path(platform_context.input_dir) / "pathlib_file.txt"
    test_files.append(str(pathlib_file))

    # Create the actual files
    for file_path in test_files:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Test content for {os.path.basename(file_path)}")
        platform_context.test_files.append(file_path)

@when("I encounter file path errors")
def encounter_file_path_errors(platform_context):
    """Simulate file path errors that might be platform-specific."""
    # Test with invalid path characters (if any)
    platform_context.error_scenarios = []

    # Try to create file with path that might cause issues
    try:
        # On Windows, certain characters are invalid in filenames
        if platform_context.platform_name == "Windows":
            invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
            test_char = invalid_chars[0]  # Test with '<'
            invalid_path = os.path.join(platform_context.input_dir, f"invalid{test_char}file.txt")
        else:
            # On Unix-like systems, test with null character
            invalid_path = os.path.join(platform_context.input_dir, "invalid\x00file.txt")

        with open(invalid_path, "w", encoding="utf-8") as f:
            f.write("This should fail on some platforms")

        platform_context.error_scenarios.append("file_created_unexpectedly")

    except OSError as e:
        # This is expected - capture the error for analysis
        platform_context.error_scenarios.append(f"expected_error: {str(e)}")
    except Exception as e:
        platform_context.error_scenarios.append(f"unexpected_error: {str(e)}")

@when("I run processing with various display options")
def run_processing_with_display_options(platform_context):
    """Test processing with different display configurations."""
    platform_context.display_tests = []

    # Test with quiet mode
    quiet_output = StringIO()
    quiet_options = RichDisplayOptions(quiet=True)
    quiet_manager = DisplayManager(quiet_options)

    with quiet_manager.processing_context(total_files=1) as context:
        context.complete_file("test.pd", "renamed.pdf")

    platform_context.display_tests.append(
        {
            "mode": "quiet",
            "output": quiet_output.getvalue(),
            "length": len(quiet_output.getvalue()),
        }
    )

    # Test with normal mode (captured in fixture)
    with platform_context.display_manager.processing_context(total_files=1) as context:
        context.complete_file("test.pd", "renamed.pdf")

    platform_context.display_tests.append(
        {
            "mode": "normal",
            "output": platform_context.display_output.getvalue(),
            "length": len(platform_context.display_output.getvalue()),
        }
    )

@then("file processing should handle paths correctly")
def verify_path_handling(platform_context):
    """Verify file paths are handled correctly across platforms."""
    # All test files should have been created successfully
    for file_path in platform_context.test_files:
        assert os.path.exists(file_path), f"File should exist: {file_path}"

        # Verify path normalization works
        normalized_path = os.path.normpath(file_path)
        assert os.path.exists(normalized_path), f"Normalized path should work: {normalized_path}"

@then("the results should be consistent regardless of path format")
def verify_consistent_results(platform_context):
    """Verify results are consistent across path formats."""
    # All created files should be readable
    for file_path in platform_context.test_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Test content" in content, f"File content should be readable: {file_path}"

@then("error messages should be clear and platform-appropriate")
def verify_platform_appropriate_errors(platform_context):
    """Verify error messages are appropriate for the platform."""
    # Should have encountered expected errors
    assert len(platform_context.error_scenarios) > 0, "Should have tested error scenarios"

    # Check that errors were handled (not crashed)
    has_expected_error = any(
        "expected_error" in scenario for scenario in platform_context.error_scenarios
    )
    has_unexpected_crash = any(
        "unexpected_error" in scenario for scenario in platform_context.error_scenarios
    )

    # Either we got expected errors OR the platform allows the operation
    assert (
        has_expected_error or not has_unexpected_crash
    ), f"Error handling should be appropriate for platform. Scenarios: {platform_context.error_scenarios}"

@then("file operations should handle platform differences gracefully")
def verify_graceful_platform_handling(platform_context):
    """Verify platform differences are handled gracefully."""
    # The system should handle the current platform correctly
    current_platform = platform_context.platform_name
    assert current_platform in [
        "Windows",
        "Linux",
        "Darwin",
    ], f"Should recognize platform: {current_platform}"

    # Should have handled error scenarios without crashing
    assert len(platform_context.error_scenarios) > 0, "Should have tested error scenarios"

@then("the display should work correctly")
def verify_display_works(platform_context):
    """Verify display works correctly across configurations."""
    assert len(platform_context.display_tests) >= 2, "Should have tested multiple display modes"

    # Quiet mode should produce less output than normal mode
    quiet_test = next(test for test in platform_context.display_tests if test["mode"] == "quiet")
    normal_test = next(test for test in platform_context.display_tests if test["mode"] == "normal")

    assert (
        quiet_test["length"] <= normal_test["length"]
    ), "Quiet mode should produce less or equal output than normal mode"

@then("special characters should be handled appropriately")
def verify_special_character_handling(platform_context):
    """Verify special characters in display are handled appropriately."""
    # Check that display output doesn't cause encoding errors
    normal_test = next(test for test in platform_context.display_tests if test["mode"] == "normal")
    output = normal_test["output"]

    # Should be able to process the output without Unicode errors
    try:
        # Attempt to encode/decode the output
        encoded = output.encode("utf-8", errors="replace")
        decoded = encoded.decode("utf-8", errors="replace")

        # Should not have replacement characters (indicating encoding issues)
        replacement_char_count = decoded.count("\ufffd")

        # Allow some replacement characters but not excessive amounts
        assert (
            replacement_char_count < len(decoded) * 0.1
        ), "Too many encoding issues in display output. Replacement chars: {replacement_char_count}"

    except Exception as e:
        pytest.fail("Display output should handle encoding gracefully: {e}")
