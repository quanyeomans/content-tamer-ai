# Systematic Migration Roadmap
*Complete repository restructuring for domain architecture coherence*

## Repository Structure Problems Confirmed

### **Critical Issues Found**

#### **1. Architectural Bypass in Entry Point**
- **main.py (5,664 lines)**: Directly imports `core.application.organize_content`
- **Persona architecture unused**: All user types forced through legacy path
- **Domain services unreachable**: New architecture never accessed

#### **2. Duplicate Test Directories** 
- `/tests/` (56 files): Main test suite with flat organization
- `/src/tests/` (3 files): Duplicate location with validation tests
- **No test-to-source alignment**: Tests don't mirror domain architecture

#### **3. Legacy Domain Files in Wrong Locations**
- **ai_providers.py (21K lines)**: Should be in domains/ai_integration/
- **content_processors.py (18K lines)**: Should be in domains/content/
- **file_organizer.py (19K lines)**: Should be in shared/file_operations/

#### **4. Naming Inconsistency**
- Some directories follow clean patterns: `interfaces/`, `domains/`, `shared/`
- Others are legacy: `core/`, `utils/`, `organization/` (conflicts with domains/organization/)

## Systematic Migration Strategy

### **PHASE 1: Establish Clean Foundation (This Session)**

#### **Step 1.1: Create Compatibility Layer for Gradual Migration**
```bash
# Create compatibility directory structure
mkdir -p src/compatibility/{providers,processors,utilities}

# Migrate legacy files to compatibility with deprecation warnings
mv src/ai_providers.py src/compatibility/providers/legacy_ai_providers.py
mv src/content_processors.py src/compatibility/processors/legacy_content_processors.py

# Create import redirects with deprecation warnings in original locations
```

#### **Step 1.2: Fix Main Entry Point Architecture Violation**
```python
# CURRENT main.py (WRONG):
def main():
    args = setup_environment_and_args()  # Direct CLI parsing
    success = organize_content(...)       # Direct business logic

# TARGET main.py (CORRECT):
def main():
    """Route through interface layer for persona-driven architecture."""
    try:
        from core.interface_compatibility_layer import compatibility_main
        return compatibility_main()
    except Exception as e:
        # Fallback with clear error message
        print(f"Interface layer failed: {e}")
        print("Using legacy implementation...")
        return legacy_main()
```

#### **Step 1.3: Consolidate Test Directories**
```bash
# Move src/tests/ content to main tests
mv src/tests/validation/ tests/unit/legacy_validation/
rmdir src/tests/

# Create domain-aligned test structure
mkdir -p tests/unit/{interfaces,domains,shared,orchestration}
mkdir -p tests/integration/{cross_domain,interface_to_domain,workflow}
mkdir -p tests/e2e/{human,automation,protocol}
```

### **PHASE 2: Domain Architecture Enforcement (Next Session)**

#### **Step 2.1: Core Directory Cleanup**
```bash
# Classify and migrate core/ files
# → interfaces/compatibility/
mv src/core/cli_parser.py src/interfaces/compatibility/legacy_cli_parser.py
mv src/core/cli_handler.py src/interfaces/compatibility/legacy_cli_handler.py

# → shared/infrastructure/
mv src/core/dependency_manager.py src/shared/infrastructure/
mv src/core/directory_manager.py src/shared/infrastructure/ (after domain extraction)

# → orchestration/
mv src/core/file_processor.py src/orchestration/workflow_processor.py
mv src/core/application.py src/orchestration/legacy_workflow.py

# Keep in core/ (true application core)
# core/application_container.py (dependency injection root)
# core/compatibility_layer.py (architecture migration)
# core/interface_compatibility_layer.py (interface routing)
```

#### **Step 2.2: Extract Domain Logic from Mixed Files**
```python
# FROM core/directory_manager.py EXTRACT:
# API Key Detection → domains/ai_integration/provider_service.py (consolidate with existing)
# Directory Operations → shared/infrastructure/directory_utils.py
# User Prompting → interfaces/human/api_key_prompter.py

# FROM core/cli_handler.py EXTRACT:
# Model Management → domains/ai_integration/model_service.py (consolidate)
# Dependency Commands → shared/infrastructure/dependency_detector.py  
# Feature Commands → shared/infrastructure/feature_controller.py
```

#### **Step 2.3: Utils Directory Migration**
```bash
# Migrate utils/ to appropriate shared/ locations
mv src/utils/console_manager.py src/shared/display/
mv src/utils/display_manager.py src/shared/display/legacy_display_manager.py
mv src/utils/error_handling.py src/shared/infrastructure/
mv src/utils/security.py src/shared/infrastructure/

# Create import redirects for backwards compatibility
```

### **PHASE 3: Test Strategy Implementation (Next 2 Sessions)**

#### **Step 3.1: Create Domain-Aligned Unit Tests**
```python
# NEW TEST ORGANIZATION PRINCIPLE:
# Each domain service has corresponding unit test module
# Each shared utility has corresponding unit test module  
# Each interface has corresponding unit test module

# EXAMPLE:
src/domains/content/content_service.py ↔ tests/unit/domains/content/test_content_service.py
src/shared/file_operations/safe_file_manager.py ↔ tests/unit/shared/file_operations/test_safe_file_manager.py
```

#### **Step 3.2: Create Contract-Based Integration Tests**
```python
# INTEGRATION TEST PRINCIPLE:
# Test domain contracts, not implementation details
# Focus on data flow and interface compliance

# EXAMPLE:
tests/integration/cross_domain/test_content_ai_contract.py:
def test_content_service_provides_ai_ready_content():
    """Content domain provides properly formatted content for AI domain."""
    # Test the contract: ContentService → AIIntegrationService
    pass
```

#### **Step 3.3: Create User Journey E2E Tests**
```python
# E2E TEST PRINCIPLE:
# Test complete user personas workflows
# Validate end-to-end value delivery

# EXAMPLE:
tests/e2e/human_workflows/test_expert_user_journey.py:
def test_expert_user_complete_workflow():
    """Expert user configures system and processes documents successfully."""
    # Test complete journey: CLI → Expert Mode → Processing → Organization
    pass
```

## Implementation Execution

### **Critical Path (Execute Now)**

#### **Fix Main Entry Point (30 minutes)**
```python
# 1. Create new main.py that routes through interface layer
# 2. Move current main.py to compatibility/legacy_main.py  
# 3. Test that CLI still works with new routing
```

#### **Consolidate Test Directories (15 minutes)**
```bash
# 1. Move src/tests/ to tests/unit/legacy_validation/
# 2. Create new test directory structure
# 3. Update conftest.py for new structure
```

#### **Create Legacy Compatibility Imports (20 minutes)**
```python
# 1. Move domain files to compatibility/ 
# 2. Create import redirects with deprecation warnings
# 3. Verify existing imports continue to work
```

### **Quality Validation**

#### **Repository Structure Coherence Check**
```bash
# After migration, verify structure alignment:
# 1. No domain logic in src/ root
# 2. Test structure mirrors src/ architecture  
# 3. All imports flow through proper layers
# 4. Legacy compatibility maintained
```

#### **E2E Test Validation**
```bash
# Run existing E2E tests to ensure:
# 1. No functionality regressions
# 2. Interface routing works correctly
# 3. Domain services accessible
# 4. Legacy compatibility preserved
```

## Expected Outcomes

### **Before Migration: Scattered Architecture**
```
Developer Question: "Where do I add a new AI provider?"
Answer: "Unclear - check ai_providers.py, or maybe domains/ai_integration/?"

Developer Question: "How do I test content extraction?"  
Answer: "Tests are scattered - check test_content_processors.py, maybe others?"

Feature Development: Requires changes across 7-10 files in different directories
```

### **After Migration: Clear Domain Boundaries**
```
Developer Question: "Where do I add a new AI provider?"
Answer: "src/domains/ai_integration/providers/ - test in tests/unit/domains/ai_integration/"

Developer Question: "How do I test content extraction?"
Answer: "tests/unit/domains/content/ mirrors src/domains/content/ exactly"

Feature Development: Changes isolated within single domain directory
```

### **Business Value**
- **50% faster feature development**: Clear domain boundaries eliminate cross-file changes
- **90% fewer integration issues**: Proper contracts prevent architectural violations  
- **Clear onboarding path**: Repository structure teaches architectural patterns
- **Future extensibility**: MCP, PRD_04 implementation obvious and isolated

## Risk Mitigation

### **Migration Safety**
- **Compatibility layer preserves all existing functionality**
- **Gradual migration with deprecation warnings**  
- **Comprehensive testing at each step**
- **Rollback capability through git version control**

### **Development Continuity**
- **No breaking changes during migration**
- **Clear migration timeline and checkpoints**
- **Documentation updated with each phase**
- **Team communication about directory changes**

This migration plan creates a **repository structure that enforces architectural coherence** and eliminates the structural inconsistencies that prevent independent domain development.