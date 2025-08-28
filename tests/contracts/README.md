# Contract Testing Implementation

This directory contains contract tests that prevent regressions at component integration boundaries.

## Overview

Contract tests verify that components maintain their interface agreements and prevent the most common source of regressions - changes to component interfaces that break dependent code.

## Contract Test Categories

### 1. Display Manager Interface Contracts (`test_display_manager_contracts.py`)
Tests that the display manager provides expected interfaces:
- `show_completion_stats` accepts application.py data format
- Progress stats provide consistent attributes expected by application layer
- No duplicate completion messages across display systems
- Success rate calculation accuracy

### 2. Processing Context State Contracts (`test_processing_context_contracts.py`) 
Tests that processing context maintains consistent state:
- `complete_file` increments succeeded count correctly
- Processing context maintains accurate total count throughout lifecycle
- `fail_file` increments failed count correctly
- Progress counters remain consistent (succeeded + failed ≤ total)
- Processing context exit preserves final statistics

### 3. Completion Message Consistency Contracts (`test_completion_consistency_contracts.py`)
Tests that completion messages are consistent:
- Single progress summary per processing session
- Success rate calculation accuracy
- Target filename tracking consistency
- No error completion messages for successful processing
- Completion messages contain accurate statistics

## Running Contract Tests

### Fast Contract Validation (Pre-commit)
```bash
pytest tests/contracts/ -m contract --maxfail=1 -x -q
```

### Detailed Contract Testing
```bash
pytest tests/contracts/ -m contract -v
```

### Contract Test Performance
- Target execution time: <30 seconds for full contract suite
- Individual contract tests: <1 second each
- Zero tolerance for contract test failures

## Contract Test Design Principles

### DO: Focus on Interface Agreements
```python
@pytest.mark.contract
@pytest.mark.critical
def test_component_interface_contract(self):
    """CONTRACT: Component must accept expected input format."""
    component = create_real_component()  # No mocking
    expected_input = create_valid_input()
    
    # Must not raise exception
    result = component.process(expected_input)
    # Must return expected format
    assert isinstance(result, ExpectedType)
```

### DON'T: Test Implementation Details
- Don't test internal methods or private state
- Don't use heavy mocking (defeats the purpose)
- Don't test complex business logic (that's for unit tests)

## Integration with Development Workflow

### Pre-commit Hook
The `.pre-commit-hooks/contract-tests.sh` script runs contract tests before commits and prevents interface-breaking changes from being committed.

### CI/CD Pipeline
Contract tests should be the first validation stage in CI/CD pipelines, providing fast feedback on interface stability.

## Contract Test Maintenance

### When to Add New Contract Tests
- When adding new component interfaces
- After fixing regressions (add prevention contract)
- When components start depending on new interface agreements

### When to Update Contract Tests
- When interfaces legitimately change (update contract first)
- When contract tests become flaky (fix or remove)
- When performance degrades (optimize or simplify)

## Known Issues

### Rich Display Testing Limitations
Some contract tests that directly instantiate Rich display components may encounter file I/O issues during test teardown. This is a known limitation of testing Rich components in pytest environments.

**Workaround**: Focus contract tests on interface agreements rather than visual output verification.

## Contract Test Success Metrics

- **Execution Time**: <30 seconds for full suite
- **Failure Rate**: <1% false positives
- **Coverage**: 100% of integration boundaries
- **Regression Prevention**: Zero interface regressions after implementation