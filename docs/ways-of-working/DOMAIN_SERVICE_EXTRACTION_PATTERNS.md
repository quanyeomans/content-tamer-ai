# Domain Service Extraction Patterns
*Architectural patterns for extracting clean domain services from monolithic code*

## Overview

This development sprint revealed **systematic approaches to domain service extraction** that create clean boundaries while maintaining functionality. These patterns enable independent development within domain contexts.

## Core Pattern: Domain Boundary Identification

### **Pattern Definition**
Identify natural domain boundaries based on **business functionality** rather than technical implementation details.

```
domains/
├─ content/              # Document processing and analysis
├─ ai_integration/       # Provider management and AI interactions
└─ organization/         # Document clustering and learning
```

### **Domain Identification Criteria**

#### **✅ Good Domain Boundaries**
- **Business cohesion**: Related business concepts grouped together
- **Single responsibility**: Domain handles one area of business logic
- **Independent evolution**: Domain can change without affecting others
- **Clear interfaces**: Well-defined inputs/outputs

#### **❌ Poor Domain Boundaries**
- **Technical grouping**: "All database code" or "All API code"
- **Cross-cutting concerns**: Logging, authentication scattered across domains
- **Implementation coupling**: Domains that can't change independently

### **Domain Extraction Process**

#### **1. Identify Business Capabilities**
```python
# BEFORE: Monolithic ai_providers.py (547 lines)
# Mixed concerns: OpenAI, Claude, Gemini, model management, hardware detection

# ANALYZE business capabilities:
# - Provider management (create, configure, validate providers)
# - Model selection (hardware detection, compatibility)
# - Request handling (API calls, retry logic, error handling)

# AFTER: Clean domain services
domains/ai_integration/
├─ provider_service.py      # Provider management capability
├─ model_service.py         # Model selection capability  
├─ request_service.py       # Request handling capability
└─ ai_integration_service.py # Domain orchestration
```

#### **2. Extract Services with Clean Interfaces**
```python
# PATTERN: Domain service with clear responsibility
class ContentService:
    """Orchestrates all content domain operations."""
    
    def __init__(self):
        # Compose domain capabilities
        self.extraction_service = ExtractionService()
        self.enhancement_service = EnhancementService()
        self.metadata_service = MetadataService()
    
    def process_document_complete(self, file_path: str) -> dict:
        # Orchestrate domain workflow
        extracted = self.extraction_service.extract_from_file(file_path)
        enhanced = self.enhancement_service.enhance_content(extracted)
        metadata = self.metadata_service.analyze_document(file_path, extracted)
        
        return {"extraction": extracted, "enhancement": enhanced, "metadata": metadata}
```

#### **3. Eliminate Cross-Domain Dependencies**
```python
# WRONG: Domains depending on each other directly
class ContentService:
    def __init__(self):
        self.ai_service = AIIntegrationService()  # Cross-domain dependency

# CORRECT: Dependencies injected through orchestration
class ApplicationKernel:
    def __init__(self, container):
        self.content_service = container.create_content_service()
        self.ai_service = container.create_ai_integration_service()
    
    def process_with_ai(self, file_path):
        # Orchestration coordinates domain services
        content_result = self.content_service.process_document_complete(file_path)
        ai_result = self.ai_service.generate_filename_with_ai(
            content_result["ai_ready_content"], 
            original_filename
        )
```

## **Shared Service Consolidation Patterns**

### **Pattern: Cross-Cutting Concern Extraction**
**Problem**: File operations, display logic, configuration scattered across domains
**Solution**: Extract to shared services consumed by all domains

```python
# BEFORE: File operations duplicated across 6 files
class FileManager:         # in file_organizer.py
class DirectoryManager:    # in directory_manager.py  
class FileProcessor:       # in file_processor.py
# ... each with similar but different file operation methods

# AFTER: Single shared service
shared/file_operations/
├─ safe_file_manager.py    # Atomic operations, locking, retry
├─ path_validator.py       # Security validation, cross-platform paths
└─ content_sanitizer.py    # Input validation and sanitization

# Usage pattern in domains:
class ContentService:
    def __init__(self):
        self.file_manager = SafeFileManager()  # Shared service
    
    def process_file(self, file_path):
        # Use shared service instead of domain-specific implementation
        if self.file_manager.validate_file_operation("read", file_path):
            # ... process file
```

### **Pattern: Utility Service Design**
```python
# PATTERN: Focused utility with single responsibility
class SafeFileManager:
    """Handles ALL file operations with security and retry logic."""
    
    def safe_move(self, src, dst, attempts=3) -> bool:
        # Atomic operation with retry
    
    def safe_copy(self, src, dst) -> bool:
        # Atomic operation with conflict resolution
    
    def validate_file_operation(self, operation, src, dst=None) -> tuple:
        # Security validation before operation

# USAGE: All domains use the same file utilities
# BENEFIT: Consistent behavior, security, testing across all domains
```

## **Orchestration Patterns**

### **Pattern: Application Kernel Coordination**
**Problem**: Domain services need coordination without tight coupling
**Solution**: Orchestration layer that coordinates domain services through dependency injection

```python
class ApplicationKernel:
    """Coordinates domain services without coupling them together."""
    
    def __init__(self, container):
        # Lazy-load domain services to avoid circular dependencies
        self._content_service = None
        self._ai_service = None
        self._organization_service = None
        self.container = container
    
    @property
    def content_service(self):
        if self._content_service is None:
            self._content_service = self.container.create_content_service()
        return self._content_service
    
    def execute_processing(self, config):
        # Coordinate domains without coupling
        content_result = self.content_service.process_documents(...)
        ai_result = self.ai_service.generate_filenames(content_result)
        if config.organization_enabled:
            org_result = self.get_organization_service().organize_documents(ai_result)
        
        return ProcessingResult(...)
```

### **Pattern: Service Container Design**
```python
class ApplicationContainer:
    """Dependency injection container for clean component wiring."""
    
    def create_content_service(self):
        return ContentService()  # No dependencies
    
    def create_ai_integration_service(self):
        return AIIntegrationService()  # No dependencies
    
    def create_organization_service(self, target_folder):
        return OrganizationService(target_folder)  # Folder-specific
    
    def create_application_kernel(self):
        return ApplicationKernel(self)  # Inject container for service access
```

## **Testing Patterns for Architecture**

### **Pattern: Test Structure Mirrors Source Architecture**
**Lesson**: Test organization should reflect architectural boundaries

```
src/domains/content/content_service.py ↔ tests/unit/domains/content/test_content_service.py
src/interfaces/human/interactive_cli.py ↔ tests/unit/interfaces/human/test_interactive_cli.py
```

### **Pattern: Domain Contract Testing**
**Problem**: Integration tests were testing implementation details instead of contracts
**Solution**: Test domain interfaces, not internal implementation

```python
# WRONG: Testing implementation details
def test_content_processor_uses_pymupdf():
    processor = PDFProcessor()
    assert processor.use_pymupdf == True  # Implementation detail

# CORRECT: Testing domain contract  
def test_content_service_provides_ai_ready_content():
    service = ContentService()
    result = service.process_document_complete("test.pdf")
    
    # Test the contract: ContentService provides AI-ready content
    assert "ai_ready_content" in result
    assert result["ready_for_ai"] in [True, False]
    assert isinstance(result["extraction"], ExtractedContent)
```

### **Pattern: Rich UI Testing Isolation**
```python
class TestInteractiveCLI(unittest.TestCase, RichTestCase):
    def setUp(self):
        RichTestCase.setUp(self)  # Proper console isolation
        self.cli = InteractiveCLI()
    
    def test_progress_display(self):
        self.cli.show_progress("Processing", 5, 10)
        output = self.get_console_output()
        # Test Rich UI behavior without console conflicts
```

## **Migration Patterns**

### **Pattern: Clean Cut vs Compatibility Layer**
**Critical Lesson**: Compatibility layers mask architectural issues and create technical debt

#### **✅ CORRECT: Clean Cut Migration**
```python
# 1. Remove old implementation completely
rm legacy_module.py

# 2. Fix ALL imports to use new architecture
from old_module import function  →  from domains.new_domain import Service

# 3. Fix ALL tests to validate new architecture
# 4. Force architectural coherence

# BENEFITS:
# - Real issues exposed immediately
# - No duplicate code maintenance
# - Clear development patterns
# - Reliable testing
```

#### **❌ WRONG: Compatibility Layers**
```python
# Creates technical debt and confusion
def old_function():
    warnings.warn("deprecated") 
    return new_function()  # Hidden complexity, double maintenance

# PROBLEMS:
# - Architectural issues hidden behind redirects
# - Tests validate compatibility layer instead of architecture
# - Developer confusion about correct patterns
# - Technical debt accumulation
```

### **Pattern: Validation-Driven Migration**
**Critical Lesson**: Each migration step requires measurable validation before proceeding

```python
class MigrationStep:
    def execute(self):
        # 1. Define acceptance criteria
        criteria = self.get_acceptance_criteria()
        
        # 2. Execute migration actions
        self.perform_migration_actions()
        
        # 3. MANDATORY validation
        validation = self.validate_against_criteria(criteria)
        
        # 4. STOP if validation fails
        if not validation.passed:
            raise MigrationError(f"Step failed validation: {validation.errors}")
        
        # 5. Only proceed after validation passes
        return validation
```

## **Anti-Patterns Discovered**

### **❌ Anti-Pattern: Premature Completion Claims**
**Problem**: Claiming completion without validation leads to architectural debt
**Solution**: Validate against measurable criteria before claiming completion

### **❌ Anti-Pattern: Scattered Concerns**
**Problem**: Similar functionality implemented differently across modules
**Example**: 6 different file operation implementations
**Solution**: Extract to shared services with single implementation

### **❌ Anti-Pattern: Dual System Confusion**
**Problem**: Two systems serving same purpose (legacy + new)
**Example**: `src/organization/` vs `src/domains/organization/`
**Solution**: Consolidate to single implementation in proper domain

### **❌ Anti-Pattern: Compatibility Layer Proliferation**
**Problem**: Multiple compatibility layers create maintenance burden
**Solution**: Clean cut migration with systematic import updates

## **Implementation Guidelines**

### **When Extracting Domain Services**
1. **Identify business capabilities** first (not technical groupings)
2. **Define clean interfaces** before implementation
3. **Extract shared concerns** to dedicated shared services
4. **Validate each extraction** before proceeding to next
5. **Use dependency injection** to wire services together

### **When Implementing Interface Layers**
1. **Define persona requirements** clearly
2. **Create interface contracts** for consistency
3. **Use Rich Console everywhere** for human interfaces
4. **Structure output appropriately** for each persona
5. **Route based on context detection** not configuration

### **When Migrating Architecture**
1. **Plan validation criteria** before starting migration
2. **Execute with validation checkpoints** at each step
3. **Use clean cut approach** instead of compatibility layers
4. **Fix all regressions systematically** after clean migration
5. **Validate architectural coherence** before declaring complete

These patterns ensure **clean architectural boundaries** that enable **independent domain development** while maintaining **system cohesion** through proper orchestration and shared services.