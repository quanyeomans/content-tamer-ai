#!/usr/bin/env python3
"""
Log Sanitization Utility
Sanitizes existing log files to remove any exposed API keys or secrets.
"""

import os
import sys
import glob
import shutil
from datetime import datetime

# Add src to path to import security utilities
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from utils.security import sanitize_log_message


def sanitize_log_file(log_file_path: str) -> tuple[int, int]:
    """
    Sanitize a log file by removing any API keys or secrets.
    
    Args:
        log_file_path: Path to the log file to sanitize
        
    Returns:
        tuple: (lines_processed, lines_sanitized)
    """
    if not os.path.exists(log_file_path):
        return 0, 0
    
    # Create backup of original log file
    backup_path = f"{log_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(log_file_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    lines_processed = 0
    lines_sanitized = 0
    
    # Read and sanitize the log file
    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as infile:
        lines = infile.readlines()
    
    sanitized_lines = []
    for line in lines:
        lines_processed += 1
        original_line = line
        sanitized_line = sanitize_log_message(line)
        
        if sanitized_line != original_line:
            lines_sanitized += 1
            print(f"Sanitized line {lines_processed}: API key/secret removed")
        
        sanitized_lines.append(sanitized_line)
    
    # Write sanitized content back to the file
    with open(log_file_path, 'w', encoding='utf-8') as outfile:
        outfile.writelines(sanitized_lines)
    
    return lines_processed, lines_sanitized


def find_and_sanitize_logs(project_root: str = None) -> None:
    """
    Find and sanitize all log files in the project.
    
    Args:
        project_root: Root directory to search (defaults to project root)
    """
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(__file__))
    
    print(f"Searching for log files in: {project_root}")
    
    # Common log file patterns
    log_patterns = [
        "**/*.log",
        "**/errors.log", 
        "**/debug.log",
        "**/app.log",
        "**/.processing/*.log",
        "**/logs/**/*.log"
    ]
    
    total_files = 0
    total_lines_processed = 0
    total_lines_sanitized = 0
    
    for pattern in log_patterns:
        search_path = os.path.join(project_root, pattern)
        for log_file in glob.glob(search_path, recursive=True):
            if os.path.isfile(log_file):
                print(f"\nProcessing: {log_file}")
                lines_proc, lines_san = sanitize_log_file(log_file)
                total_files += 1
                total_lines_processed += lines_proc
                total_lines_sanitized += lines_san
                
                if lines_san > 0:
                    print(f"  [WARNING] {lines_san} lines contained secrets and were sanitized")
                else:
                    print(f"  [OK] {lines_proc} lines processed, no secrets found")
    
    print(f"\n" + "="*50)
    print(f"LOG SANITIZATION SUMMARY")
    print(f"="*50)
    print(f"Files processed: {total_files}")
    print(f"Lines processed: {total_lines_processed}")
    print(f"Lines sanitized: {total_lines_sanitized}")
    
    if total_lines_sanitized > 0:
        print(f"\n[CRITICAL] WARNING: {total_lines_sanitized} lines contained API keys or secrets!")
        print("These have been sanitized and backups created with .backup timestamps.")
        print("Review the backups and securely delete them when satisfied.")
    else:
        print(f"\n[SUCCESS] No API keys or secrets found in log files.")
    
    if total_files == 0:
        print(f"\n[INFO] No log files found - this is expected for a clean repository.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sanitize log files to remove API keys and secrets")
    parser.add_argument("--path", help="Project root path to search (default: auto-detect)")
    parser.add_argument("--file", help="Specific log file to sanitize")
    
    args = parser.parse_args()
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} does not exist")
            sys.exit(1)
        
        print(f"Sanitizing specific file: {args.file}")
        lines_proc, lines_san = sanitize_log_file(args.file)
        
        if lines_san > 0:
            print(f"[WARNING] Sanitized {lines_san} out of {lines_proc} lines")
        else:
            print(f"[OK] No secrets found in {lines_proc} lines")
    else:
        find_and_sanitize_logs(args.path)