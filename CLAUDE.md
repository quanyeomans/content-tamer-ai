# Claude Code Configuration
*Project-specific context and working patterns for content-tamer-ai*

## Project Overview

**Content Tamer AI** - Intelligent file processing and organization system
- Processes PDFs and documents using AI providers (OpenAI, Claude, Gemini, Local LLM)
- Generates intelligent filenames and organizes content
- Cross-platform Python application with rich CLI interface
- **NEW**: Complete offline processing with Local LLM support via Ollama

## Working Patterns

### **Architectural Patterns (New)**
#### **For Persona-Driven Development:**
1. **PERSONA_DRIVEN_INTERFACE_PATTERNS.md** - Separate interfaces by user type
2. **RICH_UI_DEVELOPMENT_PATTERNS.md** - Rich Console with smart emoji usage patterns
3. **RICH_CONSOLE_TESTING_GUIDE.md** - Proper Rich testing without over-mocking

#### **For Domain Service Development:**
1. **DOMAIN_SERVICE_EXTRACTION_PATTERNS.md** - Extract clean domain boundaries
2. **Shared service consolidation** - Unify cross-cutting utilities

#### **For Architectural Changes:**
1. **VALIDATION_DRIVEN_DEVELOPMENT.md** - Measurable criteria and validation checkpoints
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Document decisions with context and consequences

### **Choose Your Workflow**

#### **For New Features/Development:**
1. **PRE-CODE_CHECKLIST.md** - Complete all 4 mandatory gates
2. **IMPLEMENTATION_WORKFLOW.md** - Test-first development
3. **DOMAIN_SERVICE_EXTRACTION_PATTERNS.md** - When creating domain services
4. **PERSONA_DRIVEN_INTERFACE_PATTERNS.md** - When adding interface functionality

#### **For Bugs/Issues/Debugging:**
1. **DEBUGGING_WORKFLOW.md** - Streamlined issue resolution
2. **VALIDATION_DRIVEN_DEVELOPMENT.md** - When architectural changes needed

#### **For Security Issues:**
1. **SECURITY_AUDIT_METHODOLOGY.md** - Systematic vulnerability discovery
2. **DEBUGGING_WORKFLOW.md** (Fast-track) - Immediate containment and fix
3. **SECURITY_TESTING_STRATEGY.md** - Adversarial testing approach

#### **For Architectural Changes:**
1. **ARCHITECTURAL_DECISION_RECORDS.md** - Document decisions with context
2. **VALIDATION_DRIVEN_DEVELOPMENT.md** - Measurable criteria and validation
3. **Clean Cut Migration over Compatibility Layers** - Systematic approach

### **ALWAYS Use TodoWrite**
- **For complex work**: Break into trackable tasks
- **For debugging**: Optional but recommended for multi-step fixes
- **For security work**: Mandatory to ensure no steps are missed
- **For refactoring**: Mandatory to track security/quality improvements

### **📊 Code Quality Refactoring Workflow**

#### **Phase 1: Analysis & Discovery (HIGH PRIORITY)**
1. **Run SAST Analysis**: `bandit -r src/ -f json | jq '.results'`
2. **Dependency Audit**: `safety check --json`  
3. **Quality Analysis**: `pylint src/ --output-format=text`
4. **Complexity Analysis**: Identify functions with >12 cyclomatic complexity
5. **Duplicate Code Detection**: Look for repeated patterns across files

#### **Phase 2: Prioritized Execution**
1. **🚨 Security Issues**: Fix HIGH/MEDIUM Bandit findings immediately
2. **🔄 Duplicate Logic**: Extract repeated code into shared utilities
3. **🧹 Quality Issues**: Address Pylint/Flake8/MyPy violations
4. **⚠️ Complexity**: Break down functions >15 complexity score

#### **Phase 3: Validation**
1. **Security Regression Testing**: Re-run complete SAST suite
2. **Code Coverage Validation**: Ensure tests still pass and coverage maintained  
3. **Integration Testing**: Verify no breaking changes introduced

### **🧪 Unit Test Expansion Methodology (CURRENT FOCUS)**

#### **Module-by-Module Approach**
1. **Target Selection**: Choose modules with 0% test coverage first
2. **Comprehensive Coverage**: Write 15-25 tests per module covering all functions, edge cases
3. **Quality Gate**: Each module must achieve 9.0+ pylint score before completion
4. **Test Categories**: 
   - Default values and initialization
   - Custom configuration validation  
   - Error handling and edge cases
   - Integration with other components
   - Security and sanitization

#### **Test Implementation Pattern**
```python
# 1. Multiple test classes per module (by functional area)
class TestModuleDefaults(unittest.TestCase):
class TestModuleValidation(unittest.TestCase): 
class TestModuleEdgeCases(unittest.TestCase):

# 2. Comprehensive edge case coverage
- Empty inputs, None values, malformed data
- Boundary conditions (min/max lengths, limits)
- Security scenarios (injection attempts, forbidden patterns)
- File system edge cases (permissions, missing directories)

# 3. Proper mocking strategy
- Mock external dependencies and user input
- Use tempfile.TemporaryDirectory() for filesystem tests
- Preserve real logic validation without external side effects
```

#### **Success Metrics**
- **Coverage**: 0% → 100% per module
- **Test Count**: 15-25 comprehensive tests per module  
- **Quality**: 9.0+ pylint score maintained
- **Reliability**: All tests passing consistently
- **Documentation**: Self-documenting test names and docstrings

### Modern Test Strategy

#### Core Testing Principles
- **Test-first development**: Always write failing tests before implementation
- **ApplicationContainer Pattern**: Use TestApplicationContainer for proper dependency injection in tests
- **RichTestCase Pattern**: Inherit from RichTestCase for Rich UI component testing
- **Minimal mocking**: Only mock external AI APIs, keep file operations real with tempfile.TemporaryDirectory()
- **Console Isolation**: Use proper console management to prevent pytest I/O conflicts

#### Rich UI Testing Patterns
```python
class TestRichUIComponent(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)
        # Access self.test_container, self.display_manager, self.test_console
    
    def test_ui_behavior(self):
        display_manager = self.test_container.create_display_manager(options)
        # Test with proper console isolation
        output = self.get_console_output()
```

#### Test Infrastructure (Current)
- **536 total tests** (494 passing, 92.2% success rate)
- **Rich UI Testing**: Comprehensive coverage with RichTestCase framework
- **Contract Tests**: Behavioral validation across component boundaries  
- **Integration Tests**: Multi-component interaction patterns
- **Unit Tests**: Module-by-module coverage expansion (15-25 tests per module)

#### Key Test Categories
- `tests/test_display_manager.py` - Rich UI components and display orchestration
- `tests/test_rich_ui_regression.py` - Rich UI behavioral regression prevention
- `tests/test_integration.py` - API/validation and multi-component tests
- `tests/test_security.py` - Security validation and injection prevention
- `tests/contracts/` - Contract tests for component agreements
- `tests/utils/rich_test_utils.py` - Rich testing framework and utilities

#### Test Quality Standards
- **🔄 Refactoring Test Maintenance**: When refactoring code:
  1. Update all affected test mocks and patches to match new internal structure
  2. Maintain the same test assertions and coverage expectations  
  3. Use RichTestCase.setUp()/tearDown() for proper console lifecycle management
  4. Ensure tests validate behavioral contracts, not implementation details

### Security Requirements
- **Never log API keys**: Use environment variables only
- **Validate file paths**: Protect against directory traversal
- **Safe error messages**: No sensitive information disclosure
- **Input sanitization**: Validate all user inputs

### Code Quality & Security Commands
```bash
# MANDATORY: Run complete compliance check before completion
make compliance-check  # Or run manually:

# 1. Security Analysis (MANDATORY)
bandit -r src/ -f text                    # Security vulnerability scan
safety check                             # Dependency vulnerability check

# 2. Code Quality Analysis (MANDATORY) 
pylint src/ --fail-under=8.0             # Code quality (min 8.0/10) - uses .pylintrc config
flake8 src/ --max-line-length=100        # PEP8 compliance
mypy src/ --ignore-missing-imports       # Type checking

# 3. Formatting & Testing (MANDATORY)
black src/ tests/ --line-length=100      # Code formatting
isort src/ tests/ --line-length=100      # Import sorting  
pytest tests/ -v --cov=src --cov-report=term-missing  # Test coverage

# 4. Git Security Check (MANDATORY)
git log --oneline -10 | grep -i "api\|key\|secret" || echo "Clean"
```

### **🔧 IDE vs CLI Quality Balance**

**Current Configuration:**
- **.pylintrc**: Balanced config that disables overly strict rules while maintaining quality
- **IDE Settings**: Your VS Code pylint extension will use `.pylintrc` automatically
- **Score Target**: 8.0+ for compliance gate, currently achieving 9.27/10

**Key Disabled Rules (for practicality):**
- `too-many-arguments` (R0913) - Some functions legitimately need many parameters
- `line-too-long` (C0301) - Black handles formatting, pylint shouldn't duplicate
- `import-outside-toplevel` (C0415) - Sometimes needed for optional imports
- `broad-exception-caught` (W0718) - Intentional for robust error handling

**Rules Still Enforced:**
- Security issues (all enabled)
- Logic errors (E**** codes)
- Code duplication detection
- Unused variables/imports
- Most code style issues

### **Compliance Gate Requirements**
**🚨 ALL MUST PASS before completing any work:**
- **Security**: Bandit scan clean + Safety check clean
- **Quality**: Pylint ≥8.0/10 + Flake8 clean + MyPy clean  
- **Tests**: 100% test passage + coverage maintained
- **Format**: Black + isort applied
- **🔄 CRITICAL - Test Updates**: When refactoring changes internal function signatures or structure, ALL affected tests must be updated to maintain the same test coverage and assertions. Breaking tests due to refactoring is a regression that must be fixed as part of the refactoring work.

## Architecture Context

### Modern Architecture (2024)

#### Core Components (Final Architecture - 2025)
- **src/main.py** - Entry point with persona-driven interface routing
- **src/interfaces/** - Persona-driven interfaces (human/, programmatic/, protocols/)
  - Human: Rich interactive CLI with smart emoji usage
  - Programmatic: Library API for automation and scripting  
  - Protocols: MCP server foundation for Claude integration
- **src/orchestration/application_kernel.py** - Main application coordination
- **src/domains/** - Business logic domains with clean boundaries
  - content/: Document processing (extraction, enhancement, metadata)
  - ai_integration/: Provider management (5 providers, model selection, requests)
  - organization/: Document organization (clustering, folders, learning, content_analysis)
- **src/shared/** - Consolidated cross-cutting services
  - file_operations/: Unified file management with security
  - display/: Rich UI components with smart emoji handling
  - infrastructure/: Configuration, dependencies, utilities (migrated from utils/)
- **src/core/application_container.py** - Dependency injection container

#### Key Architectural Patterns
- **Persona-Driven Interface Pattern**: Separate interfaces for human, programmatic, and protocol users
- **Domain Service Pattern**: Business logic organized by domain capabilities (Content, AI Integration, Organization)
- **Clean Cut Migration Pattern**: Remove compatibility layers completely, fix regressions systematically
- **Validation-Driven Development Pattern**: Measurable acceptance criteria with mandatory validation checkpoints
- **Rich-First UI Pattern**: Rich Console by default with automatic terminal capability detection and fallbacks
- **ApplicationContainer Pattern**: Dependency injection for testability and clean component wiring
- **Shared Service Pattern**: Cross-cutting utilities consolidated in shared/ layer
- **Repository Structure Alignment Pattern**: Directory structure mirrors and enforces architectural boundaries

#### Rich UI Architecture
- **Centralized Console**: Single Console instance shared via ConsoleManager
- **Display Manager**: Orchestrates CLI display, progress, and messaging components  
- **Progress Display**: Rich Live displays with proper transient handling
- **Test Framework**: RichTestCase with StringIO capture and console isolation

#### Platform Considerations
- **Windows Unicode**: Auto-detection with ASCII fallbacks via Rich's native capabilities
- **Cross-platform paths**: Use `os.path` for platform compatibility
- **Terminal compatibility**: Rich auto-detection with graceful fallbacks
- **Console I/O**: Proper file handle management preventing pytest conflicts

## Common Issues & Solutions

### API Key Validation
```python
# Detect provider from API key format
if api_key.startswith("sk-ant-"):
    return "claude"
elif api_key.startswith("sk-proj-") or (api_key.startswith("sk-") and len(api_key) > 20):
    return "openai"
```

### File Processing Error Handling
```python
# Always move failed files to unprocessed folder
except (ValueError, OSError, FileNotFoundError) as e:
    if os.path.exists(input_path):
        unprocessed_path = os.path.join(unprocessed_folder, filename)
        organizer.file_manager.safe_move(input_path, unprocessed_path)
```

### Windows Unicode Handling
```python
# Force disable Unicode on Windows to prevent encoding issues
import platform
if platform.system() == "Windows":
    return False  # Force ASCII detection
```

## Recent Context

### **Security Overhaul Completed**
- **Fixed 3 critical API key logging vulnerabilities**:
  - `src/utils/error_handling.py:212` - Debug logging of exceptions
  - `src/core/file_processor.py:179` - Direct file logging without sanitization
  - `src/core/file_processor.py:533` - Runtime error file logging
- **Comprehensive security tooling**: Automatic sanitization, SecureLogger, log cleanup utilities
- **Complete test coverage**: 7 security-specific tests validating secret protection

### **Process Improvements**
- **Enhanced Ways of Working**: Added specialized workflows for debugging vs development
- **Security methodologies**: Systematic audit and testing approaches
- **Retrospective framework**: Built-in continuous improvement process

### **Lessons Learned from Recent Sessions**
- **Persona-driven architecture**: Different user types require fundamentally different interfaces
- **Clean cut migration**: Removing compatibility layers forces proper architectural adoption
- **Validation-driven development**: Measurable acceptance criteria prevent incomplete work
- **Rich-first UI with smart emoji usage**: Use console.options.encoding detection for cross-platform emoji support
- **Domain service extraction**: Business capability boundaries create more stable architecture than technical groupings
- **Repository structure alignment**: Directory organization should mirror and enforce architectural patterns
- **Single responsibility domains**: Independent development requires proper domain isolation
- **Shared service consolidation**: Cross-cutting utilities should be unified to prevent duplication

### **Configuration Centralization Completed**
- **Fixed filename length inconsistencies**: All providers now use consistent 160-character limits
- **Centralized configuration module**: `src/core/filename_config.py` with programmatic token calculation  
- **Optimal token allocation**: 78 tokens (calculated: ceil(160/2.7) * 1.3) for all AI providers
- **Runtime validation**: All generated filenames validated against security and length constraints
- **Best practices implementation**: No backward compatibility, full centralized solution as requested

### **Local LLM Feature Completed**
- **Complete offline processing**: Full LocalLLMProvider implementation with Ollama backend
- **Hardware-optimized models**: 4 models (gemma-2-2b, llama3.2-3b, mistral-7b, llama3.1-8b) with automatic system detection
- **Robust setup workflow**: Interactive `--setup-local-llm` with progress tracking and error recovery
- **CLI command suite**: `--list-local-models`, `--check-local-requirements`, model download/removal
- **Production-ready**: Comprehensive error handling, graceful fallbacks, progress indicators
- **Privacy-first**: Zero API costs, complete data isolation, no external dependencies
- **Documentation updated**: README, installation scripts, dependency management all enhanced

### **Unit Test Infrastructure Recovery (2025-09-08)**
- **Strategic Pivot**: Shifted from large-scale integration test recovery to focused unit test expansion
- **Methodology Established**: Module-by-module approach with comprehensive edge case coverage
- **Phase 1**: `utils/feature_flags.py` - 21 tests covering feature flag management, validation, persistence
- **Phase 2**: `core/filename_config.py` - 18 tests covering configuration calculations, validation, providers  
- **Phase 3**: `utils/expert_mode.py` - 22 tests covering interactive configuration, validation, CLI conversion
- **Quality Achievement**: All modules achieving 9.0+ pylint scores with complete functional coverage
- **Documentation**: Updated CLAUDE.md and moved product docs to `docs/product/` for better organization

### **DEPENDENCY MANAGEMENT SYSTEM IMPLEMENTED (2025-09-08)**
- **Centralized dependency detection**: DependencyManager class with cross-platform support
- **Persistent configuration**: JSON-based caching prevents repeated PATH searches
- **Auto-configuration**: Tesseract and Ollama automatically detected and configured
- **CLI integration**: `--check-dependencies`, `--refresh-dependencies` commands added
- **Local LLM timeout fix**: Extended from 10 seconds to 10 minutes for large model downloads
- **Environment variable bug fixed**: API keys with whitespace now properly handled
- **Model updates completed**: Latest Claude (Opus 4.1, Sonnet 4) and Gemini (2.5 Pro/Flash) models added
- **Filename consistency resolved**: All hardcoded values replaced with centralized configuration
- **Code quality maintained**: Pylint score 9.30/10, bandit security scan clean

### **SECURITY VULNERABILITIES REMEDIATED (2025-09-08)**
- **All 29 SAST vulnerabilities fixed** from comprehensive security audit
- **CRITICAL command injection vulnerability resolved** in `src/core/cli_parser.py`
- **XXE vulnerability patched** with secure XML parsing
- **API key exposure prevention** - comprehensive sanitization implemented
- **Zero dependency vulnerabilities** - all external packages remain clean
- **Complete SAST compliance achieved** - Bandit scan clean, Safety check clean

### **CURRENT STATUS (2025-09-09)** 
#### **✅ PRODUCTION-READY FUNCTIONALITY**
- **Persona-Driven Architecture**: Complete refactoring with clean domain boundaries
- **Domain Services**: Content, AI Integration, Organization - all complete with 8.5+ PyLint scores
- **Interface Layer**: Human (Rich UI), Programmatic (API), Protocols (MCP foundation)
- **Shared Services**: Unified file operations, display management, infrastructure utilities
- **Test Framework**: 380+ tests with 100% domain alignment and 90%+ pass rates
- **Code Quality**: Excellent scores across all domains (8.5-9.4 PyLint range)
- **Security Compliance**: 0 vulnerabilities across entire codebase (comprehensive SAST clean)
- **AI Providers**: All 5 providers (OpenAI, Claude, Gemini, Deepseek, Local) in clean domain architecture
- **Rich UI**: Smart emoji usage with automatic Windows/Linux fallbacks
- **Repository Structure**: 99% alignment between directory structure and architectural design

#### **🎨 RICH UI ARCHITECTURE MIGRATION COMPLETE (2025-09-08)**
- **Phase 4 Completed**: Complete Rich testing infrastructure migration with 92.2% success rate
- **ApplicationContainer Pattern**: Dependency injection architecture implemented for clean component wiring
- **ConsoleManager Singleton**: Centralized Rich Console management preventing I/O conflicts  
- **RichTestCase Framework**: Modern test infrastructure in `tests/utils/rich_test_utils.py`
- **Legacy Cleanup**: Removed obsolete `tests/frameworks/` and 20+ debug scripts, preserved documentation
- **Contract Migration**: All 8 contract tests migrated to new Rich testing patterns
- **UI Regression Prevention**: Comprehensive Rich UI behavioral testing (14/14 tests pass)
- **Console I/O Resolution**: Fixed ANSI escape code streaming and progress display issues

#### **📊 TESTING STRATEGY EVOLUTION**  
**From**: Large-scale integration test recovery (complex, high-risk)
**To**: Focused unit test expansion (incremental, reliable, immediate value)
**Benefits**: Faster feedback loops, easier debugging, modular quality assurance
**Impact**: Building confidence in individual components before tackling integration issues

## Development Standards

### Backward Compatibility
- **Preserve existing workflows** - Default to maintaining compatibility
- **Migration paths required** for breaking changes
- **Deprecation warnings** for old patterns before removal

### Error Messages
- **User-actionable**: Include specific commands to fix issues
- **No sensitive data**: Never expose API keys or internal paths
- **Clear context**: Explain what failed and why

## 🔄 **Session Retrospective: Test Infrastructure & Linting Work**

### **Key Lessons Learned (2025-01-09)**

#### **✅ What Worked Exceptionally Well**
1. **Parallel Agent Deployment for Systematic Cleanup**
   - **Pattern**: Deploy 3+ specialized agents simultaneously for large-scale issues
   - **Result**: Fixed 100+ linting issues efficiently across entire codebase
   - **Application**: Use for any systematic codebase-wide cleanup (imports, formatting, patterns)

2. **Research-Based Pattern Implementation**  
   - **Pattern**: Research enterprise patterns before implementing custom solutions
   - **Result**: Reduced complexity estimates by 50-75% (High→Medium, Medium→Low)
   - **Application**: Always research established patterns for testing, DI containers, ML model handling

3. **Clean Code Structure Over Piecemeal Patches**
   - **Pattern**: Rewrite corrupted files with clean structure instead of patching
   - **Result**: Fixed 6 integration tests instantly vs hours of individual patches
   - **Application**: When file structure becomes inconsistent, prefer clean rewrite

4. **State Isolation Discovery Through Systematic Testing**
   - **Pattern**: Test components individually to prove they work, then identify interaction issues
   - **Result**: Proved 100% test success with proper isolation vs 63% with contamination
   - **Application**: Use for any "works individually, fails together" scenarios

#### **❌ Anti-Patterns to Avoid**
1. **Analysis Over Action Tendency**
   - **Problem**: Repeatedly analyzed test failures instead of systematically fixing each one
   - **Impact**: User had to call out avoidance behavior multiple times
   - **Prevention**: Set completion targets (e.g., "fix all 15 failures") and track progress

2. **Pattern Mixing During Refactoring**
   - **Problem**: Mixed unittest.TestCase + pytest fixtures creating systematic failures
   - **Impact**: Created more failures than fixed during refactoring  
   - **Prevention**: Maintain pattern consistency - if using unittest, stick to unittest patterns

3. **Premature Architecture Optimization**
   - **Problem**: Created complex test infrastructure before fixing basic test execution
   - **Impact**: Added complexity without solving fundamental issues
   - **Prevention**: Fix basic functionality first, then optimize architecture

#### **🚀 Process Improvements Implemented**
1. **Enhanced Linting Standards**: 4-phase systematic approach with parallel agents
2. **Research-Based Testing Patterns**: Session fixtures, state isolation, clean structure
3. **Segmented Test Execution**: Isolation patterns preventing state contamination
4. **Systematic Failure Resolution**: Root cause → fix → test → validate cycle

## 🔄 **Session Retrospective Checklist**

After any significant work session, always:
- [ ] **Conduct retrospective** using RETROSPECTIVE_PROCESS.md
- [ ] **Update this file** with key lessons learned  
- [ ] **Identify process improvements** and update Ways of Working
- [ ] **Plan concrete changes** for next session

## ⚡ **Quick Reference Commands**

### **🧹 Systematic Linting Standards (Enhanced 2025)**
```bash
# PHASE 1: Code Formatting (Always run first)
black src/ tests/ --line-length=100            # Apply consistent formatting
isort src/ tests/ --line-length=100            # Fix import ordering

# PHASE 2: Comprehensive Linting Analysis  
pylint src/ --output-format=json > pylint_results.json    # Generate detailed report
pyright src/ --outputjson > pyright_results.json         # Type checking analysis
bandit -r src/ --format json > bandit_results.json       # Security analysis

# PHASE 3: Targeted Issue Resolution (Use parallel agents)
# Deploy specialized agents for systematic cleanup:
# - AI Provider Import Fixes Agent
# - Orchestration Type Errors Agent  
# - Logging Format Cleanup Agent
# - Unused Import/Variable Cleanup Agent

# PHASE 4: Validation Gates (All must pass)
pylint src/ --fail-under=9.5                  # Target: ≥9.5/10 (was 8.0)
pyright src/ | grep "0 errors"                # Target: 0 type errors
bandit -r src/ --severity-level high          # Target: 0 high/medium security issues
```

### **📋 Systematic Cleanup Checklist**
```bash
# Common warning patterns to eliminate systematically:
pylint src/ --disable=all --enable=W0611,W0612,W0613    # Unused imports/variables
pylint src/ --disable=all --enable=W1203                # Logging f-string issues  
pylint src/ --disable=all --enable=E0401,E0611          # Import errors
pylint src/ --disable=all --enable=R1705,R1702          # Code structure issues

# Agent deployment pattern (parallel processing):
# 1. Import Resolution Agent: Fix E0401, E0611 across all provider files
# 2. Type Safety Agent: Fix pyright errors in orchestration layer
# 3. Code Quality Agent: Fix W1203, R1705, unused import patterns
# 4. Architecture Alignment Agent: Ensure proper domain import patterns
```

### **🔧 Linter Configuration Standards**
```toml
# pyproject.toml - Aligned standards
[tool.black]
line-length = 100  # Consistent with pylint
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.pyright]
reportMissingImports = "warning"      # Detect import issues
reportCallIssue = "warning"           # Function signature errors
reportAttributeAccessIssue = "warning" # Type safety
extraPaths = ["src"]                  # Proper path resolution

[tool.pylint]
fail-under = 9.5                      # High quality standard
max-line-length = 100                 # Consistent formatting
disable = C0301,R0913,R0917,W0718     # Reasonable exceptions
```

### **Complete SAST Security Audit**
```bash
# Enhanced security analysis pipeline  
bandit -r src/ --format txt                     # Security scan (Target: 0 high/medium)
safety check                                    # Dependency vulnerabilities  
pylint src/ --fail-under=9.5                   # Code quality ≥9.5/10
pyright src/                                    # Type checking (0 errors)
flake8 src/ --max-line-length=100              # PEP8 compliance

# Dependency management check
content-tamer-ai --check-dependencies           # Verify all dependencies detected
content-tamer-ai --refresh-dependencies         # Force refresh dependency paths
```

### **CI/CD Ready Commands**  
```bash
# Single command compliance check (for automation)
bandit -r src/ -f json && safety check --json && \
pylint src/ --fail-under=8.0 --output-format=json && \
flake8 src/ --format=json && \
mypy src/ --ignore-missing-imports && \
pytest tests/ -v --tb=short
```

### **Test-Driven Debugging**
```python
def test_reproduce_issue():
    # Write this test first to reproduce the bug
    pass

def test_issue_is_fixed():
    # Write this test to verify the fix works
    pass
```

*This file ensures Claude Code maintains our established patterns, learns from each session, and continuously improves development quality.*