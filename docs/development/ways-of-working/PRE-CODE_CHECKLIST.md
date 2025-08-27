# Pre-Code Checklist
*Essential gates before any implementation - use TodoWrite to track*

## 🛡️ MANDATORY GATES (All 4 Required)

### Gate 1: Strategy Alignment 
- [ ] **Test approach planned**: Which test file will I extend? What behavior will I test?
- [ ] **Security implications assessed**: Any API keys, file paths, or user inputs involved?
- [ ] **Backward compatibility considered**: Will this break existing user workflows?
- [ ] **Minimal scope defined**: What's the smallest change that solves the problem?

### Gate 2: TodoWrite Planning
- [ ] **Create todo list**: Break down the work into specific, trackable tasks
- [ ] **Identify test files**: Note which existing test files need extension
- [ ] **Plan security checks**: Note which security validations are needed
- [ ] **Define completion criteria**: What does "done" look like?

### Gate 3: Test-First Commitment
- [ ] **Test file identified**: I know exactly which `tests/test_*.py` file to extend
- [ ] **Test behavior defined**: I can describe the user-observable behavior to test
- [ ] **Mock strategy planned**: Only external services (AI APIs) - keep file ops real
- [ ] **Edge cases considered**: What error conditions need testing?

### Gate 4: Security Review
- [ ] **API key safety**: No logging, displaying, or storing of API keys
- [ ] **Path validation**: All file paths protected against directory traversal  
- [ ] **Input sanitization**: User inputs validated and sanitized appropriately
- [ ] **Error message safety**: No sensitive information in error messages

## 🚨 RED FLAGS - STOP IMMEDIATELY

**If any of these apply, STOP and ask for guidance:**
- Wanting to "just quickly fix without tests"
- Planning to mock more than external services
- Skipping security checks for "simple changes"  
- Creating new patterns instead of following existing ones
- Implementation becoming more complex than the problem

## ✋ PAUSE POINT

**Before proceeding to implementation, confirm:**
```
✅ ALL 4 GATES COMPLETED
- Strategy aligned with existing patterns
- TodoWrite list created and tasks defined
- Test-first approach planned with specific test file
- Security implications reviewed and addressed

Ready to proceed with IMPLEMENTATION_WORKFLOW.md
```

*This checklist embeds our lessons from TESTING_STRATEGY.md and SECURITY_STANDARDS.md to prevent rushing to solutions*