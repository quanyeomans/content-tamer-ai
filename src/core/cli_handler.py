"""
CLI Handler - Rich Console Management for CLI Functions

Provides centralized CLI command handling with injected Rich Console
to eliminate multiple Console instantiations in cli_parser.py.

This ensures all CLI commands use the same Console instance for
consistent output and testing compatibility.
"""

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.prompt import Confirm, Prompt
from rich.table import Table


class CLIHandler:
    """
    Centralized handler for CLI operations with injected Console.

    Manages all CLI functions that previously created their own Console
    instances, ensuring consistent Rich output through dependency injection.
    """

    def __init__(self, console: Console):
        """
        Initialize CLI handler with injected Console.

        Args:
            console: Rich Console instance to use for all CLI output
        """
        if console is None:
            raise ValueError("Console instance is required for CLIHandler")

        self.console = console

    def _get_dependency_manager(self):
        """Get or create dependency manager instance."""
        if not hasattr(self, '_dependency_manager'):
            from core.dependency_manager import get_dependency_manager
            self._dependency_manager = get_dependency_manager()
        return self._dependency_manager

    def _find_ollama_path(self) -> Optional[str]:
        """
        Find Ollama executable path using centralized dependency manager.

        Returns:
            Path to ollama executable or None if not found
        """
        return self._get_dependency_manager().find_dependency("ollama")

    def _find_tesseract_path(self) -> Optional[str]:
        """
        Find Tesseract executable path using centralized dependency manager.

        Returns:
            Path to tesseract executable or None if not found
        """
        return self._get_dependency_manager().find_dependency("tesseract")

    def setup_local_llm_interactive(self) -> bool:
        """
        Handle interactive local LLM setup.

        Returns:
            bool: True if setup was successful
        """
        import shutil
        import subprocess
        import time

        from rich.progress import Progress, TaskID

        self.console.print("⚙️ Setting up Local LLM with Ollama", style="bold blue")

        # Check if Ollama is installed
        ollama_path = self._find_ollama_path()
        if ollama_path is None:
            self.console.print(
                "❌ Ollama not found. Please install Ollama first:", style="red"
            )
            self.console.print("Visit: https://ollama.ai/download")
            return False

        # Interactive model selection with correct Ollama model names
        display_models = ["gemma-2-2b", "llama3.2-3b", "mistral-7b", "llama3.1-8b"]
        
        # Map display names to actual Ollama model names
        ollama_model_map = {
            "gemma-2-2b": "gemma2:2b",
            "llama3.2-3b": "llama3.2:3b", 
            "mistral-7b": "mistral:7b",
            "llama3.1-8b": "llama3.1:8b",
        }

        table = Table(title="Available Local LLM Models")
        table.add_column("Model", style="cyan")
        table.add_column("Size", style="magenta")
        table.add_column("Description", style="green")

        model_info = {
            "gemma-2-2b": ("1.6GB", "Fast, lightweight model for basic tasks"),
            "llama3.2-3b": ("2.0GB", "Balanced performance and speed"),
            "mistral-7b": ("4.1GB", "High quality, good reasoning"),
            "llama3.1-8b": ("4.7GB", "Best quality, requires more resources"),
        }

        for model in display_models:
            size, desc = model_info[model]
            table.add_row(model, size, desc)

        self.console.print(table)

        model_choice = Prompt.ask(
            "Select a model to download", choices=display_models, default="gemma-2-2b"
        )
        
        # Convert to actual Ollama model name
        ollama_model_name = ollama_model_map[model_choice]

        # Download model with progress
        self.console.print(f"📥 Downloading {model_choice}...", style="blue")

        try:
            with Progress(console=self.console) as progress:
                task = progress.add_task(f"Downloading {model_choice}", total=100)

                # Start ollama pull process with correct model name
                process = subprocess.Popen(
                    [ollama_path, "pull", ollama_model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # Monitor progress with longer timeout for large models
                elapsed_time = 0
                max_wait_time = 600  # 10 minutes for large models like llama3.1-8b
                
                stdout_output = []
                stderr_output = []

                while elapsed_time < max_wait_time:
                    time.sleep(1.0)  # Check every second
                    elapsed_time += 1

                    # Update progress based on elapsed time (rough estimate)
                    estimated_progress = min(95, (elapsed_time / max_wait_time) * 100)
                    progress.update(task, completed=estimated_progress)

                    if process.poll() is not None:
                        # Process finished, capture remaining output
                        stdout, stderr = process.communicate()
                        if stdout:
                            stdout_output.append(stdout)
                        if stderr:
                            stderr_output.append(stderr)
                        break

                return_code = process.wait()

                # Complete the progress bar
                progress.update(task, completed=100)

                # Capture any remaining output
                if process.stdout:
                    remaining_stdout = process.stdout.read()
                    if remaining_stdout:
                        stdout_output.append(remaining_stdout)
                if process.stderr:
                    remaining_stderr = process.stderr.read()
                    if remaining_stderr:
                        stderr_output.append(remaining_stderr)

                if return_code == 0:
                    self.console.print(
                        "✅ Local LLM setup completed successfully!", style="green"
                    )
                    return True
                else:
                    # Show detailed error information
                    self.console.print("❌ Failed to download model", style="red")
                    if stdout_output:
                        self.console.print(f"Output: {''.join(stdout_output).strip()}", style="dim")
                    if stderr_output:
                        self.console.print(f"Error: {''.join(stderr_output).strip()}", style="red")
                    self.console.print(f"Exit code: {return_code}", style="dim")
                    return False

        except Exception as e:
            self.console.print(f"❌ Error during setup: {e}", style="red")
            return False

    def check_local_requirements(self) -> bool:
        """
        Check local LLM requirements and system compatibility.

        Returns:
            bool: True if requirements are met
        """
        import platform
        import shutil

        from utils.security import InstallationError, SecurityError

        self.console.print("🔍 Checking Local LLM Requirements", style="bold blue")

        system = platform.system()

        # Check Ollama installation
        ollama_path = self._find_ollama_path()
        if ollama_path:
            self.console.print(f"✅ Ollama found: {ollama_path}", style="green")
        else:
            self.console.print("❌ Ollama not installed", style="red")
            self.console.print(
                "Install from: https://ollama.ai/download", style="yellow"
            )
            return False

        # Check system compatibility
        if system in ["Windows", "Darwin", "Linux"]:
            self.console.print(f"✅ Platform supported: {system}", style="green")
        else:
            self.console.print(
                f"⚠️ Platform may not be supported: {system}", style="yellow"
            )

        # Check available models
        try:
            import subprocess

            result = subprocess.run([ollama_path, "list"], capture_output=True, text=True)
            if result.returncode == 0:
                models = result.stdout.strip()
                if models:
                    self.console.print("✅ Local models available:", style="green")
                    self.console.print(models, style="dim")
                else:
                    self.console.print("⚠️ No local models installed", style="yellow")
                    self.console.print(
                        "Run with --setup-local-llm to install models", style="blue"
                    )
            else:
                self.console.print("⚠️ Could not check local models", style="yellow")

        except Exception as e:
            self.console.print(f"⚠️ Error checking models: {e}", style="yellow")

        return True

    def list_local_models(self) -> List[Dict[str, Any]]:
        """
        List available local LLM models.

        Returns:
            List[Dict[str, Any]]: List of model information
        """
        import subprocess

        from utils.model_manager import ModelManager

        self.console.print("📋 Available Local Models", style="bold blue")

        manager = ModelManager()
        models = []

        try:
            # Get installed models
            result = subprocess.run([ollama_path, "list"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                installed_models = result.stdout.strip().split("\n")[1:]  # Skip header

                table = Table(title="Installed Models")
                table.add_column("Model", style="cyan")
                table.add_column("Size", style="magenta")
                table.add_column("Modified", style="green")

                for line in installed_models:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            model_name = parts[0]
                            size = parts[1]
                            modified = " ".join(parts[2:])
                            table.add_row(model_name, size, modified)
                            models.append(
                                {"name": model_name, "size": size, "modified": modified}
                            )

                self.console.print(table)
            else:
                self.console.print("No local models installed", style="yellow")
                self.console.print(
                    "Use --setup-local-llm to install models", style="blue"
                )

        except Exception as e:
            self.console.print(f"❌ Error listing models: {e}", style="red")

        return models

    def show_hardware_info(self) -> Dict[str, Any]:
        """
        Display system hardware information for LLM compatibility.

        Returns:
            Dict[str, Any]: Hardware information
        """
        from utils.hardware_detector import HardwareDetector
        from utils.model_manager import ModelManager

        self.console.print("🖥️ System Hardware Information", style="bold blue")

        detector = HardwareDetector()
        manager = ModelManager()

        # Get hardware info
        hw_info = detector.get_system_info()

        # Create hardware table
        hw_table = Table(title="Hardware Configuration")
        hw_table.add_column("Component", style="cyan")
        hw_table.add_column("Details", style="green")

        hw_table.add_row("CPU", hw_info.get("cpu", "Unknown"))
        hw_table.add_row("RAM", f"{hw_info.get('ram_gb', 0)} GB")
        hw_table.add_row("GPU", hw_info.get("gpu", "None detected"))
        hw_table.add_row("Platform", hw_info.get("platform", "Unknown"))

        self.console.print(hw_table)

        # Show recommended models
        recommended_models = manager.get_recommended_models_for_hardware(hw_info)

        if recommended_models:
            rec_table = Table(title="Recommended Models")
            rec_table.add_column("Model", style="cyan")
            rec_table.add_column("Reason", style="green")

            for model, reason in recommended_models.items():
                rec_table.add_row(model, reason)

            self.console.print(rec_table)

        return hw_info

    def show_feature_flags(self) -> Dict[str, bool]:
        """
        Display current feature flags configuration.

        Returns:
            Dict[str, bool]: Feature flags status
        """
        from core.feature_manager import get_feature_manager

        self.console.print("🚩 Feature Flags Configuration", style="bold blue")

        manager = get_feature_manager()
        flags = manager.load_flags()

        table = Table(title="Feature Flags")
        table.add_column("Feature", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Description", style="dim")

        flag_descriptions = {
            "use_enhanced_processing": "Enhanced file processing with ML organization",
            "enable_temporal_intelligence": "Time-aware content analysis and naming",
            "use_post_processing_organization": "Advanced post-processing organization",
            "debug_mode": "Enable debug logging and verbose output",
            "experimental_features": "Enable experimental and beta features",
        }

        for flag_name, enabled in flags.items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            description = flag_descriptions.get(flag_name, "Feature flag")
            table.add_row(flag_name, status, description)

        self.console.print(table)

        return flags

    def install_ollama_windows(self) -> bool:
        """
        Handle Ollama installation on Windows (deprecated method).

        Returns:
            bool: True if installation guidance was provided
        """
        self.console.print(
            "⚠️ Using deprecated insecure installation method", style="yellow"
        )
        self.console.print("")

        panel = Panel(
            "For security reasons, please install Ollama manually:\n\n"
            "1. Visit: https://ollama.ai/download\n"
            "2. Download the official Windows installer\n"
            "3. Run the installer as administrator\n"
            "4. Restart your terminal\n"
            "5. Run 'ollama --version' to verify installation",
            title="Manual Installation Required",
            border_style="yellow",
        )

        self.console.print(panel)
        return True

    def download_model_with_progress(self, model_name: str) -> bool:
        """
        Download a model with progress display.

        Args:
            model_name: Name of the model to download

        Returns:
            bool: True if download was successful
        """
        import subprocess
        import time

        # Check if Ollama is available
        ollama_path = self._find_ollama_path()
        if ollama_path is None:
            self.console.print("❌ Ollama not found", style="red")
            return False

        self.console.print(f"📥 Downloading model: {model_name}", style="blue")

        try:
            with Progress(console=self.console) as progress:
                task = progress.add_task(f"Downloading {model_name}", total=100)

                # Start download process
                process = subprocess.Popen(
                    [ollama_path, "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                # Monitor progress
                for i in range(100):
                    if process.poll() is not None:
                        break
                    time.sleep(0.5)
                    progress.update(task, completed=i + 1)

                return_code = process.wait()

                if return_code == 0:
                    self.console.print(
                        f"✅ Successfully downloaded {model_name}", style="green"
                    )
                    return True
                else:
                    self.console.print(
                        f"❌ Failed to download {model_name}", style="red"
                    )
                    return False

        except Exception as e:
            self.console.print(f"❌ Download error: {e}", style="red")
            return False

    def check_all_dependencies(self) -> bool:
        """
        Comprehensive dependency check with detailed status information.

        Returns:
            True if all critical dependencies are available
        """
        self.console.print("🔍 Checking All Dependencies", style="bold blue")

        dep_manager = self._get_dependency_manager()
        dependency_info = dep_manager.get_dependency_info()

        # Create comprehensive status table
        from rich.table import Table

        table = Table(title="Dependency Status")
        table.add_column("Dependency", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Path", style="dim")

        all_good = True

        for dep_name, info in dependency_info.items():
            if info["available"]:
                status = "✅ Found" + (" (cached)" if info["cached"] else "")
                version = info["version"] or "Unknown"
                path = info["path"][:50] + "..." if len(info["path"]) > 50 else info["path"]
            else:
                status = "❌ Not Found"
                version = "N/A"
                path = "Not available"
                if dep_name in ["tesseract"]:  # Critical dependencies
                    all_good = False

            table.add_row(dep_name.capitalize(), status, version, path)

        self.console.print(table)

        # Show configuration file location
        config_path = dep_manager.get_config_path()
        self.console.print(f"\nConfiguration file: {config_path}", style="dim")

        # Provide suggestions for missing dependencies
        missing_deps = [name for name, info in dependency_info.items() if not info["available"]]
        if missing_deps:
            self.console.print("\n📋 Installation Suggestions:", style="bold yellow")
            for dep in missing_deps:
                if dep == "ollama":
                    self.console.print("  • Ollama: Download from https://ollama.ai/download")
                elif dep == "tesseract":
                    self.console.print("  • Tesseract: Download from https://github.com/UB-Mannheim/tesseract/wiki")

        return all_good

    def refresh_dependencies(self) -> None:
        """Refresh all dependency detections and show updated status."""
        self.console.print("🔄 Refreshing Dependency Detection...", style="bold blue")

        dep_manager = self._get_dependency_manager()
        results = dep_manager.refresh_all_dependencies()

        self.console.print("Refresh Results:", style="bold")
        for dep_name, path in results.items():
            if path:
                self.console.print(f"  ✅ {dep_name}: {path}", style="green")
            else:
                self.console.print(f"  ❌ {dep_name}: Not found", style="red")

        # Show updated comprehensive status
        self.check_all_dependencies()
