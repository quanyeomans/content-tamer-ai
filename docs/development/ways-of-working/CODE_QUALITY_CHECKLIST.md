# Code Quality Checklist for Complex Changes
*Systematic quality assurance for high-impact modifications*

## 🎯 When to Use This Checklist

Apply this comprehensive checklist for:
- **Multi-file changes** affecting 3+ components
- **Core architecture modifications** (file processing, AI integration, security)
- **Bug fixes for critical failures** (processing pipeline breaks, security issues)
- **New feature integrations** with external dependencies
- **Performance optimizations** affecting main workflows
- **Refactoring that changes function signatures** or module structure

## 📋 Pre-Implementation Quality Gates

### Requirements Clarity
- [ ] **User story defined**: Clear description of what user will experience
- [ ] **Acceptance criteria**: Specific, measurable outcomes defined
- [ ] **Edge cases identified**: Known failure scenarios documented
- [ ] **Performance expectations**: Response time/throughput requirements set
- [ ] **Security requirements**: Authentication, authorization, data protection needs

### Architecture Design
- [ ] **Impact analysis**: All affected components identified
- [ ] **Dependency mapping**: External services and libraries catalogued  
- [ ] **Data flow design**: Input/output transformations documented
- [ ] **Error handling strategy**: Failure modes and recovery approaches planned
- [ ] **Rollback plan**: Mechanism to revert changes if issues arise

## 🧪 Test-First Development

### Test Strategy
- [ ] **Existing test analysis**: Review current test coverage for affected areas
- [ ] **Test file selection**: Extend appropriate existing test files (never create new)
- [ ] **Behavior-focused tests**: Tests describe user outcomes, not implementation
- [ ] **Real file operations**: Use `tempfile.TemporaryDirectory()` for file tests
- [ ] **Minimal mocking**: Only mock external AI APIs and network calls

### Test Implementation
- [ ] **Failing test written**: Red-green-refactor cycle starts with failure
- [ ] **Test isolation**: Each test independent of others
- [ ] **Realistic data**: Test with actual file types and sizes
- [ ] **Edge case coverage**: Invalid inputs, boundary conditions, error states
- [ ] **Performance benchmarks**: Tests include timing assertions where relevant

## 🔨 Implementation Quality

### Code Standards
- [ ] **Single responsibility**: Functions do one thing well
- [ ] **Type hints**: All new functions have comprehensive type annotations
- [ ] **Docstrings**: Clear documentation with examples for complex functions
- [ ] **Error messages**: User-friendly messages with actionable guidance
- [ ] **No magic numbers**: Constants defined with meaningful names

### Security Implementation
- [ ] **Input validation**: All user inputs sanitized and validated
- [ ] **Path security**: File operations protected against directory traversal
- [ ] **Secret handling**: No API keys/tokens in logs or error messages
- [ ] **XML parsing**: Use `defusedxml` instead of `ElementTree`
- [ ] **SQL safety**: Parameterized queries, no string concatenation

### Integration Patterns
- [ ] **Existing patterns followed**: Code style matches surrounding modules
- [ ] **Library consistency**: Use established dependencies, don't add new ones
- [ ] **Error propagation**: Failures bubble up with context
- [ ] **Resource cleanup**: Files closed, connections released, temp dirs cleaned
- [ ] **Logging strategy**: Appropriate log levels with structured information

## 🔍 Evidence-Based Debugging (For Bug Fixes)

### Root Cause Analysis
- [ ] **Issue reproduction**: Minimal case that demonstrates the problem
- [ ] **Evidence collection**: Full logs, stack traces, environment details
- [ ] **Hypothesis formation**: Theories based on evidence, not assumptions
- [ ] **Systematic testing**: One variable changed at a time
- [ ] **Root cause identification**: Underlying issue found and documented

### Fix Implementation
- [ ] **Minimal fix**: Addresses root cause without changing other behavior
- [ ] **Feature flag option**: Ability to revert to previous behavior if needed
- [ ] **Fix validation**: Specific test confirms the bug is resolved
- [ ] **Regression prevention**: New test prevents the issue from recurring
- [ ] **Side effect check**: No unintended changes to other functionality

## 🛡️ Quality Assurance Testing

### Automated Validation
- [ ] **All tests pass**: `pytest tests/ -v --cov=src --cov-report=term-missing`
- [ ] **Code coverage**: Modified code paths covered by tests
- [ ] **SAST clean**: `bandit -r src/ -f text` shows no HIGH/MEDIUM issues
- [ ] **Dependency security**: `safety check` shows no vulnerabilities
- [ ] **Type safety**: `mypy src/ --ignore-missing-imports` passes
- [ ] **Code quality**: `pylint src/ --fail-under=8.0` meets threshold
- [ ] **Formatting**: `black src/ tests/` and `isort src/ tests/` applied

### Integration Testing
- [ ] **End-to-end validation**: Full user workflow tested with real data
- [ ] **Error path testing**: Failure scenarios produce appropriate user messages
- [ ] **Performance validation**: Response times meet established benchmarks
- [ ] **UI consistency**: Progress indicators reflect actual processing state
- [ ] **Cross-platform testing**: Works on Windows/Unix environments

### Manual Quality Review
- [ ] **Code walkthrough**: Logic reviewed line-by-line for correctness
- [ ] **Documentation accuracy**: Comments and docstrings match implementation
- [ ] **User experience**: Interface remains intuitive and helpful
- [ ] **Error messages**: Failures provide actionable guidance to users
- [ ] **Resource usage**: Memory/CPU consumption within acceptable limits

## 📊 Completion Validation

### Definition of Done
- [ ] **All acceptance criteria met**: User story requirements fulfilled
- [ ] **Security gates passed**: All automated security checks clean
- [ ] **Performance benchmarks met**: Response times within expectations
- [ ] **Documentation updated**: README, API docs reflect changes
- [ ] **Team knowledge shared**: Implementation approach communicated

### Deployment Readiness
- [ ] **Rollback tested**: Can revert changes without data loss
- [ ] **Monitoring prepared**: Appropriate logging for production troubleshooting
- [ ] **Support documentation**: Known issues and troubleshooting guide ready
- [ ] **Configuration validated**: Settings work in target environment
- [ ] **Dependencies verified**: Required libraries available in production

## 🚨 Quality Gate Failures

**If any mandatory check fails:**
1. **Stop implementation** - Do not proceed to next phase
2. **Root cause analysis** - Understand why the check failed
3. **Fix or redesign** - Address the underlying issue
4. **Re-validate completely** - Run all checks again after fix
5. **Document lessons** - Update process to prevent recurrence

## ⚡ Fast Track for Simple Changes

**For truly simple changes (single function, no new dependencies):**
- [ ] Failing test written and passes
- [ ] SAST scan clean  
- [ ] All existing tests pass
- [ ] Code formatted (black/isort)
- [ ] One manual walkthrough of user path

**Escalate to full checklist if:**
- Change touches multiple files
- New dependencies required  
- Performance characteristics change
- Security implications discovered
- Integration complexity emerges

## 🎯 Success Metrics

A quality implementation achieves:
- **Zero regressions**: No existing functionality broken
- **Security compliance**: All automated security checks pass
- **User value delivered**: Acceptance criteria demonstrably met
- **Maintainable code**: Future developers can understand and modify
- **Production ready**: Can deploy with confidence

*This checklist ensures that complex changes maintain system reliability while delivering genuine user value. Skip steps at your own risk - the time invested in quality assurance pays dividends in reduced support burden and user satisfaction.*