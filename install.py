#!/usr/bin/env python3
"""
Cross-platform installation script for Content Tamer AI.

This script checks system requirements, validates Python environment, 
and installs dependencies with user consent.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


class Colors:
    """ANSI color codes for cross-platform terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    @classmethod
    def disable_on_windows(cls):
        """Disable colors on older Windows terminals that don't support ANSI."""
        if platform.system() == "Windows":
            # Try to enable ANSI support on Windows 10+
            try:
                import colorama
                colorama.init()
            except ImportError:
                # Fallback: disable colors entirely
                for attr in dir(cls):
                    if not attr.startswith('_') and attr != 'disable_on_windows':
                        setattr(cls, attr, '')


def print_header():
    """Print installation header."""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 70)
    print("  Content Tamer AI - Intelligent Document Organization")
    print("  Cross-Platform Installation Script")
    print("=" * 70)
    print(f"{Colors.END}")


def print_step(step_num, title, description=""):
    """Print installation step with formatting."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Step {step_num}]{Colors.END} {Colors.WHITE}{title}{Colors.END}")
    if description:
        print(f"  {description}")


def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}[OK]{Colors.END} {message}")


def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}[!]{Colors.END} {message}")


def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}[X]{Colors.END} {message}")


def print_info(message):
    """Print info message."""
    print(f"{Colors.CYAN}[i]{Colors.END} {message}")


def check_python_version():
    """Check if Python version meets requirements."""
    print_step(1, "Checking Python Version")
    
    version = sys.version_info
    required_major, required_minor = 3, 8
    
    if version.major < required_major or (version.major == required_major and version.minor < required_minor):
        print_error(f"Python {required_major}.{required_minor}+ required, found {version.major}.{version.minor}.{version.micro}")
        print("  Please upgrade Python and try again.")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_pip_available():
    """Check if pip is available."""
    print_step(2, "Checking Package Manager")
    
    try:
        import pip
        print_success("pip package manager detected")
        return True
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            print_success("pip available via module")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("pip not found")
            print("  Install pip: https://pip.pypa.io/en/stable/installation/")
            return False


def check_tesseract_binary():
    """Check for Tesseract OCR binary installation."""
    print_step(3, "Checking OCR Dependencies")
    
    tesseract_cmd = "tesseract" if platform.system() != "Windows" else "tesseract.exe"
    
    if shutil.which(tesseract_cmd):
        try:
            result = subprocess.run([tesseract_cmd, "--version"], 
                                  capture_output=True, text=True, check=True)
            version_line = result.stdout.split('\n')[0]
            print_success(f"Tesseract OCR found: {version_line}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    print_warning("Tesseract OCR not found (optional for full OCR support)")
    print("  Installation instructions:")
    
    system = platform.system()
    if system == "Darwin":  # macOS
        print("    macOS: brew install tesseract")
    elif system == "Linux":
        print("    Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("    RHEL/CentOS: sudo yum install tesseract")
    elif system == "Windows":
        print("    Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("    Add installation directory to PATH")
    
    return False


def get_core_requirements():
    """Get list of core Python dependencies."""
    return [
        "pypdf>=6.0.0",
        "tiktoken>=0.11.0", 
        "tqdm>=4.67.1",
        "requests>=2.32.5",
        "pymupdf>=1.26.3",
        "pillow>=11.3.0",
        "pytesseract>=0.3.13",
        "pdfid>=1.1.0",
    ]


def get_ai_provider_options():
    """Get AI provider installation options."""
    return {
        "openai": {
            "package": "openai>=1.0.0",
            "description": "OpenAI GPT models (recommended - fully tested)",
            "status": "[OK] Tested & Working"
        },
        "claude": {
            "package": "anthropic>=0.3.0", 
            "description": "Anthropic Claude models",
            "status": "[!] Needs Testing"
        },
        "gemini": {
            "package": "google-genai>=0.3.0",
            "description": "Google Gemini models", 
            "status": "[!] Needs Testing"
        },
        "dev": {
            "package": "pytest>=8.4.1",
            "description": "Development and testing tools",
            "status": "[*] Optional"
        }
    }


def prompt_user_consent(packages, package_type="dependencies"):
    """Prompt user for installation consent."""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}Installation Consent Required{Colors.END}")
    print(f"The following {package_type} will be installed:")
    print()
    
    for pkg in packages:
        print(f"  • {pkg}")
    
    print()
    print("These packages will be installed using pip from the Python Package Index (PyPI).")
    print("Installation requires internet connection and may take several minutes.")
    print()
    
    while True:
        response = input(f"Do you consent to install these packages? {Colors.BOLD}[y/N]{Colors.END}: ").strip().lower()
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            print_info("Installation cancelled by user")
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no (default: no)")


def install_packages(packages, package_type="packages"):
    """Install Python packages using pip."""
    if not packages:
        return True
        
    print(f"\n{Colors.BLUE}Installing {package_type}...{Colors.END}")
    
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    
    try:
        # Show command being executed
        print(f"  Command: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(cmd, check=True, text=True)
        print_success(f"{package_type.capitalize()} installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install {package_type}")
        print(f"  Error code: {e.returncode}")
        print("  Try running the command manually or check your internet connection")
        return False


def select_ai_providers():
    """Interactive AI provider selection."""
    print_step(4, "AI Provider Selection")
    providers = get_ai_provider_options()
    
    print("Available AI providers:")
    print()
    
    options = list(providers.keys())
    for i, (key, info) in enumerate(providers.items(), 1):
        status_color = Colors.GREEN if "[OK]" in info["status"] else Colors.YELLOW if "[!]" in info["status"] else Colors.CYAN
        print(f"  {i}. {Colors.BOLD}{key.title()}{Colors.END} - {info['description']}")
        print(f"     {status_color}{info['status']}{Colors.END}")
        print()
    
    print(f"  0. Skip AI provider installation (install manually later)")
    print()
    
    selected_packages = []
    
    while True:
        try:
            choices = input(f"Select providers to install {Colors.BOLD}[1,2,3,4 or 0 to skip]{Colors.END}: ").strip()
            
            if choices == '0' or choices == '':
                print_info("Skipping AI provider installation")
                break
                
            # Parse comma-separated choices
            indices = [int(x.strip()) for x in choices.split(',') if x.strip()]
            
            if all(1 <= i <= len(options) for i in indices):
                for i in indices:
                    key = options[i-1]
                    selected_packages.append(providers[key]["package"])
                break
            else:
                print(f"Please enter numbers between 1-{len(options)} or 0 to skip")
                
        except ValueError:
            print("Please enter valid numbers separated by commas")
    
    return selected_packages


def create_virtual_environment():
    """Offer to create virtual environment."""
    print_step(5, "Virtual Environment (Recommended)")
    
    # Check if already in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_info("Already running in virtual environment")
        return True
    
    print("It's recommended to install packages in a virtual environment to avoid conflicts.")
    print()
    print("Virtual environment benefits:")
    print("  • Isolates project dependencies")
    print("  • Prevents system-wide package conflicts") 
    print("  • Easy to remove/recreate if needed")
    print()
    
    while True:
        response = input(f"Create virtual environment? {Colors.BOLD}[Y/n]{Colors.END}: ").strip().lower()
        
        if response in ['y', 'yes', '']:
            break
        elif response in ['n', 'no']:
            print_warning("Proceeding without virtual environment")
            return True
        else:
            print("Please enter 'y' for yes or 'n' for no")
    
    venv_name = "venv"
    venv_path = Path(venv_name)
    
    if venv_path.exists():
        print_warning(f"Directory '{venv_name}' already exists")
        while True:
            response = input("Use existing directory? [Y/n]: ").strip().lower()
            if response in ['y', 'yes', '']:
                break
            elif response in ['n', 'no']:
                print_error("Virtual environment creation cancelled")
                return False
    
    try:
        print(f"Creating virtual environment in '{venv_name}'...")
        subprocess.run([sys.executable, "-m", "venv", venv_name], check=True)
        
        # Provide activation instructions
        system = platform.system()
        if system == "Windows":
            activate_cmd = f"{venv_name}\\Scripts\\activate.bat"
            pip_cmd = f"{venv_name}\\Scripts\\pip.exe"
        else:
            activate_cmd = f"source {venv_name}/bin/activate"
            pip_cmd = f"{venv_name}/bin/pip"
        
        print_success("Virtual environment created successfully")
        print()
        print(f"{Colors.YELLOW}Next steps:{Colors.END}")
        print(f"  1. Activate: {Colors.BOLD}{activate_cmd}{Colors.END}")
        print(f"  2. Rerun installer: {Colors.BOLD}python install.py{Colors.END}")
        print()
        print("The installer will detect the active virtual environment automatically.")
        
        return False  # Don't continue installation in main environment
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        print("Continuing with system Python installation...")
        return True


def verify_installation():
    """Verify that core packages can be imported."""
    print_step(6, "Verifying Installation")
    
    core_imports = [
        ("pypdf", "pypdf"),
        ("tiktoken", "tiktoken"),
        ("tqdm", "tqdm"),
        ("requests", "requests"),
        ("pymupdf", "fitz"),
        ("pillow", "PIL"),
        ("pytesseract", "pytesseract"),
        ("pdfid", "pdfid"),
    ]
    
    failed_imports = []
    
    for package_name, import_name in core_imports:
        try:
            __import__(import_name)
            print_success(f"{package_name} imported successfully")
        except ImportError:
            print_error(f"Failed to import {package_name}")
            failed_imports.append(package_name)
    
    if failed_imports:
        print()
        print_warning("Some packages failed to import. This may indicate:")
        print("  • Installation incomplete")
        print("  • System-specific dependency issues") 
        print("  • Python path problems")
        print()
        print("Try reinstalling failed packages manually:")
        for pkg in failed_imports:
            print(f"  pip install --upgrade {pkg}")
        return False
    
    print()
    print_success("All core packages verified successfully")
    return True


def print_completion_summary(tesseract_available):
    """Print installation completion summary."""
    print()
    print(f"{Colors.GREEN}{Colors.BOLD}Installation Complete!{Colors.END}")
    print()
    
    print("What's installed:")
    print_success("Core Python dependencies")
    print_success("PDF processing capabilities")
    print_success("Image processing support")
    
    if tesseract_available:
        print_success("Full OCR capabilities (Tesseract)")
    else:
        print_warning("Limited OCR (Tesseract binary not found)")
    
    print()
    print("Next steps:")
    print(f"  1. Set up API key: {Colors.BOLD}export OPENAI_API_KEY='your-key-here'{Colors.END}")
    print(f"  2. Run the application: {Colors.BOLD}python run.py{Colors.END}")
    print(f"  3. Place files in: {Colors.BOLD}documents/input/{Colors.END}")
    print(f"  4. Find results in: {Colors.BOLD}documents/processed/{Colors.END}")
    print()
    
    print("Documentation:")
    print("  • README.md - Complete usage guide")
    print("  • Run tests: python -m pytest tests/ -v")
    print("  • List models: python run.py --list-models")


def main():
    """Main installation function."""
    # Initialize colors (disable on older Windows)
    Colors.disable_on_windows()
    
    print_header()
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check pip availability  
    if not check_pip_available():
        sys.exit(1)
    
    # Step 3: Check Tesseract (optional)
    tesseract_available = check_tesseract_binary()
    
    # Step 4: Select AI providers
    ai_packages = select_ai_providers()
    
    # Step 5: Virtual environment
    if not create_virtual_environment():
        sys.exit(0)  # Exit to let user activate venv and rerun
    
    # Get core requirements
    core_packages = get_core_requirements()
    
    # Request consent for core packages
    if not prompt_user_consent(core_packages, "core dependencies"):
        print_error("Installation cancelled")
        sys.exit(1)
    
    # Install core packages
    if not install_packages(core_packages, "core dependencies"):
        sys.exit(1)
    
    # Install AI provider packages if selected
    if ai_packages:
        if prompt_user_consent(ai_packages, "AI provider packages"):
            if not install_packages(ai_packages, "AI provider packages"):
                print_warning("AI provider installation failed, but core system should work")
        else:
            print_info("Skipped AI provider installation")
    
    # Step 6: Verify installation
    if not verify_installation():
        print_warning("Installation completed with warnings")
    
    # Print completion summary
    print_completion_summary(tesseract_available)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Installation cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)