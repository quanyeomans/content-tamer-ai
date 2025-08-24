"""
Modern setup.py - Configuration is in pyproject.toml

This minimal setup.py ensures compatibility with tools that still expect it.
All actual configuration is in pyproject.toml (PEP 621 standard).
"""

from setuptools import setup

# Everything is configured in pyproject.toml
# This setup.py exists only for backwards compatibility
setup()