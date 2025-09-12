# Feature Enhancement: Cross-Platform Rich UI with ASCII Fallback

## User Story

**As a** Content Tamer AI user  
**I want** the application to display rich terminal UI (Unicode characters, colors, progress bars) when my terminal supports it, and gracefully fall back to ASCII when it doesn't  
**So that** I get the best possible user experience regardless of my terminal environment (cmd.exe, PowerShell, Windows Terminal, bash, VS Code terminal, etc.)

## Current Problem

The application currently uses an overly aggressive approach that disables Unicode for ALL Windows users (`if platform.system() == "Windows": return False`), which breaks the rich UI experience for users with modern terminals that fully support Unicode.

Users with capable terminals (PowerShell, Windows Terminal, VS Code integrated terminal) are forced to use ASCII-only mode, while the application may crash for users with legacy terminals that can't handle Unicode characters.

## Acceptance Criteria

### Must Have
- [ ] **Accurate Terminal Detection**: Detect Unicode/color support per terminal, not per OS
- [ ] **Graceful Fallback**: When Unicode isn't supported, use ASCII equivalents without crashing
- [ ] **Consistent Experience**: Same functionality available in both rich and ASCII modes
- [ ] **No Crashes**: Never crash due to encoding issues, regardless of terminal

### Should Have  
- [ ] **Environment Override**: Support `CONTENT_TAMER_UI_MODE=ascii|unicode|auto` environment variable
- [ ] **Character-Specific Testing**: Test individual Unicode characters used (→, █, ▓, etc.) rather than generic strings
- [ ] **Terminal Type Detection**: Distinguish between cmd.exe, PowerShell, Windows Terminal, VS Code terminal
- [ ] **User Feedback**: Clearly indicate which display mode is active in verbose mode

### Could Have
- [ ] **Automatic Detection**: Smart detection based on terminal capabilities and font support
- [ ] **Progressive Enhancement**: Use best available characters (e.g., → if supported, -> if not, > as last resort)
- [ ] **Configuration Persistence**: Remember user's preferred display mode

## Technical Analysis

### Current Architecture Issues
1. **Multiple Code Pathways**: Unicode/ASCII logic scattered across files
2. **Blanket OS Detection**: `platform.system() == "Windows"` is too broad
3. **Incomplete Testing**: Only tests encoding, not actual character/font support

### Implementation Options (Ranked)

#### Option 1: Rich Library Integration ⭐ (Recommended)
**Benefits:**
- Industry standard with sophisticated terminal detection
- Single rendering pipeline with automatic fallbacks  
- Built-in `safe_box=True` for Windows legacy compatibility
- Handles 99% of cross-platform edge cases
- ~2MB dependency

**Implementation:**
```python
from rich.console import Console
from rich.progress import Progress

console = Console(
    force_terminal=True,  # Override detection if needed
    safe_box=True,       # Windows legacy terminal compatibility  
    width=80             # Fallback width
)
```

#### Option 2: Enhanced Detection with Blessed
**Benefits:**
- More sophisticated terminal capability detection than current
- Unicode input/output handling built-in
- Cross-platform support including Windows
- Smaller footprint than Rich

**Considerations:**
- May need Colorama companion for Windows color support
- Less comprehensive than Rich

#### Option 3: Improve Current Detection Logic
**Benefits:**
- No new dependencies
- Minimal changes to existing code

**Considerations:**
- Most complex to implement correctly
- Manual handling of edge cases
- Will never be as robust as dedicated libraries

### Testing Strategy

#### Testing Matrix
| Terminal | Unicode | Colors | Notes |
|----------|---------|--------|--------|
| cmd.exe (Windows) | ❌ | Limited | Legacy compatibility required |
| PowerShell | ✅ | ✅ | Modern Windows default |
| Windows Terminal | ✅ | ✅ | Best Windows experience |
| VS Code Terminal | ✅ | ✅ | Developer environment |
| bash/zsh (Linux/Mac) | ✅ | ✅ | Standard Unix terminals |

#### Test Scenarios
- [ ] **Rich Mode**: Verify Unicode characters display correctly
- [ ] **ASCII Fallback**: Verify functionality preserved with ASCII-only
- [ ] **Mixed Environment**: Test output redirection (pipes, files)
- [ ] **Environment Overrides**: Test `FORCE_ASCII=1` and `FORCE_UNICODE=1`

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing UI for power users | High | Comprehensive testing across terminals |
| New dependency bloat | Medium | Choose lightweight option (Blessed vs Rich) |
| Regression in ASCII mode | High | Maintain current ASCII functionality |
| Cross-platform compatibility issues | High | Test matrix across OS/terminal combinations |

## Technical Debt

This enhancement addresses:
- **Maintainability**: Consolidate display logic into single pipeline
- **User Experience**: Provide appropriate UI for user's capabilities
- **Reliability**: Eliminate Unicode-related crashes
- **Testing**: Enable systematic testing of both UI modes

## Definition of Done

- [ ] Feature implemented with chosen approach
- [ ] All acceptance criteria met
- [ ] Test suite updated with terminal detection scenarios
- [ ] Documentation updated with environment variable options
- [ ] Verified working across terminal matrix
- [ ] No regressions in existing ASCII functionality
- [ ] Performance impact assessed and acceptable

## Dependencies

- **Research**: Investigate Rich vs Blessed libraries
- **Architecture**: Design unified display pipeline
- **Testing**: Set up cross-platform terminal testing
- **Documentation**: Update user documentation with terminal requirements

---

*Created: August 28, 2025*  
*Priority: Medium*  
*Epic: User Experience Enhancement*