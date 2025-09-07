"""
Content Tamer AI - Command Line Interface Parser

Handles command line argument parsing, validation, and expert mode integration.
"""

import argparse
import os
import sys
from typing import Any

# Centralized imports and path management
from utils.imports import safe_import_with_fallback
from utils.paths import get_default_directories, get_project_root

# Import required modules using shared utility
modules = safe_import_with_fallback(["utils.expert_mode", "ai_providers"])
prompt_expert_mode_if_needed = modules["utils.expert_mode"].prompt_expert_mode_if_needed
AI_PROVIDERS = modules["ai_providers"].AI_PROVIDERS
AIProviderFactory = modules["ai_providers"].AIProviderFactory

# Use centralized path management
PROJECT_ROOT = get_project_root()
DEFAULT_DATA_DIR, DEFAULT_INPUT_DIR, DEFAULT_PROCESSED_DIR, _, _ = get_default_directories()


def parse_arguments():
    """Sets up and parses the command-line arguments that the script accepts."""
    parser = argparse.ArgumentParser(
        description="Content Tamer AI - Organize documents with intelligent AI-powered filename generation",
        epilog="""
Examples:
  # Process documents using defaults (data/input -> data/processed)
  content-tamer-ai

  # Use specific AI provider and model
  content-tamer-ai -p openai -m gpt-4o

  # Use custom folders for organization
  content-tamer-ai -i ./my-documents -r ./organized -u ./needs-review

  # List all available AI models
  content-tamer-ai --list-models
""",
    )
    parser.add_argument(
        "--input",
        "-i",
        help=f"Input folder containing documents to organize (PDFs, images, screenshots) (default: {DEFAULT_INPUT_DIR})",
    )
    # Note: Unprocessed folder is now automatically created within processed folder
    # Keeping argument for backward compatibility but marking as advanced/deprecated
    parser.add_argument(
        "--unprocessed",
        "-u",
        help="[ADVANCED] Custom location for unprocessed files (default: auto-created within processed folder)",
    )
    parser.add_argument(
        "--renamed",
        "-r",
        help=f"Folder for organized documents with AI-generated names (default: {DEFAULT_PROCESSED_DIR})",
    )
    parser.add_argument(
        "--provider",
        "-p",
        help=f"AI provider (options: {', '.join(AI_PROVIDERS.keys())})",
        default="openai",
        choices=AI_PROVIDERS.keys(),
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Model to use for the selected provider (run with --list-models to see options)",
    )
    parser.add_argument("--api-key", "-k", help="API key for the selected provider")
    parser.add_argument(
        "--list-models",
        "-l",
        action="store_true",
        help="List all available models by provider and exit",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="Tesseract OCR language hint (e.g., 'eng', 'eng+ind')",
    )
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Ignore and delete existing .progress file before run",
    )

    # Local LLM options
    parser.add_argument(
        "--setup-local-llm",
        action="store_true",
        help="Set up local LLM with automatic hardware detection and model recommendation",
    )
    parser.add_argument(
        "--list-local-models",
        action="store_true", 
        help="List available local models with memory requirements and system compatibility",
    )
    parser.add_argument(
        "--check-local-requirements",
        action="store_true",
        help="Check system compatibility for local LLM processing",
    )
    parser.add_argument(
        "--download-model",
        help="Download a specific local model (e.g., --download-model gemma-2-2b)",
    )
    parser.add_argument(
        "--remove-model", 
        help="Remove a specific local model (e.g., --remove-model gemma-2-2b)",
    )
    parser.add_argument(
        "--local-model-info",
        help="Show detailed information about a specific local model",
    )

    # Display options
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Self-contained mode: one-line stats output, no user prompts. Requires API key and folders as parameters.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Default mode with guided menus, auto-detecting unicode support for rich or basic UI",
    )

    return parser.parse_args()


def list_available_models() -> None:
    """Prints a list of all AI models supported by the script, grouped by provider."""
    print("Available AI models by provider:")
    for provider, models in AIProviderFactory.list_providers().items():
        print(f"\n{provider.capitalize()}:")
        for model in models:
            print(f"  - {model}")


def _print_capabilities(ocr_lang: str) -> None:
    """Prints the status of optional dependencies."""
    # Import needed constants locally to avoid redefinition issues
    try:
        from content_processors import HAVE_PYMUPDF as _HAVE_PYMUPDF
        from content_processors import HAVE_TESSERACT as _HAVE_TESSERACT
        from content_processors import OCR_PAGES as _OCR_PAGES
        from content_processors import OCR_ZOOM as _OCR_ZOOM
    except ImportError:
        import os
        import sys

        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from content_processors import HAVE_PYMUPDF as _HAVE_PYMUPDF
        from content_processors import HAVE_TESSERACT as _HAVE_TESSERACT
        from content_processors import OCR_PAGES as _OCR_PAGES
        from content_processors import OCR_ZOOM as _OCR_ZOOM
    pymupdf_status = "yes" if _HAVE_PYMUPDF else "no"
    tesseract_status = "yes" if _HAVE_TESSERACT else "no"
    print(
        f"OCR deps -> PyMuPDF: {pymupdf_status}, Tesseract: {tesseract_status}; "
        f"OCR_LANG={ocr_lang}, OCR_PAGES={_OCR_PAGES}, OCR_ZOOM={_OCR_ZOOM}"
    )


def setup_environment_and_args():
    """Setup expert mode and parse command line arguments."""
    # Handle expert mode prompting (only if no CLI args provided)
    expert_args = prompt_expert_mode_if_needed()
    if expert_args:
        # Modify sys.argv to include expert mode arguments
        sys.argv.extend(expert_args)

    # Parse arguments (including any expert mode additions)
    args = parse_arguments()

    # Set the OCR language from the command-line argument.
    if not args.quiet:
        _print_capabilities(args.ocr_lang)

    # If the user just wants to see the available models, print them and exit.
    if args.list_models:
        list_available_models()
        sys.exit(0)

    # Handle Local LLM setup commands
    if args.setup_local_llm:
        setup_local_llm()
        sys.exit(0)
    
    if args.list_local_models:
        list_local_models()
        sys.exit(0)
    
    if args.check_local_requirements:
        check_local_requirements()
        sys.exit(0)
    
    if args.download_model:
        try:
            from utils.model_manager import ModelManager
            manager = ModelManager()
            print(f"📥 Downloading model: {args.download_model}")
            success = manager.download_model(args.download_model)
            if success:
                print(f"✅ {args.download_model} downloaded successfully!")
            else:
                print(f"❌ Failed to download {args.download_model}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
        sys.exit(0)
    
    if args.remove_model:
        try:
            from utils.model_manager import ModelManager
            manager = ModelManager()
            print(f"🗑️ Removing model: {args.remove_model}")
            success = manager.remove_model(args.remove_model)
            if success:
                print(f"✅ {args.remove_model} removed successfully!")
            else:
                print(f"❌ Failed to remove {args.remove_model}")
        except Exception as e:
            print(f"❌ Removal failed: {e}")
        sys.exit(0)
    
    if args.local_model_info:
        try:
            from utils.model_manager import ModelManager
            from utils.hardware_detector import HardwareDetector
            
            manager = ModelManager()
            detector = HardwareDetector()
            
            model_info = manager.get_model_info(args.local_model_info)
            if model_info:
                print(f"\n📋 Model Information: {args.local_model_info}")
                print(f"Memory Required: {model_info.memory_requirement_gb}GB")
                print(f"Download Size: {model_info.size_gb}GB")
                print(f"Description: {model_info.description}")
                print(f"Status: {model_info.status.value.replace('_', ' ').title()}")
                
                # Show performance estimate
                performance = detector.get_performance_estimate(args.local_model_info)
                if "error" not in performance:
                    print(f"Expected Speed: {performance['inference_speed']}")
                    print(f"Memory Status: {performance['memory_status']}")
                    print(f"Recommendation: {performance['recommendation']}")
            else:
                print(f"❌ Model '{args.local_model_info}' not found")
        except Exception as e:
            print(f"❌ Failed to get model info: {e}")
        sys.exit(0)

    return args


def setup_api_key(args) -> tuple:
    """Setup API key from command line arguments."""
    original_env = None
    api_key_set = False

    if args.api_key:
        env_var = f"{args.provider.upper()}_API_KEY"
        original_env = (env_var, os.environ.get(env_var))
        os.environ[env_var] = args.api_key
        api_key_set = True
        # Use enhanced display for API key message
        if not args.quiet:
            print(f"Using provided {args.provider.capitalize()} API key")

    return original_env, api_key_set


def restore_api_key(api_key_set: bool, original_env: tuple) -> None:
    """Restore original API key environment variable."""
    if api_key_set and original_env:
        try:
            env_var, original_value = original_env
            if original_value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = original_value
        except (KeyError, TypeError):
            print("Warning: Could not restore original API key environment.")


def list_available_models() -> None:
    """List all available models for all providers and exit."""
    # Standard AI provider models
    for provider, models in AI_PROVIDERS.items():
        print(f"\n{provider.upper()} Models:")
        for model in models:
            print(f"  • {model}")
    
    # Show recommended defaults
    print(f"\nRecommended Defaults:")
    for provider, model in {
        "openai": "gpt-5-mini",
        "gemini": "gemini-2.0-flash", 
        "claude": "claude-3.5-haiku",
        "deepseek": "deepseek-chat",
        "local": "llama3.2-3b"
    }.items():
        print(f"  • {provider}: {model}")
    
    print("\nUse: content-tamer-ai -p <provider> -m <model>")
    sys.exit(0)


def setup_local_llm() -> None:
    """Interactive setup for local LLM with hardware detection."""
    try:
        from utils.hardware_detector import HardwareDetector
        from utils.model_manager import ModelManager
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm, Prompt
        from rich.table import Table
        import subprocess
        import shutil
        
        console = Console()
        
        # Check if Ollama is installed
        ollama_installed = shutil.which("ollama") is not None
        
        console.print(Panel.fit("🤖 Local LLM Setup", style="bold blue"))
        
        if not ollama_installed:
            console.print("❌ Ollama not found. Installing Ollama is required for local LLM support.", style="red")
            if Confirm.ask("Would you like to install Ollama now?"):
                install_ollama()
            else:
                console.print("❌ Setup cancelled. Ollama is required for local LLM functionality.")
                return
        else:
            console.print("✅ Ollama is already installed", style="green")
        
        # Initialize hardware detector
        detector = HardwareDetector()
        console.print("🔍 Analyzing your system...", style="blue")
        
        # Get system summary
        summary = detector.get_system_summary()
        
        # Display hardware info
        hardware_table = Table(title="System Information")
        hardware_table.add_column("Component", style="cyan")
        hardware_table.add_column("Value", style="white")
        
        for key, value in summary["hardware"].items():
            hardware_table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(hardware_table)
        
        # Display recommendations
        recommendations = summary["recommendations"]
        if recommendations:
            rec = recommendations[0]
            console.print(f"\n💡 Recommended Model: [bold green]{rec['model']}[/bold green]")
            console.print(f"Confidence: {rec['confidence']}")
            console.print(f"Reason: {rec['reason']}")
            
            if rec['alternatives']:
                console.print(f"Alternatives: {', '.join(rec['alternatives'])}")
            
            # Ask user to proceed
            if Confirm.ask(f"Download and setup {rec['model']}?"):
                setup_model(rec['model'])
            elif rec['alternatives'] and Confirm.ask("Choose a different model?"):
                # Show model selection
                show_model_selection(rec['alternatives'])
        else:
            console.print("❌ No compatible models found for your system.", style="red")
            
    except ImportError as e:
        print(f"❌ Error: Missing dependencies - {e}")
        print("Please install: pip install psutil rich")
    except Exception as e:
        print(f"❌ Setup failed: {e}")


def install_ollama() -> None:
    """Install Ollama based on the current platform."""
    import platform
    import subprocess
    from rich.console import Console
    
    console = Console()
    system = platform.system()
    
    console.print("📦 Installing Ollama...", style="blue")
    
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"], 
                         shell=True, check=True)
        elif system == "Linux":
            subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"], 
                         shell=True, check=True)
        elif system == "Windows":
            console.print("Please download Ollama from https://ollama.com/download/windows", style="yellow")
            console.print("After installation, restart this setup process.", style="yellow")
            return
        else:
            console.print(f"❌ Unsupported platform: {system}", style="red")
            return
            
        console.print("✅ Ollama installed successfully!", style="green")
        console.print("Starting Ollama service...", style="blue")
        
        # Start Ollama service
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Failed to install Ollama: {e}", style="red")
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")


def setup_model(model_name: str) -> None:
    """Download and setup a specific model."""
    try:
        from utils.model_manager import ModelManager
        from rich.console import Console
        from rich.progress import Progress, TaskID
        import time
        
        console = Console()
        manager = ModelManager()
        
        if not manager.is_ollama_running():
            console.print("🚀 Starting Ollama service...", style="blue")
            import subprocess
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)  # Give Ollama time to start
        
        console.print(f"📥 Downloading {model_name}...", style="blue")
        
        with Progress() as progress:
            task = progress.add_task(f"[green]Downloading {model_name}...", total=100)
            
            def update_progress(percent):
                progress.update(task, completed=percent)
            
            success = manager.download_model(model_name, progress_callback=update_progress)
            
            if success:
                console.print(f"✅ {model_name} downloaded successfully!", style="green")
                console.print(f"🎉 Setup complete! You can now use: content-tamer-ai --provider local --model {model_name}", style="green")
            else:
                console.print(f"❌ Failed to download {model_name}", style="red")
                
    except Exception as e:
        console.print(f"❌ Model setup failed: {e}", style="red")


def show_model_selection(alternatives: list) -> None:
    """Show model selection interface."""
    try:
        from rich.console import Console
        from rich.prompt import Prompt
        from rich.table import Table
        from utils.model_manager import ModelManager
        
        console = Console()
        manager = ModelManager()
        
        # Show available models
        table = Table(title="Available Local Models")
        table.add_column("Model", style="cyan")
        table.add_column("RAM Required", style="yellow") 
        table.add_column("Size", style="white")
        table.add_column("Description", style="green")
        
        for model_name in alternatives + ["gemma-2-2b", "llama3.2-3b", "mistral-7b", "llama3.1-8b"]:
            model_info = manager.get_model_info(model_name)
            if model_info:
                table.add_row(
                    model_name,
                    f"{model_info.memory_requirement_gb}GB",
                    f"{model_info.size_gb}GB",
                    model_info.description
                )
        
        console.print(table)
        
        model_choice = Prompt.ask("Choose a model", choices=alternatives + ["gemma-2-2b", "llama3.2-3b", "mistral-7b", "llama3.1-8b"])
        setup_model(model_choice)
        
    except Exception as e:
        print(f"❌ Model selection failed: {e}")


def list_local_models() -> None:
    """List local models with system compatibility information."""
    try:
        from utils.hardware_detector import HardwareDetector
        from utils.model_manager import ModelManager
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        detector = HardwareDetector()
        manager = ModelManager()
        
        system_info = detector.detect_system_info()
        
        console.print(f"💻 System: {system_info.available_ram_gb:.1f}GB RAM available")
        console.print()
        
        table = Table(title="Local LLM Models")
        table.add_column("Model", style="cyan")
        table.add_column("RAM Required", style="yellow")
        table.add_column("Download Size", style="white") 
        table.add_column("Status", style="green")
        table.add_column("Compatible", style="blue")
        
        for model_name in ["gemma-2-2b", "llama3.2-3b", "mistral-7b", "llama3.1-8b"]:
            model_info = manager.get_model_info(model_name)
            if model_info:
                compatible = "✅" if system_info.available_ram_gb >= model_info.memory_requirement_gb else "❌"
                status_text = model_info.status.value.replace("_", " ").title()
                
                table.add_row(
                    model_name,
                    f"{model_info.memory_requirement_gb}GB",
                    f"{model_info.size_gb}GB",
                    status_text,
                    compatible
                )
        
        console.print(table)
        
        # Show recommendations
        recommendations = detector.get_recommended_models()
        if recommendations:
            rec = recommendations[0] 
            console.print(f"\n💡 Recommended: [bold green]{rec.model_name}[/bold green] ({rec.confidence} confidence)")
            console.print(f"Reason: {rec.reason}")
        
        console.print(f"\nSetup: content-tamer-ai --setup-local-llm")
        console.print(f"Usage: content-tamer-ai --provider local --model <model_name>")
        
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install psutil rich")
    except Exception as e:
        print(f"❌ Failed to list local models: {e}")


def check_local_requirements() -> None:
    """Check system requirements for local LLM processing."""
    try:
        from utils.hardware_detector import HardwareDetector
        from rich.console import Console
        from rich.panel import Panel
        import shutil
        
        console = Console()
        detector = HardwareDetector()
        
        console.print(Panel.fit("🔍 Local LLM Requirements Check", style="bold blue"))
        
        # Check Ollama installation
        ollama_installed = shutil.which("ollama") is not None
        console.print(f"Ollama installed: {'✅' if ollama_installed else '❌'}")
        
        # Check system compatibility
        compatibility = detector.check_ollama_compatibility()
        
        console.print(f"Platform supported: {'✅' if compatibility['supported_platform'] else '❌'}")
        console.print(f"Architecture supported: {'✅' if compatibility['supported_architecture'] else '❌'}")
        console.print(f"Sufficient RAM (>2GB): {'✅' if compatibility['sufficient_ram'] else '❌'}")
        console.print(f"Recommended RAM (>4GB): {'✅' if compatibility['recommended_ram'] else '❌'}")
        
        overall = compatibility['overall_compatible'] and ollama_installed
        console.print(f"\nOverall compatible: {'✅' if overall else '❌'}")
        
        if not overall:
            console.print("\n📋 To enable local LLM support:", style="yellow")
            if not ollama_installed:
                console.print("  • Install Ollama: content-tamer-ai --setup-local-llm")
            if not compatibility['sufficient_ram']:
                console.print("  • Upgrade system RAM to at least 4GB")
        else:
            console.print("\n🎉 Your system is ready for local LLM processing!", style="green")
            console.print("Run: content-tamer-ai --setup-local-llm")
            
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install psutil rich")
    except Exception as e:
        print(f"❌ Requirements check failed: {e}")
