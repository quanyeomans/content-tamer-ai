# IDE Setup Guide

This guide helps you configure your development environment for Content Tamer AI.

## Visual Studio Code

### Quick Setup
```bash
# Copy the example settings
cp .vscode/settings.json.example .vscode/settings.json

# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8
code --install-extension ms-python.mypy-type-checker
```

### Recommended Extensions
- **Python** - Microsoft's official Python extension
- **Black Formatter** - Code formatting
- **Flake8** - Linting  
- **Mypy Type Checker** - Type checking
- **GitLens** - Enhanced Git integration
- **pytest** - Test runner integration

### Configuration Details
The example settings include:
- Python interpreter configuration
- Automatic code formatting with Black
- Linting with Flake8 and MyPy
- Test discovery with pytest
- File exclusions for cache/temp files

## Claude Code IDE

### Quick Setup
```bash
# Copy the example settings
cp .claude/settings.json.example .claude/settings.local.json

# Edit to match your preferences
# (This file is automatically ignored by git)
```

### Configuration Details
The example settings include:
- Project metadata and description
- Code style preferences (Black formatting)
- File inclusion/exclusion patterns
- AI assistance instructions for code review

## PyCharm / IntelliJ

### Project Setup
1. Open the project folder in PyCharm
2. Configure Python interpreter to use `./venv/bin/python`
3. Enable these inspections:
   - PEP 8 coding style
   - Type annotations
   - Unused imports

### Recommended Settings
- **Code Style**: Use Black formatter
- **Test Runner**: pytest
- **Type Checking**: Enable MyPy integration
- **Git**: Exclude IDE files (already configured in .gitignore)

## Vim/Neovim

### Basic Configuration
Add to your `.vimrc` or `init.vim`:

```vim
" Python development
au FileType python setlocal tabstop=4 shiftwidth=4 expandtab
au FileType python setlocal textwidth=88  " Black line length

" Use Black for formatting
au FileType python nnoremap <leader>f :!black %<CR>

" Run tests
au FileType python nnoremap <leader>t :!python -m pytest<CR>
```

## Important Notes

### Files to Never Commit
The following are automatically excluded by `.gitignore`:
- `.vscode/settings.json` (personal VS Code settings)
- `.claude/settings.local.json` (personal Claude settings)
- `.idea/` (IntelliJ/PyCharm settings)
- Any `*.local.*` configuration files

### Shared Configuration
Only commit example files:
- `.vscode/settings.json.example` ✅
- `.claude/settings.json.example` ✅
- Project-level settings that benefit all developers ✅

### Getting Help
- Check existing IDE configurations in example files
- Review `.gitignore` for excluded file patterns
- Open an issue if you need help with a specific IDE setup