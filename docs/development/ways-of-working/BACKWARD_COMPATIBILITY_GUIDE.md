# Backward Compatibility Guide
*When to preserve vs when to break existing behavior*

## Default Approach: Preserve Compatibility

**Rule**: Always preserve existing user workflows unless there's a compelling reason to break them.

### Always Preserve
- [ ] **Command line arguments**: Existing CLI flags and options continue to work
- [ ] **File formats**: Existing input file types and structures still supported
- [ ] **Directory structures**: Existing folder layouts continue to work
- [ ] **Environment variables**: Existing env var names and formats still work
- [ ] **Configuration files**: Existing config formats still parsed correctly

### Usually Preserve
- [ ] **API responses**: Function return values and error codes stay consistent
- [ ] **File output locations**: Generated files still go to expected locations  
- [ ] **Progress display**: Existing progress indicators continue to work
- [ ] **Error message formats**: Scripts parsing error messages still work
- [ ] **Exit codes**: Applications checking exit status continue to work

## When Breaking Changes Are Justified

### Security Requirements
**Break compatibility for security improvements**
- Insecure defaults → secure defaults
- Weak validation → stronger validation  
- Vulnerable patterns → secure patterns

*Example: If we discover API keys being logged, we break that behavior immediately*

### Critical Bug Fixes
**Break compatibility to fix data corruption or loss**
- Incorrect file processing → correct processing
- Data loss scenarios → data preservation
- Silent failures → proper error reporting

*Example: Files showing as "failed" when actually successful*

### Major Architecture Changes
**Break compatibility for significant improvements**
- Performance bottlenecks → efficient implementations
- Maintenance burdens → simpler, more reliable code
- User experience problems → better UX

*Only with clear user benefit and migration path*

## Compatibility Implementation Strategies

### Strategy 1: Deprecation Path (Preferred)
```python
# Support old and new, warn about old
def process_files(input_dir=None, input_folder=None):
    if input_folder is not None:
        warnings.warn("input_folder is deprecated, use input_dir", 
                     DeprecationWarning, stacklevel=2)
        input_dir = input_folder
    
    # Use input_dir for actual processing
```

### Strategy 2: Configuration Flag
```python
# Allow users to opt into new behavior
if config.get('use_new_behavior', False):
    return new_implementation()
else:
    return legacy_implementation()
```

### Strategy 3: Auto-Detection
```python
# Detect old vs new format and handle appropriately
if is_legacy_format(input_data):
    return process_legacy(input_data)
else:
    return process_new(input_data)
```

### Strategy 4: Version-Based Behavior
```python
# Different behavior based on config version
if config_version >= 2.0:
    return new_behavior()
else:
    return legacy_behavior()
```

## Breaking Change Checklist

### Before Breaking Compatibility
- [ ] **User impact assessed**: How many users/workflows will this affect?
- [ ] **Migration path defined**: How can users adapt to the change?
- [ ] **Benefits outweigh costs**: Is the improvement worth the disruption?
- [ ] **Alternatives explored**: Can we achieve the goal without breaking changes?

### Documentation Requirements
- [ ] **Change clearly documented**: What's changing and why
- [ ] **Migration guide provided**: Step-by-step instructions for users
- [ ] **Timeline specified**: When will old behavior stop working
- [ ] **Examples provided**: Before/after code examples

### Implementation Requirements
- [ ] **Graceful error messages**: If old usage detected, helpful error message
- [ ] **Version detection**: Code can detect and handle different versions appropriately
- [ ] **Testing coverage**: Both old and new behavior tested during transition
- [ ] **Rollback plan**: Can revert if breaking change causes problems

## Communication Strategy

### For Minor Breaking Changes
```
⚠️  BREAKING CHANGE in v2.1.0
The --output flag is now --output-dir for consistency.

Migration: Change --output path to --output-dir path
Old behavior supported until v3.0.0
```

### For Major Breaking Changes
```
🚨 MAJOR BREAKING CHANGE in v3.0.0
Configuration format changed for improved security.

Migration guide: docs/migration/v2-to-v3.md
Migration tool: python scripts/migrate_config.py
Support timeline: v2.x supported until Dec 2024
```

## Examples from Our Codebase

### ✅ Good Compatibility Preservation
```python
# Support both old and new API key env var names
api_key = (os.environ.get('OPENAI_API_KEY') or 
          os.environ.get('OPENAI_KEY'))  # Legacy support
```

### ❌ Avoid: Breaking Without Warning
```python
# BAD: Silently changes behavior
def process_files(input_dir):
    # Changed from relative to absolute paths without warning
    return os.path.abspath(input_dir)
```

### ✅ Good: Breaking with Migration Path
```python
def process_files(input_dir):
    if not os.path.isabs(input_dir):
        warnings.warn(
            "Relative paths deprecated. Use absolute paths. "
            "Auto-converting for now but this will be removed in v3.0",
            DeprecationWarning
        )
        input_dir = os.path.abspath(input_dir)
    
    return process_absolute_path(input_dir)
```

## Decision Framework

### Questions to Ask:
1. **Who will this affect?** (Users, scripts, integrations)
2. **What's the user benefit?** (Security, performance, reliability, UX)
3. **Can we provide a migration path?** (Gradual transition vs immediate break)
4. **How can we minimize disruption?** (Auto-detection, warnings, tooling)
5. **What's our support timeline?** (How long to maintain old behavior)

### Decision Matrix:
| Change Type | User Impact | Security Risk | Migration Path | Decision |
|-------------|-------------|---------------|----------------|-----------|
| Bug fix | Low | None | None needed | ✅ Break |
| Security fix | High | High | Documentation | ✅ Break |
| UX improvement | Medium | None | Deprecation path | ⚠️ Preserve with migration |
| Performance | Low | None | Configuration flag | ❌ Don't break |

*When in doubt, preserve compatibility and find another way to achieve the goal*