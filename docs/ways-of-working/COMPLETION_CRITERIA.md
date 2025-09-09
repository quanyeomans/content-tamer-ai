# Completion Criteria
*Definition of "done" for any code change*

## Technical Completion

### Code Quality
- [ ] **Type hints**: All new functions have proper type hints
- [ ] **Docstrings**: All new functions have clear, descriptive docstrings
- [ ] **PEP 8 compliance**: Code formatted with black/isort, follows Python standards
- [ ] **Import organization**: Imports properly organized and minimal

### Testing Requirements
- [ ] **Tests written first**: Failing test existed before implementation
- [ ] **All tests pass**: New tests pass, existing tests still pass
- [ ] **Coverage maintained**: >90% test coverage for core functionality maintained
- [ ] **Behavioral testing**: Tests verify user-observable behavior, not implementation

### Security Validation
- [ ] **API key safety**: No API keys logged, stored, or displayed inappropriately
- [ ] **Input validation**: All user inputs validated and sanitized
- [ ] **Path security**: File paths protected against directory traversal
- [ ] **Error handling**: Error messages don't leak sensitive information

## Functional Completion

### Requirements Met
- [ ] **Original problem solved**: The issue that prompted this change is resolved
- [ ] **User experience**: Solution works from user's perspective  
- [ ] **Edge cases handled**: Common error conditions handled gracefully
- [ ] **Backward compatibility**: Existing user workflows still work (unless explicitly changed)

### Integration Verified
- [ ] **Component interactions**: If change spans multiple components, integration tested
- [ ] **End-to-end flow**: Complete user workflow tested from start to finish
- [ ] **Display consistency**: UI/progress displays reflect actual system state
- [ ] **Error propagation**: Errors properly communicated to user with actionable messages

## Cleanup Completion

### Development Artifacts Removed
- [ ] **Debug code removed**: No print statements, temporary logging, or debug artifacts
- [ ] **Test files cleaned**: No temporary test files, mock data, or debug scripts
- [ ] **Comments cleaned**: No TODO comments, debugging notes, or temporary markers
- [ ] **Imports optimized**: No unused imports or debugging modules

### Documentation Updated
- [ ] **User-facing changes documented**: Any changes affecting user experience documented
- [ ] **API changes noted**: Changes to function signatures or behavior documented
- [ ] **Security implications noted**: Any security-relevant changes documented
- [ ] **Configuration updates**: New environment variables or settings documented

## Quality Gates

### Pre-Implementation
- [ ] **Strategy alignment confirmed**: Change follows our established testing and security practices
- [ ] **Test approach planned**: Clear plan for what tests to write and which files to extend
- [ ] **Minimal scope defined**: Smallest change that solves the problem identified
- [ ] **Backward compatibility considered**: Impact on existing functionality assessed

### Post-Implementation  
- [ ] **Functionality validated**: Solution actually works in realistic conditions
- [ ] **Performance acceptable**: No significant performance degradation introduced
- [ ] **Error handling tested**: Error conditions produce appropriate user messages
- [ ] **Integration stable**: System remains stable with change integrated

## Validation Methods

### Automated Validation
```bash
# Code quality
black src/ tests/
isort src/ tests/
pylint src/ tests/

# Test execution  
pytest tests/ -v --cov=src --cov-report=term-missing

# Security scan (if applicable)
safety check requirements.txt
```

### Manual Validation
- [ ] **User workflow test**: Walk through actual user scenario end-to-end
- [ ] **Error condition test**: Try to break it with invalid inputs
- [ ] **Cross-platform test**: Verify works on different terminal environments
- [ ] **Performance test**: Ensure acceptable performance with realistic data

## Declaration Format

When marking work as complete, I will provide this declaration:

```
✅ **COMPLETION CRITERIA VALIDATED**

**Technical Completion:**
- Tests written first: ✅ [brief description]
- Security validated: ✅ [key security checks performed]
- Code quality: ✅ [formatting, type hints, docstrings completed]

**Functional Completion:**
- Requirements met: ✅ [original problem solved]
- Integration verified: ✅ [end-to-end testing performed] 
- User experience: ✅ [user workflow validated]

**Cleanup Completed:**
- Debug artifacts removed: ✅ [all temporary code cleaned]
- Documentation updated: ✅ [relevant docs updated]

**Ready for review/deployment.**
```

## Red Flags: Not Done

**Work is NOT complete if:**
- [ ] Any temporary/debug code remains in the codebase
- [ ] Tests were written after implementation
- [ ] User experience hasn't been validated end-to-end
- [ ] Security implications haven't been considered
- [ ] Error conditions haven't been tested
- [ ] Performance impact hasn't been assessed
- [ ] Integration with existing system hasn't been verified

*"Done" means ready for production use, not just "code works on my machine"*