# Claude Code Configuration

## Quick Context
**Content Tamer AI** - Intelligent document processing with AI-powered organization
- Python application with Rich CLI interface
- 5 AI providers: OpenAI, Claude, Gemini, Deepseek, Local LLM
- Automated document classification and folder organization

## 📚 Documentation Structure

All detailed documentation is organized in `docs/claude/`:

### Core Files (Load these for any task)
- **[docs/claude/CLAUDE_CORE.md](docs/claude/CLAUDE_CORE.md)** - Essential context & architecture
- **[docs/claude/WORKFLOWS.md](docs/claude/WORKFLOWS.md)** - FEATURE, BUG, and SECURITY workflows
- **[docs/claude/PATTERNS.md](docs/claude/PATTERNS.md)** - Proven implementation patterns
- **[docs/claude/GUARDRAILS.md](docs/claude/GUARDRAILS.md)** - Non-negotiable rules

### Role-Specific (Load as needed)
- **[docs/claude/ARCHITECTURE.md](docs/claude/ARCHITECTURE.md)** - For architectural changes
- **[docs/claude/SECURITY_OPS.md](docs/claude/SECURITY_OPS.md)** - For security operations
- **[docs/claude/TEST_STRATEGY.md](docs/claude/TEST_STRATEGY.md)** - For test planning

### Navigation
- **[docs/claude/DOCUMENTATION_MAP.md](docs/claude/DOCUMENTATION_MAP.md)** - Complete documentation guide

## ⚡ Quick Commands

```bash
# Run from src/ directory
cd src && python main.py --help

# Quality gates (ALL must pass)
cd src && python -m pylint . --fail-under=8.0
bandit -r src/ --severity-level medium
safety check

# Testing
cd src && python -m pytest ../tests/unit -v
```

## 🎯 Current Focus
- Test imports need PYTHONPATH=src or run from src/ directory
- All UI operations through UnifiedDisplayManager
- Use % formatting in logging (not f-strings)
- File organization bug fixed - uses actual paths now

## 🔒 Critical Rules
1. NEVER log API keys or secrets
2. ALWAYS validate file paths
3. Test BEFORE implementation
4. Progress indicators for ALL operations

---
*For detailed information, see [docs/claude/](docs/claude/) directory*