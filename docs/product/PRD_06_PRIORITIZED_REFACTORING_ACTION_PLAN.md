# Prioritized Refactoring Action Plan
*High-impact architectural improvements based on coherence audit*

## Audit Results Summary

**Current Architectural Coherence: 37%**
- ✅ Domain services well-architected (interfaces/, domains/, shared/)
- ⚠️ Legacy files bypass new architecture (main.py, core/*.py)
- ❌ High DRY violations (40-60% duplication in key areas)
- ❌ SOLID violations prevent independent development

## Critical Issues Prioritized by Impact

### **🚨 CRITICAL (Fix Immediately)**

#### **1. Main Entry Point Architectural Violation**
**File**: `src/main.py`
**Issue**: Directly imports `core.application.organize_content` bypassing interface layer
**Impact**: **BREAKS persona-driven architecture** - all users forced through legacy path
**Fix**: Route through `interfaces.human.interactive_cli.InteractiveCLI` or `interfaces.programmatic.library_interface`

```python
# CURRENT (WRONG):
from core.application import organize_content

# TARGET:
from core.interface_compatibility_layer import compatibility_main
def main():
    return compatibility_main()  # Routes to appropriate interface
```

#### **2. API Key Logic Triplication** 
**Files**: `src/core/directory_manager.py`, `src/utils/security.py`, `src/domains/ai_integration/provider_service.py`
**Issue**: Same provider detection logic duplicated 3x with inconsistencies
**Impact**: **PREVENTS reliable API key handling** across interfaces
**Fix**: Centralize in `domains/ai_integration/provider_service.py`, import everywhere else

#### **3. File Operations Duplication (6 implementations)**
**Files**: `file_organizer.py`, `core/file_processor.py`, `core/application.py`, `organization/file_executor.py`, etc.
**Issue**: Different file move/copy/lock implementations with incompatible interfaces  
**Impact**: **CAUSES E2E test failures** and integration brittleness
**Fix**: Migrate all to `shared/file_operations/safe_file_manager.py`

### **🔥 HIGH PRIORITY (Fix This Week)**

#### **4. Display Manager Proliferation (8 systems)**
**Files**: `utils/display_manager.py`, `utils/rich_display_manager.py`, `utils/progress_display.py`, etc.
**Issue**: Multiple console/display managers create conflicts and duplicate functionality
**Impact**: **PREVENTS clean UI experiences** and test isolation
**Fix**: Migrate to `shared/display/unified_display_manager.py`

#### **5. CLI Handler Responsibility Bloat**
**File**: `src/core/cli_handler.py` (768+ lines)
**Issue**: Violates Single Responsibility - handles CLI commands, model management, dependencies
**Impact**: **PREVENTS independent domain development** - changes require touching CLI layer
**Fix**: Extract to domain-specific command handlers

### **📊 MEDIUM PRIORITY (Fix Next Week)**

#### **6. Core Directory Manager Coupling**
**File**: `src/core/directory_manager.py`
**Issue**: Mixes directory operations, API key prompting, provider detection
**Impact**: Tight coupling prevents clean testing and extension
**Fix**: Extract concerns to appropriate domains and shared services

#### **7. Application Container Feature Bloat** 
**File**: `src/core/application_container.py`
**Issue**: Growing responsibility for creating every possible service
**Impact**: Violates Open/Closed principle - requires modification for every new service
**Fix**: Implement service registry pattern

#### **8. Legacy Organization Module Confusion**
**Files**: `src/organization/*.py` vs `src/domains/organization/`
**Issue**: Two organization systems create confusion about which to use
**Impact**: Developer confusion and potential feature duplication
**Fix**: Migrate or deprecate legacy organization module

### **🔄 LOW PRIORITY (Continuous Improvement)**

#### **9. Error Handling Pattern Inconsistency**
**Files**: 30+ files with different exception handling approaches
**Issue**: No standardized error handling patterns
**Impact**: Inconsistent error messages and debugging complexity
**Fix**: Implement shared error handling patterns

#### **10. Configuration Loading Duplication**
**Files**: Multiple config loading patterns across utils/
**Issue**: Different configuration sources and formats not unified
**Impact**: Inconsistent configuration behavior
**Fix**: Centralize in `shared/infrastructure/configuration_loader.py`

## Implementation Strategy

### **Phase A: Critical Path (Week 1)**

#### **Day 1-2: Main Entry Point Migration**
```python
# src/main.py → Use interface layer
def main():
    try:
        from core.interface_compatibility_layer import compatibility_main
        return compatibility_main()
    except ImportError:
        # Fallback to legacy for gradual migration
        from core.application import organize_content
        # ... legacy implementation
```

#### **Day 3-4: API Key Logic Consolidation**
1. **Extract to AIIntegrationService**: Move all provider detection to domain service
2. **Update directory_manager.py**: Import from domain service instead of duplicating
3. **Update security.py**: Use domain service patterns for sanitization

#### **Day 5: File Operations Migration**
1. **Update file_organizer.py**: Use SafeFileManager backend (already started)
2. **Update core/file_processor.py**: Replace local file operations
3. **Update organization modules**: Use shared file operations

### **Phase B: High Priority (Week 2)**

#### **Display System Unification**
1. **Deprecate legacy display managers**: Add deprecation warnings
2. **Route through UnifiedDisplayManager**: Update all display calls
3. **Fix console conflicts**: Eliminate multiple console instantiation

#### **CLI Handler Decomposition**
1. **Extract model management**: Move to domains/ai_integration/
2. **Extract dependency management**: Move to shared/infrastructure/
3. **Keep only CLI-specific concerns**: Argument handling and user interaction

### **Phase C: Medium Priority (Week 3)**

#### **Service Registry Implementation**
1. **Create ServiceRegistry**: Dynamic service discovery and creation
2. **Update ApplicationContainer**: Use registry for service creation  
3. **Enable plugin architecture**: Services register themselves

#### **Legacy Organization Migration**
1. **Assess src/organization/**: Determine migration vs deprecation
2. **Consolidate functionality**: Merge useful pieces into domains/organization/
3. **Remove duplication**: Eliminate conflicting organization systems

### **Phase D: Continuous Improvement (Ongoing)**

#### **Error Handling Standardization**
1. **Define error handling contracts**: Standard patterns for all domains
2. **Implement shared error utilities**: Common error formatting and logging
3. **Update domain services**: Use standardized error handling

## Success Metrics

### **Architectural Coherence Target: 90%**
- **Domain boundary respect**: <5% cross-domain imports
- **Interface layer adoption**: >90% of user interactions through interface layer  
- **Shared service usage**: >80% of file ops through shared services
- **DRY compliance**: <10% duplicate logic across domains

### **Development Velocity Improvements**
- **Feature development time**: 50% reduction due to domain isolation
- **Integration test reliability**: >95% pass rate due to proper contracts
- **Bug fixing scope**: Issues isolated to single domains
- **Code review efficiency**: Domain-focused reviews with clear boundaries

### **SOLID Principle Compliance Target: 85%**
- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Services extensible without modification  
- **Liskov Substitution**: Interface implementations properly substitutable
- **Interface Segregation**: Focused interfaces for specific use cases
- **Dependency Inversion**: Depend on abstractions, not concretions

## Implementation Checklist

### **Critical Path (Must Complete)**
- [ ] **Fix main.py**: Route through interface layer compatibility
- [ ] **Consolidate API key logic**: Single source in AI integration domain
- [ ] **Migrate file operations**: All modules use SafeFileManager
- [ ] **Fix E2E integration tests**: Address architectural friction points

### **High Priority (Significant Improvement)**
- [ ] **Unify display systems**: Eliminate console conflicts
- [ ] **Decompose CLI handler**: Extract domain concerns
- [ ] **Implement service registry**: Enable dynamic service discovery
- [ ] **Resolve organization duplication**: Single organization system

### **Quality Gates**
- [ ] **All E2E tests pass**: 29/29 integration tests successful
- [ ] **No performance regression**: Processing time unchanged
- [ ] **Security compliance maintained**: Bandit/Safety scans clean
- [ ] **Backwards compatibility**: Existing CLI usage works unchanged

## Expected Outcomes

### **Developer Experience**
- **Feature development**: Isolated within single domain boundaries
- **Testing confidence**: Domain contracts prevent integration surprises
- **Debugging efficiency**: Clear separation of concerns
- **Code review focus**: Domain expertise applied effectively

### **System Quality**
- **Reduced coupling**: Domain services independently testable and modifiable
- **Improved cohesion**: Related functionality properly grouped
- **Enhanced extensibility**: New capabilities added without architectural changes
- **Better maintainability**: Clear ownership and responsibility boundaries

### **Business Value**
- **Faster feature delivery**: Domain isolation accelerates development cycles
- **Higher quality releases**: Better testing and isolation reduce defects
- **Easier onboarding**: Clear architectural patterns improve developer productivity
- **Future-proof foundation**: MCP integration and PRD_04 implementation ready

---

*This action plan provides systematic resolution of architectural coherence issues while maintaining system stability and enabling the independent domain development workflow that was the original goal of the refactoring effort.*