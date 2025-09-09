# Debug First Principles
*Evidence-based troubleshooting methodology for complex systems*

## 🎯 Core Philosophy

**"Debug with evidence, not assumptions"**

Debugging is investigative work that requires systematic methodology, not intuitive guessing. These principles ensure consistent, effective problem resolution while maintaining code quality and system stability.

## 🔬 The Five Debugging Principles

### 1. Evidence Over Assumptions
**"Never guess when you can verify"**

- **Collect facts first**: Gather logs, traces, error messages, and system state
- **Question everything**: Don't assume you know the cause without proof
- **Measure, don't estimate**: Use tools to verify performance, memory usage, etc.
- **Document findings**: Record what you observe, not what you think happened

```bash
# Good: Gather evidence
git log --oneline -10  # What changed recently?
pytest tests/ -v       # What tests are failing?
grep -r "error" logs/  # What errors are logged?

# Bad: Making assumptions
# "This must be a timeout issue because it's slow"
```

### 2. Root Cause Over Symptoms
**"Fix the underlying issue, not manifestations"**

- **Trace backwards**: Follow the error chain to its origin
- **Ask "why" five times**: Keep drilling down until you reach the fundamental cause
- **Fix once, solve completely**: Address the root so symptoms don't recur
- **Avoid band-aid solutions**: Quick fixes that mask problems create technical debt

```python
# Good: Fix root cause
def process_file(file_path):
    if not os.path.exists(file_path):  # Check precondition
        raise FileNotFoundError(f"File not found: {file_path}")
    # ... process file

# Bad: Treat symptoms
def process_file(file_path):
    try:
        # ... process file
    except Exception:
        pass  # Silent failure masks the real problem
```

### 3. One Change at a Time
**"Isolate variables to identify actual causes"**

- **Single variable testing**: Change one thing, test, observe result
- **Maintain control groups**: Keep working code paths intact
- **Binary search debugging**: Eliminate half the possibilities with each test
- **Rollback capability**: Always have a way to undo changes

```python
# Good: Feature flag approach
def enhanced_processing(file_path, use_new_algorithm=False):
    if use_new_algorithm:
        return new_algorithm(file_path)  # Test this path
    return original_algorithm(file_path)  # Keep this working

# Bad: Replace everything
def enhanced_processing(file_path):
    return completely_new_approach(file_path)  # No fallback
```

### 4. Preserve Working Code
**"Use feature flags rather than replacing working logic"**

- **Feature toggles**: Allow switching between old and new implementations
- **Graceful degradation**: New features should degrade to working baseline
- **Backwards compatibility**: Don't break existing functionality while fixing bugs
- **Safe deployment**: Ability to quickly revert if issues arise

### 5. Document the Journey
**"Record what was tried and why it failed/succeeded"**

- **Hypothesis tracking**: Document what you thought was wrong and why
- **Attempted solutions**: Record what fixes were tried and their results
- **Decision rationale**: Explain why you chose one approach over alternatives
- **Learning capture**: Document insights for future similar issues

## 🔍 Debugging Workflow

### Phase 1: Evidence Collection (30% of debug time)
1. **Reproduce the issue** in a controlled environment
2. **Gather comprehensive logs** with full stack traces
3. **Document the symptoms** vs expected behavior
4. **Check version control** for recent changes
5. **Verify environment** (dependencies, configuration, resources)

### Phase 2: Root Cause Analysis (50% of debug time)
1. **Form hypotheses** based on evidence (not intuition)
2. **Design tests** to validate/invalidate each hypothesis
3. **Trace code paths** through suspected areas
4. **Binary search** to isolate the problematic component
5. **Verify dependencies** and external integrations

### Phase 3: Fix Implementation (20% of debug time)
1. **Design minimal fix** that addresses root cause
2. **Implement with feature flag** to preserve working code
3. **Test fix in isolation** before full integration
4. **Verify no side effects** on other functionality
5. **Update tests** to prevent regression

## ⚠️ Common Anti-Patterns

### The Assumption Trap
```python
# DON'T: Assume based on similar issues
"This looks like a timeout issue from last month"

# DO: Gather evidence first  
logger.info(f"Request started at {start_time}")
logger.info(f"Timeout configured: {timeout_seconds}")
logger.info(f"Response received after {elapsed_time}s")
```

### The Shotgun Approach
```python
# DON'T: Change multiple things at once
def fix_processing():
    change_algorithm()      # Change 1
    update_config()        # Change 2  
    modify_dependencies()   # Change 3
    # Which one actually fixed it?

# DO: One change at a time with validation
def fix_processing():
    if USE_NEW_ALGORITHM:  # Test just this first
        return new_algorithm()
    return original_algorithm()
```

### The Quick Fix Trap
```python
# DON'T: Band-aid over symptoms
try:
    result = risky_operation()
except:
    return None  # Hide the problem

# DO: Address root cause
def safe_operation():
    if not preconditions_met():
        raise ValueError("Preconditions not met: ...")
    return risky_operation()
```

## 🎯 Success Metrics

A debugging session is successful when:
- **Issue is resolved** without creating new problems
- **Root cause is documented** and understood
- **Tests prevent regression** of the same issue
- **Knowledge is shared** with the team
- **Process improvements** are identified

## 🔧 Debugging Tools Checklist

- [ ] **Logging framework** with appropriate levels
- [ ] **Error tracking** with full stack traces  
- [ ] **Version control** for change tracking
- [ ] **Test harness** for reproduction
- [ ] **Profiling tools** for performance issues
- [ ] **Dependency checking** for environment issues
- [ ] **Feature flags** for safe deployment

## 🚨 When to Escalate

Escalate debugging when:
- Problem affects critical systems and expertise is needed
- Root cause spans multiple systems/teams
- Time investment exceeds business impact
- Security implications require specialized knowledge
- Solution requires architectural changes

*Remember: Effective debugging is a skill that improves with practice. The investment in systematic approaches pays dividends in reduced maintenance burden and increased system reliability.*