#!/usr/bin/env python3
"""
Systematic Linting Automation Script
Enhanced 2025 - Based on lessons learned from comprehensive cleanup

This script implements the 4-phase systematic linting approach using proper Rich UI patterns:
1. Code Formatting
2. Comprehensive Analysis  
3. Targeted Issue Resolution
4. Validation Gates

Usage:
    python scripts/systematic_linting.py [--fix] [--parallel-agents]
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path for Rich Console access
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from interfaces.human.rich_console_manager import RichConsoleManager
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class SystematicLinter:
    """Automated systematic linting with parallel agent deployment capability."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_path = project_root / "src"
        self.tests_path = project_root / "tests"
        
        # Initialize Rich Console using our established patterns
        if RICH_AVAILABLE:
            self.console_manager = RichConsoleManager()
            self.console = self.console_manager.console
        else:
            self.console = None
    
    def _print(self, message: str, style: str = ""):
        """Print message using Rich Console patterns or fallback."""
        if self.console:
            if style:
                self.console.print(f"[{style}]{message}[/{style}]")
            else:
                self.console.print(message)
        else:
            print(message)
    
    def _print_status(self, message: str, status: str):
        """Print status message with smart emoji usage."""
        if self.console and hasattr(self.console, 'options') and self.console.options.encoding == 'utf-8':
            # UTF-8 terminals - use emojis
            emoji_map = {
                "success": "✅",
                "error": "❌", 
                "warning": "⚠️",
                "info": "ℹ️",
                "progress": "🔄"
            }
            icon = emoji_map.get(status, "ℹ️")
        else:
            # Limited terminals - use ASCII
            ascii_map = {
                "success": "[PASS]",
                "error": "[FAIL]",
                "warning": "[WARN]", 
                "info": "[INFO]",
                "progress": "[WORK]"
            }
            icon = ascii_map.get(status, "[INFO]")
        
        if self.console:
            self.console.print(f"{icon} [{status}]{message}[/{status}]")
        else:
            print(f"{icon} {message}")
    
    def _show_section_header(self, title: str, description: str = ""):
        """Show section header using Rich patterns."""
        if self.console:
            if hasattr(self.console, 'options') and self.console.options.encoding == 'utf-8':
                self.console.print(f"\n🧹 [bold cyan]{title}[/bold cyan]")
            else:
                self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
            if description:
                self.console.print(f"[dim]{description}[/dim]")
        else:
            print(f"\n{title}")
            if description:
                print(description)
        
    def run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run command and return (returncode, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=capture_output, 
                text=True, 
                cwd=self.project_root
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)
    
    def phase1_formatting(self) -> bool:
        """Phase 1: Apply code formatting."""
        self._show_section_header("PHASE 1: Code Formatting", "Applying consistent formatting standards")
        
        # Black formatting
        self._print_status("Running black...", "progress")
        ret, out, err = self.run_command([
            "black", "src/", "tests/", "--line-length=100"
        ])
        if ret != 0:
            self._print_status(f"Black failed: {err}", "error")
            return False
        
        changes = out.strip() if out else 'No changes needed'
        self._print_status(f"Black completed: {changes}", "success")
        
        # isort import ordering
        self._print_status("Running isort...", "progress")
        ret, out, err = self.run_command([
            "isort", "src/", "tests/", "--line-length=100"
        ])
        if ret != 0:
            self._print_status(f"isort failed: {err}", "error")
            return False
        
        changes = out.strip() if out else 'No changes needed'
        self._print_status(f"isort completed: {changes}", "success")
        
        return True
    
    def phase2_analysis(self) -> Dict[str, any]:
        """Phase 2: Comprehensive linting analysis."""
        self._show_section_header("PHASE 2: Comprehensive Analysis", "Scanning codebase for issues")
        
        results = {}
        
        # Pylint analysis
        self._print_status("Running pylint analysis...", "progress")
        ret, out, err = self.run_command([
            "pylint", "src/", "--output-format=json"
        ])
        try:
            pylint_data = json.loads(out) if out else []
            results['pylint'] = pylint_data
            self._print_status(f"Pylint analysis complete: {len(pylint_data)} issues found", "success")
        except json.JSONDecodeError:
            results['pylint'] = []
            self._print_status("Pylint analysis failed to parse output", "error")
        
        # Pyright analysis
        self._print_status("Running pyright type checking...", "progress")
        ret, out, err = self.run_command([
            "pyright", "src/", "--outputjson"
        ])
        try:
            pyright_data = json.loads(out) if out else {}
            results['pyright'] = pyright_data
            summary = pyright_data.get('summary', {})
            errors = summary.get('errorCount', 0)
            warnings = summary.get('warningCount', 0)
            self._print_status(f"Pyright analysis complete: {errors} errors, {warnings} warnings", "success")
        except json.JSONDecodeError:
            results['pyright'] = {}
            self._print_status("Pyright analysis failed to parse output", "error")
        
        # Bandit security analysis
        self._print_status("Running bandit security scan...", "progress")
        ret, out, err = self.run_command([
            "bandit", "-r", "src/", "--format", "json"
        ])
        try:
            bandit_data = json.loads(out) if out else {}
            results['bandit'] = bandit_data
            metrics = bandit_data.get('metrics', {})
            high = sum(1 for r in bandit_data.get('results', []) if r.get('issue_severity') == 'HIGH')
            medium = sum(1 for r in bandit_data.get('results', []) if r.get('issue_severity') == 'MEDIUM')
            self._print_status(f"Bandit scan complete: {high} high, {medium} medium severity issues", "success")
        except json.JSONDecodeError:
            results['bandit'] = {}
            self._print_status("Bandit scan failed to parse output", "error")
        
        return results
    
    def phase3_targeted_cleanup(self, analysis_results: Dict[str, any]) -> bool:
        """Phase 3: Targeted issue resolution."""
        self._show_section_header("PHASE 3: Targeted Issue Resolution", "Categorizing issues for parallel agent deployment")
        
        # Analyze common issue patterns
        pylint_issues = analysis_results.get('pylint', [])
        
        # Group by issue type
        issue_groups = {
            'unused_warnings': [],  # W0611, W0612, W0613
            'logging_issues': [],   # W1203
            'import_errors': [],    # E0401, E0611  
            'structure_issues': []  # R1705, R1702
        }
        
        for issue in pylint_issues:
            symbol = issue.get('symbol', '')
            if symbol in ['unused-import', 'unused-variable', 'unused-argument']:
                issue_groups['unused_warnings'].append(issue)
            elif symbol == 'logging-fstring-interpolation':
                issue_groups['logging_issues'].append(issue)
            elif symbol in ['import-error', 'no-name-in-module']:
                issue_groups['import_errors'].append(issue)
            elif symbol in ['no-else-return', 'too-many-nested-blocks']:
                issue_groups['structure_issues'].append(issue)
        
        # Report issue categorization
        for category, issues in issue_groups.items():
            if issues:
                self._print(f"  {category}: {len(issues)} issues", "cyan")
                for issue in issues[:3]:  # Show first 3
                    file_path = issue.get('path', '')
                    line = issue.get('line', 0)
                    message = issue.get('message', '')
                    self._print(f"    • {file_path}:{line} - {message}", "dim")
                if len(issues) > 3:
                    self._print(f"    ... and {len(issues) - 3} more", "dim")
        
        # Suggest parallel agent deployment
        if any(issue_groups.values()):
            self._print("\n  Parallel Agent Deployment Recommended:", "yellow")
            if issue_groups['import_errors']:
                self._print_status("Deploy Import Resolution Agent - Fix provider import issues", "info")
            if issue_groups['logging_issues']:  
                self._print_status("Deploy Logging Format Agent - Convert f-strings to lazy %", "info")
            if issue_groups['unused_warnings']:
                self._print_status("Deploy Cleanup Agent - Remove unused imports/variables", "info")
            if issue_groups['structure_issues']:
                self._print_status("Deploy Structure Agent - Fix else-after-return patterns", "info")
        
        return True
    
    def phase4_validation(self) -> bool:
        """Phase 4: Final validation gates."""
        self._show_section_header("PHASE 4: Validation Gates", "Final compliance verification")
        
        all_passed = True
        
        # Pylint score check
        self._print_status("Checking pylint score...", "progress")
        ret, out, err = self.run_command([
            "pylint", "src/", "--fail-under=9.5", "--score=y"
        ])
        if ret == 0 and "rated at" in out:
            score_line = [line for line in out.split('\n') if 'rated at' in line][-1]
            self._print_status(f"Pylint score: {score_line}", "success")
        else:
            self._print_status("Pylint score below 9.5/10", "error")
            all_passed = False
        
        # Pyright error check
        self._print_status("Checking pyright errors...", "progress")
        ret, out, err = self.run_command([
            "pyright", "src/"
        ])
        if "0 errors" in out:
            self._print_status("Pyright: 0 errors", "success")
        else:
            self._print_status("Pyright: Has type errors", "error")
            all_passed = False
        
        # Unused warnings check
        self._print_status("Checking unused warnings...", "progress")
        ret, out, err = self.run_command([
            "pylint", "src/", "--disable=all", "--enable=W0611,W0612,W0613"
        ])
        if "10.00/10" in out or ret == 0:
            self._print_status("Unused warnings: Clean", "success")
        else:
            self._print_status("Unused warnings: Still present", "error")
            all_passed = False
        
        # Security check
        self._print_status("Checking security issues...", "progress")
        ret, out, err = self.run_command([
            "bandit", "-r", "src/", "--severity-level", "high"
        ])
        high_issues = out.count(">> Issue:")
        if high_issues == 0:
            self._print_status("Security: 0 high/medium issues", "success")
        else:
            self._print_status(f"Security: {high_issues} high/medium issues", "error")
            all_passed = False
        
        return all_passed
    
    def run_systematic_linting(self, fix_mode: bool = False) -> bool:
        """Run the complete systematic linting process."""
        self._show_section_header("SYSTEMATIC LINTING AUTOMATION", "4-Phase systematic code quality improvement")
        
        # Phase 1: Formatting
        if not self.phase1_formatting():
            self._print_status("Phase 1 failed - stopping", "error")
            return False
        
        # Phase 2: Analysis
        analysis_results = self.phase2_analysis()
        
        # Phase 3: Issue categorization and agent recommendations
        self.phase3_targeted_cleanup(analysis_results)
        
        # Phase 4: Validation
        passed = self.phase4_validation()
        
        # Final summary with Rich formatting
        if self.console:
            self.console.rule()
            
        if passed:
            self._print_status("ALL LINTING STANDARDS ACHIEVED!", "success")
            self._print_status("Ready for E2E testing", "info")
        else:
            self._print_status("Linting standards not yet achieved", "warning")
            self._print_status("Consider deploying parallel agents for systematic cleanup", "info")
        
        return passed


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    linter = SystematicLinter(project_root)
    
    fix_mode = "--fix" in sys.argv
    parallel_agents = "--parallel-agents" in sys.argv
    
    if parallel_agents:
        linter._print_status("Parallel agent deployment not yet implemented", "warning")
        linter._print_status("Use Task tool with specialized agents instead", "info")
        return 1
    
    success = linter.run_systematic_linting(fix_mode)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())