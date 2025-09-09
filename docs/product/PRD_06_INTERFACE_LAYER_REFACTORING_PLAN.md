# Interface Layer Refactoring Plan
*Systematic extraction of interface layer to support persona-driven architecture*

## Overview

This plan outlines the step-by-step refactoring to extract a clean interface layer from the current codebase. The refactoring will separate human interactive interfaces from programmatic and protocol-based interfaces, enabling better support for automation users and future integration patterns.

## Current State Analysis

### Problem Files Identified

#### 1. `src/core/cli_parser.py` (768 lines)
**Issues**:
- Mixed responsibilities: argument parsing, expert mode prompting, command execution
- Tight coupling between UI logic and business logic
- No clean separation for automation users

**Functions to Extract**:
- `parse_arguments()` → Pure argument parsing
- `setup_environment_and_args()` → Interactive setup logic
- Expert mode integration → Human interface layer
- Command execution logic → Application orchestration

#### 2. `src/utils/expert_mode.py` (461 lines)
**Issues**:
- UI prompting mixed with configuration logic
- No programmatic access to configuration capabilities
- Tight coupling to CLI argument system

**Classes to Extract**:
- `ExpertModePrompter` → Human interface for configuration
- Configuration logic → Programmatic configuration management
- Argument conversion → Interface translation layer

#### 3. `src/core/cli_handler.py` (768+ lines)
**Issues**:
- Command handling mixed with Rich UI management
- Dependency management scattered with command execution
- No clean programmatic access to individual functions

**Services to Extract**:
- Rich UI commands → Human interface layer
- Headless operations → Programmatic interface layer
- Model management → Domain service layer

### Dependencies Analysis

#### Current Import Chains
```python
# Problematic import chains that need breaking:
cli_parser.py → expert_mode.py → rich components
cli_handler.py → multiple utils → display managers
application.py → multiple interfaces → business logic
```

#### Target Clean Interfaces
```python
# Clean separation targets:
interfaces/human/ → Only Rich UI and user interaction
interfaces/programmatic/ → Only business logic, no UI
domains/ → Pure business logic, no interface dependencies
shared/ → Utilities usable across all layers
```

## Interface Layer Architecture

### Target Structure
```
src/interfaces/
├─ __init__.py
├─ human/
│  ├─ __init__.py
│  ├─ interactive_cli.py         # Main human CLI interface
│  ├─ configuration_wizard.py    # Expert mode functionality
│  ├─ rich_console_manager.py    # Centralized Rich UI
│  ├─ progress_orchestrator.py   # Human-friendly progress
│  └─ help_system.py            # Context-sensitive help
├─ programmatic/
│  ├─ __init__.py
│  ├─ cli_arguments.py          # Pure argument parsing
│  ├─ library_interface.py      # Python API
│  ├─ configuration_manager.py  # Headless configuration
│  └─ structured_output.py      # JSON/XML output
└─ protocols/
   ├─ __init__.py
   ├─ mcp_server.py            # Claude MCP integration
   └─ future_apis/             # Extension point
      ├─ __init__.py
      ├─ rest_api.py           # Future REST API
      └─ graphql_api.py        # Future GraphQL API
```

### Interface Contracts

#### Human Interface Contract
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from rich.console import Console

class HumanInterface(ABC):
    """Contract for all human-facing interfaces."""
    
    @abstractmethod
    def setup_console(self) -> Console:
        """Initialize Rich Console for human interaction."""
        pass
    
    @abstractmethod
    def show_progress(self, stage: str, current: int, total: int) -> None:
        """Display human-friendly progress information."""
        pass
    
    @abstractmethod
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Show user-friendly error message with guidance."""
        pass
    
    @abstractmethod
    def prompt_user_choice(self, message: str, choices: list) -> str:
        """Interactive user prompting with validation."""
        pass
```

#### Programmatic Interface Contract
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    success: bool
    files_processed: int
    errors: List[str]
    output_location: str
    metadata: Dict[str, Any]

class ProgrammaticInterface(ABC):
    """Contract for automation and scripting interfaces."""
    
    @abstractmethod
    def process_documents(self, config: Dict[str, Any]) -> ProcessingResult:
        """Headless document processing with structured result."""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration returning list of errors."""
        pass
    
    @abstractmethod
    def get_progress_status(self) -> Dict[str, Any]:
        """Return machine-readable progress information."""
        pass
```

## Phase 1: Foundation Setup

### Step 1: Create Interface Layer Structure

#### Create Directory Structure
```bash
mkdir -p src/interfaces/{human,programmatic,protocols/future_apis}
touch src/interfaces/__init__.py
touch src/interfaces/human/__init__.py
touch src/interfaces/programmatic/__init__.py
touch src/interfaces/protocols/__init__.py
touch src/interfaces/protocols/future_apis/__init__.py
```

#### Create Base Interface Contracts
**File: `src/interfaces/__init__.py`**
```python
"""
Interface Layer - Clean separation of user interaction patterns.

Provides persona-driven interfaces for:
- Human users (interactive CLI, Rich UI)
- Automation users (headless operation, structured output)
- Integration users (protocols, APIs)
"""

from .human import HumanInterface
from .programmatic import ProgrammaticInterface

__all__ = ['HumanInterface', 'ProgrammaticInterface']
```

### Step 2: Extract Pure Argument Parsing

#### Create `src/interfaces/programmatic/cli_arguments.py`
```python
"""
Pure CLI Argument Parsing - No UI Dependencies

Provides clean argument parsing for automation and programmatic use.
Separated from human interaction patterns for headless operation.
"""

import argparse
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class ParsedArguments:
    """Structured argument data without UI coupling."""
    input_dir: Optional[str]
    output_dir: Optional[str]
    provider: str
    model: Optional[str]
    api_key: Optional[str]
    ocr_language: str
    quiet_mode: bool
    organization_enabled: Optional[bool]
    ml_level: int
    # ... all other arguments

class PureCLIParser:
    """Argument parser without UI dependencies."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create parser with all arguments but no UI logic."""
        # Extract parser creation from cli_parser.py
        # Remove all UI-related code, keep pure argument definitions
        pass
    
    def parse_args(self, args: Optional[List[str]] = None) -> ParsedArguments:
        """Parse arguments returning structured data."""
        # Parse and return clean dataclass
        pass
    
    def validate_args(self, args: ParsedArguments) -> List[str]:
        """Validate arguments returning error list."""
        # Pure validation logic without UI
        pass
```

### Step 3: Create Human Interface Layer

#### Create `src/interfaces/human/interactive_cli.py`
```python
"""
Interactive CLI - Rich Human Interface

Provides guided navigation, expert mode, and Rich UI components
for human users. Depends on programmatic interface for business logic.
"""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm

from ..programmatic.cli_arguments import PureCLIParser, ParsedArguments
from ..programmatic.configuration_manager import ConfigurationManager
from .configuration_wizard import ExpertConfigurationWizard
from .rich_console_manager import RichConsoleManager

class InteractiveCLI:
    """Main human interface for Content Tamer AI."""
    
    def __init__(self):
        self.console_manager = RichConsoleManager()
        self.parser = PureCLIParser()
        self.config_manager = ConfigurationManager()
        self.wizard = ExpertConfigurationWizard(self.console_manager)
    
    def run_interactive_setup(self) -> ParsedArguments:
        """Main interactive setup flow."""
        # Determine if user wants expert mode or quick start
        # Use wizard for expert mode, smart defaults for quick start
        # Return ParsedArguments for business logic processing
        pass
    
    def show_welcome_screen(self) -> None:
        """Display welcome and mode selection."""
        # Rich UI welcome screen
        pass
    
    def handle_guided_navigation(self) -> ParsedArguments:
        """Quick start with guided prompts."""
        # Simple guided flow for casual users
        pass
```

## Phase 2: Migration Strategy

### Step 1: Gradual Function Extraction

#### Migration Pattern
```python
# BEFORE: cli_parser.py
def setup_environment_and_args():
    # Complex mixed logic
    expert_args = prompt_expert_mode_if_needed()  # UI logic
    args = parse_arguments()  # Parsing logic
    if args.organize and args.no_organize:       # Validation logic
        print("Error: Cannot specify both...")   # UI logic
        sys.exit(1)                              # Control logic
    # ... more mixed responsibilities

# AFTER: Separated responsibilities
# interfaces/programmatic/cli_arguments.py
class PureCLIParser:
    def validate_args(self, args: ParsedArguments) -> List[str]:
        errors = []
        if args.organize and args.no_organize:
            errors.append("Cannot specify both --organize and --no-organize")
        return errors

# interfaces/human/interactive_cli.py  
class InteractiveCLI:
    def handle_validation_errors(self, errors: List[str]) -> None:
        for error in errors:
            self.console.print(f"❌ {error}", style="red")
        
# orchestration/application_kernel.py
class ApplicationKernel:
    def execute_with_args(self, args: ParsedArguments) -> None:
        # Pure business logic execution
```

### Step 2: Dependency Injection Integration

#### Update ApplicationContainer
```python
# core/application_container.py (enhanced)
class ApplicationContainer:
    """Enhanced container supporting interface layer."""
    
    def create_human_interface(self) -> 'InteractiveCLI':
        """Create human interface with all dependencies."""
        return InteractiveCLI()
    
    def create_programmatic_interface(self) -> 'ProgrammaticInterface':
        """Create headless interface for automation."""
        return ProgrammaticInterface()
    
    def create_application_kernel(self) -> 'ApplicationKernel':
        """Create application orchestration kernel."""
        return ApplicationKernel(
            content_service=self.create_content_service(),
            ai_service=self.create_ai_service(),
            organization_service=self.create_organization_service()
        )
```

### Step 3: Backwards Compatibility

#### Create Compatibility Layer
```python
# core/compatibility_layer.py (enhanced)
class CLICompatibilityLayer:
    """Maintains backwards compatibility during refactoring."""
    
    def __init__(self):
        self.new_interface = InteractiveCLI()
        self.programmatic_interface = ProgrammaticInterface()
    
    def legacy_cli_entry_point(self) -> None:
        """Existing main() function compatibility."""
        # Route to new interface based on arguments
        if self._is_automation_context():
            result = self.programmatic_interface.process_documents(config)
            self._output_legacy_format(result)
        else:
            self.new_interface.run_interactive_setup()
```

## Phase 3: Detailed Implementation

### Step 1: Rich Console Management

#### Create `src/interfaces/human/rich_console_manager.py`
```python
"""
Centralized Rich Console Management

Provides singleton Rich Console management specifically for human interfaces.
Ensures consistent UI experience across all human-facing components.
"""

from typing import Optional
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.progress import Progress, TaskID

class RichConsoleManager:
    """Centralized Rich Console for human interfaces."""
    
    _instance: Optional['RichConsoleManager'] = None
    _console: Optional[Console] = None
    
    def __new__(cls) -> 'RichConsoleManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def console(self) -> Console:
        """Get or create Rich Console instance."""
        if self._console is None:
            self._console = self._create_console()
        return self._console
    
    def _create_console(self) -> Console:
        """Create Rich Console with Content Tamer AI theme."""
        theme = Theme({
            "info": "blue",
            "warning": "yellow", 
            "error": "red",
            "success": "green",
            "progress": "cyan"
        })
        return Console(theme=theme, force_terminal=True)
    
    def create_progress_display(self) -> Progress:
        """Create consistent progress display for human interface."""
        return Progress(console=self.console, transient=True)
    
    def show_welcome_panel(self) -> None:
        """Standard welcome display."""
        panel = Panel(
            "🎯 CONTENT TAMER AI\n\nIntelligent document processing with AI-powered organization",
            title="Welcome",
            border_style="blue"
        )
        self.console.print(panel)
```

### Step 2: Configuration Management

#### Create `src/interfaces/programmatic/configuration_manager.py`
```python
"""
Headless Configuration Management

Provides configuration loading and management without UI dependencies.
Supports environment variables, config files, and programmatic configuration.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import os
import json
from pathlib import Path

@dataclass
class ProcessingConfiguration:
    """Complete processing configuration structure."""
    input_dir: str
    output_dir: str
    provider: str
    model: Optional[str]
    api_key: Optional[str]
    ocr_language: str
    organization_enabled: bool
    ml_level: int
    quiet_mode: bool
    verbose_mode: bool
    # ... all configuration options

class ConfigurationManager:
    """Headless configuration management."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".content-tamer"
        self.config_file = self.config_dir / "config.json"
    
    def load_configuration(self) -> ProcessingConfiguration:
        """Load configuration from all sources with precedence."""
        # 1. Default values
        config = self._get_default_configuration()
        
        # 2. Configuration file
        if self.config_file.exists():
            config = self._merge_config_file(config)
        
        # 3. Environment variables
        config = self._merge_environment_variables(config)
        
        return config
    
    def save_configuration(self, config: ProcessingConfiguration) -> None:
        """Save configuration to persistent storage."""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(asdict(config), f, indent=2)
    
    def validate_configuration(self, config: ProcessingConfiguration) -> List[str]:
        """Validate configuration returning list of errors."""
        errors = []
        
        # Validate paths
        if not Path(config.input_dir).exists():
            errors.append(f"Input directory does not exist: {config.input_dir}")
        
        # Validate AI provider settings
        if not config.api_key:
            env_key = f"{config.provider.upper()}_API_KEY"
            if not os.getenv(env_key):
                errors.append(f"API key required for {config.provider}")
        
        # Additional validations...
        
        return errors
```

### Step 3: Library Interface

#### Create `src/interfaces/programmatic/library_interface.py`
```python
"""
Python Library Interface

Provides clean Python API for programmatic use cases.
Enables Content Tamer AI to be used as a library in other applications.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from pathlib import Path
import asyncio

from .configuration_manager import ProcessingConfiguration, ConfigurationManager
from ...orchestration.application_kernel import ApplicationKernel

@dataclass
class ProcessingResult:
    """Result of document processing operation."""
    success: bool
    files_processed: int
    files_failed: int
    output_directory: str
    errors: List[str]
    metadata: Dict[str, Any]

class ContentTamerAPI:
    """Main Python API for Content Tamer AI."""
    
    def __init__(self, config: Optional[ProcessingConfiguration] = None):
        """Initialize API with optional configuration."""
        self.config_manager = ConfigurationManager()
        self.config = config or self.config_manager.load_configuration()
        self.kernel = ApplicationKernel()
    
    def process_documents(
        self, 
        input_dir: str,
        output_dir: str,
        provider: str = "openai",
        **kwargs
    ) -> ProcessingResult:
        """Process documents with specified configuration."""
        # Update configuration
        config = self.config
        config.input_dir = input_dir
        config.output_dir = output_dir
        config.provider = provider
        
        # Apply kwargs
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Validate configuration
        errors = self.config_manager.validate_configuration(config)
        if errors:
            return ProcessingResult(
                success=False, 
                files_processed=0,
                files_failed=0,
                output_directory="",
                errors=errors,
                metadata={}
            )
        
        # Execute processing
        return self.kernel.execute_processing(config)
    
    async def process_documents_async(
        self,
        input_dir: str, 
        output_dir: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        **kwargs
    ) -> ProcessingResult:
        """Async document processing with progress callbacks."""
        # Implement async processing with callbacks
        pass
    
    def get_supported_providers(self) -> List[str]:
        """Get list of supported AI providers."""
        return self.kernel.get_ai_providers()
    
    def get_supported_models(self, provider: str) -> List[str]:
        """Get supported models for a provider."""
        return self.kernel.get_provider_models(provider)
    
    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Validate API key for a provider."""
        return self.kernel.validate_provider_api_key(provider, api_key)

# Convenience function for simple use cases
def process_documents_simple(
    input_dir: str,
    output_dir: str, 
    api_key: str,
    provider: str = "openai"
) -> ProcessingResult:
    """Simple function interface for basic processing."""
    api = ContentTamerAPI()
    return api.process_documents(
        input_dir=input_dir,
        output_dir=output_dir,
        provider=provider,
        api_key=api_key
    )
```

## Testing Strategy

### Unit Tests for Interface Layer

#### Human Interface Testing
```python
# tests/interfaces/human/test_interactive_cli.py
import unittest
from unittest.mock import Mock, patch
from src.interfaces.human.interactive_cli import InteractiveCLI

class TestInteractiveCLI(unittest.TestCase):
    
    def setUp(self):
        self.cli = InteractiveCLI()
    
    def test_welcome_screen_display(self):
        """Test welcome screen shows correctly."""
        with patch.object(self.cli.console_manager.console, 'print') as mock_print:
            self.cli.show_welcome_screen()
            mock_print.assert_called()
    
    def test_expert_mode_detection(self):
        """Test expert mode vs quick start detection."""
        # Test expert mode selection
        with patch('rich.prompt.Prompt.ask', return_value='e'):
            result = self.cli.run_interactive_setup()
            self.assertIsInstance(result, ParsedArguments)
```

#### Programmatic Interface Testing
```python
# tests/interfaces/programmatic/test_library_interface.py
import unittest
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from src.interfaces.programmatic.library_interface import ContentTamerAPI, ProcessingResult

class TestContentTamerAPI(unittest.TestCase):
    
    def setUp(self):
        self.api = ContentTamerAPI()
    
    def test_process_documents_with_valid_config(self):
        """Test successful document processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            
            # Create test file
            (input_dir / "test.pdf").touch()
            
            with patch.object(self.api.kernel, 'execute_processing') as mock_execute:
                mock_execute.return_value = ProcessingResult(
                    success=True,
                    files_processed=1,
                    files_failed=0,
                    output_directory=str(output_dir),
                    errors=[],
                    metadata={}
                )
                
                result = self.api.process_documents(
                    input_dir=str(input_dir),
                    output_dir=str(output_dir),
                    api_key="test-key"
                )
                
                self.assertTrue(result.success)
                self.assertEqual(result.files_processed, 1)
```

### Integration Tests
```python
# tests/interfaces/test_interface_integration.py
class TestInterfaceLayerIntegration(unittest.TestCase):
    """Test interaction between interface layers and core business logic."""
    
    def test_human_to_programmatic_handoff(self):
        """Test that human interface correctly calls programmatic interface."""
        # Test the handoff between interactive setup and headless execution
        pass
    
    def test_configuration_consistency(self):
        """Test configuration consistency across interfaces."""
        # Ensure human and programmatic interfaces use same configuration format
        pass
```

## Migration Checklist

### Pre-Migration Setup
- [ ] Create interface layer directory structure
- [ ] Set up base interface contracts
- [ ] Create compatibility layer for backwards compatibility
- [ ] Write comprehensive tests for new interface components

### Phase 1: Extract Pure Parsing
- [ ] Create `PureCLIParser` without UI dependencies
- [ ] Extract argument validation logic
- [ ] Create `ParsedArguments` dataclass
- [ ] Test argument parsing independently

### Phase 2: Create Human Interface
- [ ] Extract expert mode UI into `ConfigurationWizard`
- [ ] Create `InteractiveCLI` with Rich UI integration
- [ ] Implement guided navigation for casual users
- [ ] Test human interface components

### Phase 3: Create Programmatic Interface
- [ ] Implement headless `ConfigurationManager`
- [ ] Create `ContentTamerAPI` library interface
- [ ] Add structured output formats (JSON, XML)
- [ ] Test programmatic interfaces

### Phase 4: Integration & Migration
- [ ] Update `ApplicationContainer` for interface layer
- [ ] Migrate existing entry points to use new interfaces
- [ ] Update all imports and dependencies
- [ ] Comprehensive integration testing

### Phase 5: Cleanup
- [ ] Remove deprecated code from original files
- [ ] Update documentation and examples
- [ ] Verify backwards compatibility
- [ ] Performance testing and optimization

## Success Criteria

### Technical Success
- [ ] All existing functionality works through new interface layer
- [ ] No breaking changes for existing users
- [ ] Test coverage maintained at 90%+
- [ ] Performance regression < 5%

### Persona Success
- [ ] **Human Users**: Improved UI consistency and experience
- [ ] **Automation Users**: Clean headless operation capability
- [ ] **Integration Users**: Clear API interfaces for extension

### Architectural Success
- [ ] Clear separation of interface concerns
- [ ] Reduced coupling between UI and business logic
- [ ] Extensible interface patterns for future needs
- [ ] Maintainable and testable interface code

---

*This plan provides a systematic approach to extracting the interface layer while maintaining the high quality standards and security compliance established in the existing codebase.*