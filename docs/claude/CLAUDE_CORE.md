# Claude Code Essential Context

## Project Overview
**Content Tamer AI** - Intelligent document processing and organization system
- Processes PDFs/documents using AI providers (OpenAI, Claude, Gemini, Local LLM)
- Generates intelligent filenames and organizes content automatically
- Cross-platform Python application with Rich CLI interface

## Architecture (Current State)
```
src/
├── interfaces/          # Persona-driven (human/programmatic/protocols)
├── orchestration/       # ApplicationKernel - main coordination
├── domains/            # Business logic with clean boundaries
│   ├── content/        # Document processing (extraction, enhancement)
│   ├── ai_integration/ # Provider management (5 providers)
│   └── organization/   # Document organization (clustering, learning)
└── shared/            # Cross-cutting services
    ├── file_operations/
    ├── display/        # UnifiedDisplayManager, ConsoleManager
    └── infrastructure/ # Config, dependencies, utilities
```

## Execution Patterns

### FEATURE Pattern
```bash
1. TodoWrite → Plan the feature
2. Write failing test → tests/unit or tests/integration
3. Implement minimal solution → Make test pass
4. Run compliance → pylint ≥8.0, bandit clean
5. Validate UX → Progress indicators, error handling
```

### BUG Pattern
```bash
1. Write reproduction test → Confirms the bug
2. Fix the issue → Minimal change
3. Verify all tests pass → No regressions
4. Add regression test → Prevent recurrence
```

### SECURITY Pattern
```bash
1. bandit -r src/ → Identify issues
2. Fix all HIGH/MEDIUM → Immediate priority
3. safety check → Verify dependencies
4. Validate sanitization → No secrets in logs
```

## Current Issues & Active Work
- Test import errors in some integration tests (use PYTHONPATH=src)
- Keep using UnifiedDisplayManager for all UI operations
- Always use % formatting in logging (not f-strings)

## Critical Commands

### Quality Gates (ALL must pass)
```bash
# From src/ directory:
cd src && python -m pylint . --fail-under=8.0  # Must score ≥8.0
bandit -r . --severity-level medium             # 0 HIGH/MEDIUM issues
safety check                                     # 0 vulnerabilities
black . --line-length=100                        # Format code
isort . --line-length=100                        # Sort imports
```

### Testing
```bash
# From src/ directory for proper imports:
cd src && python -m pytest ../tests/unit -v     # Unit tests
cd src && python -m pytest ../tests/ -v         # All tests
```

### Run Application
```bash
cd src && python main.py --help                  # Show options
cd src && python main.py --input ../documents    # Process documents
```

## Key Patterns
- **ApplicationContainer**: Dependency injection for all services
- **RichTestCase**: Base class for UI component tests  
- **UnifiedDisplayManager**: All UI operations go through this
- **Domain boundaries**: Never cross-import between domains
- **Lazy logging**: Use % formatting, not f-strings

## Non-Negotiables
- NEVER log API keys or secrets
- ALWAYS validate file paths
- Tests BEFORE implementation
- Progress indicators for ALL operations
- Graceful error handling (no raw logs to console)