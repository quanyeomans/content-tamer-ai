#!/bin/bash
# 
# Cross-platform installation script for AI-Powered Document Organization System
# Unix/Linux/macOS version
#

set -e  # Exit on any error

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "======================================================================"
    echo "  AI-Powered Document Organization System"
    echo "  Unix/Linux/macOS Installation Script"
    echo "======================================================================"
    echo -e "${NC}"
}

print_step() {
    local step_num=$1
    local title=$2
    echo -e "\n${BLUE}${BOLD}[Step $step_num]${NC} ${title}"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[X]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[i]${NC} $1"
}

check_python() {
    print_step 1 "Checking Python Version"
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        echo "  Install Python 3.8+ from https://python.org"
        exit 1
    fi
    
    # Check version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    major=$(echo $python_version | cut -d. -f1)
    minor=$(echo $python_version | cut -d. -f2)
    
    if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 8 ]]; then
        print_error "Python 3.8+ required, found $python_version"
        echo "  Please upgrade Python and try again"
        exit 1
    fi
    
    print_success "Python $python_version detected"
}

check_pip() {
    print_step 2 "Checking Package Manager"
    
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip not found"
        echo "  Install pip: https://pip.pypa.io/en/stable/installation/"
        exit 1
    fi
    
    print_success "pip package manager detected"
}

check_tesseract() {
    print_step 3 "Checking OCR Dependencies"
    
    if command -v tesseract &> /dev/null; then
        version_info=$(tesseract --version 2>&1 | head -1)
        print_success "Tesseract OCR found: $version_info"
        return 0
    else
        print_warning "Tesseract OCR not found (optional for full OCR support)"
        echo "  Installation instructions:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "    macOS: brew install tesseract"
        elif [[ -f /etc/debian_version ]]; then
            echo "    Ubuntu/Debian: sudo apt-get install tesseract-ocr"
        elif [[ -f /etc/redhat-release ]]; then
            echo "    RHEL/CentOS: sudo yum install tesseract"
        else
            echo "    Check your distribution's package manager for tesseract"
        fi
        return 1
    fi
}

get_user_consent() {
    local package_type=$1
    shift
    local packages=("$@")
    
    echo -e "\n${YELLOW}${BOLD}Installation Consent Required${NC}"
    echo "The following $package_type will be installed:"
    echo
    
    for pkg in "${packages[@]}"; do
        echo "  • $pkg"
    done
    
    echo
    echo "These packages will be installed using pip from the Python Package Index (PyPI)."
    echo "Installation requires internet connection and may take several minutes."
    echo
    
    while true; do
        read -p "Do you consent to install these packages? [y/N]: " response
        case $response in
            [yY][eE][sS]|[yY])
                return 0
                ;;
            [nN][oO]|[nN]|"")
                print_info "Installation cancelled by user"
                return 1
                ;;
            *)
                echo "Please enter 'y' for yes or 'n' for no (default: no)"
                ;;
        esac
    done
}

install_packages() {
    local package_type=$1
    shift
    local packages=("$@")
    
    if [[ ${#packages[@]} -eq 0 ]]; then
        return 0
    fi
    
    echo -e "\n${BLUE}Installing $package_type...${NC}"
    echo "  Command: python3 -m pip install ${packages[*]}"
    echo
    
    if python3 -m pip install "${packages[@]}"; then
        print_success "$package_type installed successfully"
        return 0
    else
        print_error "Failed to install $package_type"
        echo "  Try running the command manually or check your internet connection"
        return 1
    fi
}

select_ai_providers() {
    print_step 4 "AI Provider Selection"
    
    echo "Available AI providers:"
    echo
    echo "  1. OpenAI - GPT models (recommended - fully tested) [OK] Tested & Working"
    echo "  2. Claude - Anthropic Claude models [!] Needs Testing"
    echo "  3. Gemini - Google Gemini models [!] Needs Testing"  
    echo "  4. Dev - Development and testing tools [*] Optional"
    echo "  0. Skip AI provider installation (install manually later)"
    echo
    
    selected_packages=()
    
    while true; do
        read -p "Select providers to install [1,2,3,4 or 0 to skip]: " choices
        
        if [[ "$choices" == "0" || -z "$choices" ]]; then
            print_info "Skipping AI provider installation"
            break
        fi
        
        # Parse comma-separated choices
        IFS=',' read -ra ADDR <<< "$choices"
        valid=true
        temp_packages=()
        
        for i in "${ADDR[@]}"; do
            i=$(echo "$i" | xargs)  # trim whitespace
            case $i in
                1)
                    temp_packages+=("openai>=1.0.0")
                    ;;
                2)
                    temp_packages+=("anthropic>=0.3.0")
                    ;;
                3)
                    temp_packages+=("google-genai>=0.3.0")
                    ;;
                4)
                    temp_packages+=("pytest>=8.4.1")
                    ;;
                *)
                    valid=false
                    break
                    ;;
            esac
        done
        
        if [[ "$valid" == true ]]; then
            selected_packages=("${temp_packages[@]}")
            break
        else
            echo "Please enter numbers between 1-4 or 0 to skip"
        fi
    done
    
    echo "${selected_packages[@]}"
}

check_virtual_environment() {
    print_step 5 "Virtual Environment (Recommended)"
    
    # Check if already in virtual environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        print_info "Already running in virtual environment: $VIRTUAL_ENV"
        return 0
    fi
    
    echo "It's recommended to install packages in a virtual environment to avoid conflicts."
    echo
    echo "Virtual environment benefits:"
    echo "  • Isolates project dependencies"
    echo "  • Prevents system-wide package conflicts"
    echo "  • Easy to remove/recreate if needed"
    echo
    
    while true; do
        read -p "Create virtual environment? [Y/n]: " response
        case $response in
            [yY][eE][sS]|[yY]|"")
                break
                ;;
            [nN][oO]|[nN])
                print_warning "Proceeding without virtual environment"
                return 0
                ;;
            *)
                echo "Please enter 'y' for yes or 'n' for no"
                ;;
        esac
    done
    
    venv_name="venv"
    
    if [[ -d "$venv_name" ]]; then
        print_warning "Directory '$venv_name' already exists"
        while true; do
            read -p "Use existing directory? [Y/n]: " response
            case $response in
                [yY][eE][sS]|[yY]|"")
                    break
                    ;;
                [nN][oO]|[nN])
                    print_error "Virtual environment creation cancelled"
                    return 1
                    ;;
            esac
        done
    fi
    
    if ! [[ -d "$venv_name" ]]; then
        echo "Creating virtual environment in '$venv_name'..."
        if python3 -m venv "$venv_name"; then
            print_success "Virtual environment created successfully"
        else
            print_error "Failed to create virtual environment"
            echo "Continuing with system Python installation..."
            return 0
        fi
    fi
    
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Activate: ${BOLD}source $venv_name/bin/activate${NC}"
    echo -e "  2. Rerun installer: ${BOLD}./install.sh${NC}"
    echo
    echo "The installer will detect the active virtual environment automatically."
    
    return 1  # Don't continue installation in main environment
}

verify_installation() {
    print_step 6 "Verifying Installation"
    
    core_packages=(
        "PyPDF2"
        "tiktoken"
        "tqdm"
        "requests"
        "fitz:pymupdf"
        "PIL:pillow"
        "pytesseract"
    )
    
    failed_imports=()
    
    for pkg_info in "${core_packages[@]}"; do
        IFS=':' read -ra pkg_parts <<< "$pkg_info"
        import_name=${pkg_parts[0]}
        package_name=${pkg_parts[1]:-$import_name}
        
        if python3 -c "import $import_name" 2>/dev/null; then
            print_success "$package_name imported successfully"
        else
            print_error "Failed to import $package_name"
            failed_imports+=("$package_name")
        fi
    done
    
    if [[ ${#failed_imports[@]} -gt 0 ]]; then
        echo
        print_warning "Some packages failed to import. This may indicate:"
        echo "  • Installation incomplete"
        echo "  • System-specific dependency issues"
        echo "  • Python path problems"
        echo
        echo "Try reinstalling failed packages manually:"
        for pkg in "${failed_imports[@]}"; do
            echo "  python3 -m pip install --upgrade $pkg"
        done
        return 1
    fi
    
    echo
    print_success "All core packages verified successfully"
    return 0
}

print_completion_summary() {
    local tesseract_available=$1
    
    echo
    echo -e "${GREEN}${BOLD}Installation Complete!${NC}"
    echo
    
    echo "What's installed:"
    print_success "Core Python dependencies"
    print_success "PDF processing capabilities" 
    print_success "Image processing support"
    
    if [[ $tesseract_available -eq 0 ]]; then
        print_success "Full OCR capabilities (Tesseract)"
    else
        print_warning "Limited OCR (Tesseract binary not found)"
    fi
    
    echo
    echo "Next steps:"
    echo -e "  1. Set up API key: ${BOLD}export OPENAI_API_KEY='your-key-here'${NC}"
    echo -e "  2. Run the application: ${BOLD}python3 run.py${NC}"
    echo -e "  3. Place files in: ${BOLD}documents/input/${NC}"
    echo -e "  4. Find results in: ${BOLD}documents/processed/${NC}"
    echo
    
    echo "Documentation:"
    echo "  • README.md - Complete usage guide"
    echo "  • Run tests: python3 -m pytest tests/ -v"
    echo "  • List models: python3 run.py --list-models"
}

main() {
    print_header
    
    # Step 1: Check Python version
    check_python
    
    # Step 2: Check pip availability
    check_pip
    
    # Step 3: Check Tesseract (optional)
    check_tesseract
    tesseract_available=$?
    
    # Step 4: Select AI providers  
    ai_packages_str=$(select_ai_providers)
    IFS=' ' read -ra ai_packages <<< "$ai_packages_str"
    
    # Step 5: Virtual environment
    if ! check_virtual_environment; then
        exit 0  # Exit to let user activate venv and rerun
    fi
    
    # Core requirements
    core_packages=(
        "PyPDF2>=6.0.0"
        "tiktoken>=0.11.0"
        "tqdm>=4.67.1"
        "requests>=2.32.5"
        "pymupdf>=1.26.3"
        "pillow>=11.3.0"
        "pytesseract>=0.3.13"
    )
    
    # Request consent for core packages
    if ! get_user_consent "core dependencies" "${core_packages[@]}"; then
        print_error "Installation cancelled"
        exit 1
    fi
    
    # Install core packages
    if ! install_packages "core dependencies" "${core_packages[@]}"; then
        exit 1
    fi
    
    # Install AI provider packages if selected
    if [[ ${#ai_packages[@]} -gt 0 ]]; then
        if get_user_consent "AI provider packages" "${ai_packages[@]}"; then
            if ! install_packages "AI provider packages" "${ai_packages[@]}"; then
                print_warning "AI provider installation failed, but core system should work"
            fi
        else
            print_info "Skipped AI provider installation"
        fi
    fi
    
    # Step 6: Verify installation
    if ! verify_installation; then
        print_warning "Installation completed with warnings"
    fi
    
    # Print completion summary
    print_completion_summary $tesseract_available
}

# Handle interrupts gracefully
trap 'echo -e "\n${YELLOW}Installation cancelled by user${NC}"; exit 1' INT

# Run main function
main "$@"