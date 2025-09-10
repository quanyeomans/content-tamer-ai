"""
Step definitions for Error Recovery E2E BDD scenarios
Tests temporary failure recovery and permanent failure handling
"""

import os
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pytest
from pytest_bdd import given, when, then, parsers

from src.core.application_container import ApplicationContainer
from src.interfaces.human.cli_interface import CLIInterface
from tests.utils.rich_test_utils import RichTestCase


class ErrorRecoveryTestContext(RichTestCase):
    """Test context for error recovery scenarios"""
    
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
        self.file_locks = {}
        self.processing_result = None
        self.display_output = None
        
        # Mock controls
        self.ai_service_available = True
        self.network_available = True
        self.disk_space_available = True
        
        # Application components
        self.container = None
        self.cli_interface = None


@pytest.fixture
def error_recovery_context():
    """Provide test context for error recovery scenarios"""
    context = ErrorRecoveryTestContext()
    yield context
    context.cleanup_test_environment()


# Background steps
@given("I have a clean working environment")
def clean_working_environment(error_recovery_context):
    """Set up clean test environment"""
    context = error_recovery_context
    
    context.temp_dir = tempfile.mkdtemp()
    context.input_dir = os.path.join(context.temp_dir, "input")
    context.processed_dir = os.path.join(context.temp_dir, "processed")
    context.unprocessed_dir = os.path.join(context.temp_dir, "unprocessed")
    
    os.makedirs(context.input_dir)
    os.makedirs(context.processed_dir)
    os.makedirs(context.unprocessed_dir)
    
    context.container = ApplicationContainer.create_for_testing(
        input_dir=context.input_dir,
        processed_dir=context.processed_dir,
        unprocessed_dir=context.unprocessed_dir,
        console=context.test_console
    )


@given("retry mechanisms are enabled")
def enable_retry_mechanisms(error_recovery_context):
    """Enable retry mechanisms for testing"""
    context = error_recovery_context
    
    # Configure retry settings for faster testing
    context.retry_config_patch = patch.dict(
        'src.domains.content.services.content_orchestrator.RETRY_CONFIG',
        {
            'max_retries': 3,
            'retry_delay': 0.1,  # Fast retries for testing
            'backoff_multiplier': 1.0
        }
    )
    context.retry_config_patch.start()


@given("I have an unprocessed directory for failed files")
def verify_unprocessed_directory(error_recovery_context):
    """Verify unprocessed directory exists"""
    context = error_recovery_context
    assert os.path.exists(context.unprocessed_dir), "Unprocessed directory not found"


# File setup with specific conditions
@given(parsers.parse("I have {count:d} PDF files in the input directory"))
def create_pdf_files_basic(error_recovery_context, count):
    """Create basic PDF test files"""
    context = error_recovery_context
    
    for i in range(count):
        filename = f"test_file_{i+1}.pdf"
        filepath = os.path.join(context.input_dir, filename)
        
        content = f"Mock PDF content for file {i+1}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': content,
            'status': 'normal'
        }


@given("the first file is temporarily locked by antivirus scanning")
def create_antivirus_locked_file(error_recovery_context):
    """Create file that simulates antivirus lock"""
    context = error_recovery_context
    
    # Find first file and mark it as locked
    first_filename = list(context.test_files.keys())[0]
    context.test_files[first_filename]['status'] = 'antivirus_locked'
    
    # Mock file operations to simulate lock
    def mock_file_operation(filepath, *args, **kwargs):
        filename = os.path.basename(filepath)
        if context.test_files.get(filename, {}).get('status') == 'antivirus_locked':
            raise PermissionError("File is locked by antivirus scanner")
        return True
    
    context.file_lock_patch = patch(
        'src.shared.file_operations.file_manager.FileManager.move_file',
        side_effect=mock_file_operation
    )
    context.file_lock_patch.start()


@given(parsers.parse("the antivirus will release the lock after {seconds:d} seconds"))
def schedule_lock_release(error_recovery_context, seconds):
    """Schedule antivirus lock release"""
    context = error_recovery_context
    
    def release_lock():
        time.sleep(seconds)
        # Find locked file and release it
        for filename, file_info in context.test_files.items():
            if file_info.get('status') == 'antivirus_locked':
                file_info['status'] = 'normal'
    
    # Start lock release timer
    threading.Thread(target=release_lock, daemon=True).start()


@given("the primary AI service becomes temporarily unavailable")
def make_ai_service_unavailable(error_recovery_context):
    """Make AI service temporarily unavailable"""
    context = error_recovery_context
    context.ai_service_available = False
    
    def mock_ai_request(*args, **kwargs):
        if not context.ai_service_available:
            raise ConnectionError("AI service temporarily unavailable")
        return "Fallback_Generated_Filename.pdf"
    
    context.ai_unavailable_patch = patch(
        'src.domains.ai_integration.services.ai_orchestrator.AIOrchestrator.generate_filename',
        side_effect=mock_ai_request
    )
    context.ai_unavailable_patch.start()


@given("a fallback naming strategy is configured")
def configure_fallback_naming(error_recovery_context):
    """Configure fallback naming strategy"""
    context = error_recovery_context
    
    def fallback_naming(content, **kwargs):
        # Simple content-based fallback naming
        if "budget" in content.lower():
            return "Financial_Document_Fallback.pdf"
        elif "meeting" in content.lower():
            return "Meeting_Notes_Fallback.pdf"
        else:
            return f"Document_Fallback_{int(time.time())}.pdf"
    
    context.fallback_patch = patch(
        'src.domains.content.services.content_processor.ContentProcessor.generate_fallback_filename',
        side_effect=fallback_naming
    )
    context.fallback_patch.start()


# File creation with specific issues
@given("I have 5 files in the input directory:")
def create_files_with_table(error_recovery_context, table):
    """Create files based on table specification"""
    context = error_recovery_context
    
    for row in table:
        filename = row['filename']
        file_status = row['file_status']
        filepath = os.path.join(context.input_dir, filename)
        
        if file_status == 'valid':
            content = f"Valid PDF content for {filename}"
        elif file_status == 'corrupted':
            content = "%%CORRUPTED_PDF_DATA%%"
        elif file_status == 'empty':
            content = ""
        else:
            content = f"Content for {filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': content,
            'status': file_status
        }


@given("I have 6 files in the input directory:")
def create_files_with_types_table(error_recovery_context, table):
    """Create files with specific types based on table"""
    context = error_recovery_context
    
    for row in table:
        filename = row['filename']
        file_type = row['file_type']
        filepath = os.path.join(context.input_dir, filename)
        
        if file_type == 'supported':
            content = f"Valid content for {filename}"
        elif file_type == 'unsupported':
            content = f"Unsupported format content for {filename}"
        else:
            content = f"Unknown format content for {filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': content,
            'type': file_type
        }


# Processing actions
@when("I run the document processing")
def run_document_processing(error_recovery_context):
    """Run document processing with error conditions"""
    context = error_recovery_context
    
    context.cli_interface = CLIInterface(context.container)
    
    with context.capture_console_output():
        try:
            context.processing_result = context.cli_interface.process_documents(
                input_dir=context.input_dir,
                processed_dir=context.processed_dir,
                unprocessed_dir=context.unprocessed_dir,
                ai_provider="test_provider",
                enable_retries=True
            )
        except Exception as e:
            context.processing_error = e
        
        context.display_output = context.get_console_output()


# Assertion steps
@then("I should see the other 2 files process immediately")
def verify_immediate_processing(error_recovery_context):
    """Verify non-locked files process immediately"""
    context = error_recovery_context
    
    # Check that processing started for available files
    assert context.display_output is not None, "No display output captured"
    
    # Should see processing messages for non-locked files
    processing_indicators = ["Processing", "Success"]
    found_processing = any(indicator in context.display_output for indicator in processing_indicators)
    assert found_processing, f"No immediate processing found in: {context.display_output}"


@then(parsers.parse('I should see "{message}" for the first file'))
def verify_specific_message(error_recovery_context, message):
    """Verify specific message appears for a file"""
    context = error_recovery_context
    
    assert context.display_output is not None, "No display output captured"
    assert message in context.display_output, \
        f"Expected message '{message}' not found in: {context.display_output}"


@then("the system should wait and retry the locked file")
def verify_retry_mechanism(error_recovery_context):
    """Verify retry mechanism is working"""
    context = error_recovery_context
    
    # Should see retry-related messages
    retry_indicators = ["retry", "Retry", "retrying", "Retrying"]
    found_retry = any(indicator in context.display_output for indicator in retry_indicators)
    assert found_retry, f"No retry mechanism found in: {context.display_output}"


@then("after the antivirus releases the lock, the file should process successfully")
def verify_lock_release_success(error_recovery_context):
    """Verify file processes after lock release"""
    context = error_recovery_context
    
    # Check processing result shows all files successful
    assert context.processing_result is not None, "No processing result available"
    
    total_files = len(context.test_files)
    success_count = context.processing_result.get('success_count', 0)
    assert success_count == total_files, \
        f"Expected {total_files} successful files, got {success_count}"


@then(parsers.parse('the final statistics should show "{expected_stats}"'))
def verify_final_statistics(error_recovery_context, expected_stats):
    """Verify final statistics match expected"""
    context = error_recovery_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Parse expected stats and verify
    if "successful" in expected_stats and "failed" in expected_stats:
        assert expected_stats in context.display_output, \
            f"Expected statistics '{expected_stats}' not found in: {context.display_output}"


@then("all 3 files should appear in the processed directory")
def verify_all_files_processed(error_recovery_context):
    """Verify all files appear in processed directory"""
    context = error_recovery_context
    
    processed_files = os.listdir(context.processed_dir)
    expected_count = len(context.test_files)
    
    assert len(processed_files) == expected_count, \
        f"Expected {expected_count} files in processed directory, found {len(processed_files)}"


@then("I should see clear communication about the temporary lock and recovery")
def verify_lock_communication(error_recovery_context):
    """Verify clear communication about lock and recovery"""
    context = error_recovery_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Should contain information about the lock and recovery
    communication_indicators = [
        "locked", "Lock", "temporary", "Temporary",
        "retry", "Retry", "recovered", "success"
    ]
    
    found_communication = any(indicator in context.display_output for indicator in communication_indicators)
    assert found_communication, \
        f"No clear lock/recovery communication found in: {context.display_output}"


# AI service fallback assertions
@then(parsers.parse('I should see "{message}" message'))
def verify_fallback_message(error_recovery_context, message):
    """Verify fallback service message"""
    context = error_recovery_context
    
    assert context.display_output is not None, "No display output captured"
    assert message in context.display_output, \
        f"Expected message '{message}' not found in: {context.display_output}"


@then("the system should switch to fallback naming automatically")
def verify_fallback_naming_switch(error_recovery_context):
    """Verify system switches to fallback naming"""
    context = error_recovery_context
    
    # Check that fallback naming was used
    fallback_indicators = ["fallback", "Fallback", "alternative", "backup"]
    found_fallback = any(indicator in context.display_output for indicator in fallback_indicators)
    assert found_fallback, f"No fallback naming switch found in: {context.display_output}"


@then("files should receive meaningful fallback names based on content analysis")
def verify_meaningful_fallback_names(error_recovery_context):
    """Verify fallback names are meaningful"""
    context = error_recovery_context
    
    processed_files = os.listdir(context.processed_dir)
    
    # Fallback names should not be generic
    for filename in processed_files:
        assert "Fallback" in filename or "Document" in filename, \
            f"Expected fallback naming pattern in {filename}"


# File status verification
@then("the 3 valid files should process successfully")
def verify_valid_files_success(error_recovery_context):
    """Verify valid files process successfully"""
    context = error_recovery_context
    
    # Count valid files
    valid_files = sum(1 for f in context.test_files.values() if f.get('status') == 'valid')
    
    processed_files = os.listdir(context.processed_dir)
    assert len(processed_files) == valid_files, \
        f"Expected {valid_files} processed files, found {len(processed_files)}"


@then(parsers.parse('I should see "{error_message}" for {filename}'))
def verify_file_error_message(error_recovery_context, error_message, filename):
    """Verify specific error message for a file"""
    context = error_recovery_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Should contain both the error message and filename
    assert error_message in context.display_output, \
        f"Expected error message '{error_message}' not found in: {context.display_output}"
    assert filename in context.display_output, \
        f"Expected filename '{filename}' not found in: {context.display_output}"


@then("the corrupted files should be moved to the unprocessed directory")
def verify_corrupted_files_moved(error_recovery_context):
    """Verify corrupted files moved to unprocessed directory"""
    context = error_recovery_context
    
    unprocessed_files = os.listdir(context.unprocessed_dir)
    
    # Count corrupted files
    corrupted_count = sum(1 for f in context.test_files.values() 
                         if f.get('status') in ['corrupted', 'empty'])
    
    assert len(unprocessed_files) == corrupted_count, \
        f"Expected {corrupted_count} unprocessed files, found {len(unprocessed_files)}"


@then("I should see detailed error explanations for each failed file")
def verify_detailed_error_explanations(error_recovery_context):
    """Verify detailed error explanations are provided"""
    context = error_recovery_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Should contain explanatory text about errors
    explanation_indicators = [
        "corrupted", "Corrupted", "empty", "Empty",
        "explanation", "reason", "because", "error"
    ]
    
    found_explanations = sum(1 for indicator in explanation_indicators 
                           if indicator in context.display_output)
    
    assert found_explanations >= 2, \
        f"Expected detailed error explanations, found minimal indicators in: {context.display_output}"


@then("the error messages should be user-friendly and actionable")
def verify_user_friendly_errors(error_recovery_context):
    """Verify error messages are user-friendly and actionable"""
    context = error_recovery_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Should not contain technical jargon
    technical_terms = ["traceback", "exception", "stack", "null pointer"]
    found_technical = any(term in context.display_output.lower() for term in technical_terms)
    assert not found_technical, \
        f"Found technical jargon in user-facing errors: {context.display_output}"
    
    # Should contain actionable guidance
    actionable_terms = ["try", "check", "ensure", "verify", "contact"]
    found_actionable = any(term in context.display_output.lower() for term in actionable_terms)
    assert found_actionable, \
        f"No actionable guidance found in errors: {context.display_output}"


# Cleanup
def cleanup_error_recovery_environment(context):
    """Clean up error recovery test environment"""
    # Stop all patches
    patches_to_stop = [
        'retry_config_patch', 'file_lock_patch', 'ai_unavailable_patch', 
        'fallback_patch'
    ]
    
    for patch_name in patches_to_stop:
        if hasattr(context, patch_name):
            getattr(context, patch_name).stop()
    
    # Clean up directories
    if context.temp_dir and os.path.exists(context.temp_dir):
        import shutil
        shutil.rmtree(context.temp_dir)
    
    # Clean up Rich test environment
    context.teardown_rich_test_environment()


# Enhance context with cleanup
def enhance_error_recovery_context_cleanup(context):
    """Add cleanup method to error recovery context"""
    original_cleanup = getattr(context, 'cleanup_test_environment', lambda: None)
    
    def enhanced_cleanup():
        cleanup_error_recovery_environment(context)
        original_cleanup()
    
    context.cleanup_test_environment = enhanced_cleanup


@pytest.fixture
def error_recovery_context():
    """Provide test context for error recovery scenarios"""
    context = ErrorRecoveryTestContext()
    enhance_error_recovery_context_cleanup(context)
    yield context
    context.cleanup_test_environment()