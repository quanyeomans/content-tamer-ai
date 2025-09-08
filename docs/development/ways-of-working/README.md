# Ways of Working
*Guardrails for consistent, high-quality development*

## Purpose

These documents provide the structure and checkpoints to ensure I consistently follow our established practices instead of rushing to code solutions.

## Streamlined Workflow

### 🛡️ [PRE-CODE_CHECKLIST.md](./PRE-CODE_CHECKLIST.md)
**Essential gates before any implementation**
- 4 mandatory pre-implementation gates
- TodoWrite planning integration
- Security and backward compatibility review
- Red flags and pause points

### 🧪 [IMPLEMENTATION_WORKFLOW.md](./IMPLEMENTATION_WORKFLOW.md)  
**Step-by-step TDD process with TodoWrite integration**
- Test-first implementation steps
- Security validation checkpoints
- Integration testing guidance
- Completion validation criteria

### 📊 **UNIT TEST EXPANSION WORKFLOW** *(Current Focus)*
**Module-by-module test coverage expansion**
- Target modules with 0% test coverage first
- Write 15-25 comprehensive tests per module
- Achieve 9.0+ pylint score before completion
- Cover defaults, validation, edge cases, and security scenarios
- Use proper mocking for external dependencies
- Maintain quality with systematic approach

## Usage Instructions

### For Every Code Change

1. **Start with PRE-CODE_CHECKLIST.md**
   - Complete all 4 mandatory gates
   - Use TodoWrite to plan and track tasks
   - Confirm test file and security approach

2. **Follow IMPLEMENTATION_WORKFLOW.md** 
   - Write failing test first
   - Implement minimal solution
   - Validate security and integration
   - Complete with proper cleanup

### For Unit Test Coverage Expansion *(Current Priority)*

**When to Use**: Improving test coverage on existing modules without functional changes

1. **Module Selection**: Choose modules with low/zero test coverage
2. **TodoWrite Planning**: Break into phases (defaults, validation, edge cases, security)
3. **Comprehensive Testing**: Write 15-25 tests covering all functions and edge cases
4. **Quality Gate**: Ensure 9.0+ pylint score maintained throughout
5. **Success Validation**: All tests pass, coverage achieved, quality maintained

**Pattern**: `utils/feature_flags.py` (21 tests), `core/filename_config.py` (18 tests), `utils/expert_mode.py` (22 tests)

**Current Architecture (2024)**: Modern dependency injection with ApplicationContainer pattern, centralized Rich UI management via ConsoleManager, and comprehensive Rich testing infrastructure via RichTestCase framework.

## Reference Documents

The following detailed guides provide additional context:

### 🔒 [SECURITY_REVIEW_CHECKLIST.md](./SECURITY_REVIEW_CHECKLIST.md)
**Comprehensive security validation**
- API key security requirements
- File system security checks  
- Input validation patterns
- Common vulnerability prevention

### ✅ [COMPLETION_CRITERIA.md](./COMPLETION_CRITERIA.md)
**Detailed definition of "done"**
- Technical completion requirements
- Functional validation steps
- Quality gate confirmation
- Documentation standards

### 🔄 [BACKWARD_COMPATIBILITY_GUIDE.md](./BACKWARD_COMPATIBILITY_GUIDE.md)
**When to preserve vs break existing behavior**
- Default preservation approach
- Breaking change decision framework
- Migration strategies
- Communication requirements

## Key Principles

### Test-Driven Development
- **Always write tests first** - No exceptions
- **Test user behavior** - Not implementation details  
- **ApplicationContainer Pattern** - Use TestApplicationContainer for dependency injection in tests
- **Rich UI Testing** - Inherit from RichTestCase for Rich UI component testing
- **Minimal mocking** - Only mock external services
- **Real file operations** - Use temp directories
- **Console isolation** - Use proper console management to prevent pytest I/O conflicts

### Security by Design
- **Never log API keys** - Environment variables only
- **Validate all inputs** - File paths, user data, content
- **Secure defaults** - Fail safely, restrict permissions
- **Safe error messages** - No information disclosure

### Quality Standards
- **Type hints required** - All new functions
- **Docstrings required** - Clear descriptions
- **Clean up after yourself** - No debug artifacts
- **Backward compatibility** - Preserve user workflows

## Red Flags: Stop and Ask for Help

If any of these occur, **STOP** immediately and ask for guidance:

- Feeling pressured to skip these processes
- Wanting to "just quickly fix without tests"
- Creating new patterns instead of following existing ones
- Skipping security checks for "simple changes"
- Implementation becoming more complex than the problem

## Process Enforcement

### Self-Check Questions
Before any implementation:
- "What does our testing strategy say about this?"
- "Which existing test file should I extend?"
- "What security implications does this have?"
- "Will this break existing user workflows?"

### Completion Declaration
When finished, provide this confirmation:
```
✅ WAYS OF WORKING FOLLOWED
- Development checklist: All 4 gates completed
- Testing first: Tests written before implementation  
- Security review: All security checks validated
- Completion criteria: Technical, functional, cleanup verified
- Compatibility: Impact assessed and addressed
```

## Benefits

### For Development Quality
- Prevents rushing to solutions
- Ensures comprehensive test coverage
- Maintains security standards
- Preserves system stability

### For Team Productivity  
- Reduces debugging sessions
- Prevents regression bugs
- Maintains consistent code quality
- Enables safe refactoring

### For User Experience
- Maintains reliable functionality
- Provides helpful error messages
- Preserves familiar workflows
- Ensures secure operation

*These Ways of Working embed lessons from our TESTING_STRATEGY.md, DEVELOPMENT_STANDARDS.md, and SECURITY_STANDARDS.md to prevent repeating past issues.*