"""Simple step definitions to validate BDD framework setup."""
import os
import tempfile
import shutil
from pytest_bdd import given, when, then, scenario
import pytest


@pytest.fixture
def simple_context():
    """Simple test context."""
    context = type('Context', (), {})()
    context.temp_dir = tempfile.mkdtemp()
    yield context
    if os.path.exists(context.temp_dir):
        shutil.rmtree(context.temp_dir)


@scenario('../simple_document_processing.feature', 'User sees processing starts')
def test_user_sees_processing_starts():
    pass


@given('I have a test directory')
def test_directory(simple_context):
    """Create a test directory."""
    assert os.path.exists(simple_context.temp_dir)
    simple_context.input_dir = os.path.join(simple_context.temp_dir, "input")
    os.makedirs(simple_context.input_dir)


@when('I create a simple test file')
def create_simple_file(simple_context):
    """Create a simple test file."""
    simple_context.test_file = os.path.join(simple_context.input_dir, "test.txt")
    with open(simple_context.test_file, 'w') as f:
        f.write("Hello, BDD World!")


@then('I should see the file exists')
def verify_file_exists(simple_context):
    """Verify the file exists."""
    assert os.path.exists(simple_context.test_file), "Test file should exist"
    with open(simple_context.test_file, 'r') as f:
        content = f.read()
    assert "Hello, BDD World!" in content, "File should contain expected content"