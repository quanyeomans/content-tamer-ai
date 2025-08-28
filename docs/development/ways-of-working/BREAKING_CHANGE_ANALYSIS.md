# Breaking Change Analysis & Test Coverage Strategy
*Systematic approach to identifying and mitigating integration failures*

## 🎯 Purpose

When refactoring causes test failures, this methodology ensures we:
1. **Identify root cause** using git diff analysis
2. **Create targeted test coverage** for changed interfaces
3. **Prevent similar failures** through proactive test design

## 🔍 Git Diff Analysis for Test Impact

### Step 1: Identify Changed Components
```bash
# Show files changed in recent commits
git show --name-status HEAD
git diff HEAD~1 HEAD --name-only

# Focus on core modules that tests depend on
git diff HEAD~1 HEAD -- src/core/ src/utils/
```

### Step 2: Analyze Function Signature Changes
```bash
# Look for function signature changes
git diff HEAD~1 HEAD | grep -E "^[+-].*def "

# Check for import changes that affect test mocks
git diff HEAD~1 HEAD | grep -E "^[+-].*import|from.*import"

# Find parameter changes in function calls
git diff HEAD~1 HEAD | grep -E "^[+-].*\("
```

### Step 3: Map Breaking Changes to Test Impact

| Change Type | Git Diff Pattern | Test Impact | Mitigation |
|-------------|------------------|-------------|------------|
| **Function signature** | `def function_name(old_params)` → `def function_name(new_params)` | Mock call patterns break | Update mock calls with new signatures |
| **Function rename** | `def old_name()` → `def new_name()` | Import and call failures | Update imports and references in tests |
| **Return type change** | Different return statements | Assertion failures | Update test expectations |
| **Module restructure** | Import path changes | Import errors | Update sys.path and import statements |
| **Parameter consolidation** | Multiple params → single object | Mock setup breaks | Restructure mock objects |

## 📊 Real Example: File Processor Breaking Change

**Git diff showed:**
```python
# Before (2-parameter version)
def _extract_file_content(input_path: str, ocr_lang: str) -> tuple:

# After (3-parameter version) 
def _extract_file_content(input_path: str, ocr_lang: str, display_context) -> tuple:
```

**Test Impact:**
- Existing mocks expected 2-parameter calls
- Function calls in production code used 3 parameters
- TypeError: `_extract_file_content() missing 1 required positional argument`

**Fix Required:**
```python
# Update test mocks to match new signature
mock_extract.return_value = ("text", None)
# Ensure mock is called with correct number of parameters
```

## 🧪 Targeted Test Coverage Strategy

### High-Risk Change Detection

**Always create specific tests for these change patterns:**

1. **Function signature changes**
   ```python
   def test_function_signature_compatibility(self):
       """Ensure new signature works with existing callers."""
       # Test both old-style and new-style calls if backward compatibility needed
   ```

2. **Import restructuring**
   ```python
   def test_module_imports(self):
       """Verify all expected functions can be imported."""
       from core.file_processor import process_file_enhanced
       self.assertTrue(callable(process_file_enhanced))
   ```

3. **Return type changes** 
   ```python
   def test_return_type_consistency(self):
       """Verify return values match expected types."""
       result = process_file(test_input)
       self.assertIsInstance(result, tuple)
       self.assertEqual(len(result), 2)  # Ensure tuple structure
   ```

### Test Update Automation

**Use git hooks to automatically identify needed test updates:**

```bash
#!/bin/bash
# pre-commit hook to detect breaking changes
changed_functions=$(git diff --staged | grep -E "^[+-].*def " | wc -l)
if [ $changed_functions -gt 0 ]; then
    echo "⚠️  Function signatures changed. Review test mocks:"
    git diff --staged | grep -E "^[+-].*def "
    echo "Run: grep -r 'mock.*function_name' tests/"
fi
```

## 🎯 Interface Stability Testing

### Create Integration Smoke Tests

**For each major module interface:**

```python
class TestCoreInterfaceStability(unittest.TestCase):
    """Ensure core module interfaces remain stable."""
    
    def test_file_processor_public_api(self):
        """Test that public API functions exist and are callable."""
        from core.file_processor import process_file, pdfs_to_text_string
        
        # Verify function exists
        self.assertTrue(callable(process_file))
        self.assertTrue(callable(pdfs_to_text_string))
        
        # Test signature compatibility with None inputs
        # This catches signature changes without full integration test
        try:
            # Should fail gracefully, not with signature error
            result = process_file(None, None, None)
        except TypeError as e:
            if "positional argument" in str(e):
                self.fail(f"Function signature changed: {e}")
        except Exception:
            pass  # Other exceptions are fine - we're testing signature only
```

### Mock Validation Tests

```python
class TestMockAccuracy(unittest.TestCase):
    """Ensure test mocks match actual function signatures."""
    
    def test_mock_matches_real_signature(self):
        """Verify that test mocks use correct signatures."""
        import inspect
        from core.file_processor import process_file_enhanced
        
        # Get real signature
        real_sig = inspect.signature(process_file_enhanced)
        
        # In actual test, verify mock is called with parameters matching real signature
        with patch('core.file_processor.process_file_enhanced') as mock_func:
            # Call should match real signature
            organize_content(test_input, test_output, test_unprocessed, "openai", "gpt-4")
            
            # Verify mock was called with correct parameter count
            call_args = mock_func.call_args
            if call_args:
                actual_param_count = len(call_args[0]) + len(call_args[1])
                expected_param_count = len(real_sig.parameters)
                self.assertEqual(actual_param_count, expected_param_count, 
                               f"Mock called with {actual_param_count} params, expected {expected_param_count}")
```

## 🚨 Breaking Change Prevention

### Pre-Commit Validation

**Before any refactoring commit:**

```bash
# 1. Run targeted test suite for changed modules
pytest tests/test_integration.py -v

# 2. Verify function signatures haven't changed unexpectedly  
pyright src/ | grep -E "(redeclaration|obscured)"

# 3. Check for import changes that might affect tests
git diff --staged | grep -E "^[+-].*import" 

# 4. Run smoke tests for major interfaces
pytest tests/test_smoke.py -v
```

### Refactoring Discipline

**When changing function signatures:**

1. **Feature flags first**: Keep old signature working
   ```python
   def process_file(input_path, output_path, unprocessed_path, provider, model, display_context=None):
       if display_context is None:
           # Backward compatibility path
           display_context = create_default_display_context()
       return process_file_enhanced(input_path, output_path, unprocessed_path, provider, model, display_context)
   ```

2. **Update tests with signature**: Same commit that changes function updates its tests
3. **Integration test verification**: Ensure end-to-end scenarios still work
4. **Rollback plan**: Tag working commit before major refactoring

## 📋 Breaking Change Checklist

**Before merging refactoring changes:**

- [ ] **Git diff reviewed**: All function signature changes identified
- [ ] **Test impact assessed**: Each breaking change mapped to affected tests  
- [ ] **Mocks updated**: Test doubles match new function signatures
- [ ] **Integration tests pass**: End-to-end workflows still functional
- [ ] **Pyright clean**: No redeclaration or type errors
- [ ] **Smoke tests added**: Interface stability tests for changed modules
- [ ] **Documentation updated**: API changes reflected in docs

**Post-merge validation:**

- [ ] **CI/CD pipeline passes**: All automated tests successful
- [ ] **Manual smoke test**: Core user workflows verified
- [ ] **Rollback tested**: Can revert cleanly if issues arise
- [ ] **Team notification**: Breaking changes communicated to other developers

## 🎯 Success Metrics

A successful refactoring achieves:
- **Zero test regressions**: All existing tests pass or are appropriately updated
- **Interface stability**: Public APIs remain backward-compatible where possible
- **Clear change documentation**: Breaking changes are explicitly documented
- **Targeted test coverage**: New tests specifically cover changed interfaces
- **Fast failure detection**: Issues caught in development, not production

*This methodology ensures that refactoring improves code quality without introducing integration failures or breaking existing functionality.*