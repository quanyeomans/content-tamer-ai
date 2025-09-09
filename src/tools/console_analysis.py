#!/usr/bin/env python3
"""
Console Creation Static Analysis Tool

Scans the codebase for direct Console() instantiations that violate
the singleton pattern architecture. This tool enforces the architectural
rule that all Console instances must go through ConsoleManager.

Used as part of quality gates to prevent Console creation regressions.
"""

import ast
import os
import sys
from typing import List, Dict, Any, NamedTuple
from pathlib import Path


class ConsoleCreation(NamedTuple):
    """Represents a detected Console creation in code."""
    file_path: str
    line_number: int
    column: int
    context: str
    creation_type: str  # 'direct', 'import_alias', 'attribute'


class ConsoleCreationDetector(ast.NodeVisitor):
    """AST visitor that detects Rich Console instantiations."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.console_creations: List[ConsoleCreation] = []
        self.source_lines: List[str] = []

        # Load source for context extraction
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.source_lines = f.readlines()
        except Exception:
            self.source_lines = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes to detect Console() creations."""
        creation_type = None

        # Direct Console() call
        if isinstance(node.func, ast.Name) and node.func.id == 'Console':
            creation_type = 'direct'

        # Module.Console() call (e.g., rich.console.Console())
        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'Console':
            creation_type = 'attribute'

        # Imported alias call (less common but possible)
        elif isinstance(node.func, ast.Name) and 'console' in node.func.id.lower():
            # Check if it might be a Console constructor alias
            creation_type = 'import_alias'

        if creation_type:
            context = self._get_line_context(node.lineno)
            creation = ConsoleCreation(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                context=context,
                creation_type=creation_type
            )
            self.console_creations.append(creation)

        # Continue visiting child nodes
        self.generic_visit(node)

    def _get_line_context(self, line_number: int) -> str:
        """Get the source code context around a line."""
        if not self.source_lines or line_number <= 0 or line_number > len(self.source_lines):
            return ""

        # Return the actual line, stripped of whitespace
        return self.source_lines[line_number - 1].strip()


def scan_file_for_console_creations(file_path: str) -> List[ConsoleCreation]:
    """
    Scan a single Python file for Console creations.

    Args:
        file_path: Path to Python file to scan

    Returns:
        List[ConsoleCreation]: Detected Console instantiations
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Parse the AST
        tree = ast.parse(source, filename=file_path)

        # Detect Console creations
        detector = ConsoleCreationDetector(file_path)
        detector.visit(tree)

        return detector.console_creations

    except Exception as e:
        print(f"Warning: Could not analyze {file_path}: {e}", file=sys.stderr)
        return []


def scan_directory_for_console_creations(directory: str, exclude_patterns: List[str] = None) -> List[ConsoleCreation]:
    """
    Recursively scan directory for Console creations.

    Args:
        directory: Root directory to scan
        exclude_patterns: File/directory patterns to exclude

    Returns:
        List[ConsoleCreation]: All detected Console instantiations
    """
    if exclude_patterns is None:
        exclude_patterns = [
            '__pycache__',
            '.pytest_cache',
            '.git',
            'node_modules',
            'venv',
            '.venv',
            'console_manager.py',  # Exclude our own Console management
            'console_analysis.py'  # Exclude this analysis tool
        ]

    all_creations = []

    for root, dirs, files in os.walk(directory):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]

        for file in files:
            if file.endswith('.py'):
                # Skip excluded files
                if any(pattern in file for pattern in exclude_patterns):
                    continue

                file_path = os.path.join(root, file)
                creations = scan_file_for_console_creations(file_path)
                all_creations.extend(creations)

    return all_creations


def analyze_console_creations(creations: List[ConsoleCreation]) -> Dict[str, Any]:
    """
    Analyze detected Console creations for reporting.

    Args:
        creations: List of detected Console creations

    Returns:
        Dict[str, Any]: Analysis summary
    """
    if not creations:
        return {
            'total_violations': 0,
            'files_affected': 0,
            'creation_types': {},
            'severity': 'NONE'
        }

    # Count by file
    files_affected = len(set(c.file_path for c in creations))

    # Count by creation type
    creation_types = {}
    for creation in creations:
        creation_types[creation.creation_type] = creation_types.get(creation.creation_type, 0) + 1

    # Determine severity
    total_violations = len(creations)
    if total_violations == 0:
        severity = 'NONE'
    elif total_violations <= 2:
        severity = 'LOW'
    elif total_violations <= 5:
        severity = 'MEDIUM'
    else:
        severity = 'HIGH'

    return {
        'total_violations': total_violations,
        'files_affected': files_affected,
        'creation_types': creation_types,
        'severity': severity
    }


def generate_report(creations: List[ConsoleCreation], analysis: Dict[str, Any]) -> str:
    """
    Generate a human-readable analysis report.

    Args:
        creations: List of detected Console creations
        analysis: Analysis summary

    Returns:
        str: Formatted report
    """
    if analysis['total_violations'] == 0:
        return """
[PASS] CONSOLE ANALYSIS: PASSED
No Console() instantiations found.
Architecture compliance: EXCELLENT
"""

    report = f"""
[FAIL] CONSOLE ANALYSIS: VIOLATIONS DETECTED
Severity: {analysis['severity']}
Total violations: {analysis['total_violations']}
Files affected: {analysis['files_affected']}

VIOLATIONS BY TYPE:
"""

    for creation_type, count in analysis['creation_types'].items():
        report += f"  {creation_type}: {count}\n"

    report += "\nDETAILED VIOLATIONS:\n"

    for creation in creations:
        relative_path = os.path.relpath(creation.file_path)
        report += f"""
File: {relative_path}:{creation.line_number}:{creation.column}
Type: {creation.creation_type}
Code: {creation.context}
"""

    report += """
REMEDIATION:
Replace direct Console() calls with:
- ConsoleManager.get_console() for application code
- create_test_console() for testing code
- Dependency injection through ApplicationContainer

ARCHITECTURE RULE:
All Console instances must go through ConsoleManager singleton.
"""

    return report


def main() -> None:
    """Main entry point for console analysis tool."""
    # Determine scan directory
    if len(sys.argv) > 1:
        scan_dir = sys.argv[1]
    else:
        # Default to src/ directory relative to this script
        script_dir = Path(__file__).parent
        scan_dir = script_dir.parent / 'src'

    if not os.path.exists(scan_dir):
        print(f"Error: Directory {scan_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {scan_dir} for Console() instantiations...")

    # Scan for violations
    creations = scan_directory_for_console_creations(str(scan_dir))
    analysis = analyze_console_creations(creations)

    # Generate and display report
    report = generate_report(creations, analysis)
    print(report)

    # Exit with appropriate code
    if analysis['total_violations'] > 0:
        print("\n[FAIL] CONSOLE ANALYSIS: FAILED")
        print("Architecture violations must be resolved before proceeding.")
        sys.exit(1)
    else:
        print("\n[PASS] CONSOLE ANALYSIS: PASSED")
        print("Architecture compliance verified.")
        sys.exit(0)


if __name__ == '__main__':
    main()
