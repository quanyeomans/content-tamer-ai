# Proven Patterns

## Architecture Patterns

### ApplicationContainer (Dependency Injection)
```python
# src/core/application_container.py
class ApplicationContainer:
    """Central DI container for all services."""
    
    def create_display_manager(self, options=None):
        return UnifiedDisplayManager(
            console=self.get_console(),
            quiet_mode=options.get('quiet', False)
        )
    
    def create_service(self, target_folder=None):
        return ServiceClass(
            display_manager=self.create_display_manager(),
            file_manager=self.create_file_manager(),
            config=self.config
        )

# In tests:
class TestApplicationContainer(ApplicationContainer):
    """Test container with mocked external services."""
    def create_ai_provider(self):
        return MockAIProvider()  # Only mock external APIs
```

### Domain Service Pattern
```python
# Clean domain boundaries - no cross-imports
src/domains/
├── content/           # Document processing
│   ├── extraction_service.py
│   ├── enhancement_service.py
│   └── metadata_service.py
├── ai_integration/    # AI provider management  
│   ├── provider_service.py
│   └── request_service.py
└── organization/      # Document organization
    ├── clustering_service.py
    └── organization_service.py

# Each domain service follows:
class DomainService:
    def __init__(self, dependencies_from_container):
        self.display = dependencies_from_container.display_manager
        self.logger = logging.getLogger(__name__)
```

### Persona-Driven Interfaces
```python
src/interfaces/
├── human/           # Rich CLI for humans
│   └── rich_interface.py
├── programmatic/    # Library API for scripts
│   └── api_interface.py  
└── protocols/       # MCP server for Claude
    └── mcp_server.py
```

## Testing Patterns

### RichTestCase Pattern
```python
from tests.utils.rich_test_utils import RichTestCase

class TestRichComponent(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)  # Sets up console capture
        self.display = self.test_container.create_display_manager()
    
    def test_progress_display(self):
        self.display.show_progress("Testing")
        output = self.get_console_output()
        self.assertIn("Testing", output)
```

### Minimal Mocking Strategy
```python
# GOOD - Only mock external services
@patch('openai.ChatCompletion.create')
def test_ai_integration(self, mock_openai):
    mock_openai.return_value = {"choices": [{"message": {"content": "response"}}]}
    # Test with real file operations
    with tempfile.TemporaryDirectory() as tmpdir:
        result = service.process(os.path.join(tmpdir, "test.pdf"))

# BAD - Don't mock internal components
@patch('src.domains.content.extraction_service')  # DON'T DO THIS
```

### Test Organization
```python
tests/
├── unit/              # 70% - Business logic
│   ├── domains/       # Mirror src structure
│   └── shared/
├── integration/       # 25% - Component boundaries
│   └── cross_domain/  # Service interactions
└── e2e/              # 5% - User journeys
    └── workflows/     # Complete workflows
```

## Code Quality Patterns

### Lazy Logging Pattern
```python
# Use % formatting for lazy evaluation
logger.info("Processing %d documents from %s", count, path)
logger.error("Failed to process %s: %s", filename, error)

# NOT f-strings (causes W1203)
logger.info(f"Processing {count} documents")  # BAD
```

### Type Hints Pattern
```python
from typing import Dict, List, Optional, Any

def process_documents(
    documents: List[str],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process documents with optional configuration.
    
    Args:
        documents: List of document paths
        options: Optional processing configuration
        
    Returns:
        Dictionary with results and metadata
    """
    options = options or {}
    return {"processed": len(documents), "options": options}
```

### Error Handling Pattern
```python
class ServiceError(Exception):
    """Base exception for service errors."""
    pass

def process_with_graceful_errors(self, data):
    try:
        # Progress indication
        progress_id = self.display.start_progress("Processing")
        result = self._internal_process(data)
        self.display.success("Processing complete")
        return result
    except ValidationError as e:
        # User-friendly error message
        self.display.error("Invalid input: %s", str(e))
        raise ServiceError("Please check your input format") from e
    except Exception as e:
        # Log technical details, show simple message to user
        logger.error("Processing failed: %s", sanitize_error(e))
        self.display.error("Processing failed. Check logs for details.")
        raise ServiceError("Processing failed") from e
    finally:
        self.display.finish_progress(progress_id)
```

## UI/Display Patterns

### UnifiedDisplayManager Usage
```python
# Always use UnifiedDisplayManager for output
from shared.display import UnifiedDisplayManager

class Service:
    def __init__(self, display_manager: UnifiedDisplayManager):
        self.display = display_manager
    
    def process(self):
        # Progress tracking
        progress_id = self.display.start_progress("Processing files")
        
        # Status messages
        self.display.info("Starting processing")
        
        # Errors (never raw logging to console)
        self.display.error("Failed: %s", error_msg)
        
        # Success
        self.display.success("✓ Complete")
```

### Smart Emoji Handling
```python
# Let SmartEmojiHandler handle cross-platform compatibility
emoji = SmartEmojiHandler(console)
success_icon = emoji.get("success")  # ✓ on Windows, ✅ on Unix
```

## File Operation Patterns

### Safe File Operations
```python
from shared.file_operations import SafeFileManager

class DocumentProcessor:
    def __init__(self, file_manager: SafeFileManager):
        self.file_manager = file_manager
    
    def process_document(self, path: str):
        # Validate path security
        if not self.file_manager.validate_path(path):
            raise ValueError("Invalid path")
        
        # Safe move with conflict resolution
        new_path = self.file_manager.safe_move(
            path, 
            target_dir,
            handle_conflicts=True
        )
```

### Temporary File Pattern
```python
# Always use temp directories for testing
import tempfile

def test_file_processing():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.pdf")
        # Create test file
        with open(test_file, 'wb') as f:
            f.write(b"test content")
        
        # Test with real file operations
        result = processor.process(test_file)
        assert os.path.exists(result.output_path)
```