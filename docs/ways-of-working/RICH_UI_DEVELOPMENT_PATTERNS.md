# Rich UI Development Patterns
*Patterns for beautiful, interactive interfaces with automatic fallback support*

## Core Philosophy: Rich-First Design

### **Principle**
Build **rich, interactive, emoji-filled interfaces by default** with automatic graceful degradation for limited terminals. Trust Rich's built-in capability detection instead of manual terminal management.

## **Pattern 1: Rich Console with Smart Emoji Usage**

### **Problem**
Direct `print()` statements bypass Rich's capabilities, and emojis fail in terminals with limited encoding (cp1252).

### **Solution**
Use Rich Console for all output with smart emoji detection based on terminal encoding capabilities.

#### **✅ CORRECT Implementation**
```python
# Smart emoji usage: emojis where supported, ASCII where not
from interfaces.human.rich_console_manager import RichConsoleManager

def show_welcome():
    console_manager = RichConsoleManager()
    console = console_manager.console
    
    # Rich handles colors and styling automatically (always work)
    console.print("[bold blue]CONTENT TAMER AI[/bold blue]")
    
    # Smart emoji usage based on terminal encoding
    if hasattr(console, 'options') and console.options.encoding == 'utf-8':
        console.print("🎯 [cyan]With emoji support[/cyan]")  # UTF-8 terminals
    else:
        console.print(">> [cyan]Without emoji support[/cyan] <<")  # cp1252 terminals
        
def show_status(message: str, status: str):
    if hasattr(console, 'options') and console.options.encoding == 'utf-8':
        emoji_styles = {"success": "✅", "error": "❌", "warning": "⚠️"}
        icon = emoji_styles.get(status, "ℹ️")
    else:
        ascii_styles = {"success": "[OK]", "error": "[X]", "warning": "[!]"}
        icon = ascii_styles.get(status, "[i]")
    
    console.print(f"{icon} [{status}]{message}[/{status}]")
```

#### **❌ WRONG Implementation**
```python
# Direct Unicode always fails in cp1252
def show_welcome():
    print("🎯 CONTENT TAMER AI")  # Fails in Windows cp1252

# Manual terminal checking everywhere (brittle anti-pattern)
def show_status(message, status):
    if console.legacy_windows:  # Brittle manual checking
        icon = "[OK]"
    else:
        icon = "✅"
    console.print(f"{icon} {message}")
```

## **Pattern 2: Smart Emoji Detection (Correct Rich Approach)**

### **Problem**
Emojis fail in some terminal encodings (cp1252), but manual checking creates brittle code.

### **Solution**
Use Rich's console.options.encoding to detect emoji support and provide appropriate alternatives.

#### **✅ CORRECT Implementation**
```python
class RichConsoleManager:
    def _create_console(self):
        return Console(
            theme=Theme({...}),
            force_terminal=None,  # Let Rich auto-detect everything
            width=None,          # Auto-detect terminal width
            # Rich handles terminal capability detection automatically
        )
    
    def show_status(self, message: str, status: str = "info"):
        # Smart emoji usage based on console encoding detection
        if hasattr(self.console, 'options') and self.console.options.encoding == 'utf-8':
            # UTF-8 terminals: Full emoji support
            emoji_styles = {"success": "✅", "error": "❌", "warning": "⚠️"}
            icon = emoji_styles.get(status, "ℹ️")
        else:
            # Non-UTF-8 terminals: ASCII alternatives  
            ascii_styles = {"success": "[OK]", "error": "[X]", "warning": "[!]"}
            icon = ascii_styles.get(status, "[i]")
        
        self.console.print(f"{icon} [{status}]{message}[/{status}]")
```

#### **❌ WRONG Implementation**
```python
# Manual legacy_windows checking everywhere (brittle anti-pattern)
def show_status(self, message, status):
    if self.console.legacy_windows:  # Brittle, repetitive
        styles = {"success": "[OK]", "error": "[X]"}
    else:
        styles = {"success": "✅", "error": "❌"}
    # Repeated in every method - maintenance burden
```

## **Pattern 3: Rich UI Component Design**

### **Problem**
Inconsistent UI patterns across different features create confusing user experience.

### **Solution**
Create reusable Rich UI components with consistent styling.

#### **Component Library Pattern**
```python
class RichConsoleManager:
    def show_info_panel(self, title: str, content: str):
        """Standard info panel with consistent styling."""
        panel = Panel(
            content,
            title=f"[blue]{title}[/blue]",
            border_style="blue",
            padding=(0, 1)
        )
        self.console.print(panel)
    
    def show_success_panel(self, title: str, message: str, details: dict = None):
        """Standard success panel with optional details."""
        content = f"[green]{message}[/green]"
        
        if details:
            content += "\n\n[bold white]Details:[/bold white]"
            for key, value in details.items():
                content += f"\n• {key}: [highlight]{value}[/highlight]"
        
        panel = Panel(
            content,
            title="[green]✅ Success[/green]",
            border_style="green"
        )
        self.console.print(panel)
```

#### **Progress Display Pattern**
```python
def create_progress_display(self, description: str = "Processing"):
    """Consistent progress display across all features."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="progress.complete"),
        MofNCompleteColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=self.console,
        transient=False  # Keep visible after completion
    )
```

## **Pattern 4: Error Handling with Rich**

### **Problem**
Error messages without Rich formatting are hard to read and don't provide context-appropriate guidance.

### **Solution**
Use Rich for all error display with context-sensitive suggestions.

#### **Rich Error Handling Pattern**
```python
def handle_error(self, error: Exception, context: dict):
    """Show user-friendly error with Rich formatting and suggestions."""
    error_msg = str(error)
    suggestions = []
    
    # Context-sensitive suggestions
    if "API key" in error_msg.lower():
        provider = context.get('provider', 'AI')
        suggestions.extend([
            f"Check your {provider} API key is set correctly",
            f"Set environment variable: {provider.upper()}_API_KEY", 
            "Use --api-key argument to provide key directly"
        ])
    
    # Rich error panel with suggestions
    content = f"[red]{error_msg}[/red]"
    if suggestions:
        content += "\n\n[bold white]Suggestions:[/bold white]"
        for suggestion in suggestions:
            content += f"\n• {suggestion}"
    
    panel = Panel(
        content,
        title="[red]❌ Error[/red]",
        border_style="red"
    )
    self.console.print(panel)
```

## **Pattern 5: Persona-Appropriate Output**

### **Problem**
Same output format doesn't work for all user personas (human vs automation).

### **Solution** 
Adapt output format to persona needs while using Rich for all rendering.

#### **Human Interface Output**
```python
def show_results_for_humans(self, result):
    """Rich, detailed output for human users."""
    if result.success:
        self.console.print("🎉 [bold green]Processing Complete![/bold green]")
        
        # Rich table for detailed results
        table = Table(title="Processing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Files Processed", str(result.files_processed))
        table.add_row("Output Directory", result.output_directory)
        self.console.print(table)
    else:
        self.show_error_panel("Processing Failed", result.error)
```

#### **Programmatic Interface Output**
```python
def show_results_for_automation(self, result):
    """Structured output for automation users."""
    if result.success:
        # Still use Rich, but minimal formatting for parsing
        self.console.print(f"SUCCESS: {result.files_processed} files processed, output: {result.output_directory}")
    else:
        self.console.print(f"FAILED: {result.error}")
```

## **Testing Patterns for Rich UI**

### **Pattern: Rich UI Testing with Minimal Mocking**
```python
class TestRichUIComponents(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)  # Proper console isolation
        self.console_manager = RichConsoleManager()
        # Override with test console for isolation
        self.console_manager._console = self.test_console
    
    def test_smart_emoji_usage(self):
        """Test smart emoji detection in both UTF-8 and ASCII modes."""
        # Test UTF-8 mode
        if hasattr(self.test_console, 'options'):
            self.test_console.options.encoding = 'utf-8'
        
        self.console_manager.show_status("Test message", "success")
        output = self.get_console_output()
        
        # Should use emoji in UTF-8 mode
        if self.test_console.options.encoding == 'utf-8':
            self.assertIn("✅", output)
        else:
            self.assertIn("[OK]", output)
    
    @patch("builtins.input")  # Only mock inputs, not console output
    def test_minimal_mocking_approach(self, mock_input):
        """Demonstrate minimal mocking - let Rich handle output."""
        mock_input.return_value = "test input"
        
        # Use Rich console for output (no mocking needed)
        self.console_manager.show_welcome_panel()
        
        output = self.get_console_output()
        self.assertIn("CONTENT TAMER AI", output)
        
        # Rich output captured without Unicode issues through test framework
```

### **Pattern: Progress Display Testing**
```python
def test_progress_display(self):
    """Test progress display functionality."""
    progress_id = self.console_manager.start_progress("Test Progress")
    
    self.console_manager.update_progress(progress_id, 5, 10, "Processing files")
    self.console_manager.finish_progress(progress_id)
    
    output = self.get_console_output()
    self.assertIn("Test Progress", output)
    self.assertIn("Processing files", output)
```

## **Rich Console Singleton Management**

### **Pattern: Centralized Console Management**
```python
class RichConsoleManager:
    """Singleton manager ensuring single Console instance across application."""
    
    _instance = None
    _console = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @property 
    def console(self):
        if self._console is None:
            self._console = self._create_console()
        return self._console
    
    def _create_console(self):
        """Create Rich Console with Content Tamer AI theme."""
        theme = Theme({
            "info": "blue",
            "warning": "yellow",
            "error": "red bold", 
            "success": "green bold",
            "progress": "cyan"
        })
        
        return Console(
            theme=theme,
            force_terminal=None,      # Auto-detect
            width=None,              # Auto-detect  
            legacy_windows=False     # Use modern features
        )
```

## **Implementation Guidelines**

### **✅ DO: Rich-First Development with Smart Emoji Usage**
1. **Always use Rich Console** for user-facing output
2. **Use smart emoji detection** - `console.options.encoding == 'utf-8'`
3. **Provide ASCII fallbacks** for non-UTF-8 terminals
4. **Trust Rich for colors and styling** (always work across terminals)
5. **Use Rich components** (Panel, Table, Progress) for consistent UI

### **❌ DON'T: Brittle Anti-Patterns**
1. **Don't use direct print()** for user-facing messages
2. **Don't manually check legacy_windows** in every method
3. **Don't create excessive if/else** emoji checking constructs
4. **Don't remove emojis completely** to "solve" encoding issues
5. **Don't over-mock in tests** - use Rich test framework instead

### **Testing Rich UI Components**
1. **Use RichTestCase** for proper console isolation
2. **Test UI behavior** through captured output analysis
3. **Isolate Rich components** from business logic in tests
4. **Validate consistent styling** across all UI components

These patterns ensure **beautiful, interactive user experiences** that **automatically adapt** to terminal capabilities while maintaining **clean architectural boundaries** and **reliable testing patterns**.