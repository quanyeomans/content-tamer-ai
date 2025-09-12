# Executable Workflows

## 🚀 FEATURE Workflow

### Step 1: Plan with TodoWrite
```python
# Break down the feature into tasks
TodoWrite([
    "Write failing test for feature",
    "Implement minimal solution", 
    "Add progress indicators",
    "Run compliance checks",
    "Update documentation"
])
```

### Step 2: Write Failing Test
```python
# Find appropriate test file or create new one
# tests/unit/domain/test_feature.py
def test_new_feature_behavior():
    """Test expected behavior of new feature."""
    service = TestApplicationContainer().create_service()
    result = service.new_feature(input_data)
    assert result.status == "success"  # Should FAIL initially
```

### Step 3: Implement Minimal Solution
```python
# src/domains/appropriate_domain/service.py
def new_feature(self, input_data: Dict) -> Result:
    """Implement just enough to pass the test."""
    # Add progress indicator
    progress_id = self.display_manager.start_progress("Processing feature")
    try:
        # Minimal implementation
        result = self._process(input_data)
        self.display_manager.update_progress(progress_id, 100, 100)
        return Result(status="success", data=result)
    except Exception as e:
        self.display_manager.error("Feature failed: %s", str(e))
        raise
    finally:
        self.display_manager.finish_progress(progress_id)
```

### Step 4: Run Compliance
```bash
cd src
black . --line-length=100
isort . --line-length=100  
python -m pylint . --fail-under=8.0
bandit -r . --severity-level medium
python -m pytest ../tests/unit/domain/test_feature.py -v
```

### Step 5: Update Documentation
- Update CLAUDE_CORE.md if architecture changed
- Add to "Current Issues" if known limitations

---

## 🐛 BUG Workflow

### Step 1: Create Reproduction Test
```python
# tests/regression/test_bug_xxx.py
def test_bug_reproduction():
    """Reproduce the reported bug."""
    # Set up exact conditions that cause the bug
    service = TestApplicationContainer().create_service()
    
    # This should demonstrate the bug
    with pytest.raises(ExpectedError):  # or assert wrong behavior
        service.buggy_operation(trigger_data)
```

### Step 2: Fix the Issue
```python
# Find the bug in src/
# Make minimal change to fix it
# Original (buggy):
if result_container["error"]:
    raise result_container["error"]  # Could be None!

# Fixed:
if result_container["error"]:
    error = result_container["error"]
    if isinstance(error, Exception):
        raise error
    else:
        raise RuntimeError(f"Request failed: {error}")
```

### Step 3: Verify All Tests Pass
```bash
cd src
python -m pytest ../tests/ -v --tb=short
# Ensure no regressions introduced
```

### Step 4: Add Permanent Regression Test
```python
def test_bug_xxx_regression():
    """Ensure bug XXX doesn't reoccur."""
    service = TestApplicationContainer().create_service()
    result = service.previously_buggy_operation(trigger_data)
    assert result.status == "success"  # Now works correctly
```

---

## 🔒 SECURITY Workflow

### Step 1: Security Scan
```bash
# Full security audit
bandit -r src/ -f txt > security_report.txt
safety check --json > dependencies_report.json

# Check for secrets in history
git log --oneline -20 | grep -i "api\|key\|secret" || echo "Clean"
```

### Step 2: Fix HIGH/MEDIUM Issues
```python
# Example: Fixing logging that could expose secrets
# BAD (could log API keys):
logger.error(f"API call failed: {exception}")

# GOOD (sanitized):
logger.error("API call failed: %s", sanitize_error(exception))

# Sanitization helper:
def sanitize_error(error: Exception) -> str:
    """Remove sensitive data from error messages."""
    msg = str(error)
    # Remove anything that looks like an API key
    msg = re.sub(r'(sk-[a-zA-Z0-9]{48})', '[API_KEY]', msg)
    msg = re.sub(r'(key["\']?\s*[:=]\s*["\'][^"\']+["\'])', '[REDACTED]', msg)
    return msg
```

### Step 3: Update Dependencies
```bash
# Check for vulnerable packages
safety check

# Update if needed
pip install --upgrade vulnerable-package

# Verify fix
safety check
```

### Step 4: Validate No Secrets
```python
# Add test to prevent future leaks
def test_no_api_keys_in_logs():
    """Ensure no API keys appear in logs."""
    with self.assertLogs(level='ERROR') as logs:
        service.process_with_api_key("sk-secret-key-12345")
    
    # Check no logs contain the actual key
    for log in logs.output:
        self.assertNotIn("sk-secret-key-12345", log)
        self.assertIn("[API_KEY]", log)  # Should be sanitized
```

---

## 📋 Common Patterns

### Using TestApplicationContainer
```python
class TestFeature(unittest.TestCase):
    def setUp(self):
        self.container = TestApplicationContainer()
        self.service = self.container.create_service()
```

### Using RichTestCase for UI
```python
class TestDisplay(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)
        self.display = self.test_container.create_display_manager()
```

### Progress Indicators
```python
progress_id = display_manager.start_progress("Operation")
try:
    for i, item in enumerate(items):
        display_manager.update_progress(progress_id, i, len(items))
        process(item)
finally:
    display_manager.finish_progress(progress_id)
```

### Lazy Logging Format
```python
# GOOD - Lazy formatting
logger.info("Processing %s documents", count)
logger.error("Failed to process %s: %s", filename, error)

# BAD - Don't use f-strings
logger.info(f"Processing {count} documents")  # W1203 warning
```