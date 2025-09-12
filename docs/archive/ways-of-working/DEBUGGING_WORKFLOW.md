# Debugging & Issue Resolution Workflow
*Streamlined process for fixing bugs vs developing new features*

## 🔧 **When to Use This Workflow**

**Use for:**
- Fixing existing bugs or issues
- Resolving test failures  
- Improving existing functionality
- Security vulnerability remediation
- Performance issues

**Don't use for:**
- New feature development (use IMPLEMENTATION_WORKFLOW.md)
- Major architecture changes
- Adding new components

## 🚀 **Rapid Issue Resolution Process**

### Step 1: Issue Analysis (5 minutes max)
```
✅ QUICK ANALYSIS CHECKLIST
- [ ] **Problem clearly defined**: Can I reproduce the issue?
- [ ] **Scope identified**: Single function, module, or system-wide?
- [ ] **Risk assessed**: Security, data loss, or functionality impact?
- [ ] **Existing tests**: Are there tests that should be passing but aren't?
```

### Step 2: Minimal Reproduction (TodoWrite optional)
```python
# Create minimal test case that demonstrates the issue
def test_reproduce_bug():
    """Minimal reproduction of the reported issue."""
    # Arrange - minimal setup to trigger issue
    # Act - perform the action that causes the bug
    # Assert - verify the bug occurs (test should fail initially)
    pass
```

### Step 3: Root Cause Identification
- **Read the error**: What's the actual error message?
- **Trace the path**: Follow the code execution path
- **Check assumptions**: Are my assumptions about the code correct?
- **Identify the cause**: What specific line/logic is causing the issue?

### Step 4: Minimal Fix Implementation
```python
def test_bug_is_fixed():
    """Test that verifies the bug is resolved."""
    # Arrange - same setup as reproduction test
    # Act - perform the action that previously failed  
    # Assert - verify the issue is now resolved
    pass

# Implement the minimal fix to make this test pass
```

### Step 5: Regression Prevention
- **Extend existing tests**: Add the new test to appropriate test file
- **Run full test suite**: Ensure no other functionality is broken
- **Update documentation**: If behavior changed, update docs

## ⚡ **Fast-Track Security Issues**

For security vulnerabilities, use this expedited process:

### Security Bug Fast-Track
1. **Immediate containment**: Comment out vulnerable code if possible
2. **Create failing security test**: Test that secret is being exposed
3. **Implement fix**: Apply minimal change to stop the exposure
4. **Verify fix**: Run security test to confirm issue resolved
5. **Full security audit**: Use SECURITY_AUDIT_METHODOLOGY.md

## 🎯 **Debug vs Develop Decision Matrix**

| Scenario | Use Debugging Workflow | Use Development Workflow |
|----------|----------------------|------------------------|
| Test is failing unexpectedly | ✅ Debug | ❌ |
| Function returns wrong value | ✅ Debug | ❌ |
| Security vulnerability found | ✅ Debug (Fast-track) | ❌ |
| Adding validation to existing function | ❌ | ✅ Develop |
| Creating new feature | ❌ | ✅ Develop |
| Refactoring architecture | ❌ | ✅ Develop |

## 🚨 **Debug Workflow Red Flags**

**STOP debugging and switch to development workflow if:**
- Solution requires >50 lines of new code
- Need to create new classes or modules
- Touching >3 files to implement fix
- Change affects public APIs or interfaces
- Fix requires new dependencies

## 📋 **Debug Completion Criteria**

✅ **Debug Complete When:**
- [ ] **Issue reproduction test** passes (verifies fix works)
- [ ] **All existing tests** still pass (no regressions)
- [ ] **Root cause documented** (comment or commit message)
- [ ] **Minimal change implemented** (smallest fix that works)

**No need for:**
- Extensive documentation updates
- New feature testing
- Architecture reviews  
- Complex test scenarios

*This workflow optimizes for speed and safety when fixing existing issues.*