# Architecture Reference

## Current State (2024)

### Layer Architecture
```
┌─────────────────────────────────────────┐
│         Interface Layer                  │
│  (Human, Programmatic, Protocols)        │
├─────────────────────────────────────────┤
│       Orchestration Layer                │
│      (ApplicationKernel)                 │
├─────────────────────────────────────────┤
│         Domain Layer                     │
│  (Content | AI Integration | Organization)│
├─────────────────────────────────────────┤
│         Shared Layer                     │
│  (File Ops, Display, Infrastructure)     │
└─────────────────────────────────────────┘
```

### Domain Boundaries (Invariant)
```python
# STRICT: No cross-domain imports
domains/content/     → Cannot import from domains/organization/
domains/organization → Cannot import from domains/ai_integration/
domains/ai_integration → Cannot import from domains/content/

# Coordination ONLY through orchestration layer
orchestration/application_kernel.py → Coordinates all domains
```

### Dependency Injection Pattern
```python
# All services created through ApplicationContainer
container = ApplicationContainer(config)
service = container.create_service()
display = container.create_display_manager()

# Test container for testing
test_container = TestApplicationContainer()
mock_service = test_container.create_service()  # AI providers mocked
```

## Architectural Invariants

### Must Never Change
1. **Domain boundaries are absolute** - No cross-imports
2. **DI through ApplicationContainer** - No direct instantiation
3. **UI through UnifiedDisplayManager** - No print/console.log
4. **External APIs mocked in tests** - Real file ops with tempdir

### Extension Points
1. **New AI Provider**: Add to `domains/ai_integration/providers/`
2. **New Domain**: Create under `domains/` with service pattern
3. **New Interface**: Add to `interfaces/` (human/programmatic/protocols)

## Component Responsibilities

### ApplicationKernel
- Document discovery and validation
- Pipeline orchestration (Extract → AI → Organize)
- Progress coordination
- Error aggregation

### Domain: Content
- PDF/document extraction (via Tesseract)
- Content enhancement and cleaning
- Metadata extraction
- Quality assessment

### Domain: AI Integration
- Provider factory (OpenAI, Claude, Gemini, Local, Deepseek)
- Request management with timeout
- Response validation
- Token management

### Domain: Organization
- Document classification/clustering
- Folder structure creation
- File movement operations
- Learning from patterns

### Shared Services
- **SafeFileManager**: Path validation, conflict resolution
- **UnifiedDisplayManager**: All UI output, progress tracking
- **ConsoleManager**: Singleton Rich console
- **DependencyManager**: External tool detection

## Key Design Decisions

### ADR-001: Persona-Driven Interfaces
**Decision**: Separate interfaces by user type
**Rationale**: Humans need Rich UI, scripts need API, Claude needs MCP
**Consequence**: 3 interface packages, shared orchestration

### ADR-002: Domain Service Pattern
**Decision**: Organize by business capability, not technical layer
**Rationale**: Independent development, clear boundaries
**Consequence**: Some duplication acceptable for independence

### ADR-003: ApplicationContainer for DI
**Decision**: Central container for all dependency injection
**Rationale**: Testability, loose coupling, configuration management
**Consequence**: All services created through container

### ADR-004: Rich-First UI
**Decision**: Rich library for all human output
**Rationale**: Professional UI, cross-platform support
**Consequence**: ConsoleManager singleton, RichTestCase for tests

## Performance Targets
- Startup: <3 seconds to interactive
- Processing: <2 seconds per document
- Memory: <500MB for 100 documents
- Test suite: <30 seconds for unit tests

## Scalability Considerations
- Batch processing: Handles 1000+ documents
- Async AI calls: Parallel provider requests
- Streaming extraction: Large PDFs processed in chunks
- Progressive organization: Learn and improve over time