#!/usr/bin/env python3
"""
Validation script for E2E BDD test structure
Ensures all files are properly structured and connected
"""

import os
import sys
from pathlib import Path

def validate_e2e_structure():
    """Validate E2E test structure and report findings"""
    
    base_dir = Path(__file__).parent
    results = {
        'feature_files': [],
        'step_definitions': [],
        'scenarios_count': 0,
        'errors': [],
        'warnings': []
    }
    
    print("Validating E2E BDD Test Structure")
    print("=" * 50)
    
    # 1. Check feature files
    feature_dirs = ['golden_path', 'error_recovery', 'workflows']
    
    for feature_dir in feature_dirs:
        dir_path = base_dir / feature_dir
        if not dir_path.exists():
            results['errors'].append(f"Missing directory: {feature_dir}")
            continue
            
        feature_files = list(dir_path.glob("*.feature"))
        if not feature_files:
            results['warnings'].append(f"No .feature files in {feature_dir}")
        
        for feature_file in feature_files:
            results['feature_files'].append(str(feature_file.relative_to(base_dir)))
            
            # Count scenarios in this file
            with open(feature_file, 'r', encoding='utf-8') as f:
                content = f.read()
                scenario_count = content.count("Scenario:")
                results['scenarios_count'] += scenario_count
    
    # 2. Check step definitions
    step_def_dir = base_dir.parent / "features" / "step_definitions"
    
    if not step_def_dir.exists():
        results['errors'].append("Missing step_definitions directory")
    else:
        step_files = list(step_def_dir.glob("*_steps.py"))
        for step_file in step_files:
            results['step_definitions'].append(step_file.name)
    
    # 3. Check for required step definition files
    required_step_files = [
        'golden_path_steps.py',
        'error_recovery_steps.py', 
        'workflow_steps.py'
    ]
    
    existing_step_files = [f for f in results['step_definitions']]
    for required_file in required_step_files:
        if required_file not in existing_step_files:
            results['errors'].append(f"Missing step definition file: {required_file}")
    
    # 4. Print results
    print(f"Feature Files Found: {len(results['feature_files'])}")
    for feature_file in results['feature_files']:
        print(f"   [+] {feature_file}")
    
    print(f"\nTotal Scenarios: {results['scenarios_count']}")
    
    print(f"\nStep Definition Files: {len(results['step_definitions'])}")
    for step_file in results['step_definitions']:
        print(f"   [+] {step_file}")
    
    if results['errors']:
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   [-] {error}")
    
    if results['warnings']:
        print(f"\nWarnings ({len(results['warnings'])}):")
        for warning in results['warnings']:
            print(f"   [!] {warning}")
    
    if not results['errors']:
        print("\n[SUCCESS] E2E BDD Structure Validation: PASSED")
        print(f"   Total Test Scenarios: {results['scenarios_count']}")
        print(f"   Target Achievement: {'EXCEEDED' if results['scenarios_count'] >= 20 else 'INSUFFICIENT'} (Target: 20-25)")
        print(f"   Coverage Categories: 3 (Golden Path, Error Recovery, Workflows)")
        print(f"   Step Definitions: {len(results['step_definitions'])} files")
        return True
    else:
        print("\n[FAILED] E2E BDD Structure Validation: FAILED")
        return False

if __name__ == "__main__":
    success = validate_e2e_structure()
    sys.exit(0 if success else 1)