# Validation-Driven Development
*Ensuring architectural changes meet measurable criteria before proceeding*

## Pattern Origin

This pattern emerged during the domain architecture refactoring when **premature completion claims** and **incomplete validation** led to architectural inconsistencies and technical debt accumulation.

## Core Principle

**Every architectural change must pass measurable validation criteria before being considered complete.**

## The Problem This Solves

### **Traditional Approach Issues**
- Developer claims "X is complete" without validation
- Architectural issues hidden by compatibility layers
- Technical debt accumulates through incomplete migrations  
- Integration tests validate compatibility layers instead of real architecture
- Cross-cutting changes break system coherence

### **Validation-Driven Solution**
- **Measurable criteria** defined before implementation starts
- **Mandatory validation checkpoints** at each step
- **Stop-and-fix protocol** when validation fails
- **Evidence-based completion** with verifiable results

## Implementation Framework

### **Step 1: Define Acceptance Criteria**

#### **Before Starting ANY Architectural Work**
```python
# EXAMPLE: Domain Service Extraction
ACCEPTANCE_CRITERIA = {
    "repository_structure": {
        "src_root_files": 0,  # Only main.py, __init__.py allowed
        "legacy_files": 0,    # No compatibility/legacy files
        "provider_files": 6,  # All providers extracted
    },
    "functionality": {
        "domain_services_import": True,    # All services must import
        "provider_service_working": True,  # All providers functional
        "cli_commands_working": True,      # CLI functionality preserved
    },
    "quality": {
        "security_issues": 0,     # Bandit scan clean
        "import_errors": 0,       # No import/collection errors
        "test_pass_rate": 80,     # Minimum test success rate
    }
}
```

#### **Validation Script Template**
```python
def validate_architecture_change(criteria):
    """Validate architectural change against measurable criteria."""
    results = {}
    passed = True
    
    for category, requirements in criteria.items():
        category_results = {}
        
        for requirement, expected_value in requirements.items():
            actual_value = measure_requirement(requirement)
            requirement_passed = (actual_value == expected_value)
            
            category_results[requirement] = {
                "expected": expected_value,
                "actual": actual_value, 
                "passed": requirement_passed
            }
            
            if not requirement_passed:
                passed = False
        
        results[category] = category_results
    
    return ValidationResult(passed=passed, results=results)
```

### **Step 2: Execute with Validation Checkpoints**

#### **Migration Step Pattern**
```python
def execute_migration_step(step_name, actions, criteria):
    """Execute migration step with mandatory validation."""
    
    print(f"EXECUTING: {step_name}")
    
    # 1. Execute actions
    for action in actions:
        action.execute()
    
    # 2. MANDATORY validation
    validation = validate_architecture_change(criteria)
    
    # 3. STOP if validation fails
    if not validation.passed:
        print(f"VALIDATION FAILED for {step_name}")
        for category, results in validation.results.items():
            for req, result in results.items():
                if not result["passed"]:
                    print(f"  FAIL {category}.{req}: expected {result['expected']}, got {result['actual']}")
        
        raise MigrationError(f"Step '{step_name}' failed validation - MUST FIX before proceeding")
    
    # 4. Only proceed after validation passes
    print(f"VALIDATION PASSED for {step_name}")
    return validation
```

### **Step 3: Evidence-Based Completion**

#### **Completion Validation Protocol**
```python
def validate_complete_architecture():
    """Validate that architectural refactoring is truly complete."""
    
    evidence = {}
    
    # Repository structure evidence
    evidence["structure"] = {
        "src_files": os.listdir("src/"),
        "domain_services": glob.glob("src/domains/*/"),
        "interface_layers": glob.glob("src/interfaces/*/"),
        "shared_services": glob.glob("src/shared/*/")
    }
    
    # Functional evidence  
    evidence["functionality"] = {
        "domain_imports": test_all_domain_imports(),
        "cli_commands": test_all_cli_commands(),
        "service_health": test_service_health_checks()
    }
    
    # Quality evidence
    evidence["quality"] = {
        "security_scan": run_security_scan(),
        "code_quality": run_code_quality_scan(),
        "test_results": run_test_suite()
    }
    
    return evidence
```

## **Validation Patterns by Architecture Layer**

### **Interface Layer Validation**
```python
def validate_interface_layer():
    criteria = {
        "persona_support": {
            "human_interface": can_import("interfaces.human.interactive_cli"),
            "programmatic_interface": can_import("interfaces.programmatic.library_interface"),
            "protocol_interface": interface_extension_points_exist(),
        },
        "functionality": {
            "argument_parsing": test_cli_argument_parsing(),
            "configuration_management": test_configuration_loading(),
            "rich_ui_working": test_rich_console_functionality(),
        }
    }
    return validate_against_criteria(criteria)
```

### **Domain Service Validation**
```python
def validate_domain_services():
    criteria = {
        "service_isolation": {
            "content_domain": can_modify_content_without_affecting_ai(),
            "ai_domain": can_modify_providers_without_affecting_content(),
            "organization_domain": can_modify_clustering_without_affecting_others(),
        },
        "service_completeness": {
            "all_providers_working": test_all_ai_providers(),
            "content_processing_working": test_content_extraction(),
            "organization_clustering_working": test_document_clustering(),
        }
    }
    return validate_against_criteria(criteria)
```

### **Shared Service Validation**
```python
def validate_shared_services():
    criteria = {
        "consolidation": {
            "single_file_manager": count_file_operation_implementations() == 1,
            "single_display_manager": count_console_instances() == 1,
            "single_config_loader": count_configuration_loaders() == 1,
        },
        "usage": {
            "domains_use_shared": all_domains_use_shared_services(),
            "no_utility_duplication": no_duplicate_utility_code(),
        }
    }
    return validate_against_criteria(criteria)
```

## **Testing Validation Patterns**

### **Pattern: Test Architecture Alignment**
**Requirement**: Test structure must mirror source architecture

```python
def validate_test_alignment():
    """Ensure tests mirror source structure."""
    
    src_structure = get_directory_structure("src/")
    test_structure = get_directory_structure("tests/unit/")
    
    # Each src/ directory should have corresponding test/ directory
    for src_dir in src_structure:
        expected_test_dir = f"tests/unit/{src_dir}"
        if not os.path.exists(expected_test_dir):
            return False, f"Missing test directory for {src_dir}"
    
    return True, "Test structure aligned with source"
```

### **Pattern: Contract-Based Integration Testing**
**Requirement**: Integration tests validate domain contracts, not implementation

```python
def validate_domain_contracts():
    """Validate that domain contracts are properly tested."""
    
    contracts = [
        ("Content → AI", test_content_provides_ai_ready_format),
        ("AI → Organization", test_ai_provides_organization_ready_format),
        ("Interface → Orchestration", test_interface_routes_to_orchestration),
    ]
    
    for contract_name, contract_test in contracts:
        try:
            contract_test()
            print(f"PASS: {contract_name} contract validated")
        except Exception as e:
            print(f"FAIL: {contract_name} contract broken: {e}")
            return False
    
    return True
```

## **Common Validation Anti-Patterns**

### **❌ Anti-Pattern: Mock-Only Testing**
**Problem**: Mocking hides real integration issues
**Solution**: Use real domain services in integration tests

```python
# WRONG: Everything mocked
@patch("domains.content.ContentService")
@patch("domains.ai_integration.AIIntegrationService")  
def test_processing_workflow(mock_content, mock_ai):
    # Tests nothing real

# CORRECT: Test real integration with test doubles only for external services
def test_processing_workflow():
    container = TestApplicationContainer()  # Real services, test console
    kernel = container.create_application_kernel()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test real workflow with real domain services
        result = kernel.execute_processing(test_config)
        assert result.success
```

### **❌ Anti-Pattern: Validation Without Criteria**
**Problem**: Subjective "looks good" validation
**Solution**: Measurable pass/fail criteria

```python
# WRONG: Subjective validation
def validate_migration():
    if "architecture seems better":
        return True

# CORRECT: Objective validation
def validate_migration():
    return all([
        count_files_in_wrong_location() == 0,
        count_import_errors() == 0,
        count_security_issues() == 0,
        cli_commands_working() == True
    ])
```

## **Benefits of Validation-Driven Development**

### **Architectural Quality**
- **Prevents half-completed migrations** that create technical debt
- **Ensures real functionality** instead of compatibility layers
- **Validates architectural coherence** through measurable criteria
- **Exposes integration issues** early instead of hiding them

### **Development Confidence**  
- **Clear completion criteria** eliminate ambiguity
- **Evidence-based progress** tracking
- **Reliable integration** through contract validation
- **Predictable migration** outcomes

### **Team Trust**
- **Accountable development** with validation evidence
- **Consistent quality standards** across all architectural changes
- **Transparent progress** with measurable checkpoints
- **Reduced integration surprises** through systematic validation

This pattern ensures **architectural changes deliver real value** instead of creating **technical debt disguised as progress**.