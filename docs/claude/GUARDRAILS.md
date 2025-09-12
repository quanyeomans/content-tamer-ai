# Non-Negotiable Guardrails

## 🔒 Security Rules

### NEVER Log Secrets
```python
# FORBIDDEN - Will expose API keys
logger.info(f"Using API key: {api_key}")
logger.error(f"Request failed: {exception}")  # Exception may contain key

# REQUIRED - Sanitized logging
logger.info("Using API key: [REDACTED]")
logger.error("Request failed: %s", sanitize_error(exception))
```

### ALWAYS Validate Paths
```python
# REQUIRED - Prevent directory traversal
def validate_path(file_path: str, base_dir: str) -> bool:
    """Ensure path is within allowed directory."""
    real_path = os.path.realpath(file_path)
    real_base = os.path.realpath(base_dir)
    return real_path.startswith(real_base)

# Before ANY file operation:
if not validate_path(user_path, allowed_dir):
    raise ValueError("Invalid path")
```

### NO Sensitive Data in Errors
```python
# FORBIDDEN
raise ValueError(f"API call failed with key {api_key}")

# REQUIRED
raise ValueError("API authentication failed")
```

## ✅ Quality Gates

### Mandatory Before Merge
```bash
# ALL must pass - no exceptions
pylint src/ --fail-under=8.0     # Score ≥8.0/10
bandit -r src/ -ll                # 0 HIGH/MEDIUM issues
safety check                      # 0 vulnerabilities
python -m pytest tests/           # 100% pass
```

### Code Formatting (Auto-fix)
```bash
black src/ tests/ --line-length=100
isort src/ tests/ --line-length=100
```

## 🔄 Backward Compatibility

### Default: Preserve Everything
```python
# Adding new parameter? Make it optional
def process(file_path: str, new_option: bool = False):  # Good
def process(file_path: str, new_option: bool):          # Breaking!
```

### Deprecation Required
```python
# Mark old pattern as deprecated BEFORE removal
import warnings

def old_method(self):
    warnings.warn(
        "old_method is deprecated, use new_method instead",
        DeprecationWarning,
        stacklevel=2
    )
    return self.new_method()
```

### Migration Path Required
```markdown
# If breaking change is necessary:
1. Add deprecation warning in version X
2. Provide migration guide in CHANGELOG
3. Remove in version X+2 (minimum)
```

## 🧪 Testing Requirements

### Test BEFORE Implementation
```python
# This order is MANDATORY:
1. Write failing test
2. Run test - verify it fails
3. Write implementation
4. Run test - verify it passes
5. Run ALL tests - verify no regressions
```

### Test Coverage Rules
- New features: Must have unit tests
- Bug fixes: Must have regression test
- Security fixes: Must have security test
- Coverage: Cannot decrease

## 🎯 Definition of Done

### A task is NOT done until:
```markdown
✅ Tests written and passing
✅ Pylint score ≥8.0
✅ Security scan clean
✅ Documentation updated
✅ No console log pollution
✅ Progress indicators working
✅ Error messages user-friendly
```

## 🚫 Forbidden Patterns

### Direct Logging to Console
```python
# FORBIDDEN
print("Processing...")
sys.stdout.write("Done")

# REQUIRED - Use display manager
self.display.info("Processing...")
```

### Mocking Internal Components
```python
# FORBIDDEN
@patch('src.domains.content.service')

# ALLOWED - Only external services
@patch('openai.ChatCompletion.create')
```

### Cross-Domain Imports
```python
# FORBIDDEN
# In src/domains/content/
from domains.organization import SomeService

# REQUIRED - Use orchestration layer
# In src/orchestration/
from domains.content import ContentService
from domains.organization import OrgService
```

## 🛑 Stop and Ask

### STOP if you're about to:
- Skip writing tests "just this once"
- Disable a security check "temporarily"  
- Add a quick fix without understanding root cause
- Create a new pattern instead of using existing one
- Log anything that might be sensitive

## 📝 Compliance Declaration

### When claiming "done", confirm:
```markdown
✅ GUARDRAILS FOLLOWED
- Security: No secrets logged, paths validated
- Quality: Pylint ≥8.0, Bandit clean
- Testing: Test-first, coverage maintained
- Compatibility: No breaking changes
- UX: Progress shown, errors handled
```

## ⚡ Quick Reference

### One-Line Compliance Check
```bash
cd src && black . --check && pylint . --fail-under=8.0 && bandit -r . -ll && safety check && python -m pytest ../tests/ -q
```

### If This Fails, NOT Done
```bash
grep -r "f\".*{.*}\"" src/ --include="*.py" | grep logger  # Find f-string logging
git diff HEAD~1 | grep "^+" | grep -i "api_key\|secret"    # Check for secrets
```