#!/usr/bin/env python3
"""
Segmented Test Runner - Addresses the 3 fundamental test execution issues:

1. Properly segmented tests based on code change analysis (not monolithic)
2. Sequenced execution isolating slow runners from fast feedback
3. Atomic performance evaluation with appropriate timeouts

Usage:
    python scripts/segmented_test_runner.py [--changed-files file1.py,file2.py]
    python scripts/segmented_test_runner.py --segment=fast
    python scripts/segmented_test_runner.py --all-segments
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add src to path for Rich Console access
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from interfaces.human.rich_console_manager import RichConsoleManager
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class SegmentedTestRunner:
    """Intelligent test execution based on code change analysis and performance profiling."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
        # Initialize Rich Console
        if RICH_AVAILABLE:
            self.console_manager = RichConsoleManager()
            self.console = self.console_manager.console
        else:
            self.console = None
        
        # Test segmentation based on actual performance analysis
        self.test_segments = {
            "fast": {
                "patterns": [
                    "tests/unit/shared/infrastructure/test_dependency_manager.py",
                    "tests/unit/shared/infrastructure/test_error_handling.py", 
                    "tests/unit/shared/infrastructure/test_filename_config.py",
                    "tests/unit/shared/infrastructure/test_security.py",
                    "tests/unit/shared/file_operations/",
                    "tests/unit/shared/display/test_cli_display.py",
                    "tests/unit/shared/display/test_progress_display.py",
                ],
                "timeout": 30,
                "expected_duration": "< 15 seconds",
                "description": "Infrastructure and utilities - fast feedback"
            },
            "medium": {
                "patterns": [
                    "tests/unit/domains/content/",
                    "tests/unit/shared/display/test_display_manager.py",
                    "tests/unit/shared/display/test_rich_testing_utils.py", 
                    "tests/unit/orchestration/",
                    "tests/unit/domains/ai_integration/test_hardware_detection.py"
                ],
                "timeout": 120, 
                "expected_duration": "< 1 minute",
                "description": "Content processing and basic domain services"
            },
            "slow": {
                "patterns": [
                    "tests/unit/domains/organization/test_clustering_service.py",
                    "tests/unit/domains/organization/test_learning_service.py",
                    "tests/unit/domains/organization/test_organization_service.py",
                    "tests/unit/domains/ai_integration/test_model_service.py"
                ],
                "timeout": 600,
                "expected_duration": "1-5 minutes",  
                "description": "ML-heavy organization and model services"
            },
            "contracts": {
                "patterns": [
                    "tests/contracts/"
                ],
                "timeout": 180,
                "expected_duration": "< 3 minutes",
                "description": "Component contract validation"
            },
            "integration": {
                "patterns": [
                    "tests/integration/",
                    "tests/domains/"
                ],
                "timeout": 300,
                "expected_duration": "< 5 minutes", 
                "description": "Cross-component interaction testing"
            },
            "e2e": {
                "patterns": [
                    "tests/e2e/",
                    "tests/features/"
                ],
                "timeout": 1200,
                "expected_duration": "5-20 minutes",
                "description": "End-to-end user workflow validation"
            }
        }
        
        # Code-to-test dependency mapping for targeted execution
        self.code_to_tests = {
            "src/domains/ai_integration/": ["fast", "medium"],  # Skip slow org tests
            "src/domains/content/": ["medium", "integration"],  # Content-focused
            "src/domains/organization/": ["slow", "integration", "e2e"],  # Full pyramid
            "src/shared/infrastructure/": ["fast"],  # Infrastructure only
            "src/shared/display/": ["fast", "medium", "contracts"],  # Display focused
            "src/shared/file_operations/": ["fast", "medium", "integration"],  # File ops
            "src/interfaces/": ["medium", "integration", "e2e"],  # Interface testing
            "src/orchestration/": ["medium", "integration", "e2e"],  # Full workflow
            "src/main.py": ["integration", "e2e"],  # Entry point testing
        }
    
    def _print_status(self, message: str, status: str):
        """Print status with smart emoji usage."""
        if self.console and hasattr(self.console, 'options') and self.console.options.encoding == 'utf-8':
            emoji_map = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️", "progress": "🔄"}
            icon = emoji_map.get(status, "ℹ️")
        else:
            ascii_map = {"success": "[PASS]", "error": "[FAIL]", "warning": "[WARN]", "info": "[INFO]", "progress": "[WORK]"}
            icon = ascii_map.get(status, "[INFO]")
        
        if self.console:
            self.console.print(f"{icon} [{status}]{message}[/{status}]")
        else:
            print(f"{icon} {message}")
    
    def analyze_changed_files(self, changed_files: List[str]) -> Set[str]:
        """Determine which test segments to run based on changed files."""
        required_segments = set()
        
        for file_path in changed_files:
            # Normalize path
            norm_path = file_path.replace('\\', '/').replace('//', '/')
            
            # Map to test segments
            for code_pattern, segments in self.code_to_tests.items():
                if norm_path.startswith(code_pattern):
                    required_segments.update(segments)
                    break
        
        # If no specific mapping, run all segments (safe default)
        if not required_segments:
            required_segments = set(self.test_segments.keys())
            
        return required_segments
    
    def run_test_segment(self, segment_name: str) -> Tuple[bool, Dict]:
        """Run a specific test segment with appropriate timeout and sequencing."""
        segment = self.test_segments[segment_name]
        
        self._print_status(f"Running {segment_name} tests: {segment['description']}", "progress")
        self._print_status(f"Expected duration: {segment['expected_duration']}", "info")
        
        # Build pytest command
        test_patterns = []
        for pattern in segment["patterns"]:
            if os.path.exists(pattern):
                test_patterns.append(pattern)
        
        if not test_patterns:
            self._print_status(f"No tests found for {segment_name} segment", "warning")
            return True, {"passed": 0, "failed": 0, "duration": 0}
        
        cmd = [
            "python", "-m", "pytest",
            *test_patterns,
            "--tb=short",
            "-v",
            f"--timeout={segment['timeout']}"
        ]
        
        # Execute with timing
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=segment['timeout'] + 30  # Buffer for pytest overhead
            )
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            output = result.stdout
            passed_tests = output.count(" PASSED")
            failed_tests = output.count(" FAILED") 
            
            # Report results
            if failed_tests == 0:
                self._print_status(f"{segment_name}: {passed_tests} PASSED in {duration:.1f}s", "success")
            else:
                self._print_status(f"{segment_name}: {passed_tests} PASSED, {failed_tests} FAILED in {duration:.1f}s", "warning")
                
                # Show first few failures for immediate feedback
                failure_lines = [line for line in output.split('\n') if 'FAILED' in line]
                for failure in failure_lines[:3]:
                    self._print_status(f"  → {failure.strip()}", "error")
                    
            return failed_tests == 0, {
                "passed": passed_tests,
                "failed": failed_tests, 
                "duration": duration,
                "output": output,
                "errors": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            self._print_status(f"{segment_name}: TIMEOUT after {duration:.1f}s", "error")
            return False, {"timeout": True, "duration": duration}
        except Exception as e:
            self._print_status(f"{segment_name}: EXECUTION ERROR: {e}", "error")
            return False, {"error": str(e)}
    
    def run_targeted_execution(self, changed_files: List[str] = None) -> Dict[str, any]:
        """Run tests based on changed files analysis."""
        if changed_files:
            self._print_status(f"Analyzing {len(changed_files)} changed files for test targeting", "info")
            required_segments = self.analyze_changed_files(changed_files)
            self._print_status(f"Required test segments: {', '.join(sorted(required_segments))}", "info")
        else:
            self._print_status("No specific files changed - running all segments", "info") 
            required_segments = set(self.test_segments.keys())
        
        results = {}
        overall_success = True
        
        # Execute segments in optimal order (fast -> slow)
        execution_order = ["fast", "medium", "contracts", "slow", "integration", "e2e"]
        segments_to_run = [seg for seg in execution_order if seg in required_segments]
        
        for segment in segments_to_run:
            success, result = self.run_test_segment(segment)
            results[segment] = result
            
            if not success:
                overall_success = False
                
                # For fast/medium tests, failure is blocking
                if segment in ["fast", "medium"]:
                    self._print_status(f"Critical {segment} test failures - stopping execution", "error") 
                    break
        
        return {
            "overall_success": overall_success,
            "segment_results": results,
            "segments_run": segments_to_run
        }
    
    def run_single_segment(self, segment_name: str) -> bool:
        """Run a single test segment for focused debugging."""
        if segment_name not in self.test_segments:
            self._print_status(f"Unknown segment: {segment_name}", "error")
            self._print_status(f"Available: {', '.join(self.test_segments.keys())}", "info")
            return False
        
        success, result = self.run_test_segment(segment_name)
        return success
    
    def show_segment_info(self):
        """Display test segmentation information."""
        self._print_status("Test Segmentation Configuration", "info")
        
        for segment_name, config in self.test_segments.items():
            self._print_status(f"{segment_name}: {config['description']}", "info")
            self._print_status(f"  Timeout: {config['timeout']}s, Expected: {config['expected_duration']}", "info")


def main():
    """Main entry point for segmented test execution."""
    parser = argparse.ArgumentParser(description="Segmented test execution for efficient CI/CD")
    parser.add_argument("--changed-files", help="Comma-separated list of changed files")
    parser.add_argument("--segment", help="Run specific segment only") 
    parser.add_argument("--all-segments", action="store_true", help="Run all segments in sequence")
    parser.add_argument("--info", action="store_true", help="Show segmentation info")
    
    args = parser.parse_args()
    runner = SegmentedTestRunner()
    
    if args.info:
        runner.show_segment_info()
        return 0
    
    if args.segment:
        success = runner.run_single_segment(args.segment)
        return 0 if success else 1
    
    # Parse changed files
    changed_files = []
    if args.changed_files:
        changed_files = [f.strip() for f in args.changed_files.split(',')]
    elif args.all_segments:
        changed_files = None  # Run all
    else:
        # Default: run based on git changes
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                changed_files = result.stdout.strip().split('\n')
                changed_files = [f for f in changed_files if f.strip()]
        except:
            changed_files = None  # Fallback to all segments
    
    # Execute targeted tests
    results = runner.run_targeted_execution(changed_files)
    
    return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())