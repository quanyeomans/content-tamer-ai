# Claude Code Configuration
*Project-specific context and working patterns for content-tamer-ai*

## Project Overview

**Content Tamer AI** - Intelligent file processing and organization system
- Processes PDFs and documents using AI providers (OpenAI, Claude, Gemini, Local LLM)
- Generates intelligent filenames and organizes content
- Cross-platform Python application with rich CLI interface
- **NEW**: Complete offline processing with Local LLM support via Ollama

## Working Patterns

### **Choose Your Workflow**

#### **For New Features/Development:**
1. **PRE-CODE_CHECKLIST.md** - Complete all 4 mandatory gates
2. **IMPLEMENTATION_WORKFLOW.md** - Test-first development

#### **For Bugs/Issues/Debugging:**
1. **DEBUGGING_WORKFLOW.md** - Streamlined issue resolution
   - Quick analysis and minimal reproduction
   - Root cause identification and minimal fix
   - Focus on speed and safety

#### **For Security Issues:**
1. **SECURITY_AUDIT_METHODOLOGY.md** - Systematic vulnerability discovery
2. **DEBUGGING_WORKFLOW.md** (Fast-track) - Immediate containment and fix
3. **SECURITY_TESTING_STRATEGY.md** - Adversarial testing approach

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

### Test Strategy
- **Test-first development**: Always write failing tests before implementation
- **Minimal mocking**: Only mock external AI APIs, keep file operations real
- **Use tempfile.TemporaryDirectory()** for file-based tests
- **Extend existing test files**: Never create new test files
- **🔄 Refactoring Test Maintenance**: When refactoring code:
  1. Update all affected test mocks and patches to match new internal structure
  2. Maintain the same test assertions and coverage expectations
  3. Fix Unicode/encoding issues in tests by setting proper environment variables
  4. Ensure tests validate the same behavioral contracts, not implementation details

### Key Test Files
- `tests/test_integration.py` - API/validation tests
- `tests/test_error_handling.py` - Error handling tests  
- `tests/test_success_failure_integration.py` - File processing tests
- `tests/test_display_manager.py` - UI/display tests
- `tests/test_security.py` - Security validation tests

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

### Core Components
- **src/core/file_processor.py** - Main file processing logic
- **src/core/directory_manager.py** - Directory operations and API key validation
- **src/utils/cli_display.py** - Terminal display and Unicode handling
- **src/utils/error_handling.py** - Centralized error handling with retry logic

### Key Patterns
- **DisplayContext pattern**: For progress and status updates
- **FileOrganizer pattern**: For file operations and organization
- **Provider detection**: API key format validation for OpenAI vs Claude

### Platform Considerations
- **Windows Unicode issues**: Force ASCII detection on Windows platform
- **Cross-platform paths**: Use `os.path` for platform compatibility
- **Terminal compatibility**: Rich display with fallbacks for different terminals

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

### **Lessons Learned from This Session**
- **Security-first mindset**: Always audit for secret exposure when touching logging/error code
- **Test-driven debugging**: Write reproduction tests before implementing fixes
- **Architecture simplicity**: Prefer single-layer solutions over complex dual-layer approaches
- **Process discipline**: Following Ways of Working prevents quality issues even under time pressure

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

### **Updated Session Context**
- **Environment variable bug fixed**: API keys with whitespace now properly handled
- **Model updates completed**: Latest Claude (Opus 4.1, Sonnet 4) and Gemini (2.5 Pro/Flash) models added
- **Filename consistency resolved**: All hardcoded values replaced with centralized configuration
- **Code quality maintained**: Pylint score 9.30/10, bandit security scan clean

### **CRITICAL SECURITY AUDIT FINDINGS (2025-09-07)**
- **29 vulnerabilities identified** in comprehensive SAST audit
- **2 CRITICAL severity** - Command injection & XXE vulnerabilities requiring immediate action
- **Detailed remediation plan**: `docs/security/SECURITY_REMEDIATION_PLAN.md`
- **Priority focus**: `src/core/cli_parser.py` command injection (CVSS 9.8)
- **Zero dependency vulnerabilities** - all external packages clean

### **Known Working State**  
- **All systems consistent** - unified 160-char filename limits across all AI providers
- **🚨 SECURITY VULNERABILITIES FOUND** - comprehensive audit completed, remediation plan documented
- **Clean repository structure** - organized documentation and centralized config
- **Robust error handling** - files properly moved, errors properly logged (securely)
- **Rich UI bugs fixed** - border wrapping and line persistence issues resolved
- **Complete E2E test coverage** - comprehensive user workflow and BDD regression tests added

## Development Standards

### Backward Compatibility
- **Preserve existing workflows** - Default to maintaining compatibility
- **Migration paths required** for breaking changes
- **Deprecation warnings** for old patterns before removal

### Error Messages
- **User-actionable**: Include specific commands to fix issues
- **No sensitive data**: Never expose API keys or internal paths
- **Clear context**: Explain what failed and why

## 🔄 **Session Retrospective Checklist**

After any significant work session, always:
- [ ] **Conduct retrospective** using RETROSPECTIVE_PROCESS.md
- [ ] **Update this file** with key lessons learned
- [ ] **Identify process improvements** and update Ways of Working
- [ ] **Plan concrete changes** for next session

## ⚡ **Quick Reference Commands**

### **Complete SAST Security Audit**
```bash
# Comprehensive security analysis pipeline
bandit -r src/ -f text                           # Static security analysis
safety check                                    # Dependency vulnerabilities  
pylint src/ --fail-under=8.0 | grep -E "(E|W|C|R)[0-9]" # Quality issues
flake8 src/ --max-line-length=100               # PEP8 compliance
mypy src/ --ignore-missing-imports              # Type checking

# Legacy manual security scan (deprecated - use above instead)
grep -r "print\|log.*\(.*api.*key\|str(.*e.*)" src/

# Sanitize any existing logs
python scripts/sanitize_logs.py
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