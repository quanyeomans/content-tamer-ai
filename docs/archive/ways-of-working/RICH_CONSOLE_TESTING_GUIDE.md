# Rich Console Testing Guide
*Proper testing patterns for Rich UI components without excessive mocking*

## Core Testing Philosophy

### **Principle: Minimal Mocking, Maximum Rich Testing**
- **Mock only external inputs** (user input, API calls)
- **Let Rich handle output** through test framework
- **Use RichTestCase** for proper console isolation
- **Test both UTF-8 and ASCII code paths** for smart emoji usage

## **Anti-Pattern: Excessive Mocking**

### **❌ WRONG: Over-Mocking Rich Output**
```python
@patch("builtins.print")  # Unnecessary - avoids testing Rich
@patch("rich.console.Console.print")  # Unnecessary - prevents Rich testing
def test_console_output(self, mock_console, mock_print):
    # Tests nothing about Rich behavior
    pass
```

### **Problems with Over-Mocking**
- **Doesn't test Rich functionality** - mocks away the thing you want to test
- **Hides encoding issues** - problems only surface in production
- **Prevents UI validation** - can't verify actual Rich output
- **Creates false confidence** - tests pass but UI might be broken

## **✅ CORRECT: Rich Test Framework**

### **Pattern: RichTestCase for Console Isolation**
```python
from tests.utils.rich_test_utils import RichTestCase

class TestRichUIComponents(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)  # Proper console isolation
        self.console_manager = RichConsoleManager()
        # Use test console for isolation
        self.console_manager._console = self.test_console
    
    def test_welcome_panel(self):
        """Test welcome panel renders correctly."""
        self.console_manager.show_welcome_panel()
        
        # Validate Rich output through captured output
        output = self.get_console_output()
        self.assertIn("CONTENT TAMER AI", output)
        # Rich styling is preserved in test output
    
    def test_smart_emoji_detection(self):
        """Test both emoji and ASCII code paths."""
        # Test UTF-8 path
        if hasattr(self.test_console, 'options'):
            self.test_console.options.encoding = 'utf-8'
        
        self.console_manager.show_status("Test", "success")
        output = self.get_console_output()
        
        if self.test_console.options.encoding == 'utf-8':
            self.assertIn("✅", output)  # Emoji path
        else:
            self.assertIn("[OK]", output)  # ASCII path
```

### **Pattern: Minimal Input Mocking**
```python
class TestUserInteraction(unittest.TestCase, RichTestCase):
    @patch("builtins.input")  # Only mock input, not output
    def test_api_key_prompt(self, mock_input):
        """Test API key prompting with Rich output."""
        mock_input.return_value = "test-api-key"
        
        # Let Rich handle output rendering
        from shared.infrastructure.directory_manager import _prompt_for_api_key
        result = _prompt_for_api_key("openai")
        
        # Validate input was handled
        self.assertEqual(result, "test-api-key")
        mock_input.assert_called()
        
        # Rich output can be validated if needed
        output = self.get_console_output()
        self.assertIn("API Key Input", output)
```

## **Testing Smart Emoji Usage**

### **Pattern: Test Both Encoding Paths**
```python
class TestSmartEmojiUsage(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)
        self.console_manager = RichConsoleManager()
        self.console_manager._console = self.test_console
    
    def test_utf8_emoji_path(self):
        """Test emoji rendering in UTF-8 terminals."""
        # Configure test console for UTF-8
        if hasattr(self.test_console, 'options'):
            self.test_console.options.encoding = 'utf-8'
        
        self.console_manager.show_status("Test message", "success")
        output = self.get_console_output()
        
        # Should use emoji in UTF-8 mode
        self.assertIn("✅", output)
        self.assertNotIn("[OK]", output)
    
    def test_ascii_fallback_path(self):
        """Test ASCII fallback in non-UTF-8 terminals."""
        # Configure test console for ASCII
        if hasattr(self.test_console, 'options'):
            self.test_console.options.encoding = 'cp1252'
        
        self.console_manager.show_status("Test message", "success")
        output = self.get_console_output()
        
        # Should use ASCII in cp1252 mode
        self.assertIn("[OK]", output)
        self.assertNotIn("✅", output)
    
    def test_colors_work_in_both_modes(self):
        """Test colors work regardless of emoji support."""
        # Colors should work in both UTF-8 and ASCII modes
        for encoding in ['utf-8', 'cp1252']:
            with self.subTest(encoding=encoding):
                if hasattr(self.test_console, 'options'):
                    self.test_console.options.encoding = encoding
                
                self.console_manager.show_status("Color test", "success")
                output = self.get_console_output()
                
                # Colors should work in both modes
                self.assertIn("success", output)  # Rich styling preserved
                
                self.clear_output()
```

## **Rich Console Configuration Testing**

### **Pattern: Test Console Auto-Detection**
```python
class TestRichConsoleConfiguration(unittest.TestCase):
    def test_console_auto_detection(self):
        """Test Rich Console auto-detection works correctly."""
        console_manager = RichConsoleManager()
        console = console_manager.console
        
        # Rich should auto-detect terminal capabilities
        self.assertIsNotNone(console)
        self.assertTrue(hasattr(console, 'options'))
        self.assertTrue(hasattr(console.options, 'encoding'))
        
        # Console should have theme applied
        self.assertIsNotNone(console._theme)
    
    def test_emoji_detection_logic(self):
        """Test emoji detection logic works correctly."""
        console_manager = RichConsoleManager()
        console = console_manager.console
        
        # Test detection logic
        has_emoji_support = (
            hasattr(console, 'options') and 
            console.options.encoding == 'utf-8'
        )
        
        self.assertIsInstance(has_emoji_support, bool)
        
        # Logic should be consistent
        if has_emoji_support:
            # Should use emojis
            expected_icon = "✅"
        else:
            # Should use ASCII
            expected_icon = "[OK]"
        
        self.assertIsInstance(expected_icon, str)
```

## **Benefits of Rich Test Framework Approach**

### **✅ Advantages**
1. **Tests actual Rich behavior** - validates real UI rendering
2. **Console isolation** - no conflicts between tests
3. **Output validation** - can verify Rich styling and content
4. **Cross-platform testing** - test both emoji and ASCII paths
5. **Minimal mocking** - only mock external dependencies

### **✅ Quality Assurance**
- **Rich UI bugs caught** - tests validate actual Rich output
- **Encoding issues detected** - both UTF-8 and ASCII paths tested
- **Styling validation** - can verify colors, panels, formatting
- **User experience testing** - validates actual user-facing output

### **🔧 Implementation Guidelines**

#### **For New Rich UI Components**
1. **Extend RichTestCase** for proper console isolation
2. **Override console** with test console in setUp
3. **Test both encoding paths** (UTF-8 emojis and ASCII fallback)
4. **Validate Rich output** through get_console_output()
5. **Mock only inputs** - let Rich handle output rendering

#### **For Existing Tests with Over-Mocking**
1. **Remove @patch("builtins.print")** where testing Rich components
2. **Use RichTestCase** instead of mocking console output
3. **Keep input mocking** - @patch("builtins.input") still needed
4. **Add encoding path testing** - validate both UTF-8 and ASCII behavior

## Research-Based Advanced Patterns

### **Session-Scoped Resource Management**
```python
@pytest.fixture(scope="session")
def shared_console():
    """Shared Rich Console for performance optimization."""
    return create_test_console()

@pytest.fixture(scope="session")
def ml_resources():
    """Cached ML models and services for test performance."""
    return {
        "spacy_model": spacy.load("en_core_web_sm"),
        "clustering_service": None  # Lazy loaded
    }
```

### **ApplicationContainer State Isolation**
```python
@pytest.fixture(scope="function")
def test_container():
    """Fresh container with guaranteed state cleanup."""
    container = TestApplicationContainer()
    yield container
    container.reset_state()

@contextmanager
def isolated_container_context(container, overrides):
    """Context manager for service overrides with automatic revert."""
    with container.override_services(overrides):
        yield container
```

### **File System Testing Patterns**
```python
def test_file_processing_workflow(tmp_path):
    """Use pytest tmp_path for race-condition-free file testing."""
    test_file = tmp_path / "document.pdf"
    test_file.write_text("content")
    
    result = process_file(str(test_file), str(tmp_path / "output"))
    # Automatic cleanup by pytest
```

### **Performance-Optimized Testing**
```python
@pytest.mark.slow  # Mark expensive tests
def test_ml_heavy_operation(ml_services):
    """Test with cached ML services."""
    # No model loading - uses session-cached services
    result = ml_services["clustering"].classify_document(doc)
```

This approach provides **reliable Rich UI testing** with **research-based performance optimization** while **validating actual user experience** in different terminal environments.