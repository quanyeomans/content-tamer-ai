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

### **🚨 MANDATORY Security & Quality Gates**
- [ ] **SAST Scan Clean**: `bandit -r src/ -f text` shows no HIGH/MEDIUM issues
- [ ] **Dependency Scan**: `safety check` shows no known vulnerabilities  
- [ ] **Code Quality**: `pylint src/ --fail-under=8.0` passes minimum threshold
- [ ] **Type Safety**: `pyright src/` shows no errors or redeclarations
- [ ] **Mypy Validation**: `mypy src/ --ignore-missing-imports` shows no critical errors
- [ ] **Formatting**: `black --check src/` and `isort --check-only src/` pass
- [ ] **Test Coverage**: All modified code paths covered by passing tests
- [ ] **Integration Validation**: End-to-end functionality verified with real data
- [ ] **Debugging Evidence**: All fixes backed by root cause analysis documentation

**🚨 CRITICAL: Pyright is our early warning system for structural issues like duplicate functions. Always run `pyright src/` before declaring work complete.**

### Security Validation (Enhanced)
- [ ] **API key safety**: Verify no API keys in logs/displays using `grep -r "sk-" src/`
- [ ] **Path security**: Validate file paths against directory traversal
- [ ] **Input validation**: Check all user inputs are sanitized  
- [ ] **Error handling**: Ensure safe error messages (no stack traces with secrets)
- [ ] **XML/JSON parsing**: Use secure parsers (defusedxml, not ElementTree)

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

## 🔍 Evidence-Based Debugging Protocol

**When issues arise, follow this mandatory protocol:**

### Phase 1: Evidence Collection
- [ ] **Reproduce issue**: Create minimal reproduction case
- [ ] **Gather logs**: Collect full error traces and context
- [ ] **Document symptoms**: What exactly is failing vs what's expected
- [ ] **Version control status**: Check what changed since last working state

### Phase 2: Root Cause Analysis
- [ ] **Hypothesis formation**: Based on evidence, not assumptions
- [ ] **Systematic testing**: Test one variable at a time
- [ ] **Code path tracing**: Follow execution through suspected areas
- [ ] **Dependency verification**: Check imports, versions, configurations

### Phase 3: Fix Implementation
- [ ] **Minimal viable fix**: Address root cause, not symptoms
- [ ] **Feature flags/alternatives**: Preserve working paths during changes
- [ ] **Test fix in isolation**: Verify fix resolves specific issue
- [ ] **No functionality changes**: Fix the bug without altering behavior

### Debugging First Principles
1. **Evidence over assumptions**: Never guess when you can verify
2. **Root cause over symptoms**: Fix the underlying issue, not manifestations
3. **One change at a time**: Isolate variables to identify actual causes
4. **Preserve working code**: Use feature flags rather than replacing working logic
5. **Document the journey**: Record what was tried and why it failed/succeeded

## 📋 TodoWrite Integration Points

1. **Pre-implementation**: Create todo list with specific tasks
2. **During work**: Mark tasks "in_progress" before starting, "completed" immediately after finishing
3. **Task discovery**: Add new tasks as they're discovered during implementation
4. **Completion**: Final todo should be completion validation

## 📚 Related Documentation

- **[DEBUG_FIRST_PRINCIPLES.md](DEBUG_FIRST_PRINCIPLES.md)**: Evidence-based debugging methodology
- **[CODE_QUALITY_CHECKLIST.md](CODE_QUALITY_CHECKLIST.md)**: Comprehensive quality gates for complex changes
- **[TESTING_STRATEGY.md](../TESTING_STRATEGY.md)**: Test-first development patterns and practices

## 🎯 Process Integration

**For complex changes affecting multiple components:**
1. Follow this IMPLEMENTATION_WORKFLOW.md for TDD process
2. Apply CODE_QUALITY_CHECKLIST.md for comprehensive quality gates  
3. Use DEBUG_FIRST_PRINCIPLES.md when issues arise
4. Maintain TodoWrite discipline throughout

**For debugging sessions:**
1. Start with DEBUG_FIRST_PRINCIPLES.md evidence collection
2. Apply systematic root cause analysis
3. Implement fixes using this workflow's TDD approach
4. Validate with appropriate sections of CODE_QUALITY_CHECKLIST.md

*This workflow integrates our TESTING_STRATEGY.md patterns with TodoWrite discipline and evidence-based debugging to ensure consistent, high-quality development*