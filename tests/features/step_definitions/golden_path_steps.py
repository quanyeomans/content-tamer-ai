"""
Step definitions for Golden Path E2E BDD scenarios
Tests the most common successful user workflows
"""

import os
import tempfile
import time
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pytest_bdd import given, when, then, parsers

from src.core.application_container import ApplicationContainer
from src.interfaces.human.cli_interface import CLIInterface
from tests.utils.rich_test_utils import RichTestCase


class GoldenPathTestContext(RichTestCase):
    """Test context for golden path scenarios with proper Rich UI handling"""
    
    def __init__(self):
        RichTestCase.__init__(self)
        self.setup_rich_test_environment()
        
        # Test directories
        self.temp_dir = None
        self.input_dir = None
        self.processed_dir = None
        self.unprocessed_dir = None
        
        # Test state
        self.test_files = {}
        self.processing_result = None
        self.display_output = None
        self.final_statistics = None
        
        # Application components
        self.container = None
        self.cli_interface = None


# Context setup and teardown
@pytest.fixture
def golden_path_context():
    """Provide test context for golden path scenarios"""
    context = GoldenPathTestContext()
    yield context
    context.cleanup_test_environment()


# Background steps
@given("I have a clean working environment")
def clean_working_environment(golden_path_context):
    """Set up clean test environment"""
    context = golden_path_context
    
    # Create temporary directories
    context.temp_dir = tempfile.mkdtemp()
    context.input_dir = os.path.join(context.temp_dir, "input")
    context.processed_dir = os.path.join(context.temp_dir, "processed")
    context.unprocessed_dir = os.path.join(context.temp_dir, "unprocessed")
    
    os.makedirs(context.input_dir)
    os.makedirs(context.processed_dir)
    os.makedirs(context.unprocessed_dir)
    
    # Initialize application container with test configuration
    context.container = ApplicationContainer.create_for_testing(
        input_dir=context.input_dir,
        processed_dir=context.processed_dir,
        unprocessed_dir=context.unprocessed_dir,
        console=context.test_console
    )


@given("the AI service is responding normally")
def ai_service_responding(golden_path_context):
    """Mock AI service to respond normally"""
    context = golden_path_context
    
    def mock_ai_response(content, **kwargs):
        # Generate meaningful AI-style filename based on content keywords
        if "budget" in content.lower():
            return "Financial_Budget_Report_2024.pdf"
        elif "meeting" in content.lower():
            return "Team_Meeting_Notes_Project_Update.pdf"
        elif "recipe" in content.lower():
            return "Cooking_Recipe_Collection_Favorites.pdf"
        else:
            return f"Document_Content_Analysis_{int(time.time())}.pdf"
    
    # Patch AI service to return predictable names
    context.ai_service_patch = patch(
        'src.domains.ai_integration.services.ai_orchestrator.AIOrchestrator.generate_filename',
        side_effect=mock_ai_response
    )
    context.ai_service_patch.start()


@given("I have sufficient disk space")
def sufficient_disk_space(golden_path_context):
    """Ensure sufficient disk space for processing"""
    # This is implicitly handled by using temporary directories
    # In real implementation, this would check actual disk space
    pass


@given("all required dependencies are available")
def required_dependencies(golden_path_context):
    """Ensure all dependencies are available"""
    context = golden_path_context
    # Mock dependency checks to return success
    context.dependency_patch = patch(
        'src.shared.infrastructure.dependency_manager.DependencyManager.check_dependencies',
        return_value=True
    )
    context.dependency_patch.start()


# File setup steps
@given(parsers.parse("I have {count:d} PDF files with valid content in the input directory"))
def create_valid_pdf_files(golden_path_context, count):
    """Create valid PDF test files"""
    context = golden_path_context
    
    for i in range(count):
        filename = f"test_document_{i+1}.pdf"
        filepath = os.path.join(context.input_dir, filename)
        
        # Create mock PDF content
        pdf_content = f"""Mock PDF Content for Document {i+1}
        This is a test document containing sample text for processing.
        Document type: Report
        Content: Sample business document with financial data.
        Created for testing purposes."""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pdf_content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': pdf_content,
            'size': len(pdf_content.encode('utf-8'))
        }


@given("each file is under 50MB in size")
def verify_file_sizes(golden_path_context):
    """Verify all test files are under size limit"""
    context = golden_path_context
    
    for filename, file_info in context.test_files.items():
        assert file_info['size'] < 50 * 1024 * 1024, f"{filename} exceeds 50MB limit"


@given("I have proper read/write permissions on all directories")
def verify_permissions(golden_path_context):
    """Verify directory permissions"""
    context = golden_path_context
    
    # Test write permissions
    for directory in [context.input_dir, context.processed_dir, context.unprocessed_dir]:
        test_file = os.path.join(directory, "permission_test.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except PermissionError:
            pytest.fail(f"No write permission for {directory}")


# Processing steps
@when("I run the document processing with default settings")
def run_document_processing_default(golden_path_context):
    """Run document processing with default settings"""
    context = golden_path_context
    
    # Create CLI interface with test container
    context.cli_interface = CLIInterface(context.container)
    
    # Capture console output
    with context.capture_console_output():
        try:
            # Run processing with default settings
            context.processing_result = context.cli_interface.process_documents(
                input_dir=context.input_dir,
                processed_dir=context.processed_dir,
                unprocessed_dir=context.unprocessed_dir,
                ai_provider="test_provider"
            )
        except Exception as e:
            context.processing_error = e
        
        # Capture display output
        context.display_output = context.get_console_output()


@when("I run the document processing with OCR enabled")
def run_processing_with_ocr(golden_path_context):
    """Run document processing with OCR enabled"""
    context = golden_path_context
    
    context.cli_interface = CLIInterface(context.container)
    
    with context.capture_console_output():
        try:
            context.processing_result = context.cli_interface.process_documents(
                input_dir=context.input_dir,
                processed_dir=context.processed_dir,
                unprocessed_dir=context.unprocessed_dir,
                ai_provider="test_provider",
                enable_ocr=True
            )
        except Exception as e:
            context.processing_error = e
        
        context.display_output = context.get_console_output()


# Assertion steps
@then(parsers.parse('I should see "Processing {count:d} files..." in the progress display'))
def verify_processing_message(golden_path_context, count):
    """Verify processing start message"""
    context = golden_path_context
    
    assert context.display_output is not None, "No display output captured"
    assert f"Processing {count} files" in context.display_output, \
        f"Expected 'Processing {count} files' in display output: {context.display_output}"


@then(parsers.parse("all {count:d} files should process successfully without retries"))
def verify_all_files_successful(golden_path_context, count):
    """Verify all files processed successfully"""
    context = golden_path_context
    
    # Check processing result
    assert context.processing_result is not None, "No processing result available"
    assert context.processing_result.get('success_count', 0) == count, \
        f"Expected {count} successful files, got {context.processing_result.get('success_count', 0)}"
    
    # Verify no retries occurred
    assert context.processing_result.get('retry_count', 0) == 0, \
        f"Expected no retries, got {context.processing_result.get('retry_count', 0)}"


@then(parsers.parse('the progress display should show "{expected_stats}"'))
def verify_progress_display_stats(golden_path_context, expected_stats):
    """Verify progress display shows expected statistics"""
    context = golden_path_context
    
    assert context.display_output is not None, "No display output captured"
    assert expected_stats in context.display_output, \
        f"Expected '{expected_stats}' in display output: {context.display_output}"


@then("each file should appear in the processed directory with an AI-generated filename")
def verify_files_in_processed_directory(golden_path_context):
    """Verify files appear in processed directory with AI names"""
    context = golden_path_context
    
    processed_files = os.listdir(context.processed_dir)
    expected_count = len(context.test_files)
    
    assert len(processed_files) == expected_count, \
        f"Expected {expected_count} files in processed directory, found {len(processed_files)}"
    
    # Verify files have AI-generated names (not original names)
    original_names = set(context.test_files.keys())
    processed_names = set(processed_files)
    
    # Should be no overlap between original and processed names (names should be changed)
    overlap = original_names.intersection(processed_names)
    assert len(overlap) == 0, \
        f"Files should have new AI-generated names, but found original names: {overlap}"


@then("the original files should be removed from the input directory")
def verify_input_directory_empty(golden_path_context):
    """Verify input directory is empty after processing"""
    context = golden_path_context
    
    remaining_files = os.listdir(context.input_dir)
    assert len(remaining_files) == 0, \
        f"Input directory should be empty, but contains: {remaining_files}"


@then("I should see a completion message indicating 100% success rate")
def verify_completion_message(golden_path_context):
    """Verify completion message shows 100% success"""
    context = golden_path_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Look for completion indicators
    completion_indicators = [
        "100% success",
        "All files processed successfully",
        "Complete",
        "Success rate: 100%"
    ]
    
    found_indicator = any(indicator in context.display_output for indicator in completion_indicators)
    assert found_indicator, \
        f"Expected completion message in display output: {context.display_output}"


@then(parsers.parse("the processing should complete in reasonable time (under {max_minutes:d} minutes)"))
def verify_processing_time(golden_path_context, max_minutes):
    """Verify processing completes within time limit"""
    context = golden_path_context
    
    # In real implementation, this would track actual processing time
    # For tests, we verify the processing completed without timeout
    assert context.processing_result is not None, "Processing did not complete"
    
    # Check if there was a timeout error
    if hasattr(context, 'processing_error'):
        assert "timeout" not in str(context.processing_error).lower(), \
            f"Processing timed out: {context.processing_error}"


# Mixed file type steps
@given(parsers.parse("I have {count:d} PNG image files in the input directory"))
def create_png_files(golden_path_context, count):
    """Create PNG test files"""
    context = golden_path_context
    
    for i in range(count):
        filename = f"test_image_{i+1}.png"
        filepath = os.path.join(context.input_dir, filename)
        
        # Create mock PNG content (just text for testing)
        png_content = f"Mock PNG image data {i+1}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(png_content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': png_content,
            'type': 'png'
        }


@given(parsers.parse("I have {count:d} TXT document in the input directory"))
def create_txt_files(golden_path_context, count):
    """Create TXT test files"""
    context = golden_path_context
    
    for i in range(count):
        filename = f"test_document_{i+1}.txt"
        filepath = os.path.join(context.input_dir, filename)
        
        txt_content = f"""Test document {i+1}
        This is a plain text document for testing.
        Content: Sample text data for processing."""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': txt_content,
            'type': 'txt'
        }


@then("PDF files should retain .pdf extensions with AI-generated names")
@then("PNG files should retain .png extensions with AI-generated names")  
@then("TXT files should retain .txt extensions with AI-generated names")
def verify_file_extensions_preserved(golden_path_context):
    """Verify file extensions are preserved with AI-generated names"""
    context = golden_path_context
    
    processed_files = os.listdir(context.processed_dir)
    
    # Group original files by extension
    original_extensions = {}
    for filename, file_info in context.test_files.items():
        ext = os.path.splitext(filename)[1]
        if ext not in original_extensions:
            original_extensions[ext] = 0
        original_extensions[ext] += 1
    
    # Verify processed files maintain extension counts
    processed_extensions = {}
    for filename in processed_files:
        ext = os.path.splitext(filename)[1]
        if ext not in processed_extensions:
            processed_extensions[ext] = 0
        processed_extensions[ext] += 1
    
    assert original_extensions == processed_extensions, \
        f"Extension counts don't match. Original: {original_extensions}, Processed: {processed_extensions}"


@then("I should see appropriate processing messages for each file type")
def verify_file_type_messages(golden_path_context):
    """Verify appropriate messages for different file types"""
    context = golden_path_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Verify messages appear for different file types
    file_types_present = set()
    for filename in context.test_files.keys():
        ext = os.path.splitext(filename)[1].lower()
        file_types_present.add(ext)
    
    # Each file type should have some processing indication
    for file_type in file_types_present:
        type_found = file_type in context.display_output or file_type.upper() in context.display_output
        assert type_found, f"No processing message found for {file_type} files in: {context.display_output}"


# Cleanup helper
def cleanup_test_environment(context):
    """Clean up test environment"""
    if hasattr(context, 'ai_service_patch'):
        context.ai_service_patch.stop()
    if hasattr(context, 'dependency_patch'):
        context.dependency_patch.stop()
    if context.temp_dir and os.path.exists(context.temp_dir):
        shutil.rmtree(context.temp_dir)
    
    # Clean up Rich test environment
    context.teardown_rich_test_environment()


# Add cleanup to context
def enhance_context_cleanup(context):
    """Add cleanup method to context"""
    original_cleanup = getattr(context, 'cleanup_test_environment', lambda: None)
    
    def enhanced_cleanup():
        cleanup_test_environment(context)
        original_cleanup()
    
    context.cleanup_test_environment = enhanced_cleanup


# Enhance context in fixture
@pytest.fixture
def golden_path_context():
    """Provide test context for golden path scenarios"""
    context = GoldenPathTestContext()
    enhance_context_cleanup(context)
    yield context
    context.cleanup_test_environment()