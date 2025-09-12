# Repository Maintenance Guide
*Guidelines for maintaining clean architecture and code quality*

## Repository Structure (Final State)

### **Clean Architecture Achieved**
```
content-tamer-ai/
├─ src/
│  ├─ main.py                    # Entry point with persona routing
│  ├─ __init__.py                # Package exports (main, domain services, API)
│  ├─ interfaces/                # Persona-driven interface layer
│  │  ├─ human/                  # Rich interactive interfaces
│  │  ├─ programmatic/           # API and library interfaces  
│  │  └─ protocols/              # MCP server and protocol extensions
│  ├─ orchestration/             # Application coordination
│  │  ├─ application_kernel.py   # Main workflow orchestration
│  │  └─ main_workflow.py        # Legacy workflow support
│  ├─ domains/                   # Business logic domains
│  │  ├─ content/                # Document processing
│  │  ├─ ai_integration/         # Provider management
│  │  └─ organization/           # Document organization + content_analysis
│  ├─ shared/                    # Cross-cutting utilities
│  │  ├─ file_operations/        # Unified file management
│  │  ├─ display/                # Rich UI components and console management
│  │  └─ infrastructure/         # Configuration, dependencies, utilities
│  ├─ core/                      # True application core
│  │  └─ application_container.py # Dependency injection container
│  └─ tools/                     # Development and analysis tools
├─ tests/                        # Test structure mirroring src/
│  ├─ unit/                      # Domain-aligned unit tests
│  ├─ integration/               # Cross-domain contract tests
│  └─ e2e/                       # User persona journey tests
├─ docs/                         # Documentation and ADRs
└─ [project files]
```

## Maintenance Standards

### **Code Quality Gates (MANDATORY)**
```bash
# PHASE 1: Code Formatting (Run first)
black src/ tests/ --line-length=100      # Consistent formatting
isort src/ tests/ --line-length=100      # Import ordering

# PHASE 2: Comprehensive Analysis
pylint src/ --fail-under=9.5             # Code quality ≥9.5/10 (Enhanced standard)
pyright src/                             # Type checking (0 errors required)
flake8 src/ --max-line-length=100        # Style compliance
bandit -r src/ --severity-level high     # Security scan (0 high/medium issues)
safety check                             # Dependency vulnerabilities
pytest tests/ -x --tb=short              # Test suite passing

# PHASE 3: Systematic Cleanup Validation
pylint src/ --disable=all --enable=W0611,W0612,W0613  # Must be 10.00/10 (unused warnings)
pylint src/ --disable=all --enable=W1203              # Must be 10.00/10 (logging format)
pylint src/ --disable=all --enable=E0401,E0611        # Must be 10.00/10 (import errors)
```

### **🧹 Systematic Linting Workflow**
```bash
# Use parallel agent approach for large-scale cleanup:

# 1. Deploy Import Resolution Agent
# Task: Fix all E0401, E0611 errors across provider files
# Focus: shared.infrastructure.filename_config imports, provider signatures

# 2. Deploy Type Safety Agent  
# Task: Fix orchestration layer pyright errors
# Focus: return types, function signatures, missing imports

# 3. Deploy Code Quality Agent
# Task: Fix W1203 logging, R1705 structure issues
# Focus: f-string logging → lazy %, unnecessary else after return

# 4. Deploy Cleanup Agent
# Task: Eliminate W0611, W0612, W0613 warnings
# Focus: unused imports/variables, proper _ prefixing

# Final validation must achieve:
# - Pylint: ≥9.5/10 overall
# - Pyright: 0 errors (warnings acceptable)  
# - Unused warnings: 10.00/10 perfect score
```

### **🧪 Test Infrastructure Architecture Patterns (Proven)**

#### **Test Execution Isolation (Critical for Integration Tests)**
```bash
# LESSON: Tests that pass individually but fail in suite = state contamination

# Solution 1: Process-Level Isolation (100% reliable)
python tools/testing/isolated_test_runner.py --integration
# Result: 41/41 integration tests pass (100% vs 63% in suite)

# Solution 2: Enhanced State Cleanup (conftest.py)
def pytest_runtest_teardown(item, nextitem):
    gc.collect()  # Clear ML models
    spacy.info._CACHE.clear()  # Clear spaCy state
    sys.path cleanup  # Reset import paths

# Solution 3: Segmented Execution by Performance
fast_tests: <2s (infrastructure) → immediate feedback
slow_tests: >10s (ML-heavy) → separate execution with timeouts
```

#### **Pattern Consistency During Refactoring**
```python
# ✅ CORRECT: Consistent unittest patterns
class TestService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def test_method(self):  # No pytest fixture parameters
        # Use self.temp_dir

# ❌ WRONG: Mixed unittest + pytest patterns  
class TestService(unittest.TestCase):
    def test_method(self, tmp_path):  # Causes TypeError
        # unittest.TestCase doesn't support pytest fixtures
```

#### **ML Model Testing Optimization**
```python
# Session-scoped fixtures reduce 55s → 5s (90% improvement)
@pytest.fixture(scope="session")
def spacy_model():
    return spacy.load("en_core_web_sm")

# State cleanup prevents cross-test contamination
def pytest_runtest_teardown(item, nextitem):
    gc.collect()  # Critical for ML model tests
```

### **Architecture Compliance Checks**
```bash
# Domain boundary validation
grep -r "from core\." src/domains/        # Must be empty (no core imports in domains)
grep -r "from utils\." src/domains/       # Must be empty (utils migrated to shared)

# Import structure validation  
python -c "from domains.content import ContentService"           # Must work
python -c "from domains.ai_integration import AIIntegrationService" # Must work
python -c "from shared.infrastructure.security import ContentValidator" # Must work
```

### **Repository Hygiene**
```bash
# Clean repository maintenance
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null  # Remove Python cache
find . -name "*.pyc" -delete                             # Remove compiled files
find . -name "temp_*" -delete                           # Remove temporary files
find . -name "validate_*" -delete                       # Remove validation scripts
```

## Development Guidelines

### **Adding New Features**

#### **Domain Service Features**
```python
# Add to appropriate domain only
# Content Domain: New file types
src/domains/content/extraction_service.py  # Add new processor

# AI Integration: New providers  
src/domains/ai_integration/providers/new_provider.py  # Add new provider

# Organization: New clustering methods
src/domains/organization/clustering_service.py  # Add new method
```

#### **Interface Features**
```python
# Add to appropriate persona interface
# Human Interface: New UI components
src/interfaces/human/rich_console_manager.py  # Add new UI patterns

# Programmatic: New API methods
src/interfaces/programmatic/library_interface.py  # Add new API functions

# Protocol: New integrations
src/interfaces/protocols/new_protocol_server.py  # Add new protocol
```

### **Testing Standards**

#### **Test Structure Requirements**
- **Tests must mirror src/ structure exactly**
- **Unit tests**: `tests/unit/domains/content/` ↔ `src/domains/content/`
- **Integration tests**: Cross-domain contracts in `tests/integration/`
- **E2E tests**: User persona workflows in `tests/e2e/`

#### **Test Quality Standards**
```python
# Use proper Rich test framework
class TestDomainService(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)  # Proper console isolation
        # Test domain service directly, not legacy implementations
```

### **Import Standards**

#### **Correct Import Patterns**
```python
# Domain services import from shared only
from shared.infrastructure.security import ContentValidator
from shared.file_operations.safe_file_manager import SafeFileManager
from shared.display.unified_display_manager import UnifiedDisplayManager

# Interfaces can import from domains (for orchestration)
from domains.content import ContentService
from orchestration.application_kernel import ApplicationKernel

# Never import (violations of architecture)
from utils.something import Something        # ❌ utils removed
from core.something import Something        # ❌ core only for application_container
from ai_providers import Something          # ❌ legacy modules removed
```

#### **Rich Console Standards**
```python
# Always use smart emoji pattern
if hasattr(console, 'options') and console.options.encoding == 'utf-8':
    console.print("🎯 [blue]With emojis[/blue]")
else:
    console.print(">> [blue]Without emojis[/blue] <<")

# Never use direct print() for user-facing output
# Always route through RichConsoleManager or UnifiedDisplayManager
```

## Quality Assurance

### **Architecture Validation Commands**
```bash
# Repository structure check
python -c "
import os
structure = {
    'src/domains': 3,     # content, ai_integration, organization
    'src/shared': 3,      # file_operations, display, infrastructure  
    'src/interfaces': 3,  # human, programmatic, protocols
}
for path, expected in structure.items():
    actual = len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
    print(f'{path}: {actual}/{expected} (\{\"PASS\" if actual == expected else \"FAIL\"})')
"

# Import health check
python -c "
from core.application_container import ApplicationContainer
from orchestration.application_kernel import ApplicationKernel
container = ApplicationContainer()
kernel = container.create_application_kernel()
health = kernel.health_check()
print(f'System health: {health[\"healthy\"]}')
"
```

### **Commit Quality Gates**
Before any commit:
1. ✅ **All tests passing**: `pytest tests/`
2. ✅ **Code quality**: PyLint ≥8.5, Flake8 clean
3. ✅ **Security clean**: Bandit scan, Safety check
4. ✅ **Import architecture**: No cross-layer violations
5. ✅ **Documentation updated**: Changes reflected in docs

## Emergency Recovery

### **If Architecture Gets Compromised**
1. **Identify violations**: Use validation commands above
2. **Revert to clean state**: Git reset to last known good commit
3. **Apply changes incrementally**: Small commits with validation
4. **Use domain isolation**: Fix one domain at a time

### **Common Issues and Fixes**
```bash
# Import errors after changes
grep -r "from utils\." src/ | head -5     # Find old utils imports
# Fix: Update to use shared.infrastructure or shared.display

# Test failures after refactoring  
pytest tests/unit/domains/content/ -v    # Test specific domain
# Fix: Update tests to use domain services, not legacy implementations

# Rich console issues
grep -r "print(" src/ | head -5           # Find direct print statements  
# Fix: Use RichConsoleManager or UnifiedDisplayManager
```

This guide ensures the **clean architecture is maintained** and **quality standards preserved** throughout future development.