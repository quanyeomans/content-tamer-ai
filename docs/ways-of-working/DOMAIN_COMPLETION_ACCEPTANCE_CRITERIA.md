# Domain Completion Acceptance Criteria
*Measurable criteria for declaring a domain complete during iterative cleanup*

## Overview

Each domain must meet **all acceptance criteria** before being considered complete. No domain cleanup is finished until **every criterion passes validation**.

## **Mandatory Acceptance Criteria**

### **1. Working Test Coverage (MANDATORY)**

#### **✅ PASS Thresholds**
```bash
# Unit Tests (Domain Isolation)
pytest tests/unit/domains/{domain}/ -v                    # Must: 90%+ pass rate
pytest tests/unit/domains/{domain}/ --cov=src/domains/{domain} # Must: 85%+ coverage

# Integration Tests (Cross-Domain Contracts)  
pytest tests/integration/cross_domain/ -k {domain} -v     # Must: 80%+ pass rate

# E2E Tests (User Journey Impact)
pytest tests/e2e/ -k {domain} -v                         # Must: No regressions
```

#### **❌ FAIL Conditions**
- Any test collection errors (ImportError, ModuleNotFoundError)
- Test pass rate below thresholds
- Missing tests for critical domain functionality
- Tests that don't actually validate domain services

#### **Validation Script**
```bash
#!/bin/bash
domain=$1
echo "Testing domain: $domain"

# Unit test validation
unit_result=$(python -m pytest tests/unit/domains/$domain/ --tb=no -q)
unit_pass_rate=$(echo "$unit_result" | grep -o '[0-9]*% passed' | grep -o '[0-9]*')

if [ ${unit_pass_rate:-0} -lt 90 ]; then
    echo "FAIL: Unit tests below 90% ($unit_pass_rate%)"
    exit 1
fi

echo "PASS: Unit tests $unit_pass_rate%"
```

### **2. Code Quality Linting (MANDATORY)**

#### **✅ PASS Thresholds**
```bash
# PyLint Score (Code Quality)
pylint src/domains/{domain}/ --fail-under=8.5             # Must: 8.5+/10 score

# Flake8 Style Compliance  
flake8 src/domains/{domain}/ --max-line-length=100        # Must: 0 errors

# MyPy Type Safety
mypy src/domains/{domain}/ --ignore-missing-imports       # Must: 0 type errors

# Import Quality
python -c "check_import_violations('src/domains/{domain}')" # Must: 0 cross-layer imports
```

#### **❌ FAIL Conditions**
- PyLint score below 8.5/10
- Any Flake8 style violations
- MyPy type errors
- Cross-layer import violations (domains importing from core/, etc.)

#### **Quality Standards**
```python
DOMAIN_QUALITY_REQUIREMENTS = {
    "pylint_minimum": 8.5,    # Higher than general codebase (8.0)
    "flake8_errors": 0,       # Zero tolerance for style violations
    "mypy_errors": 0,         # Zero tolerance for type errors  
    "complex_functions": 3,   # Max functions with complexity >12
    "duplicate_code": 5,      # Max % duplicate code within domain
}
```

### **3. DRY/SOLID Evaluation (MANDATORY)**

#### **✅ PASS Criteria**

##### **DRY (Don't Repeat Yourself)**
```bash
# Code Duplication Analysis
python -c "
import ast
duplicates = find_duplicate_code_blocks('src/domains/{domain}/')
if len(duplicates) > 5:
    print(f'FAIL: {len(duplicates)} duplicate code blocks')
    exit(1)
print(f'PASS: {len(duplicates)} duplicate blocks (acceptable)')
"
```

##### **SOLID Principles**
```python
# Single Responsibility Principle
classes_with_multiple_responsibilities = count_multi_responsibility_classes(domain)
# Must: <10% of classes have multiple responsibilities

# Open/Closed Principle  
hard_coded_dependencies = count_hard_coded_dependencies(domain)
# Must: <5% of methods have hard-coded dependencies

# Interface Segregation
fat_interfaces = count_fat_interfaces(domain) 
# Must: <2 interfaces with >10 methods

# Dependency Inversion
concrete_dependencies = count_concrete_dependencies(domain)
# Must: <10% of classes depend on concrete implementations
```

#### **❌ FAIL Conditions**
- >5% duplicate code within domain
- >10% classes violating Single Responsibility
- >5% methods with hard-coded dependencies
- Any violation of domain boundary isolation

### **4. SAST Security Compliance (MANDATORY)**

#### **✅ PASS Requirements**
```bash
# Security Vulnerability Scan
bandit -r src/domains/{domain}/ -f json                   # Must: 0 HIGH/MEDIUM issues

# Dependency Security  
safety check --json                                       # Must: 0 vulnerable dependencies

# Secret Detection
grep -r "api.*key\|password\|token" src/domains/{domain}/ # Must: 0 hardcoded secrets
```

#### **❌ FAIL Conditions**
- Any HIGH or MEDIUM security vulnerabilities
- Any vulnerable dependencies specific to domain
- Any hardcoded secrets or credentials
- Any command injection or path traversal vulnerabilities

#### **Security Standards**
```python
DOMAIN_SECURITY_REQUIREMENTS = {
    "bandit_high_issues": 0,      # Zero high-severity issues
    "bandit_medium_issues": 0,    # Zero medium-severity issues  
    "hardcoded_secrets": 0,       # Zero secret leaks
    "sql_injection_risks": 0,     # Zero SQL injection points
    "path_traversal_risks": 0,    # Zero path traversal vulnerabilities
}
```

## **Domain-Specific Acceptance Criteria**

### **Content Domain**

#### **Functional Requirements**
- ✅ All file types (PDF, images) processable through domain service
- ✅ Content extraction working with multiple methods (PyMuPDF, pypdf, OCR)
- ✅ Content enhancement providing AI-ready output
- ✅ Metadata extraction analyzing documents comprehensively

#### **Architecture Requirements**
- ✅ No dependencies on AI or Organization domains
- ✅ Only uses shared services (file operations, display)
- ✅ Clean service interfaces for orchestration layer

### **AI Integration Domain**

#### **Functional Requirements**
- ✅ All 5 providers (OpenAI, Claude, Gemini, Deepseek, Local) working
- ✅ Provider service can create and validate all providers
- ✅ Model service provides hardware-appropriate recommendations
- ✅ Request service handles retries and errors properly

#### **Architecture Requirements**
- ✅ No dependencies on Content or Organization domains
- ✅ Providers isolated in providers/ subdirectory
- ✅ Clean service interfaces for orchestration layer

### **Organization Domain**

#### **Functional Requirements**
- ✅ Document clustering working with progressive enhancement
- ✅ Folder service managing directory operations safely
- ✅ Learning service tracking and improving organization quality
- ✅ Integration with PRD_04 specification requirements

#### **Architecture Requirements**
- ✅ No dependencies on Content or AI domains
- ✅ State management isolated per target folder
- ✅ Clean service interfaces for orchestration layer

## **Validation Protocol**

### **Pre-Domain Cleanup Checklist**
Before starting cleanup of any domain:
- [ ] **All acceptance criteria defined** with measurable thresholds
- [ ] **Validation script created** for objective pass/fail determination
- [ ] **Current baseline measured** to track improvement
- [ ] **Domain boundaries confirmed** through import analysis

### **During Domain Cleanup Protocol**
1. **Make incremental changes** to improve specific quality metrics
2. **Run validation after each change** to ensure no regressions
3. **Stop if any acceptance criteria fails** and fix before proceeding
4. **Document improvements made** with evidence of quality gains

### **Post-Domain Cleanup Validation**
```bash
#!/bin/bash
validate_domain_completion() {
    domain=$1
    
    echo "=== DOMAIN COMPLETION VALIDATION: $domain ==="
    
    # 1. Test Coverage
    test_result=$(python -m pytest tests/unit/domains/$domain/ --tb=no -q)
    test_pass_rate=$(echo "$test_result" | grep -o '[0-9]*% passed' | grep -o '[0-9]*')
    
    if [ ${test_pass_rate:-0} -lt 90 ]; then
        echo "FAIL: Tests below 90% (${test_pass_rate}%)"
        return 1
    fi
    
    # 2. Code Quality  
    pylint_score=$(pylint src/domains/$domain/ --score=y | grep "Your code has been rated" | grep -o '[0-9.]*')
    
    if (( $(echo "$pylint_score < 8.5" | bc -l) )); then
        echo "FAIL: PyLint below 8.5 ($pylint_score)"
        return 1
    fi
    
    # 3. Security Scan
    bandit_issues=$(bandit -r src/domains/$domain/ -f json | jq '.results | length')
    
    if [ $bandit_issues -gt 0 ]; then
        echo "FAIL: $bandit_issues security issues found"
        return 1
    fi
    
    # 4. DRY/SOLID Check (simplified)
    import_violations=$(grep -r "from core\." src/domains/$domain/ | wc -l)
    
    if [ $import_violations -gt 0 ]; then
        echo "FAIL: $import_violations cross-layer import violations"
        return 1
    fi
    
    echo "PASS: All acceptance criteria met"
    echo "DOMAIN COMPLETION: VALIDATED"
    return 0
}
```

## **Domain Completion Order**

### **Recommended Sequence**
1. **Content Domain** (least dependencies, foundational)
2. **AI Integration Domain** (depends on content for input)
3. **Organization Domain** (depends on both content and AI results)

### **Success Metrics**
- **Domain completion time**: Target 2-3 hours per domain
- **Quality improvement**: Measurable gains in all criteria
- **Regression prevention**: No existing functionality broken
- **Test reliability**: Domain tests remain stable after completion

## **Commitment Protocol**

### **No Premature Completion**
- **ALL criteria must pass** before declaring domain complete
- **Evidence required** for each acceptance criterion  
- **Validation script must pass** before moving to next domain
- **No exceptions or "good enough"** - criteria are mandatory

### **Quality Gates**
- **Stop when validation fails** and fix specific issues
- **Re-run full validation** after any fixes
- **Document completion evidence** with specific metrics
- **Only proceed** when all criteria verified as PASS

This framework ensures **each domain is truly complete** and **maintainable** before moving to the next, preventing the accumulation of technical debt during cleanup.

**Ready to begin with Content Domain using these criteria?**