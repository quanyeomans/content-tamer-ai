# Claude Code Configuration
*Project-specific context and working patterns for content-tamer-ai*

## Project Overview

**Content Tamer AI** - Intelligent file processing and organization system
- Processes PDFs and documents using AI providers (OpenAI, Claude)
- Generates intelligent filenames and organizes content
- Cross-platform Python application with rich CLI interface

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

### Test Strategy
- **Test-first development**: Always write failing tests before implementation
- **Minimal mocking**: Only mock external AI APIs, keep file operations real
- **Use tempfile.TemporaryDirectory()** for file-based tests
- **Extend existing test files**: Never create new test files

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

### Code Quality Commands
```bash
# Always run these before completion
pytest tests/ -v --cov=src --cov-report=term-missing
black src/ tests/
isort src/ tests/
```

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

### **Known Working State**
- **All 264 tests passing** - comprehensive test coverage maintained
- **Zero security vulnerabilities** - complete protection against API key exposure
- **Clean repository structure** - organized documentation and code
- **Robust error handling** - files properly moved, errors properly logged (securely)

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

### **Security Audit**
```bash
# Quick security scan for potential issues
grep -r "print\|log.*\(.*api.*key\|str(.*e.*)" src/

# Sanitize any existing logs
python scripts/sanitize_logs.py
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