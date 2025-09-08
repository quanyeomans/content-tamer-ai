"""
Dependency Manager - Centralized Configuration for External Dependencies

Provides centralized detection, configuration, and caching of external dependency paths
to avoid repeated PATH searches and enable configuration persistence.
"""

import json
import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DependencyManager:
    """
    Centralized manager for external dependency detection and configuration.
    
    Features:
    - Automatic detection of dependencies in common installation locations
    - Persistent configuration caching to avoid repeated searches
    - Cross-platform path detection with Windows-specific handling
    - Graceful fallback to PATH-based detection
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize dependency manager with optional custom config directory.
        
        Args:
            config_dir: Custom directory for storing dependency config (defaults to user data dir)
        """
        self.system = platform.system()
        
        # Set up config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Use platform-appropriate user data directory
            if self.system == "Windows":
                base_dir = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
                self.config_dir = Path(base_dir) / "content-tamer-ai"
            else:
                base_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
                self.config_dir = Path(base_dir) / "content-tamer-ai"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "dependencies.json"
        
        # Load existing configuration
        self.config = self._load_config()
        
        # Define common installation locations per platform
        self._define_common_locations()

    def _define_common_locations(self) -> None:
        """Define common installation locations for each dependency by platform."""
        if self.system == "Windows":
            self.common_locations = {
                "ollama": [
                    os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe"),
                    "C:\\Program Files\\Ollama\\ollama.exe",
                    "C:\\Program Files (x86)\\Ollama\\ollama.exe"
                ],
                "tesseract": [
                    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
                    "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
                    os.path.expanduser("~\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"),
                    "C:\\Tools\\tesseract\\tesseract.exe",
                    "C:\\tesseract\\tesseract.exe"
                ]
            }
        elif self.system == "Darwin":  # macOS
            self.common_locations = {
                "ollama": [
                    "/usr/local/bin/ollama",
                    "/opt/homebrew/bin/ollama",
                    os.path.expanduser("~/bin/ollama")
                ],
                "tesseract": [
                    "/usr/local/bin/tesseract",
                    "/opt/homebrew/bin/tesseract",
                    "/usr/bin/tesseract"
                ]
            }
        else:  # Linux and others
            self.common_locations = {
                "ollama": [
                    "/usr/local/bin/ollama",
                    "/usr/bin/ollama",
                    os.path.expanduser("~/.local/bin/ollama"),
                    os.path.expanduser("~/bin/ollama")
                ],
                "tesseract": [
                    "/usr/bin/tesseract",
                    "/usr/local/bin/tesseract",
                    "/snap/bin/tesseract"
                ]
            }

    def _load_config(self) -> Dict[str, str]:
        """Load dependency configuration from file."""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"Failed to load dependency config: {e}")
            return {}

    def _save_config(self) -> None:
        """Save dependency configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except OSError as e:
            logging.warning(f"Failed to save dependency config: {e}")

    def find_dependency(self, name: str, force_refresh: bool = False) -> Optional[str]:
        """
        Find dependency path, checking cache first, then common locations.
        
        Args:
            name: Dependency name (e.g., 'ollama', 'tesseract')
            force_refresh: Force re-detection even if cached
            
        Returns:
            Path to dependency executable or None if not found
        """
        # Return cached path if available and not forcing refresh
        if not force_refresh and name in self.config:
            cached_path = self.config[name]
            if os.path.exists(cached_path):
                return cached_path
            else:
                # Cached path no longer valid, remove it
                del self.config[name]
                self._save_config()

        # Check if dependency is in PATH
        path_result = shutil.which(name)
        if path_result:
            self.config[name] = path_result
            self._save_config()
            return path_result

        # Check common installation locations
        common_paths = self.common_locations.get(name, [])
        for path in common_paths:
            if os.path.exists(path):
                self.config[name] = path
                self._save_config()
                return path

        logging.debug(f"Dependency '{name}' not found in PATH or common locations")
        return None

    def configure_dependency(self, name: str, path: str) -> bool:
        """
        Manually configure dependency path.
        
        Args:
            name: Dependency name
            path: Full path to dependency executable
            
        Returns:
            True if path is valid and was configured
        """
        if not os.path.exists(path):
            logging.error(f"Dependency path does not exist: {path}")
            return False
        
        self.config[name] = path
        self._save_config()
        logging.info(f"Configured {name} at {path}")
        return True

    def get_dependency_info(self) -> Dict[str, Dict[str, any]]:
        """
        Get comprehensive information about all configured dependencies.
        
        Returns:
            Dictionary with dependency status, paths, and versions
        """
        info = {}
        
        for dep_name in ["ollama", "tesseract"]:
            dep_path = self.find_dependency(dep_name)
            info[dep_name] = {
                "available": dep_path is not None,
                "path": dep_path,
                "version": self._get_version(dep_name, dep_path) if dep_path else None,
                "cached": dep_name in self.config
            }
        
        return info

    def _get_version(self, name: str, path: str) -> Optional[str]:
        """Get version string for a dependency."""
        try:
            import subprocess
            
            if name == "ollama":
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Extract version from "ollama version is X.Y.Z"
                    output = result.stdout.strip()
                    if "version is" in output:
                        return output.split("version is")[-1].strip()
            elif name == "tesseract":
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Extract version from first line
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        return lines[0].replace('tesseract ', '').strip()
                        
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass
        
        return None

    def refresh_all_dependencies(self) -> Dict[str, Optional[str]]:
        """
        Refresh detection for all dependencies.
        
        Returns:
            Dictionary mapping dependency names to their detected paths
        """
        results = {}
        for dep_name in ["ollama", "tesseract"]:
            results[dep_name] = self.find_dependency(dep_name, force_refresh=True)
        
        return results

    def get_config_path(self) -> Path:
        """Get path to the configuration file."""
        return self.config_file

    def reset_config(self) -> None:
        """Reset all dependency configuration."""
        self.config = {}
        if self.config_file.exists():
            self.config_file.unlink()
        logging.info("Reset dependency configuration")

    def validate_dependency(self, name: str) -> Tuple[bool, str]:
        """
        Validate that a dependency is properly configured and working.
        
        Args:
            name: Dependency name to validate
            
        Returns:
            Tuple of (is_valid, status_message)
        """
        dep_path = self.find_dependency(name)
        
        if not dep_path:
            return False, f"{name} not found in PATH or common locations"
        
        if not os.path.exists(dep_path):
            return False, f"{name} path no longer exists: {dep_path}"
        
        try:
            version = self._get_version(name, dep_path)
            if version:
                return True, f"{name} v{version} found at {dep_path}"
            else:
                return True, f"{name} found at {dep_path} (version unknown)"
        except Exception as e:
            return False, f"{name} found but not working: {e}"


# Global instance for easy access
_dependency_manager = None

def get_dependency_manager() -> DependencyManager:
    """Get or create global dependency manager instance."""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager