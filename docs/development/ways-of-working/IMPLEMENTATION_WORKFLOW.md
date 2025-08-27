# Implementation Workflow
*Step-by-step TDD process with TodoWrite integration*

## 🧪 STEP 1: Write Failing Test

### Update TodoWrite
```
Mark current implementation task as "in_progress"
```

### Test Requirements
- [ ] **Test file selected**: Extend existing `tests/test_*.py` file (never create new)
- [ ] **Behavior focused**: Test describes user-observable behavior, not implementation
- [ ] **Real operations**: Use `tempfile.TemporaryDirectory()` for file tests
- [ ] **Minimal mocking**: Only mock external AI APIs, keep everything else real

### Test Pattern
```python
def test_specific_user_behavior(self):
    """
    When [user does X]
    Then [user should see Y]  
    Because [business reason]
    """
    # Arrange: Set up realistic test conditions
    # Act: Perform the user action
    # Assert: Verify user-observable outcome
```

## 🔨 STEP 2: Minimal Implementation

### Implementation Rules
- [ ] **Make test pass**: Write just enough code to make the test pass
- [ ] **No extra features**: Don't add functionality the test doesn't require
- [ ] **Follow patterns**: Mimic existing codebase patterns and style
- [ ] **Type hints**: Add type hints to all new functions

## 🔄 STEP 3: Refactor & Polish

### Code Quality
- [ ] **Clean code**: Remove any temporary/debug code
- [ ] **Docstrings**: Add clear docstrings to new functions
- [ ] **Import optimization**: Remove unused imports
- [ ] **PEP 8 compliance**: Ensure proper formatting

### Security Validation
- [ ] **API key safety**: Verify no API keys in logs/displays
- [ ] **Path security**: Validate file paths against directory traversal
- [ ] **Input validation**: Check all user inputs are sanitized
- [ ] **Error handling**: Ensure safe error messages

## 🔗 STEP 4: Integration Testing (If Multi-Component)

### When Required
If change affects multiple components:
- [ ] **Integration test**: Add test verifying components work together
- [ ] **End-to-end validation**: Test complete user workflow
- [ ] **UI consistency**: Verify display/progress reflects actual state
- [ ] **Error propagation**: Ensure errors reach user with actionable messages

## ✅ STEP 5: Completion Validation

### Update TodoWrite
```
Mark current task as "completed"
Mark any discovered follow-up tasks as "pending"
```

### Automated Checks
```bash
# Run these before marking complete
pytest tests/ -v --cov=src --cov-report=term-missing
black src/ tests/
isort src/ tests/
```

### Manual Validation
- [ ] **User workflow test**: Walk through actual user scenario end-to-end
- [ ] **Error condition test**: Try to break it with invalid inputs
- [ ] **Performance check**: Ensure acceptable performance with realistic data

### Final Declaration
```
✅ IMPLEMENTATION COMPLETE

**Technical:** Tests written first ✅ | Security validated ✅ | Code quality ✅
**Functional:** Requirements met ✅ | Integration verified ✅ | User experience validated ✅  
**Cleanup:** Debug artifacts removed ✅ | Documentation updated ✅

Ready for review/deployment.
```

## 🎯 Which Test File to Extend?

- **API/Validation**: `tests/test_integration.py`
- **Error Handling**: `tests/test_error_handling.py`  
- **File Processing**: `tests/test_success_failure_integration.py`
- **UI/Display**: `tests/test_display_manager.py`
- **Security**: `tests/test_security.py`

## 🚨 Red Flags During Implementation

**Stop and reassess if:**
- Test passes immediately (probably testing nothing meaningful)
- Mocking more than external services
- Implementation much more complex than expected
- Creating new patterns instead of following existing ones
- Wanting to skip steps for "simple changes"

## 📋 TodoWrite Integration Points

1. **Pre-implementation**: Create todo list with specific tasks
2. **During work**: Mark tasks "in_progress" before starting, "completed" immediately after finishing
3. **Task discovery**: Add new tasks as they're discovered during implementation
4. **Completion**: Final todo should be completion validation

*This workflow integrates our TESTING_STRATEGY.md patterns with TodoWrite discipline to ensure consistent, high-quality development*