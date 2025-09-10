"""
Pytest File System Utilities - tmp_path-based test environment management

Provides standardized utilities for creating test file environments using pytest's
tmp_path fixtures instead of manual tempfile management. Eliminates race conditions
and ensures proper cleanup through pytest's built-in fixture lifecycle.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


def create_processing_directories(tmp_path: Path) -> Dict[str, Path]:
    """
    Create standard processing directories structure.
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        Dict[str, Path]: Dictionary containing directory paths
    """
    directories = {
        "input": tmp_path / "input",
        "output": tmp_path / "output", 
        "processed": tmp_path / "processed",
        "unprocessed": tmp_path / "unprocessed",
        "temp": tmp_path / "temp"
    }
    
    # Create all directories
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        
    return directories


def create_test_files(base_path: Path, file_specs: List[Tuple[str, str]]) -> List[Path]:
    """
    Create test files with specified content.
    
    Args:
        base_path: Base directory path
        file_specs: List of (filename, content) tuples
        
    Returns:
        List[Path]: Created file paths
    """
    created_files = []
    
    for filename, content in file_specs:
        file_path = base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        created_files.append(file_path)
        
    return created_files


def create_realistic_test_documents(input_dir: Path) -> List[Path]:
    """
    Create realistic test documents for organization workflow testing.
    
    Args:
        input_dir: Input directory path
        
    Returns:
        List[Path]: Created file paths
    """
    file_specs = [
        (
            "invoice_abc_company_2024.pdf",
            "Invoice from ABC Company dated March 15, 2024. Amount due: $1,250.00. Service period: February 2024. Payment terms: Net 30 days. Invoice number: INV-2024-001.",
        ),
        (
            "contract_legal_services.pdf",
            "Legal services agreement between XYZ Law Firm and client for consulting services. Term: 12 months starting January 2024. Retainer: $5,000. Hourly rate: $250.",
        ),
        (
            "receipt_office_supplies.pdf",
            "Receipt for office supplies purchased from Supply Store. Date: 2024-03-10. Total: $89.45. Items: paper, pens, folders. Receipt #R-12345.",
        ),
        (
            "bank_statement_jan_2024.pdf",
            "Monthly bank statement for January 2024. Account summary and transaction details included. Beginning balance: $10,000. Ending balance: $12,500.",
        ),
        (
            "medical_report_consultation.pdf",
            "Medical consultation report from Dr. Smith, MD. Patient visit date: March 8, 2024. Diagnosis and treatment plan. Follow-up required in 30 days.",
        ),
    ]
    
    return create_test_files(input_dir, file_specs)


def create_mixed_content_documents(input_dir: Path) -> List[Path]:
    """
    Create diverse test documents with various content patterns.
    
    Args:
        input_dir: Input directory path
        
    Returns:
        List[Path]: Created file paths
    """
    file_specs = [
        (
            "financial_report_q1.pdf",
            "Quarterly financial report Q1 2024. Revenue: $50,000. Expenses: $35,000. Net profit analysis.",
        ),
        (
            "employee_handbook.pdf",
            "Company employee handbook. Policies, procedures, and benefits information for all staff members.",
        ),
        (
            "technical_specification.pdf",
            "Technical specifications for software development project. API documentation and system requirements.",
        ),
        (
            "marketing_proposal.pdf",
            "Marketing campaign proposal for product launch. Target demographics and budget allocation details.",
        ),
        (
            "utility_bill_march.pdf",
            "Utility bill for March 2024. Electricity usage: 450 kWh. Amount due: $125.67.",
        ),
        (
            "insurance_policy.pdf",
            "Insurance policy document. Coverage details, premium information, and terms and conditions.",
        ),
        (
            "research_paper.pdf",
            "Academic research paper on machine learning applications. Published in Journal of AI Research 2024.",
        ),
    ]
    
    return create_test_files(input_dir, file_specs)


def create_temporal_test_documents(input_dir: Path) -> List[Path]:
    """
    Create test documents with clear temporal patterns.
    
    Args:
        input_dir: Input directory path
        
    Returns:
        List[Path]: Created file paths
    """
    file_specs = [
        (
            "invoice_jan_2024.pdf",
            "Invoice #001 dated January 15, 2024. First quarter billing cycle.",
        ),
        (
            "invoice_feb_2024.pdf",
            "Invoice #002 dated February 15, 2024. First quarter billing cycle.",
        ),
        (
            "invoice_mar_2024.pdf",
            "Invoice #003 dated March 15, 2024. First quarter billing cycle.",
        ),
        (
            "report_q1_2024.pdf",
            "Q1 2024 quarterly report. January-March analysis and performance metrics.",
        ),
        (
            "statement_fy2024.pdf",
            "Annual statement for fiscal year 2024. July 2023 - June 2024 period.",
        ),
        ("tax_return_2023.pdf", "Tax return for calendar year 2023. Filed in April 2024."),
        (
            "budget_fy2025.pdf",
            "Budget planning for fiscal year 2025. Projected expenditures and revenue.",
        ),
    ]
    
    return create_test_files(input_dir, file_specs)


def create_config_test_environment(tmp_path: Path, config_data: Optional[Dict] = None) -> Path:
    """
    Create a test configuration environment.
    
    Args:
        tmp_path: pytest tmp_path fixture
        config_data: Optional configuration data to write
        
    Returns:
        Path: Configuration directory path
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    if config_data:
        import json
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    
    return config_dir


def create_dependency_test_environment(tmp_path: Path) -> Tuple[Path, Path]:
    """
    Create test environment for dependency management testing.
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        Tuple[Path, Path]: (config_dir, dependencies_file)
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock dependencies file
    deps_file = config_dir / "dependencies.json"
    deps_data = {
        "tesseract": {"path": "/usr/bin/tesseract", "version": "5.3.0"},
        "ollama": {"path": "/usr/local/bin/ollama", "version": "0.1.26"}
    }
    
    import json
    deps_file.write_text(json.dumps(deps_data, indent=2), encoding="utf-8")
    
    return config_dir, deps_file


def create_organization_test_environment(tmp_path: Path) -> Dict[str, Path]:
    """
    Create test environment for organization service testing.
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        Dict[str, Path]: Dictionary containing environment paths
    """
    env = create_processing_directories(tmp_path)
    
    # Add organization-specific directories
    env["content_tamer"] = tmp_path / ".content_tamer"
    env["organization"] = env["content_tamer"] / "organization" 
    env["learning"] = env["content_tamer"] / "learning"
    env["clustering"] = env["content_tamer"] / "clustering"
    
    # Create organization directories
    for key in ["content_tamer", "organization", "learning", "clustering"]:
        env[key].mkdir(parents=True, exist_ok=True)
    
    return env


def setup_bdd_test_context(tmp_path: Path) -> Dict[str, Union[Path, str]]:
    """
    Set up BDD test context with standard directories and attributes.
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        Dict[str, Union[Path, str]]: Context dictionary with paths and attributes
    """
    dirs = create_processing_directories(tmp_path)
    
    context = {
        "temp_dir": tmp_path,
        "input_dir": dirs["input"],
        "processed_dir": dirs["processed"],
        "unprocessed_dir": dirs["unprocessed"],
        "output_dir": dirs["output"],
        "user_type": "new_user",
        "test_files": [],
        "console_output": None,
    }
    
    return context


def create_platform_test_environment(tmp_path: Path) -> Dict[str, Union[Path, str, List]]:
    """
    Create platform-specific test environment.
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        Dict[str, Union[Path, str, List]]: Platform test context
    """
    import platform
    from io import StringIO
    
    return {
        "temp_dir": tmp_path,
        "platform_name": platform.system(),
        "test_files": [],
        "display_output": StringIO(),
    }


def get_legacy_temp_dir_as_string(tmp_path: Path) -> str:
    """
    Convert tmp_path to string for legacy code compatibility.
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        str: Temporary directory path as string
    """
    return str(tmp_path)


def create_security_test_files(tmp_path: Path) -> Tuple[List[str], Path]:
    """
    Create files for security testing (path traversal, etc).
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        Tuple[List[str], Path]: (dangerous_paths, safe_directory)
    """
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir(parents=True, exist_ok=True)
    
    # These are the dangerous paths that should be validated against
    dangerous_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/shadow",
        "C:\\Windows\\System32\\config\\SAM",
        "..\\..\\..\\..\\..\\..\\..\\..\\..\\..\\.\\etc\\passwd",
        "../../../../../../../../etc/passwd%00.txt",
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "..%252F..%252F..%252Fetc%252Fpasswd",
    ]
    
    return dangerous_paths, safe_dir


# Context managers for complex test scenarios

class TestFileEnvironment:
    """
    Context manager for complex file test environments.
    
    Provides a comprehensive test file environment with automatic cleanup
    through pytest tmp_path fixture lifecycle.
    """
    
    def __init__(self, tmp_path: Path, environment_type: str = "standard"):
        """
        Initialize test file environment.
        
        Args:
            tmp_path: pytest tmp_path fixture
            environment_type: Type of environment ('standard', 'organization', 'bdd', 'security')
        """
        self.tmp_path = tmp_path
        self.environment_type = environment_type
        self.directories = {}
        self.files = []
        
    def __enter__(self) -> "TestFileEnvironment":
        """Set up the test environment."""
        if self.environment_type == "standard":
            self.directories = create_processing_directories(self.tmp_path)
        elif self.environment_type == "organization":
            self.directories = create_organization_test_environment(self.tmp_path)
        elif self.environment_type == "bdd":
            self.directories = setup_bdd_test_context(self.tmp_path)
        elif self.environment_type == "security":
            dangerous_paths, safe_dir = create_security_test_files(self.tmp_path)
            self.directories = {"safe": safe_dir}
            self.dangerous_paths = dangerous_paths
        else:
            self.directories = create_processing_directories(self.tmp_path)
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up handled automatically by pytest tmp_path fixture."""
        # No manual cleanup needed - pytest handles tmp_path cleanup
        pass
        
    def create_files(self, file_specs: List[Tuple[str, str]], target_dir: str = "input") -> List[Path]:
        """
        Create test files in the environment.
        
        Args:
            file_specs: List of (filename, content) tuples
            target_dir: Target directory key from self.directories
            
        Returns:
            List[Path]: Created file paths
        """
        target_path = self.directories[target_dir]
        created_files = create_test_files(target_path, file_specs)
        self.files.extend(created_files)
        return created_files
        
    def get_path(self, key: str) -> Path:
        """Get path for directory key."""
        return self.directories[key]
        
    def get_string_path(self, key: str) -> str:
        """Get string path for legacy compatibility."""
        return str(self.directories[key])