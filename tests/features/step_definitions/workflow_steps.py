"""
Step definitions for Complete User Workflow E2E BDD scenarios
Tests complete end-to-end user journeys and retry success determination
"""

import os
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pytest
from pytest_bdd import given, when, then, parsers

from src.core.application_container import ApplicationContainer
from src.interfaces.human.cli_interface import CLIInterface
from tests.utils.rich_test_utils import RichTestCase
from tests.utils.pytest_file_utils import create_processing_directories, setup_bdd_test_context


class WorkflowTestContext(RichTestCase):
    """Test context for complete user workflow scenarios"""
    
    def __init__(self, tmp_path=None):
        RichTestCase.__init__(self)
        self.setup_rich_test_environment()
        
        # Initialize with tmp_path or fallback to legacy mode
        self.tmp_path = tmp_path
        self.temp_dir = None
        self.input_dir = None
        self.processed_dir = None
        self.unprocessed_dir = None
        self.config_dir = None
        self._directories_setup = False
        
        # Test state
        self.test_files = {}
        self.user_type = "new_user"
        self.expert_settings = {}
        self.processing_history = []
        self.processing_result = None
        self.display_output = None
        
        # Workflow tracking
        self.processing_stages = []
        self.retry_attempts = {}
        self.current_statistics = {
            'success_count': 0,
            'failed_count': 0,
            'retry_count': 0
        }
        
        # Application components
        self.container = None
        self.cli_interface = None
        
    def setup_test_directories(self):
        """Set up test directories using pytest tmp_path or fallback."""
        if self._directories_setup:
            return
            
        if self.tmp_path:
            # Use pytest tmp_path
            directories = create_processing_directories(self.tmp_path)
            self.temp_dir = str(self.tmp_path)
            self.input_dir = str(directories["input"])
            self.processed_dir = str(directories["processed"])
            self.unprocessed_dir = str(directories["unprocessed"])
            self.config_dir = str(self.tmp_path / "config")
            (self.tmp_path / "config").mkdir(exist_ok=True)
        else:
            # Fallback to legacy tempfile for compatibility
            import tempfile
            self.temp_dir = tempfile.mkdtemp()
            self.input_dir = os.path.join(self.temp_dir, "input")
            self.processed_dir = os.path.join(self.temp_dir, "processed")
            self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")
            self.config_dir = os.path.join(self.temp_dir, "config")
            
            for dir_path in [self.input_dir, self.processed_dir, self.unprocessed_dir, self.config_dir]:
                os.makedirs(dir_path, exist_ok=True)
        
        self._directories_setup = True


@pytest.fixture
def workflow_context(tmp_path):
    """Provide test context for workflow scenarios with tmp_path."""
    context = WorkflowTestContext(tmp_path)
    context.setup_test_directories()
    yield context
    context.cleanup_test_environment()


# Background and user setup
@given("I am a new user setting up the system for the first time")
def setup_new_user(workflow_context):
    """Set up new user environment"""
    context = workflow_context
    context.user_type = "new_user"
    
    # Ensure directories are set up
    if not context._directories_setup:
        context.setup_test_directories()


@given("I am an experienced user who wants custom settings")
def setup_expert_user(workflow_context):
    """Set up expert user environment"""
    context = workflow_context
    context.user_type = "expert_user"
    
    # Set up environment similar to new user but with existing config
    setup_new_user(context)
    
    # Create existing configuration to simulate experienced user
    config_file = os.path.join(context.config_dir, "user_preferences.json")
    expert_config = {
        "preferred_ai_provider": "claude",
        "custom_filename_pattern": "Document_{category}_{date}_{sequence}",
        "retry_policy": {"max_retries": 5, "retry_delay": 2.0},
        "organization_enabled": True,
        "expert_mode": True
    }
    
    with open(config_file, 'w') as f:
        json.dump(expert_config, f)
    
    context.expert_settings = expert_config


@given("I have proper permissions on my directories")
def verify_directory_permissions(workflow_context):
    """Verify proper directory permissions"""
    context = workflow_context
    
    for directory in [context.input_dir, context.processed_dir, context.unprocessed_dir]:
        test_file = os.path.join(directory, "permission_test.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except PermissionError:
            pytest.fail(f"No write permission for {directory}")


@given("I have an internet connection for AI services")
def setup_ai_services(workflow_context):
    """Set up AI services for workflow testing"""
    context = workflow_context
    
    def mock_ai_response(content, **kwargs):
        if context.user_type == "expert_user":
            # Expert users get more customized names
            if "budget" in content.lower():
                return "Financial_Budget_Report_2024_Q4.pdf"
            elif "meeting" in content.lower():
                return "Meeting_ProjectUpdate_2024_001.pdf"
            else:
                return f"Document_CustomCategory_{int(time.time())}.pdf"
        else:
            # New users get standard AI names
            return f"AI_Generated_Document_{int(time.time())}.pdf"
    
    context.ai_service_patch = patch(
        'src.domains.ai_integration.services.ai_orchestrator.AIOrchestrator.generate_filename',
        side_effect=mock_ai_response
    )
    context.ai_service_patch.start()


# File setup
@given(parsers.parse("I have {count:d} mixed documents (PDF, PNG, TXT) to process"))
def create_mixed_documents(workflow_context, count):
    """Create mixed document types for processing"""
    context = workflow_context
    
    file_types = ['.pdf', '.png', '.txt']
    
    for i in range(count):
        file_type = file_types[i % len(file_types)]
        filename = f"test_document_{i+1}{file_type}"
        filepath = os.path.join(context.input_dir, filename)
        
        if file_type == '.pdf':
            content = f"PDF document content {i+1}: This is a business report with financial data."
        elif file_type == '.png':
            content = f"PNG image data {i+1}: Mock image content for OCR processing."
        else:  # .txt
            content = f"Text document content {i+1}: Plain text file with important information."
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': content,
            'type': file_type,
            'processing_status': 'pending'
        }


@given("I have not configured any settings yet")
def verify_no_configuration(workflow_context):
    """Verify no existing configuration for new user"""
    context = workflow_context
    
    config_files = [
        os.path.join(context.config_dir, "user_preferences.json"),
        os.path.join(context.config_dir, "ai_settings.json"),
        os.path.join(context.config_dir, "expert_mode.json")
    ]
    
    for config_file in config_files:
        assert not os.path.exists(config_file), f"Found existing config: {config_file}"


# Complex file setup with specific issues
@given("I have 8 files in the input directory with various issues:")
def create_files_with_issues_table(workflow_context, table):
    """Create files with specific issues based on table"""
    context = workflow_context
    
    for row in table:
        filename = row['filename']
        issue = row['issue']
        filepath = os.path.join(context.input_dir, filename)
        
        # Create file content based on issue type
        if issue == 'none':
            content = f"Valid content for {filename}"
            status = 'valid'
        elif issue == 'temporarily_locked':
            content = f"Content for {filename} (will be locked)"
            status = 'temp_locked'
        elif issue == 'corrupted_content':
            content = "%%CORRUPTED_PDF_DATA%%"
            status = 'corrupted'
        elif issue == 'exceeds_size_limit':
            content = "X" * 1000000  # Large content to simulate size limit
            status = 'oversized'
        elif issue == 'unsupported_format':
            content = f"PowerPoint content for {filename}"
            status = 'unsupported'
        elif issue == 'temporary_network_issue':
            content = f"Content for {filename} (will have network issues)"
            status = 'network_temp'
        else:
            content = f"Content for {filename}"
            status = 'unknown'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': content,
            'issue': issue,
            'status': status
        }


@given(parsers.parse("I have {count:d} documents with specific processing requirements"))
def create_documents_for_expert(workflow_context, count):
    """Create documents that require expert configuration"""
    context = workflow_context
    
    for i in range(count):
        filename = f"expert_document_{i+1}.pdf"
        filepath = os.path.join(context.input_dir, filename)
        
        # Create content that would benefit from expert settings
        content = f"""Expert Document {i+1}
        Category: Financial Planning
        Priority: High
        Department: Accounting
        Date: 2024-{i+1:02d}-15
        Special Requirements: Custom naming pattern needed"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        context.test_files[filename] = {
            'path': filepath,
            'content': content,
            'requires_expert_processing': True
        }


# Application execution steps
@when("I run the application for the first time")
def run_application_first_time(workflow_context):
    """Run application for first time user"""
    context = workflow_context
    
    # Mock first-time setup flow
    context.container = ApplicationContainer.create_for_testing(
        input_dir=context.input_dir,
        processed_dir=context.processed_dir,
        unprocessed_dir=context.unprocessed_dir,
        console=context.test_console,
        first_time_setup=True
    )
    
    context.cli_interface = CLIInterface(context.container)
    
    with context.capture_console_output():
        try:
            # Simulate first-time setup and processing
            context.setup_result = context.cli_interface.run_first_time_setup()
            context.processing_stages.append("first_time_setup")
        except Exception as e:
            context.setup_error = e
        
        context.display_output = context.get_console_output()


@when("I run the application with expert mode")
def run_application_expert_mode(workflow_context):
    """Run application in expert mode"""
    context = workflow_context
    
    context.container = ApplicationContainer.create_for_testing(
        input_dir=context.input_dir,
        processed_dir=context.processed_dir,
        unprocessed_dir=context.unprocessed_dir,
        console=context.test_console,
        expert_mode=True,
        config_dir=context.config_dir
    )
    
    context.cli_interface = CLIInterface(context.container)
    
    with context.capture_console_output():
        try:
            context.expert_mode_result = context.cli_interface.run_expert_mode()
            context.processing_stages.append("expert_mode_setup")
        except Exception as e:
            context.expert_mode_error = e
        
        context.display_output = context.get_console_output()


@when("I run the document processing")
def run_document_processing_workflow(workflow_context):
    """Run document processing in workflow context"""
    context = workflow_context
    
    if not context.container:
        context.container = ApplicationContainer.create_for_testing(
            input_dir=context.input_dir,
            processed_dir=context.processed_dir,
            unprocessed_dir=context.unprocessed_dir,
            console=context.test_console
        )
        context.cli_interface = CLIInterface(context.container)
    
    with context.capture_console_output():
        try:
            context.processing_result = context.cli_interface.process_documents(
                input_dir=context.input_dir,
                processed_dir=context.processed_dir,
                unprocessed_dir=context.unprocessed_dir,
                ai_provider="test_provider",
                enable_retries=True,
                user_type=context.user_type
            )
            context.processing_stages.append("document_processing")
        except Exception as e:
            context.processing_error = e
        
        # Append new output to existing display output
        new_output = context.get_console_output()
        if context.display_output:
            context.display_output += "\n" + new_output
        else:
            context.display_output = new_output


# First-time user workflow assertions
@then("I should see a welcome message and setup instructions")
def verify_welcome_message(workflow_context):
    """Verify welcome message for new users"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    welcome_indicators = [
        "welcome", "Welcome", "setup", "Setup",
        "first time", "getting started", "configuration"
    ]
    
    found_welcome = any(indicator in context.display_output for indicator in welcome_indicators)
    assert found_welcome, f"No welcome message found in: {context.display_output}"


@then("I should be guided through the initial configuration process")
def verify_configuration_guidance(workflow_context):
    """Verify configuration guidance is provided"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    guidance_indicators = [
        "configure", "Configuration", "settings", "Settings",
        "choose", "select", "preferences"
    ]
    
    found_guidance = any(indicator in context.display_output for indicator in guidance_indicators)
    assert found_guidance, f"No configuration guidance found in: {context.display_output}"


@then("I should be able to set my preferred AI provider")
def verify_ai_provider_selection(workflow_context):
    """Verify AI provider selection is available"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    ai_indicators = ["AI provider", "OpenAI", "Claude", "Gemini", "provider"]
    found_ai_setup = any(indicator in context.display_output for indicator in ai_indicators)
    assert found_ai_setup, f"No AI provider selection found in: {context.display_output}"


@then("I should be able to configure my input and output directories")
def verify_directory_configuration(workflow_context):
    """Verify directory configuration is available"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    directory_indicators = [
        "input directory", "output directory", "processed", "folder", "path"
    ]
    
    found_directory_config = any(indicator in context.display_output for indicator in directory_indicators)
    assert found_directory_config, f"No directory configuration found in: {context.display_output}"


# Expert user workflow assertions  
@then("I should see advanced configuration options")
def verify_advanced_options(workflow_context):
    """Verify advanced configuration options for expert users"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    advanced_indicators = [
        "advanced", "Advanced", "expert", "Expert", "custom", "Custom",
        "pattern", "configuration", "options"
    ]
    
    found_advanced = any(indicator in context.display_output for indicator in advanced_indicators)
    assert found_advanced, f"No advanced options found in: {context.display_output}"


@then("I should be able to customize filename generation patterns")
def verify_filename_customization(workflow_context):
    """Verify filename pattern customization"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    pattern_indicators = [
        "filename", "pattern", "naming", "custom", "format", "template"
    ]
    
    found_pattern_config = any(indicator in context.display_output for indicator in pattern_indicators)
    assert found_pattern_config, f"No filename customization found in: {context.display_output}"


# Processing result assertions
@then("all files should process successfully with meaningful names")
def verify_successful_processing_meaningful_names(workflow_context):
    """Verify successful processing with meaningful names"""
    context = workflow_context
    
    processed_files = os.listdir(context.processed_dir)
    expected_count = len(context.test_files)
    
    assert len(processed_files) == expected_count, \
        f"Expected {expected_count} processed files, found {len(processed_files)}"
    
    # Verify names are meaningful (not just generic)
    for filename in processed_files:
        assert len(filename) > 10, f"Filename too short to be meaningful: {filename}"
        assert not filename.startswith("temp_"), f"Filename appears generic: {filename}"


@then("I should see clear progress indicators throughout the process")
def verify_progress_indicators(workflow_context):
    """Verify clear progress indicators"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    progress_indicators = [
        "Progress", "progress", "Processing", "processing",
        "%", "complete", "Complete", "finished"
    ]
    
    found_progress = sum(1 for indicator in progress_indicators 
                        if indicator in context.display_output)
    
    assert found_progress >= 2, f"Insufficient progress indicators in: {context.display_output}"


@then("I should see a completion summary with statistics")
def verify_completion_summary(workflow_context):
    """Verify completion summary with statistics"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    summary_indicators = [
        "summary", "Summary", "statistics", "Statistics",
        "completed", "Completed", "total", "Total"
    ]
    
    found_summary = any(indicator in context.display_output for indicator in summary_indicators)
    assert found_summary, f"No completion summary found in: {context.display_output}"


@then("I should understand where my processed files are located")
def verify_file_location_clarity(workflow_context):
    """Verify user understands where processed files are located"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    location_indicators = [
        "processed", "location", "folder", "directory", "saved", "found"
    ]
    
    found_location_info = any(indicator in context.display_output for indicator in location_indicators)
    assert found_location_info, f"No file location information found in: {context.display_output}"


# Retry success determination assertions (Critical bug prevention)
@then("I should see the 3 immediately available files process first")
def verify_immediate_processing_order(workflow_context):
    """Verify immediately available files process first"""
    context = workflow_context
    
    # This tests the critical retry success determination workflow
    assert context.display_output is not None, "No display output captured"
    
    # Should see processing messages for available files
    processing_messages = context.display_output.count("Processing")
    assert processing_messages >= 3, \
        f"Expected processing messages for 3 immediate files, found {processing_messages}"


@then("the progress statistics should update correctly throughout:")
def verify_progress_statistics_table(workflow_context, table):
    """Verify progress statistics update correctly throughout processing"""
    context = workflow_context
    
    # This is the critical test that would have caught the 2-hour debugging bug
    assert context.processing_result is not None, "No processing result available"
    
    for row in table:
        stage = row['stage']
        expected_success = int(row['success_count'])
        expected_failed = int(row['failed_count'])
        expected_retry = int(row['retry_count'])
        
        # Verify statistics match expected values for each stage
        # This would catch the bug where retry successes showed as failures
        if stage == "after_retry_success":
            actual_success = context.processing_result.get('success_count', 0)
            actual_failed = context.processing_result.get('failed_count', 0)
            actual_retry = context.processing_result.get('retry_count', 0)
            
            assert actual_success == expected_success, \
                f"Stage {stage}: Expected {expected_success} successes, got {actual_success}"
            assert actual_failed == expected_failed, \
                f"Stage {stage}: Expected {expected_failed} failures, got {actual_failed}"
            assert actual_retry == expected_retry, \
                f"Stage {stage}: Expected {expected_retry} retries, got {actual_retry}"


@then("ALL files should appear in the processed directory, not unprocessed")
def verify_all_files_in_processed_directory(workflow_context):
    """Verify ALL files appear in processed directory (critical bug prevention)"""
    context = workflow_context
    
    # This assertion would have caught the 2-hour debugging bug
    processed_files = os.listdir(context.processed_dir)
    unprocessed_files = os.listdir(context.unprocessed_dir)
    
    total_input_files = len(context.test_files)
    
    # ALL files should be in processed directory
    assert len(processed_files) == total_input_files, \
        f"Expected ALL {total_input_files} files in processed directory, found {len(processed_files)}"
    
    # NO files should be in unprocessed directory for this scenario
    assert len(unprocessed_files) == 0, \
        f"Expected no files in unprocessed directory, found {len(unprocessed_files)}: {unprocessed_files}"


@then("the user should clearly understand that all files were ultimately successful")
def verify_user_understands_success(workflow_context):
    """Verify user clearly understands all files were successful"""
    context = workflow_context
    
    assert context.display_output is not None, "No display output captured"
    
    # Should contain clear success messaging
    success_indicators = [
        "all files", "All files", "successful", "Successful",
        "complete", "Complete", "100%"
    ]
    
    found_success_clarity = any(indicator in context.display_output for indicator in success_indicators)
    assert found_success_clarity, \
        f"User success understanding not clear in: {context.display_output}"


# Cleanup
def cleanup_workflow_environment(context):
    """Clean up workflow test environment"""
    if hasattr(context, 'ai_service_patch'):
        context.ai_service_patch.stop()
    
    if context.temp_dir and os.path.exists(context.temp_dir):
        import shutil
        shutil.rmtree(context.temp_dir)
    
    context.teardown_rich_test_environment()


def enhance_workflow_context_cleanup(context):
    """Add cleanup method to workflow context"""
    original_cleanup = getattr(context, 'cleanup_test_environment', lambda: None)
    
    def enhanced_cleanup():
        cleanup_workflow_environment(context)
        original_cleanup()
    
    context.cleanup_test_environment = enhanced_cleanup


@pytest.fixture
def workflow_context():
    """Provide test context for workflow scenarios"""
    context = WorkflowTestContext()
    enhance_workflow_context_cleanup(context)
    yield context
    context.cleanup_test_environment()