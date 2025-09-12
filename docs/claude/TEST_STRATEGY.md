# Test Strategy

## Coverage Targets

### By Layer
```
Unit Tests        : 80% minimum (business logic)
Integration Tests : Critical paths only
E2E Tests        : User journeys only
Security Tests   : All security functions
```

### By Domain
```
domains/content/        : 85% (critical extraction logic)
domains/ai_integration/ : 75% (providers mocked)
domains/organization/   : 80% (clustering algorithms)
shared/                : 90% (utilities heavily used)
orchestration/         : 70% (mostly coordination)
```

## Test Selection Rules

### When to Write What Test

#### Feature Development
```python
# ALWAYS start with unit test
def test_new_feature():
    """Unit test for specific behavior."""
    assert feature.calculate(5) == 25

# Add integration if crosses boundary
def test_feature_integration():
    """Test interaction with other services."""
    content = content_service.extract()
    result = ai_service.process(content)
    assert result.status == "success"

# Add E2E only for critical user path
def test_user_journey():
    """Complete workflow from user perspective."""
    run_command(["python", "main.py", "--input", "test.pdf"])
```

#### Bug Fixes
```python
# FIRST: Reproduction test
def test_bug_reproduction():
    """Demonstrates the bug exists."""
    with pytest.raises(BuggyError):
        service.trigger_bug()

# SECOND: Fix verification
def test_bug_fixed():
    """Proves bug is fixed."""
    result = service.previously_buggy_operation()
    assert result == expected

# THIRD: Regression prevention
def test_bug_regression():
    """Ensures bug doesn't return."""
    # Test edge cases around the bug
```

#### Security Issues
```python
# Security-specific test required
def test_no_path_traversal():
    """Prevent directory traversal attacks."""
    malicious = "../../../etc/passwd"
    with pytest.raises(SecurityError):
        file_manager.validate_path(malicious)

def test_api_key_sanitization():
    """Ensure secrets never logged."""
    with self.assertLogs() as logs:
        service.process_with_key("sk-secret123")
    for message in logs.output:
        self.assertNotIn("sk-secret123", message)
```

## Test Organization

### Directory Structure
```
tests/
├── unit/                      # Fast, isolated tests
│   ├── domains/              
│   │   ├── content/          # Mirror src structure
│   │   ├── ai_integration/
│   │   └── organization/
│   └── shared/
├── integration/              # Component interaction
│   ├── cross_domain/        # Service coordination
│   └── external/            # API integration (mocked)
├── e2e/                     # Full workflows
│   └── workflows/
├── security/                # Security-specific
└── regression/              # Bug prevention
```

### Naming Conventions
```python
# Unit tests - test what it does
test_extracts_text_from_pdf()
test_calculates_token_count()
test_validates_api_key_format()

# Integration - test interaction
test_content_to_ai_pipeline()
test_ai_to_organization_flow()

# E2E - test user stories
test_user_processes_batch_of_pdfs()
test_user_organizes_with_ml_enhancement()

# Regression - reference bug/issue
test_regression_issue_423_path_traversal()
test_regression_pr_99_unicode_handling()
```

## Test Patterns

### TestApplicationContainer Pattern
```python
class TestService(unittest.TestCase):
    def setUp(self):
        # Use test container for DI
        self.container = TestApplicationContainer()
        self.service = self.container.create_service()
        # External APIs already mocked in test container
```

### RichTestCase Pattern
```python
class TestUIComponent(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)
        self.display = self.test_container.create_display_manager()
    
    def test_progress_display(self):
        self.display.show_progress("Test")
        output = self.get_console_output()
        self.assertIn("Test", output)
```

### Temp Directory Pattern
```python
def test_file_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Real file operations in isolated env
        test_file = Path(tmpdir) / "test.pdf"
        test_file.write_bytes(b"content")
        
        result = processor.process(str(test_file))
        assert result.output_path.exists()
```

## Test Execution

### Local Development
```bash
# Fast feedback - unit only
cd src && python -m pytest ../tests/unit -v

# Before commit - unit + integration  
cd src && python -m pytest ../tests/unit ../tests/integration -v

# Full validation - everything
cd src && python -m pytest ../tests/ -v --cov=src
```

### CI Pipeline
```yaml
test:
  stage: test
  script:
    # Parallel test execution
    - pytest tests/unit --junit-xml=unit.xml
    - pytest tests/integration --junit-xml=integration.xml
    - pytest tests/security --junit-xml=security.xml
    # Coverage report
    - pytest tests/ --cov=src --cov-report=xml
  parallel: 3
```

## Mocking Strategy

### Mock Only External Services
```python
# GOOD - Mock external APIs
@patch('openai.ChatCompletion.create')
@patch('requests.post')  # External HTTP

# BAD - Don't mock internal
@patch('src.domains.content.service')  # NO!
@patch('src.shared.file_manager')      # NO!
```

### Fixture Best Practices
```python
@pytest.fixture
def mock_ai_response():
    """Reusable AI response mock."""
    return {
        "choices": [{
            "message": {
                "content": "Mocked response"
            }
        }]
    }

@pytest.fixture
def test_documents(tmp_path):
    """Create test documents."""
    docs = []
    for i in range(3):
        doc = tmp_path / f"test_{i}.pdf"
        doc.write_bytes(b"test content")
        docs.append(str(doc))
    return docs
```

## Performance Benchmarks

### Test Speed Targets
```
Unit test suite     : <10 seconds
Integration suite   : <30 seconds
E2E suite          : <2 minutes
Full test suite    : <5 minutes
```

### Slow Test Optimization
```python
# Mark slow tests
@pytest.mark.slow
def test_large_batch_processing():
    """Process 1000 documents."""
    pass

# Skip in fast mode
pytest -m "not slow"  # Quick feedback
pytest              # Full suite
```

## Test Quality Metrics

### Monthly Review
- Test coverage: ___% (target: 80%)
- Test execution time: ___ seconds
- Flaky tests: ___ (target: 0)
- Tests added: ___
- Tests removed: ___

### Test Debt
```bash
# Find untested code
pytest --cov=src --cov-report=term-missing

# Find TODO tests
grep -r "TODO\|FIXME\|test_skip" tests/

# Find disabled tests  
grep -r "@skip\|@pytest.mark.skip" tests/
```