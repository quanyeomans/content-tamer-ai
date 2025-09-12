# Testing First Template
*Step-by-step TDD workflow based on our TESTING_STRATEGY.md*

## Problem Analysis Template

### What's Broken?
- **User impact**: What does the user experience when this fails?
- **Root cause**: What's actually broken (not just symptoms)?
- **Component scope**: Does this affect one component or multiple?

### Strategy Alignment
- **Test pyramid level**: Is this a unit test, integration test, or BDD scenario?
- **Existing tests**: Which test file should I extend? (`tests/test_*.py`)
- **Anti-pattern check**: Am I about to over-mock or test implementation details?

## Test Planning

### Test Design (Write This First)
```python
def test_[specific_behavior_user_experiences](self):
    """
    When [user does X]
    Then [user should see Y]
    Because [business reason]
    """
    # Arrange: Set up realistic conditions
    
    # Act: Perform the actual user action
    
    # Assert: Verify user-observable outcome
```

### Mock Strategy
- **External only**: Only mock AI APIs, external services
- **Keep real**: File operations, internal logic, data structures
- **Temporary directories**: Use `tempfile.TemporaryDirectory()` for file tests
- **Real objects**: Use actual classes with test data, not mocks

## Implementation Steps

### Step 1: Write Failing Test
- [ ] Test fails for the right reason (problem doesn't exist yet)
- [ ] Test describes user behavior, not code implementation
- [ ] Test uses realistic data and real file operations where possible

### Step 2: Minimal Implementation
- [ ] Write just enough code to make the test pass
- [ ] Don't add features the test doesn't require
- [ ] Keep it simple and readable

### Step 3: Refactor
- [ ] Clean up code without changing behavior
- [ ] Ensure it follows our patterns from existing codebase
- [ ] Add type hints and docstrings

### Step 4: Integration Check
If change affects multiple components:
- [ ] Add integration test to verify components work together
- [ ] Test the complete user workflow end-to-end
- [ ] Verify display/UI reflects correct state

## Test File Extensions

### Which File to Extend?
- **API/Validation**: `tests/test_integration.py`
- **Error Handling**: `tests/test_error_handling.py`
- **File Processing**: `tests/test_success_failure_integration.py`
- **UI/Display**: `tests/test_display_manager.py`
- **Security**: `tests/test_security.py`
- **New Feature**: Create new test file following naming pattern

### BDD Scenarios (When Appropriate)
For user-facing features, add to `tests/features/`:
```gherkin
Feature: User-friendly error messages
  Scenario: User provides wrong API key type
    Given the application is configured for OpenAI
    When user provides a Claude API key
    Then user sees clear error message explaining the mismatch
    And user gets exact commands to fix the problem
```

## Common Patterns

### File Processing Tests
```python
def test_file_processing_behavior(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = create_test_file(temp_dir, "test.pdf")
        
        # Only mock external AI call
        with patch('ai_client.generate_filename') as mock_ai:
            mock_ai.return_value = "expected_name"
            
            result = process_file(input_file, ...)
            
            # Test user-observable outcomes
            self.assertTrue(os.path.exists(expected_output_path))
            self.assertEqual(result.status, "success")
```

### Error Handling Tests  
```python
def test_helpful_error_message(self):
    with self.assertRaises(ValueError) as context:
        validate_api_key(wrong_key, "openai")
    
    error_message = str(context.exception)
    self.assertIn("API key mismatch", error_message)
    self.assertIn("--provider claude", error_message)  # Actionable fix
```

## Red Flags

**Stop and ask for help if:**
- I want to mock more than 2 things in one test
- I'm testing private methods or internal state
- I'm writing tests after implementation
- I'm copying existing test patterns that use excessive mocking
- The test passes immediately (probably testing nothing meaningful)

*Based on lessons from TESTING_STRATEGY.md to prevent repeating our 2-hour debugging session*