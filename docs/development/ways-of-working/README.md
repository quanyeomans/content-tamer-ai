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
- **Minimal mocking** - Only mock external services
- **Real file operations** - Use temp directories

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