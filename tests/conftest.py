"""
Pytest configuration and fixtures for content-tamer-ai test suite.

Provides pytest-compatible Rich display management and cleanup.
"""

import io
import sys
import pytest
from contextlib import contextmanager
from typing import Optional

# Add src to path for test imports
sys.path.insert(0, 'src')

from utils.rich_display_manager import RichDisplayManager, RichDisplayOptions
from core.application_container import TestApplicationContainer


class TestSafeDisplayManager:
    """Pytest-safe wrapper for Rich display components."""
    
    def __init__(self, no_color: bool = True):
        self.output = io.StringIO()
        self.manager = None
        self.no_color = no_color
        self.container = None
        
    def __enter__(self):
        """Create a managed Rich display for tests."""
        try:
            # Create test container with proper Console injection
            self.container = TestApplicationContainer(capture_output=True)
            
            # Create display with safe test configuration
            options = RichDisplayOptions(
                no_color=self.no_color,
                verbose=False,
                quiet=False,
                show_stats=True
            )
            self.manager = self.container.create_display_manager(options)
            
            # Patch Rich Console to prevent file closure issues
            if hasattr(self.manager, 'console'):
                # Force Rich to use our managed output stream
                self.manager.console._file = self.output
                
            return self.manager
        except Exception as e:
            # Fallback to simple output for tests that fail Rich initialization
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up Rich display components safely."""
        try:
            if self.manager and hasattr(self.manager, 'progress'):
                # Force cleanup of any live displays
                if hasattr(self.manager.progress, '_live') and self.manager.progress._live:
                    try:
                        self.manager.progress._live.stop()
                    except:
                        pass  # Ignore cleanup errors
                        
                # Close any open file handles
                if hasattr(self.manager.progress, '_progress'):
                    self.manager.progress._progress = None
                    
            # Close output stream safely
            if self.output and not self.output.closed:
                self.output.close()
                
        except Exception:
            # Ignore cleanup errors to prevent test failures
            pass


@pytest.fixture
def test_display_manager():
    """Provide a pytest-safe Rich display manager."""
    with TestSafeDisplayManager() as manager:
        yield manager


@pytest.fixture
def test_output_capture():
    """Provide a safe output capture mechanism for testing display components."""
    output = io.StringIO()
    try:
        yield output
    finally:
        try:
            if not output.closed:
                output.close()
        except:
            pass


@contextmanager
def safe_rich_context():
    """Context manager for safe Rich display testing."""
    with TestSafeDisplayManager() as manager:
        yield manager


# Configure pytest to handle Rich display components
def pytest_configure(config):
    """Configure pytest for Rich display compatibility."""
    # Disable Rich auto-detection of terminal capabilities during tests
    import os
    os.environ['TERM'] = 'dumb'  # Force basic terminal mode
    os.environ['NO_COLOR'] = '1'  # Disable colors
    

def pytest_unconfigure(config):
    """Clean up after pytest session."""
    # Clean up any remaining Rich state
    try:
        import rich.console
        # Force cleanup of any global Rich state
        if hasattr(rich.console, '_console_stack'):
            rich.console._console_stack.clear()
    except:
        pass