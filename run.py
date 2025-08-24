#!/usr/bin/env python3
"""
Simple entry point for AI-Powered Document Organization System

This script provides an easy way to run the document processing system.
For new users, simply run: python run.py

For advanced usage, see: python run.py --help
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main function
from main import main

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code if exit_code is not None else 0)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)