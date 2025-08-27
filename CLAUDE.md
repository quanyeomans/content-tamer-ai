# Claude Code Configuration
*Project-specific context and working patterns for content-tamer-ai*

## Project Overview

**Content Tamer AI** - Intelligent file processing and organization system
- Processes PDFs and documents using AI providers (OpenAI, Claude)
- Generates intelligent filenames and organizes content
- Cross-platform Python application with rich CLI interface

## Working Patterns

### Mandatory Workflow
**ALWAYS follow this sequence - no exceptions:**

1. **PRE-CODE_CHECKLIST.md** - Complete all 4 mandatory gates
   - Use TodoWrite for task planning and tracking
   - Identify test file and security requirements
   - Confirm backward compatibility approach

2. **IMPLEMENTATION_WORKFLOW.md** - Test-first development
   - Write failing test first in existing `tests/test_*.py` files
   - Implement minimal solution
   - Validate security and integration

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

### Last Major Changes
- Fixed Unicode encoding crashes on Windows terminals
- Implemented comprehensive API key provider validation
- Resolved file processing regression where failed files weren't moved
- Optimized Ways of Working documentation structure

### Test Coverage Focus
- Need tests for API key validation logic in directory_manager.py:712
- Need tests for error handling fixes in process_file_enhanced_core
- All new security validation code needs test coverage

### Known Working State
- All tests passing (resolved from 17 failures to 0)
- Repository structure cleaned and organized
- Code quality: 30 pyright errors resolved, 7.97/10 pylint score
- File processing functional with proper error handling

## Development Standards

### Backward Compatibility
- **Preserve existing workflows** - Default to maintaining compatibility
- **Migration paths required** for breaking changes
- **Deprecation warnings** for old patterns before removal

### Error Messages
- **User-actionable**: Include specific commands to fix issues
- **No sensitive data**: Never expose API keys or internal paths
- **Clear context**: Explain what failed and why

*This file ensures Claude Code maintains our established patterns and quality standards across sessions*