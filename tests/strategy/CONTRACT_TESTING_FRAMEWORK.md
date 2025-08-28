# Contract Testing Framework: Implementation Guide
## Practical Framework for Preventing Integration Regressions

> **Purpose**: Provide immediate, actionable patterns for implementing contract tests that prevent component interface regressions.

## Quick Start: 5-Minute Contract Test Setup

### Step 1: Add Contract Markers to pytest.ini
```ini
# pytest.ini - ADD THESE MARKERS
markers =
    contract: Component interface agreement tests - MUST PASS
    interface: Interface stability contracts  
    dataflow: Data flow between components contracts
    state: State consistency contracts
```

### Step 2: Create Contract Test Template
```python
# tests/contracts/test_contract_template.py
"""
Contract Test Template - Copy this for new contracts
"""
import unittest

class TestComponentNameContract(unittest.TestCase):
    """
    CONTRACT AGREEMENTS TESTED:
    1. [Describe what interface agreement is being tested]
    2. [Describe what data format is expected]  
    3. [Describe what state consistency is required]
    """
    
    @pytest.mark.contract
    @pytest.mark.interface  
    def test_component_provides_required_interface(self):
        """CONTRACT: Component must provide expected interface."""
        component = create_real_component()  # No mocking
        
        # Interface existence
        assert hasattr(component, 'required_method'), "Component missing required method"
        assert callable(component.required_method), "Required method not callable"
        
        # Interface behavior
        result = component.required_method(valid_input)
        assert isinstance(result, ExpectedType), f"Expected {ExpectedType}, got {type(result)}"
        
    @pytest.mark.contract
    @pytest.mark.dataflow
    def test_component_accepts_expected_data_format(self):
        """CONTRACT: Component must accept data in expected format."""
        component = create_real_component()
        
        # Valid input format
        valid_data = {
            'required_field': 'value',
            'expected_type': 42
        }
        
        # Should not raise exception
        result = component.process(valid_data)
        
        # Should return expected format
        assert 'result_field' in result, "Missing required result field"
        assert isinstance(result['result_field'], str), "Result field wrong type"
```

### Step 3: Run Contract Tests
```bash
# Fast contract validation
pytest -m contract --maxfail=1 -v

# Contract tests must run in <30 seconds
timeout 30 pytest -m contract
```

## Contract Test Patterns Library

### Pattern 1: Display Manager Interface Contract
```python
class TestDisplayManagerInterfaceContract(unittest.TestCase):
    """Contracts for display manager that prevent UI regressions."""
    
    @pytest.mark.contract
    @pytest.mark.interface
    def test_show_completion_stats_interface_contract(self):
        """CONTRACT: show_completion_stats accepts application.py data format."""
        from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
        
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        # Must accept this exact format from application.py
        stats = {
            'total_files': 5,
            'successful': 3,
            'errors': 2, 
            'warnings': 1,
            'recoverable_errors': 0,
            'successful_retries': 1,
            'error_details': []
        }
        
        # Must not raise exception  
        try:
            manager.show_completion_stats(stats)
        except Exception as e:
            self.fail(f"show_completion_stats failed with valid application data: {e}")
            
    @pytest.mark.contract  
    @pytest.mark.dataflow
    def test_progress_stats_provides_required_attributes_contract(self):
        """CONTRACT: progress.stats must provide attributes that application expects."""
        from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
        
        manager = RichDisplayManager(RichDisplayOptions())
        
        # These attributes must always exist
        required_attributes = ['total', 'succeeded', 'failed', 'warnings', 'success_rate']
        
        for attr in required_attributes:
            assert hasattr(manager.progress.stats, attr), \
                f"progress.stats missing required attribute: {attr}"
            
            # Must be numeric types
            value = getattr(manager.progress.stats, attr)
            assert isinstance(value, (int, float)), \
                f"progress.stats.{attr} must be numeric, got {type(value)}"
```

### Pattern 2: Processing Context State Contract  
```python
class TestProcessingContextStateContract(unittest.TestCase):
    """Contracts for processing context state management."""
    
    @pytest.mark.contract
    @pytest.mark.state
    def test_complete_file_updates_progress_stats_contract(self):
        """CONTRACT: complete_file must increment succeeded count."""
        from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
        
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        
        with manager.processing_context(2, "Contract Test") as ctx:
            initial_succeeded = ctx.display.progress.stats.succeeded
            
            # Contract: This operation must increment succeeded
            ctx.complete_file("test.pdf", "result.pdf")
            
            final_succeeded = ctx.display.progress.stats.succeeded
            
            assert final_succeeded == initial_succeeded + 1, \
                f"complete_file must increment succeeded count: {initial_succeeded} -> {final_succeeded}"
                
    @pytest.mark.contract
    @pytest.mark.state  
    def test_processing_context_maintains_total_count_contract(self):
        """CONTRACT: processing context must maintain accurate total throughout lifecycle."""
        from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
        
        manager = RichDisplayManager(RichDisplayOptions(quiet=True))
        expected_total = 3
        
        with manager.processing_context(expected_total, "Contract Test") as ctx:
            # Total must be set correctly at start
            assert ctx.display.progress.stats.total == expected_total, \
                f"Expected total {expected_total}, got {ctx.display.progress.stats.total}"
            
            # Total must remain stable during operations
            ctx.start_file("file1.pdf")
            assert ctx.display.progress.stats.total == expected_total, \
                "Total changed during start_file operation"
                
            ctx.complete_file("file1.pdf", "result1.pdf")  
            assert ctx.display.progress.stats.total == expected_total, \
                "Total changed during complete_file operation"
```

### Pattern 3: No Duplicate Messages Contract
```python
class TestDisplayMessageConsistencyContract(unittest.TestCase):
    """Contracts preventing duplicate/conflicting display messages."""
    
    @pytest.mark.contract
    @pytest.mark.state
    def test_no_duplicate_completion_messages_contract(self):
        """CONTRACT: Only one completion message should appear in output."""
        from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
        from io import StringIO
        
        output = StringIO()
        manager = RichDisplayManager(RichDisplayOptions(no_color=True, file=output))
        
        # Simulate full processing workflow  
        with manager.processing_context(2, "Contract Test") as ctx:
            ctx.complete_file("file1.pdf", "result1.pdf")
            ctx.complete_file("file2.pdf", "result2.pdf")
            
        # Call completion stats (this was causing duplication)
        stats = {
            'total_files': 2,
            'successful': 2,
            'errors': 0,
            'warnings': 0
        }
        manager.show_completion_stats(stats)
        
        output_content = output.getvalue()
        
        # Contract: Must not have duplicate completion messages
        error_completions = output_content.count("[ERROR] Processing complete:")
        ok_completions = output_content.count("[OK] Processing complete:")
        
        assert error_completions == 0, \
            f"Found {error_completions} error completion messages, expected 0"
        assert ok_completions <= 1, \
            f"Found {ok_completions} OK completion messages, expected ≤1"
```

## Regression Prevention Contract Templates

### Template A: Interface Change Prevention
```python
def test_component_interface_remains_stable_contract(self):
    """CONTRACT: Component interface must remain backward compatible."""
    component = create_component()
    
    # Required methods must exist
    required_methods = ['method1', 'method2', 'method3']
    for method in required_methods:
        assert hasattr(component, method), f"Component missing required method: {method}"
        assert callable(getattr(component, method)), f"Method {method} not callable"
        
    # Method signatures must remain compatible
    result = component.method1(expected_args)
    assert result is not None, "Method must return a value"
```

### Template B: Data Format Compatibility  
```python
def test_data_format_remains_compatible_contract(self):
    """CONTRACT: Data format must remain compatible with dependent components."""
    component = create_component()
    
    # Input format compatibility
    legacy_format = create_legacy_format_data()
    new_format = create_new_format_data()
    
    # Must accept both formats  
    assert component.accepts_data(legacy_format), "Component must accept legacy data format"
    assert component.accepts_data(new_format), "Component must accept new data format"
    
    # Output format compatibility
    result = component.process_data(legacy_format)
    assert result.has_required_fields(), "Output missing required fields"
```

### Template C: State Synchronization
```python
def test_state_remains_synchronized_contract(self):
    """CONTRACT: Component state must stay synchronized with related components."""
    component_a, component_b = create_related_components()
    
    # Initial state sync
    assert component_a.get_state() == component_b.get_state(), "Initial state not synchronized"
    
    # State change sync
    component_a.update_state(change)
    assert component_a.get_state() == component_b.get_state(), "State not synchronized after update"
```

## Contract Test Implementation Guidelines

### DO: Contract Test Best Practices

#### ✅ Test Real Component Interfaces
```python
# GOOD: Test real component interface
def test_real_interface_contract(self):
    real_component = ActualComponent()  # No mocking
    result = real_component.actual_method(real_input)
    assert result.meets_contract_requirements()
```

#### ✅ Focus on Interface Agreements
```python
# GOOD: Test what components agree to provide/accept  
def test_interface_agreement_contract(self):
    # Component A promises to accept this format
    data = {'field': 'value'}
    component_a.process(data)  # Must not fail
    
    # Component A promises to return this format
    result = component_a.get_result()
    assert 'required_field' in result
```

#### ✅ Keep Contracts Simple and Fast
```python
# GOOD: Simple, focused contract test
def test_simple_contract(self):
    component = create_component()
    result = component.required_method()
    assert isinstance(result, ExpectedType)  # One clear assertion
```

### DON'T: Contract Test Anti-Patterns

#### ❌ Don't Test Implementation Details
```python
# BAD: Testing how something works internally  
def test_internal_implementation(self):
    component = create_component()
    component.internal_method()  # Don't test internal methods
    assert component.internal_state == expected  # Don't test internal state
```

#### ❌ Don't Mock in Contract Tests
```python
# BAD: Heavy mocking defeats the purpose
@patch('component.dependency')
def test_mocked_contract(self, mock_dep):
    mock_dep.return_value = "fake"
    # This doesn't test real component interactions!
```

#### ❌ Don't Make Contract Tests Complex
```python
# BAD: Complex setup defeats fast execution requirement
def test_complex_contract(self):
    # 50 lines of setup
    # Complex business logic
    # Multiple assertions
    # This should be an integration test, not a contract test
```

## Integration with Existing Workflow

### Pre-Commit Hook Setup
```bash
#!/bin/sh
# .pre-commit-hooks/contract-tests.sh

echo "Running contract tests..."
pytest -m contract --maxfail=1 -q

if [ $? -ne 0 ]; then
    echo "❌ Contract tests failed! Cannot commit interface-breaking changes."
    echo "Fix contract violations before committing."
    exit 1
fi

echo "✅ All contracts satisfied"
```

### CI/CD Pipeline Integration
```yaml
# .github/workflows/contracts.yml
name: Contract Validation

on: [push, pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run Contract Tests
      run: |
        pytest -m contract --maxfail=1 --tb=short
        if [ $? -ne 0 ]; then
          echo "Contract violations detected!"
          exit 1
        fi
```

### Development Workflow Integration

#### When Adding New Features
1. **Define contracts first**: What interface will this component provide?
2. **Write contract tests**: Verify the interface works as promised
3. **Implement feature**: Make the contract tests pass
4. **Verify integration**: Run all contract + integration tests

#### When Fixing Bugs  
1. **Identify missing contract**: What contract would have prevented this bug?
2. **Add regression prevention contract**: Write contract test that would catch this
3. **Fix the bug**: Make the contract test pass
4. **Verify no regressions**: Run full test suite

#### When Refactoring
1. **Run contract tests first**: Establish interface baseline
2. **Refactor implementation**: Keep contracts passing
3. **Verify contracts still pass**: Interface preserved
4. **Run integration tests**: Verify interactions still work

## Contract Test Maintenance

### Weekly Contract Review
- Review failed contract tests for false positives
- Update contracts when interfaces legitimately change
- Remove obsolete contracts for deprecated components
- Add contracts for new integration points

### Contract Performance Monitoring  
- Contract test suite must run in <30 seconds
- Individual contract tests must run in <1 second  
- Profile slow contract tests and optimize
- Remove redundant or overly complex contracts

### Contract Coverage Tracking
```python
# tools/contract_coverage.py
def calculate_contract_coverage():
    """Track which integration points have contract tests."""
    integration_points = find_all_integration_points()
    contract_tests = find_all_contract_tests()
    
    coverage = len(contract_tests) / len(integration_points) * 100
    print(f"Contract coverage: {coverage:.1f}%")
    
    missing_contracts = integration_points - contract_tests
    if missing_contracts:
        print("Missing contracts for:")
        for point in missing_contracts:
            print(f"  - {point}")
```

## Success Measurement

### Contract Test Success Metrics
- **Contract test failures**: Should be <1% false positive rate
- **Regression prevention**: Zero interface regressions after contract implementation  
- **Execution time**: Contract test suite <30 seconds
- **Coverage**: 100% of integration boundaries have contracts

### Team Adoption Metrics
- **Developer satisfaction**: Contract tests help rather than hinder development
- **Time to resolution**: Faster bug identification and resolution
- **Confidence**: Higher confidence in refactoring and changes

This framework provides the practical tools to immediately start preventing interface regressions while maintaining development velocity.