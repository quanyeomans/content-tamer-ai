# Development Checklist
*Required gates before any code changes*

## Before I Start (Gate 1: Strategy Alignment)

### Test Strategy Check
- [ ] **Review testing approach**: What does TESTING_STRATEGY.md say about this type of change?
- [ ] **Check existing tests**: Which test files should I extend instead of creating new ones?
- [ ] **Avoid anti-patterns**: Am I about to over-mock or test implementation instead of behavior?

### Security Review
- [ ] **API key handling**: Will this change touch API keys? (Never log, store, or display them)
- [ ] **File operations**: Will this process user files? (Validate paths, check permissions, sanitize content)
- [ ] **Input validation**: Will this accept user input? (Validate all inputs before processing)

### Architecture Alignment
- [ ] **Existing patterns**: Can I build on existing code patterns instead of creating new complexity?
- [ ] **Backward compatibility**: Will this break existing user workflows? Do I need to preserve old behavior?
- [ ] **Minimal change**: What's the smallest change that solves the problem?

## Implementation Planning (Gate 2: Test-First Approach)

### Write Tests First
- [ ] **Failing test written**: I have a test that fails before my implementation
- [ ] **Behavioral focus**: My test validates what users experience, not how code works internally
- [ ] **Real dependencies**: I only mock external services (AI APIs), not internal file operations
- [ ] **Integration coverage**: If my change spans multiple components, I have integration tests

### Implementation Plan
- [ ] **Incremental approach**: Can I implement this in small, testable steps?
- [ ] **Error handling**: How will this fail gracefully? What error messages will users see?
- [ ] **Cleanup strategy**: What temporary/debug code will I need to remove?

## During Implementation (Gate 3: Quality Checks)

### Code Quality
- [ ] **Type hints added**: All new functions have proper type hints
- [ ] **Docstrings written**: All new functions have clear docstrings
- [ ] **Error messages**: All error messages are actionable and user-friendly
- [ ] **No debug code**: No print statements, temporary files, or debugging artifacts

### Security Implementation
- [ ] **Path validation**: All file paths validated against directory traversal
- [ ] **Content sanitization**: All extracted content sanitized before AI processing  
- [ ] **Memory protection**: API keys cleared from memory after use
- [ ] **Secure defaults**: All new configurations use secure defaults

## Before Completion (Gate 4: Validation)

### Test Execution
- [ ] **Tests pass**: All new tests pass
- [ ] **Regression check**: Existing tests still pass  
- [ ] **Coverage maintained**: Test coverage >90% for core functionality
- [ ] **Integration verified**: End-to-end user scenarios work

### Final Review
- [ ] **Requirements met**: Solution addresses original problem
- [ ] **Standards compliance**: Code follows PEP 8, has proper imports organization
- [ ] **Documentation updated**: Any user-facing changes documented
- [ ] **Debug cleanup**: All temporary files, debug scripts, and test artifacts removed

## Red Flags: Stop Immediately

If any of these happen, **STOP** and ask for guidance:

- [ ] **Rushing**: I feel pressured to skip these checks
- [ ] **Over-engineering**: My solution is more complex than the problem
- [ ] **Test skipping**: I want to "just quickly fix this without tests"
- [ ] **Pattern breaking**: I'm creating new ways of doing things instead of following existing patterns
- [ ] **Security shortcuts**: I'm tempted to skip security checks for "simple changes"

## Declaration

When I complete work, I will state:

> "✅ **Checklist Complete**: I have followed all gates, written tests first, validated security requirements, and cleaned up all debug code. The solution is ready for review."

*This checklist embeds our established practices from TESTING_STRATEGY.md, DEVELOPMENT_STANDARDS.md, and SECURITY_STANDARDS.md*