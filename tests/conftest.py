"""
Pytest configuration and fixtures for content-tamer-ai test suite.

Provides pytest-compatible Rich display management and cleanup.
"""

import io
import sys
from contextlib import contextmanager

import pytest

# Add src to path for test imports
sys.path.insert(0, "src")

from core.application_container import TestApplicationContainer
from shared.display.rich_display_manager import RichDisplayManager, RichDisplayOptions

# ML model imports for session-scoped fixtures
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None


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
                no_color=self.no_color, verbose=False, quiet=False, show_stats=True
            )
            self.manager = self.container.create_display_manager(options)

            # Patch Rich Console to prevent file closure issues
            if hasattr(self.manager, "console"):
                # Force Rich to use our managed output stream
                self.manager.console._file = self.output

            return self.manager
        except Exception:
            # Fallback to simple output for tests that fail Rich initialization
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up Rich display components safely."""
        try:
            if self.manager and hasattr(self.manager, "progress"):
                # Force cleanup of any live displays
                if hasattr(self.manager.progress, "_live") and self.manager.progress._live:
                    try:
                        self.manager.progress._live.stop()
                    except Exception:
                        pass  # Ignore cleanup errors

                # Close any open file handles
                if hasattr(self.manager.progress, "_progress"):
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
        except Exception:
            pass


@contextmanager
def safe_rich_context():
    """Context manager for safe Rich display testing."""
    with TestSafeDisplayManager() as manager:
        yield manager


# Configure pytest to handle Rich display components
def pytest_configure(config):  # pylint: disable=unused-argument
    """Configure pytest for Rich display compatibility."""
    # Disable Rich auto-detection of terminal capabilities during tests
    import os

    os.environ["TERM"] = "dumb"  # Force basic terminal mode
    os.environ["NO_COLOR"] = "1"  # Disable colors


def pytest_unconfigure(config):  # pylint: disable=unused-argument
    """Clean up after pytest session."""
    # Clean up any remaining Rich state
    try:
        import rich.console

        # Force cleanup of any global Rich state
        if hasattr(rich.console, "_console_stack"):
            rich.console._console_stack.clear()
    except Exception:
        pass


# ============================================================================
# Session-scoped ML model fixtures for performance optimization
# ============================================================================

@pytest.fixture(scope="session")
def spacy_model():
    """Load spaCy model once per session to improve test performance.
    
    This fixture reduces test execution time from ~55s to ~5s by loading
    the spaCy model only once per test session instead of per test.
    """
    if not SPACY_AVAILABLE:
        pytest.skip("spaCy not available")
    
    try:
        # Load spaCy model with minimal components for speed
        model = spacy.load("en_core_web_sm", disable=["parser", "tagger"])
        return model
    except OSError:
        pytest.skip("spaCy model 'en_core_web_sm' not available")


@pytest.fixture(scope="session")
def en_vocab(spacy_model):
    """Provide spaCy vocabulary for manual Doc creation in unit tests.
    
    This allows tests to create spaCy Doc objects without loading the full model.
    """
    return spacy_model.vocab


@pytest.fixture(scope="session")
def ml_services(spacy_model):
    """Session-scoped ML services with cached spaCy model.
    
    Provides pre-initialized clustering and learning services that reuse
    the session-scoped spaCy model for optimal performance.
    """
    # Import here to avoid circular imports
    from domains.organization.clustering_service import ClusteringService
    from domains.organization.learning_service import LearningService
    import tempfile
    
    # Create temporary directory for learning service
    temp_dir = tempfile.mkdtemp()
    
    # Create services with shared spaCy model
    clustering_service = ClusteringService(spacy_model=spacy_model)
    learning_service = LearningService(temp_dir, spacy_model=spacy_model)
    
    return {
        "clustering": clustering_service,
        "learning": learning_service,
        "temp_dir": temp_dir
    }

# Clean up ML model state between test sessions
def pytest_sessionfinish(session, exitstatus):
    """Clean up ML models and state after test session."""
    try:
        import spacy
        if hasattr(spacy, 'info') and hasattr(spacy.info, '_CACHE'):
            spacy.info._CACHE.clear()
    except (ImportError, AttributeError):
        pass
    
    # Force garbage collection of ML models
    import gc
    gc.collect()

def pytest_runtest_teardown(item, nextitem):
    """Comprehensive state cleanup to prevent cross-test contamination."""
    import gc
    import os
    import sys
    
    # 1. Force aggressive garbage collection to clear ML model state
    gc.collect()
    
    # 2. Clear spaCy model state that might persist across tests
    try:
        import spacy
        if hasattr(spacy.util, 'registry'):
            # Reset any cached components
            pass
        if hasattr(spacy, '_MODELS_CACHE'):
            spacy._MODELS_CACHE.clear()
        # Clear any other spaCy caches
        if hasattr(spacy, 'info') and hasattr(spacy.info, '_CACHE'):
            spacy.info._CACHE.clear()
    except (ImportError, AttributeError):
        pass
    
    # 3. Reset sys.path to prevent contamination - CRITICAL for organization tests
    src_path = os.path.join(os.path.dirname(__file__), "src")
    resolved_src_path = os.path.abspath(src_path)
    
    # Clean sys.path and ensure only our src path is at the front
    sys.path = [p for p in sys.path if os.path.abspath(p) != resolved_src_path]
    sys.path.insert(0, resolved_src_path)
    
    # 4. Clear any module-level state that might persist
    # Reset any imported organization services to prevent state leakage
    modules_to_reset = [
        'domains.organization.clustering_service',
        'domains.organization.learning_service', 
        'domains.organization.organization_service',
        'domains.organization.folder_service'
    ]
    
    for module_name in modules_to_reset:
        if module_name in sys.modules:
            # Don't remove the module, but clear any class-level state if possible
            try:
                module = sys.modules[module_name]
                # Clear any caches or class-level state
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if hasattr(attr, '_cache') and hasattr(attr._cache, 'clear'):
                        attr._cache.clear()
            except (AttributeError, TypeError):
                pass
    
    # 5. Force another garbage collection after cleanup
    gc.collect()
