# Development Tools

This directory contains development utilities and tools for maintaining code quality and testing infrastructure.

## Directory Structure

```
tools/
├── testing/                    # Test execution and management tools
│   ├── isolated_test_runner.py    # Isolated test execution with state cleanup
│   ├── segmented_test_runner.py   # Performance-optimized segmented execution
│   └── pytest_segments.ini        # Test segmentation configuration
├── linting/                    # Code quality and linting tools
│   └── systematic_linting.py      # 4-phase systematic code quality improvement
└── README.md                   # This file
```

## Testing Tools

### **isolated_test_runner.py**
Implements process-level isolation for integration tests, achieving 100% test reliability.

```bash
# Run integration tests with proven isolation patterns
python tools/testing/isolated_test_runner.py --integration

# Result: 41/41 integration tests pass (vs 63% in standard execution)
```

**Use When:** Integration tests pass individually but fail in suite execution due to state contamination.

### **segmented_test_runner.py**  
Performance-optimized test execution based on code change analysis and execution time profiling.

```bash
# Run tests based on changed files
python tools/testing/segmented_test_runner.py --changed-files="src/domains/organization/clustering_service.py"

# Run specific performance segment
python tools/testing/segmented_test_runner.py --segment=fast  # <2s tests
python tools/testing/segmented_test_runner.py --segment=slow  # ML-heavy tests
```

**Use When:** Need fast feedback loops or want to avoid expensive ML model loading for infrastructure changes.

### **pytest_segments.ini**
Configuration mapping code areas to relevant test segments for targeted execution.

**Use When:** Customizing test execution patterns or adding new test categories.

## Linting Tools

### **systematic_linting.py**
4-phase systematic code quality improvement following research-based patterns.

```bash
# Run complete systematic linting analysis
python tools/linting/systematic_linting.py

# Phases: Formatting → Analysis → Issue Resolution → Validation
```

**Use When:** Performing comprehensive code quality improvements or preparing for release.

## Application Tools (src/tools/)

The main application also includes tools in `src/tools/`:
- **console_analysis.py**: Rich console capability analysis
- **sanitize_logs.py**: Log sanitization for security (removes API keys)
- **token_analysis.py**: Token usage analysis for AI providers

```bash
# Security log sanitization
python -m src.tools.sanitize_logs

# Console capability analysis  
python -m src.tools.console_analysis
```

## Usage Guidelines

### **Directory Organization**
- **scripts/**: Application installation and setup (install.py, install.sh, install.bat)
- **tools/**: Development utilities and code quality tools (testing, linting)
- **src/tools/**: Application runtime tools (analysis, security, utilities)

### **Integration with CI/CD**
```bash
# Fast feedback for development
python tools/testing/segmented_test_runner.py --segment=fast

# Comprehensive quality check before merge
python tools/linting/systematic_linting.py
python tools/testing/isolated_test_runner.py --integration
```

### **Development Workflow Integration**
- **Pre-commit**: Fast segmented tests for immediate feedback
- **Pre-merge**: Isolated integration tests for reliability verification  
- **Release prep**: Systematic linting for code quality compliance

All tools follow established Rich console patterns and maintain architectural consistency with the main application.