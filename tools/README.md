# Development Tools

This directory contains utility scripts for development and analysis.

## Available Tools

### `token_analysis.py`
Analyzes optimal token settings for 160-character filename generation.

```bash
# Run token analysis
python tools/token_analysis.py
```

**What it does:**
- Tests various filename lengths against token limits
- Calculates optimal AI output token settings
- Analyzes content input truncation settings
- Provides recommendations for AI configuration

**Use cases:**
- Optimizing AI model parameters
- Understanding token-to-character ratios
- Debugging filename generation issues
- Performance tuning

## Adding New Tools

When adding development utilities:

1. **Place in `tools/` directory** - Keep utilities separate from main code
2. **Add documentation** - Update this README with tool description
3. **Use relative imports** - Ensure tools can find project modules
4. **Add to .gitignore if needed** - For tools that generate temporary files