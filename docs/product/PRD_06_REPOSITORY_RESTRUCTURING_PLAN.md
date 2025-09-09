# Repository Restructuring Plan
*Comprehensive plan for aligning repository structure with domain architecture*

## Current vs Target Repository Structure

### **CURRENT: Inconsistent Structure (37% Coherence)**
```
content-tamer-ai/
├─ src/
│  ├─ main.py                    # ❌ Entry point bypasses architecture
│  ├─ ai_providers.py            # ❌ Domain logic in wrong location  
│  ├─ content_processors.py      # ❌ Domain logic in wrong location
│  ├─ file_organizer.py          # ❌ Shared utility in wrong location
│  ├─ core/                      # ⚠️ Mix of legacy and architecture
│  ├─ utils/                     # ❌ Should be shared/
│  ├─ organization/              # ❌ Legacy system conflicts with domains/
│  ├─ interfaces/ ✅             # ✅ Clean architectural layer
│  ├─ domains/ ✅                # ✅ Clean architectural layer 
│  ├─ shared/ ✅                 # ✅ Clean architectural layer
│  └─ tests/                     # ❌ Tests inside src/
├─ tests/                        # ⚠️ Main test directory
└─ docs/                         # ✅ Good documentation structure
```

### **TARGET: Coherent Domain-Aligned Structure (95% Coherence)**
```
content-tamer-ai/
├─ src/
│  ├─ main.py                    # ✅ Routes through interface compatibility layer
│  ├─ interfaces/                # ✅ Persona-driven interface layer
│  │  ├─ human/                  # Interactive CLI, Rich UI, configuration wizard
│  │  ├─ programmatic/           # Headless operation, library API, config management  
│  │  └─ protocols/              # MCP, REST, GraphQL extension points
│  ├─ orchestration/             # ✅ Application coordination layer
│  │  ├─ application_kernel.py   # Main workflow orchestration
│  │  ├─ workflow_engine.py      # Pipeline management (future)
│  │  └─ session_manager.py      # State persistence (future)
│  ├─ domains/                   # ✅ Business logic domains
│  │  ├─ content/                # Document processing domain
│  │  ├─ ai_integration/         # Provider management domain  
│  │  └─ organization/           # Document organization domain (PRD_04)
│  ├─ shared/                    # ✅ Cross-cutting utilities
│  │  ├─ file_operations/        # Unified file management
│  │  ├─ display/                # Unified UI components
│  │  └─ infrastructure/         # Config, dependencies, features
│  └─ compatibility/             # ✅ Legacy compatibility during transition
│     ├─ legacy_ai_providers.py  # Migrated from ai_providers.py
│     ├─ legacy_content_processors.py # Migrated from content_processors.py
│     └─ migration_helpers.py    # Migration utilities
├─ tests/                        # ✅ Unified test structure
│  ├─ unit/                      # Unit tests aligned with src/ structure
│  │  ├─ interfaces/
│  │  ├─ domains/
│  │  ├─ shared/
│  │  └─ orchestration/
│  ├─ integration/               # Component integration tests
│  │  ├─ cross_domain/           # Tests spanning multiple domains
│  │  ├─ interface_integration/  # Interface layer integration
│  │  └─ workflow_integration/   # Complete workflow tests
│  ├─ e2e/                       # End-to-end user journey tests
│  │  ├─ cli_workflows/          # CLI user scenarios
│  │  ├─ api_workflows/          # Programmatic API scenarios  
│  │  └─ protocol_workflows/     # Protocol-based scenarios
│  ├─ fixtures/                  # Test data and fixtures
│  └─ utils/                     # Test utilities and helpers
├─ docs/
└─ [other root files]
```

## Repository Migration Strategy

### **Phase 1: Test Directory Consolidation**

#### **Issue Analysis**
- `/tests/` contains 533 files (main test suite)
- `/src/tests/` contains only validation tests
- **No coherent organization** by architecture layer
- **Test structure doesn't mirror** src/ domain boundaries

#### **Target Test Organization**
```
tests/
├─ unit/                         # Pure unit tests (isolated classes/functions)
│  ├─ interfaces/
│  │  ├─ human/                  # Interactive CLI tests
│  │  ├─ programmatic/           # Library API tests
│  │  └─ protocols/              # Protocol interface tests
│  ├─ domains/
│  │  ├─ content/                # Content domain unit tests
│  │  ├─ ai_integration/         # AI domain unit tests
│  │  └─ organization/           # Organization domain unit tests
│  ├─ shared/
│  │  ├─ file_operations/        # File utility tests
│  │  ├─ display/                # Display utility tests
│  │  └─ infrastructure/         # Infrastructure utility tests
│  └─ orchestration/             # Application kernel tests
├─ integration/                  # Component integration tests
│  ├─ interface_to_domain/       # Interface → Domain integration
│  ├─ cross_domain/              # Domain → Domain integration
│  ├─ shared_service/            # Shared service integration
│  └─ legacy_compatibility/      # Backwards compatibility tests
├─ e2e/                          # End-to-end user journey tests
│  ├─ human_workflows/           # Interactive user scenarios
│  ├─ automation_workflows/      # Headless/batch scenarios
│  └─ protocol_workflows/        # MCP/API scenarios
├─ fixtures/                     # Test data, mock files, etc.
├─ utils/                        # Test utilities and frameworks
│  ├─ rich_test_utils.py         # Rich UI testing framework (existing)
│  ├─ domain_test_helpers.py     # Domain service test helpers
│  └─ integration_test_base.py   # Base classes for integration tests
└─ conftest.py                   # Pytest configuration
```

### **Phase 2: src/ Directory Cleanup**

#### **Legacy Files to Migrate**
```python
# HIGH PRIORITY MIGRATIONS:

# Domain Services (move to proper domains)
src/ai_providers.py → src/compatibility/legacy_ai_providers.py
src/content_processors.py → src/compatibility/legacy_content_processors.py  

# Shared Utilities (move to shared/)
src/file_organizer.py → src/shared/file_operations/ (partially done)
src/utils/* → src/shared/infrastructure/ or src/shared/display/

# Legacy Organization (consolidate or remove)
src/organization/ → Merge into src/domains/organization/ or deprecate

# Core Cleanup (architectural classification)
src/core/cli_parser.py → src/interfaces/compatibility/ (legacy routing)
src/core/cli_handler.py → Split between domains and interfaces
src/core/directory_manager.py → src/shared/infrastructure/
src/core/dependency_manager.py → src/shared/infrastructure/
src/core/file_processor.py → src/domains/content/ or src/orchestration/
```

### **Phase 3: Architectural Coherence**

#### **Clear Naming and Organization**
```
src/
├─ main.py                       # ✅ Entry point (routes through interfaces)
├─ interfaces/                   # ✅ User interaction layer
│  ├─ human/                     # Human-facing interfaces
│  │  ├─ interactive_cli.py      # Main interactive interface
│  │  ├─ rich_console_manager.py # Rich UI singleton management
│  │  └─ configuration_wizard.py # Expert configuration interface
│  ├─ programmatic/              # Automation-friendly interfaces  
│  │  ├─ cli_arguments.py        # Pure argument parsing
│  │  ├─ library_interface.py    # Python API
│  │  └─ configuration_manager.py # Headless configuration
│  ├─ protocols/                 # Protocol-based interfaces
│  │  ├─ mcp_server.py          # Claude MCP integration
│  │  └─ future_apis/           # REST, GraphQL extension points
│  └─ compatibility/             # Legacy interface routing
│     ├─ legacy_cli_router.py   # Routes legacy CLI to new interfaces
│     └─ interface_adapter.py   # Adapts old interfaces to new contracts
├─ orchestration/                # ✅ Application coordination layer
│  ├─ application_kernel.py     # Main application coordination
│  ├─ workflow_engine.py        # Pipeline orchestration (future)
│  └─ session_manager.py        # State and resume management (future)
├─ domains/                      # ✅ Business logic domains
│  ├─ content/                   # Document processing domain
│  │  ├─ extraction_service.py  # PDF, image, document extraction
│  │  ├─ enhancement_service.py # Quality improvement and preparation
│  │  ├─ metadata_service.py    # Document analysis and entity extraction
│  │  └─ content_service.py     # Domain orchestration
│  ├─ ai_integration/            # AI provider management domain
│  │  ├─ provider_service.py    # Provider factory and management
│  │  ├─ model_service.py       # Hardware detection and selection
│  │  ├─ request_service.py     # API calls and retry logic
│  │  ├─ ai_integration_service.py # Domain orchestration
│  │  └─ providers/             # Individual provider implementations
│  └─ organization/              # Document organization domain (PRD_04 ready)
│     ├─ clustering_service.py  # Progressive enhancement classification
│     ├─ folder_service.py      # Directory operations and structure
│     ├─ learning_service.py    # State management and improvement
│     └─ organization_service.py # Domain orchestration
├─ shared/                       # ✅ Cross-cutting utilities
│  ├─ file_operations/          # Unified file management
│  │  ├─ safe_file_manager.py   # Atomic operations, locking, retry
│  │  ├─ path_validator.py      # Security, cross-platform paths
│  │  └─ content_sanitizer.py   # Input validation and cleaning
│  ├─ display/                  # Unified UI components
│  │  ├─ unified_display_manager.py # Consolidated Rich UI management
│  │  ├─ progress_tracker.py    # Generic progress handling
│  │  └─ message_formatter.py   # Consistent error and status messages
│  └─ infrastructure/           # Configuration and system services
│     ├─ configuration_loader.py # Multi-source configuration
│     ├─ dependency_detector.py # Auto-detection and PATH management
│     └─ feature_controller.py  # Feature flags and rollout control
└─ compatibility/                # ✅ Migration support
   ├─ legacy_providers.py       # Temporary: migrated ai_providers.py
   ├─ legacy_processors.py      # Temporary: migrated content_processors.py
   ├─ legacy_utils.py           # Temporary: migrated utils functionality
   └─ migration_tracker.py      # Track migration progress
```

## Test Strategy Aligned with Architecture

### **Unit Tests: Domain Isolation**
```
tests/unit/
├─ interfaces/                   # Interface layer unit tests
│  ├─ human/
│  │  ├─ test_interactive_cli.py
│  │  ├─ test_configuration_wizard.py
│  │  └─ test_rich_console_manager.py
│  ├─ programmatic/
│  │  ├─ test_cli_arguments.py
│  │  ├─ test_library_interface.py
│  │  └─ test_configuration_manager.py
│  └─ protocols/
├─ domains/                      # Domain service unit tests
│  ├─ content/
│  │  ├─ test_extraction_service.py
│  │  ├─ test_enhancement_service.py
│  │  ├─ test_metadata_service.py
│  │  └─ test_content_service.py
│  ├─ ai_integration/
│  │  ├─ test_provider_service.py
│  │  ├─ test_model_service.py
│  │  ├─ test_request_service.py
│  │  └─ test_ai_integration_service.py
│  └─ organization/
│     ├─ test_clustering_service.py
│     ├─ test_folder_service.py
│     ├─ test_learning_service.py
│     └─ test_organization_service.py
├─ shared/                       # Shared utility unit tests
│  ├─ file_operations/
│  ├─ display/
│  └─ infrastructure/
└─ orchestration/                # Application kernel unit tests
   └─ test_application_kernel.py
```

### **Integration Tests: Contract Validation**
```
tests/integration/
├─ interface_to_orchestration/   # Interface → Orchestration contracts
├─ orchestration_to_domain/      # Orchestration → Domain contracts
├─ cross_domain/                 # Domain → Domain interactions
├─ shared_service_integration/   # Shared service usage
└─ legacy_compatibility/         # Backwards compatibility validation
```

### **E2E Tests: User Journey Validation**  
```
tests/e2e/
├─ human_workflows/              # Interactive user scenarios
│  ├─ test_first_time_user.py
│  ├─ test_expert_configuration.py
│  └─ test_guided_processing.py
├─ automation_workflows/         # Headless/scripting scenarios
│  ├─ test_batch_processing.py
│  ├─ test_ci_cd_integration.py
│  └─ test_library_api_usage.py
└─ protocol_workflows/           # Future: MCP, REST, GraphQL
   └─ test_mcp_integration.py
```

## Migration Plan

### **Step 1: Test Directory Consolidation**

#### **Immediate Action: Merge Test Directories**
```bash
# Move src/tests/validation/ to main tests
mv src/tests/validation/ tests/unit/legacy_validation/

# Remove empty src/tests/ directory
rmdir src/tests/

# Reorganize main tests by architecture
mkdir -p tests/unit/{interfaces,domains,shared,orchestration}
mkdir -p tests/integration/{cross_domain,interface_integration,workflow_integration}
mkdir -p tests/e2e/{human_workflows,automation_workflows,protocol_workflows}
```

#### **Test Migration Strategy**
```python
# CURRENT: tests/test_integration.py (flat organization)
# TARGET: tests/integration/cross_domain/test_content_ai_integration.py

# CURRENT: tests/test_display_manager.py (mixed concerns)  
# TARGET: tests/unit/shared/display/test_unified_display_manager.py

# CURRENT: tests/contracts/ (good concept, wrong location)
# TARGET: tests/integration/cross_domain/ (tests domain contracts)
```

### **Step 2: src/ Directory Restructuring**

#### **Legacy File Migration**
```bash
# Create compatibility directory
mkdir -p src/compatibility/

# Migrate legacy domain files
mv src/ai_providers.py src/compatibility/legacy_ai_providers.py
mv src/content_processors.py src/compatibility/legacy_content_processors.py

# Migrate shared utilities
mv src/utils/ src/shared/infrastructure_legacy/
# Then selectively migrate utils to proper shared/ locations

# Consolidate organization systems
# Assess src/organization/ vs src/domains/organization/
# Keep domains/organization/, deprecate legacy organization/
```

#### **Core Directory Cleanup**
```bash
# Classify core/ files by architectural role:

# → interfaces/compatibility/
core/cli_parser.py (legacy CLI routing)
core/interface_compatibility_layer.py (already in right place)

# → shared/infrastructure/ 
core/dependency_manager.py
core/directory_manager.py (after extracting domain concerns)
core/filename_config.py

# → orchestration/
core/application_kernel.py (if not using existing orchestration/)
core/file_processor.py (workflow coordination)

# → Keep in core/ (true application core)
core/application_container.py (dependency injection root)
core/compatibility_layer.py (architecture migration support)
```

### **Step 3: Naming Consistency and Clarity**

#### **File Naming Conventions**
```python
# DOMAIN SERVICES: {domain}_service.py as main orchestrator
domains/content/content_service.py           # Main content domain service
domains/ai_integration/ai_integration_service.py # Main AI domain service  
domains/organization/organization_service.py # Main organization domain service

# SUB-SERVICES: {capability}_service.py
domains/content/extraction_service.py        # Content extraction capability
domains/ai_integration/provider_service.py   # Provider management capability

# SHARED UTILITIES: {function}_manager.py or {function}_utils.py
shared/file_operations/safe_file_manager.py  # File operation utilities
shared/display/unified_display_manager.py    # Display utilities

# INTERFACE IMPLEMENTATIONS: {persona}_{interface}.py
interfaces/human/interactive_cli.py          # Human interface implementation
interfaces/programmatic/library_interface.py # Programmatic interface implementation
```

#### **Directory Naming Conventions**
- **Architectural Layers**: `interfaces/`, `orchestration/`, `domains/`, `shared/`
- **Domain Boundaries**: `content/`, `ai_integration/`, `organization/`
- **Interface Types**: `human/`, `programmatic/`, `protocols/`
- **Test Categories**: `unit/`, `integration/`, `e2e/`

## Implementation Checklist

### **Critical Path (This Session)**

#### **Test Directory Consolidation**
- [ ] **Audit current test organization**: Map all test files to new structure
- [ ] **Create new test directory structure**: Align with domain architecture
- [ ] **Migrate unit tests**: Move to domain-aligned locations
- [ ] **Separate integration tests**: Extract cross-domain test logic
- [ ] **Identify E2E scenarios**: Create user journey test organization

#### **Legacy File Migration**
- [ ] **Create compatibility directory**: Temporary home for legacy files  
- [ ] **Migrate ai_providers.py**: Move to compatibility with import redirects
- [ ] **Migrate content_processors.py**: Move to compatibility with import redirects
- [ ] **Update import statements**: Point to new locations with compatibility layer

### **High Priority (Next Session)**

#### **Core Directory Cleanup**  
- [ ] **Classify core/ files**: Determine architectural layer for each file
- [ ] **Extract shared concerns**: Move utilities to shared/
- [ ] **Extract domain concerns**: Move business logic to domains/
- [ ] **Keep true core**: Application container and compatibility only

#### **Naming Standardization**
- [ ] **Rename inconsistent files**: Align with naming conventions
- [ ] **Update import statements**: Reflect new naming patterns
- [ ] **Add architectural documentation**: README in each directory explaining purpose

### **Quality Gates**

#### **Repository Structure Validation**
- [ ] **Directory purpose clarity**: Each directory has single architectural responsibility
- [ ] **Import dependency direction**: No circular dependencies between layers
- [ ] **Test organization consistency**: Tests mirror src/ structure
- [ ] **Legacy compatibility**: All existing functionality works during migration

#### **Developer Experience Validation**
- [ ] **Clear navigation**: Developers can find functionality intuitively  
- [ ] **Domain isolation**: Changes in one domain don't require touching others
- [ ] **Test discoverability**: Tests are easy to find and run by architectural layer
- [ ] **Documentation alignment**: Architecture docs match actual structure

## Benefits of Coherent Repository Structure

### **Development Workflow Improvements**
```
BEFORE: 
- "Where do I add a new AI provider?" (unclear - multiple places)
- "How do I test display functionality?" (scattered across 8 files)
- "What tests will break if I change content extraction?" (unknown - no boundaries)

AFTER:
- "Add AI provider" → domains/ai_integration/providers/ (clear)  
- "Test display" → tests/unit/shared/display/ (obvious)
- "Content changes affect" → tests/unit/domains/content/ (isolated)
```

### **Architecture Enforcement**
- **Import analysis tools** can validate dependency direction
- **CI/CD checks** can prevent cross-domain violations
- **Code review focus** aligned with architectural boundaries
- **New developer onboarding** follows clear architectural patterns

### **Future Extension Support**
- **MCP integration**: Clear placement in interfaces/protocols/
- **New domains**: Template structure for consistent implementation
- **Shared utilities**: Obvious location for cross-cutting concerns
- **Protocol implementations**: Extension points prepared

## Migration Timeline

### **Week 1: Foundation** 
- Test directory consolidation
- Legacy file migration to compatibility/
- Import statement updates

### **Week 2: Structural Cleanup**
- Core directory reorganization  
- Shared utility migration
- Naming consistency implementation

### **Week 3: Integration Testing**
- E2E test fixes aligned with new structure
- Cross-domain integration validation  
- Legacy compatibility verification

### **Week 4: Documentation and Finalization**
- Update all documentation to reflect structure
- Create architectural decision records
- Finalize migration with comprehensive testing

This restructuring will create a **repository structure that enforces our domain architecture** and eliminates the structural inconsistencies that cause integration brittleness.