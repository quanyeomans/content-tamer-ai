# Pre-Code Checklist
*Essential gates before any implementation - use TodoWrite to track*

## 🛡️ MANDATORY GATES (All 4 Required)

### Gate 1: Strategy Alignment 
- [ ] **Test approach planned**: Which test file will I extend? What behavior will I test?
- [ ] **Security implications assessed**: Any API keys, file paths, or user inputs involved?
- [ ] **Backward compatibility considered**: Will this break existing user workflows?
- [ ] **Minimal scope defined**: What's the smallest change that solves the problem?
- [ ] **Linting baseline established**: Current pylint/pyright status known for regression prevention

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

## 🧹 POST-IMPLEMENTATION LINTING CHECKLIST

**After any code changes, systematically validate:**

### Phase 1: Immediate Quality Check
```bash
# Must achieve before declaring work complete:
pylint [changed_files] --fail-under=9.5        # Individual file quality
pyright [changed_files]                        # Type safety validation
```

### Phase 2: Common Warning Elimination
```bash
# Zero tolerance for these common issues:
pylint src/ --disable=all --enable=W0611      # unused-import (remove or disable)
pylint src/ --disable=all --enable=W0612      # unused-variable (use _ prefix) 
pylint src/ --disable=all --enable=W0613      # unused-argument (add disable comment)
pylint src/ --disable=all --enable=W1203      # logging-fstring (convert to lazy %)
pylint src/ --disable=all --enable=E0401      # import-error (fix paths)
```

### Phase 3: Full Compliance Validation  
```bash
# Final quality gates (ALL must pass):
pylint src/ --fail-under=9.5                  # Overall quality ≥9.5/10
pyright src/ | grep "0 errors"                # Zero type errors
bandit -r src/ --severity-level high          # Zero high/medium security issues

# Perfect score verification:
pylint src/ --disable=all --enable=W0611,W0612,W0613  # Must be 10.00/10
```

### Parallel Agent Deployment Pattern
```
When facing systematic issues across multiple files:

1. 🤖 **Import Resolution Agent**: Fix provider import errors
2. 🤖 **Type Safety Agent**: Fix orchestration layer type issues  
3. 🤖 **Code Quality Agent**: Fix logging format and structure
4. 🤖 **Cleanup Agent**: Eliminate unused import/variable warnings

Deploy multiple agents simultaneously for maximum efficiency.
```

### **Retrospective Lessons (2025-01-09)**

#### **Research-First Approach**
- **Before implementing**: Research enterprise patterns for similar problems
- **Complexity estimation**: Research typically reduces estimates by 50-75%
- **Pattern sources**: pytest docs, DI testing patterns, ML model testing guides

#### **Systematic Completion Over Analysis**  
- **Set clear targets**: "Fix all X failures" instead of "improve test reliability"
- **Track progress**: Use TodoWrite to prevent analysis loops
- **Avoid avoidance**: Call out tendency to analyze instead of systematically fixing

#### **Clean Code Structure Wins**
- **When files become corrupted from edits**: Prefer clean rewrite over piecemeal patches
- **Pattern consistency**: Don't mix unittest + pytest patterns during refactoring
- **Structural integrity**: Clean structure fixes multiple issues simultaneously

#### **Agent Safety (Critical for Production)**
- **Before agent deployment**: Document expected import patterns and architecture constraints
- **Test critical functionality**: Run provider import validation after any agent changes
- **Security-critical code**: Never allow agents to modify API key handling, auth, or config storage
- **Incremental validation**: Test core workflows after each agent, not just at completion

### **Mandatory Smoke Tests Before Any Deployment**
```bash
# CRITICAL: These must pass before any release
python tests/smoke/test_critical_user_workflows.py

# AI Provider validation (catches import regressions)
python -c "from src.domains.ai_integration.providers.openai_provider import OpenAIProvider"

# Configuration wizard validation (catches workflow breaks)  
python -c "from src.interfaces.human.configuration_wizard import ExpertConfigurationWizard"

# Security validation (catches API key storage issues)
python tests/smoke/test_critical_user_workflows.py -v
```

*This checklist embeds lessons from linting cleanup, test infrastructure work, and the critical AI provider import regression that broke user configuration*