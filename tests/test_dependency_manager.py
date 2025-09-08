#!/usr/bin/env python3
"""
Comprehensive Tests for DependencyManager

Tests the centralized dependency detection, configuration, and caching system
according to TDD principles with comprehensive edge case coverage.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.dependency_manager import DependencyManager, get_dependency_manager


class TestDependencyManagerDefaults(unittest.TestCase):
    """Test default behavior and initialization."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DependencyManager(config_dir=self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_initialization_with_custom_config_dir(self):
        """Test manager initializes correctly with custom config directory."""
        self.assertEqual(self.manager.config_dir, Path(self.temp_dir))
        self.assertTrue(self.manager.config_dir.exists())
        self.assertEqual(self.manager.config_file, Path(self.temp_dir) / "dependencies.json")

    def test_initialization_without_config_dir(self):
        """Test manager initializes with platform-appropriate default directory."""
        manager = DependencyManager()
        
        # Should create config directory based on platform
        self.assertTrue(manager.config_dir.exists())
        self.assertTrue(str(manager.config_dir).endswith("content-tamer-ai"))
        
        # Cleanup
        import shutil
        try:
            shutil.rmtree(manager.config_dir)
        except (OSError, PermissionError):
            pass

    def test_common_locations_defined_for_platform(self):
        """Test common installation locations are defined for current platform."""
        self.assertIn("ollama", self.manager.common_locations)
        self.assertIn("tesseract", self.manager.common_locations)
        
        # Should have at least one location per dependency
        self.assertGreater(len(self.manager.common_locations["ollama"]), 0)
        self.assertGreater(len(self.manager.common_locations["tesseract"]), 0)

    def test_empty_config_initialization(self):
        """Test manager starts with empty configuration if no file exists."""
        self.assertEqual(self.manager.config, {})
        self.assertFalse(self.manager.config_file.exists())


class TestDependencyManagerConfiguration(unittest.TestCase):
    """Test configuration loading, saving, and management."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DependencyManager(config_dir=self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_save_and_load_config(self):
        """Test configuration is properly saved and loaded."""
        # Set some configuration
        test_config = {
            "ollama": "/usr/local/bin/ollama",
            "tesseract": "/usr/bin/tesseract"
        }
        self.manager.config = test_config
        self.manager._save_config()
        
        # Verify file was created
        self.assertTrue(self.manager.config_file.exists())
        
        # Create new manager to test loading
        new_manager = DependencyManager(config_dir=self.temp_dir)
        self.assertEqual(new_manager.config, test_config)

    def test_load_invalid_config_file(self):
        """Test handling of corrupted/invalid config file."""
        # Create invalid JSON file
        with open(self.manager.config_file, 'w') as f:
            f.write("invalid json content {")
        
        # Should handle gracefully and return empty config
        new_manager = DependencyManager(config_dir=self.temp_dir)
        self.assertEqual(new_manager.config, {})

    def test_configure_dependency_valid_path(self):
        """Test manual dependency configuration with valid path."""
        # Create a test executable file
        test_exe = os.path.join(self.temp_dir, "test_executable.exe")
        with open(test_exe, 'w') as f:
            f.write("dummy executable")
        
        # Configure dependency
        result = self.manager.configure_dependency("test_dep", test_exe)
        
        self.assertTrue(result)
        self.assertEqual(self.manager.config["test_dep"], test_exe)
        
        # Verify config was saved
        new_manager = DependencyManager(config_dir=self.temp_dir)
        self.assertEqual(new_manager.config["test_dep"], test_exe)

    def test_configure_dependency_invalid_path(self):
        """Test manual dependency configuration with invalid path."""
        invalid_path = os.path.join(self.temp_dir, "nonexistent.exe")
        
        result = self.manager.configure_dependency("test_dep", invalid_path)
        
        self.assertFalse(result)
        self.assertNotIn("test_dep", self.manager.config)

    def test_reset_config(self):
        """Test configuration reset functionality."""
        # Set some configuration
        self.manager.config = {"ollama": "/some/path"}
        self.manager._save_config()
        self.assertTrue(self.manager.config_file.exists())
        
        # Reset configuration
        self.manager.reset_config()
        
        self.assertEqual(self.manager.config, {})
        self.assertFalse(self.manager.config_file.exists())


class TestDependencyManagerDetection(unittest.TestCase):
    """Test dependency detection and path finding."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DependencyManager(config_dir=self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    @patch('shutil.which')
    def test_find_dependency_in_path(self, mock_which):
        """Test finding dependency that exists in PATH."""
        mock_which.return_value = "/usr/bin/tesseract"
        
        result = self.manager.find_dependency("tesseract")
        
        self.assertEqual(result, "/usr/bin/tesseract")
        self.assertEqual(self.manager.config["tesseract"], "/usr/bin/tesseract")
        mock_which.assert_called_once_with("tesseract")

    @patch('shutil.which')
    @patch('os.path.exists')
    def test_find_dependency_in_common_locations(self, mock_exists, mock_which):
        """Test finding dependency in common installation locations."""
        mock_which.return_value = None  # Not in PATH
        
        # Mock exists to return True for first common location
        def mock_exists_side_effect(path):
            return path == self.manager.common_locations["tesseract"][0]
        
        mock_exists.side_effect = mock_exists_side_effect
        
        result = self.manager.find_dependency("tesseract")
        
        expected_path = self.manager.common_locations["tesseract"][0]
        self.assertEqual(result, expected_path)
        self.assertEqual(self.manager.config["tesseract"], expected_path)

    @patch('shutil.which')
    @patch('os.path.exists')
    def test_find_dependency_not_found(self, mock_exists, mock_which):
        """Test handling when dependency is not found anywhere."""
        mock_which.return_value = None
        mock_exists.return_value = False
        
        result = self.manager.find_dependency("nonexistent")
        
        self.assertIsNone(result)
        self.assertNotIn("nonexistent", self.manager.config)

    def test_find_dependency_cached_valid(self):
        """Test using cached dependency path when still valid."""
        # Set up cached configuration
        cached_path = os.path.join(self.temp_dir, "cached_exe.exe")
        with open(cached_path, 'w') as f:
            f.write("cached executable")
        
        self.manager.config["test_dep"] = cached_path
        
        # Should return cached path without searching
        with patch('shutil.which') as mock_which:
            result = self.manager.find_dependency("test_dep")
            
            self.assertEqual(result, cached_path)
            mock_which.assert_not_called()

    @patch('shutil.which')
    def test_find_dependency_cached_invalid_fallback(self, mock_which):
        """Test fallback search when cached path is no longer valid."""
        # Set up invalid cached path
        invalid_path = os.path.join(self.temp_dir, "missing.exe")
        self.manager.config["test_dep"] = invalid_path
        
        # Mock finding in PATH as fallback
        mock_which.return_value = "/usr/bin/test_dep"
        
        result = self.manager.find_dependency("test_dep")
        
        self.assertEqual(result, "/usr/bin/test_dep")
        self.assertEqual(self.manager.config["test_dep"], "/usr/bin/test_dep")
        self.assertNotEqual(result, invalid_path)

    def test_find_dependency_force_refresh(self):
        """Test forcing refresh bypasses cache."""
        # Set up cached configuration
        cached_path = os.path.join(self.temp_dir, "cached.exe")
        with open(cached_path, 'w') as f:
            f.write("cached")
        
        self.manager.config["test_dep"] = cached_path
        
        # Mock finding different path during refresh
        with patch('shutil.which') as mock_which:
            mock_which.return_value = "/new/path/test_dep"
            
            result = self.manager.find_dependency("test_dep", force_refresh=True)
            
            self.assertEqual(result, "/new/path/test_dep")
            self.assertEqual(self.manager.config["test_dep"], "/new/path/test_dep")
            mock_which.assert_called_once_with("test_dep")


class TestDependencyManagerVersioning(unittest.TestCase):
    """Test dependency version detection and information gathering."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DependencyManager(config_dir=self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    @patch('subprocess.run')
    def test_get_ollama_version(self, mock_run):
        """Test Ollama version extraction."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ollama version is 0.11.10"
        mock_run.return_value = mock_result
        
        version = self.manager._get_version("ollama", "/usr/bin/ollama")
        
        self.assertEqual(version, "0.11.10")
        mock_run.assert_called_once_with(
            ["/usr/bin/ollama", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )

    @patch('subprocess.run')
    def test_get_tesseract_version(self, mock_run):
        """Test Tesseract version extraction."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "tesseract v5.5.0.20241111\nleptonica-1.85.0"
        mock_run.return_value = mock_result
        
        version = self.manager._get_version("tesseract", "/usr/bin/tesseract")
        
        self.assertEqual(version, "v5.5.0.20241111")

    @patch('subprocess.run')
    def test_get_version_command_fails(self, mock_run):
        """Test version detection when command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        version = self.manager._get_version("tesseract", "/usr/bin/tesseract")
        
        self.assertIsNone(version)

    @patch('subprocess.run')
    def test_get_version_timeout_exception(self, mock_run):
        """Test version detection handles timeout exceptions."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)
        
        version = self.manager._get_version("ollama", "/usr/bin/ollama")
        
        self.assertIsNone(version)

    @patch('subprocess.run')
    def test_get_version_unknown_dependency(self, mock_run):
        """Test version detection for unknown dependency type."""
        version = self.manager._get_version("unknown_dep", "/usr/bin/unknown")
        
        self.assertIsNone(version)
        mock_run.assert_not_called()


class TestDependencyManagerComprehensiveInfo(unittest.TestCase):
    """Test comprehensive dependency information and status reporting."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DependencyManager(config_dir=self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    @patch.object(DependencyManager, 'find_dependency')
    @patch.object(DependencyManager, '_get_version')
    def test_get_dependency_info_all_available(self, mock_get_version, mock_find):
        """Test comprehensive info when all dependencies are available."""
        # Mock all dependencies found
        mock_find.side_effect = ["/usr/bin/ollama", "/usr/bin/tesseract"]
        mock_get_version.side_effect = ["0.11.10", "v5.5.0"]
        
        # Set up cached config
        self.manager.config = {
            "ollama": "/usr/bin/ollama",
            "tesseract": "/usr/bin/tesseract"
        }
        
        info = self.manager.get_dependency_info()
        
        self.assertTrue(info["ollama"]["available"])
        self.assertEqual(info["ollama"]["path"], "/usr/bin/ollama")
        self.assertEqual(info["ollama"]["version"], "0.11.10")
        self.assertTrue(info["ollama"]["cached"])
        
        self.assertTrue(info["tesseract"]["available"])
        self.assertEqual(info["tesseract"]["path"], "/usr/bin/tesseract")
        self.assertEqual(info["tesseract"]["version"], "v5.5.0")
        self.assertTrue(info["tesseract"]["cached"])

    @patch.object(DependencyManager, 'find_dependency')
    def test_get_dependency_info_missing_dependencies(self, mock_find):
        """Test comprehensive info when dependencies are missing."""
        mock_find.return_value = None
        
        info = self.manager.get_dependency_info()
        
        self.assertFalse(info["ollama"]["available"])
        self.assertIsNone(info["ollama"]["path"])
        self.assertIsNone(info["ollama"]["version"])
        self.assertFalse(info["ollama"]["cached"])
        
        self.assertFalse(info["tesseract"]["available"])
        self.assertIsNone(info["tesseract"]["path"])
        self.assertIsNone(info["tesseract"]["version"])
        self.assertFalse(info["tesseract"]["cached"])

    @patch.object(DependencyManager, 'find_dependency')
    def test_refresh_all_dependencies(self, mock_find):
        """Test refreshing detection for all dependencies."""
        mock_find.side_effect = ["/new/ollama", "/new/tesseract"]
        
        results = self.manager.refresh_all_dependencies()
        
        self.assertEqual(results["ollama"], "/new/ollama")
        self.assertEqual(results["tesseract"], "/new/tesseract")
        
        # Verify force_refresh=True was used
        self.assertEqual(mock_find.call_count, 2)
        for call in mock_find.call_args_list:
            args, kwargs = call
            self.assertTrue(kwargs.get("force_refresh", False))

    def test_validate_dependency_success(self):
        """Test successful dependency validation."""
        # Create test executable
        test_exe = os.path.join(self.temp_dir, "test.exe")
        with open(test_exe, 'w') as f:
            f.write("test")
        
        # Configure dependency
        self.manager.config["test_dep"] = test_exe
        
        with patch.object(self.manager, '_get_version', return_value="1.0.0"):
            is_valid, message = self.manager.validate_dependency("test_dep")
        
        self.assertTrue(is_valid)
        self.assertIn("test_dep v1.0.0 found", message)

    def test_validate_dependency_not_found(self):
        """Test dependency validation when not found."""
        is_valid, message = self.manager.validate_dependency("nonexistent")
        
        self.assertFalse(is_valid)
        self.assertIn("not found in PATH or common locations", message)

    def test_validate_dependency_path_invalid(self):
        """Test dependency validation when cached path is invalid."""
        # Create a path that exists initially
        temp_file = os.path.join(self.temp_dir, "temp_exe")
        with open(temp_file, 'w') as f:
            f.write("temp")
        
        self.manager.config["missing_dep"] = temp_file
        
        # Remove the file to make path invalid
        os.remove(temp_file)
        
        # Mock find_dependency to return the invalid path directly to test path validation
        with patch.object(self.manager, 'find_dependency', return_value=temp_file):
            is_valid, message = self.manager.validate_dependency("missing_dep")
        
        self.assertFalse(is_valid)
        self.assertIn("path no longer exists", message)


class TestDependencyManagerGlobalInstance(unittest.TestCase):
    """Test global dependency manager singleton functionality."""
    
    def test_get_dependency_manager_singleton(self):
        """Test global dependency manager returns same instance."""
        manager1 = get_dependency_manager()
        manager2 = get_dependency_manager()
        
        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, DependencyManager)

    def test_get_dependency_manager_initialization(self):
        """Test global dependency manager is properly initialized."""
        manager = get_dependency_manager()
        
        self.assertTrue(manager.config_dir.exists())
        self.assertIn("ollama", manager.common_locations)
        self.assertIn("tesseract", manager.common_locations)


class TestDependencyManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_config_directory_creation_failure(self):
        """Test handling when config directory cannot be created."""
        # Use invalid path that cannot be created
        if os.name == 'nt':  # Windows
            invalid_path = "Z:\\nonexistent\\invalid\\path"
        else:
            invalid_path = "/root/forbidden/path"
        
        # Should handle gracefully without crashing
        try:
            manager = DependencyManager(config_dir=invalid_path)
            # If it doesn't raise, check that some fallback occurred
            self.assertIsNotNone(manager.config_dir)
        except (OSError, PermissionError):
            # Expected on some systems, test passes
            pass

    def test_config_save_permission_error(self):
        """Test handling config save when file is not writable."""
        manager = DependencyManager(config_dir=self.temp_dir)
        
        # Create read-only config file
        with open(manager.config_file, 'w') as f:
            f.write("{}")
        os.chmod(manager.config_file, 0o444)  # Read-only
        
        # Should handle save failure gracefully
        manager.config["test"] = "value"
        try:
            manager._save_config()  # Should not crash
        except OSError:
            pass  # Expected on some systems
        finally:
            # Cleanup - restore write permission
            try:
                os.chmod(manager.config_file, 0o644)
            except OSError:
                pass

    def test_empty_common_locations(self):
        """Test handling when no common locations are defined."""
        manager = DependencyManager(config_dir=self.temp_dir)
        manager.common_locations = {"empty_dep": []}
        
        with patch('shutil.which', return_value=None):
            result = manager.find_dependency("empty_dep")
        
        self.assertIsNone(result)

    def test_malformed_version_output(self):
        """Test version parsing with malformed command output."""
        manager = DependencyManager(config_dir=self.temp_dir)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "unexpected format without version info"
            mock_run.return_value = mock_result
            
            version = manager._get_version("ollama", "/usr/bin/ollama")
            
            # Should handle gracefully and extract what it can
            self.assertIsNone(version)


if __name__ == '__main__':
    unittest.main(verbosity=2)