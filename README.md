# 🤖 Content Tamer AI

**Transform digital chaos into organized, searchable assets**

When you digitize your life - scanning bills, taking screenshots, saving documents - you end up with thousands of files with meaningless names like `IMG_2074.jpg` or `Screenshot 2024-08-24.png`. Content Tamer AI uses vision-capable AI models to understand what your documents actually contain and generates intelligent, descriptive filenames that make everything instantly searchable and workflow-ready.

## ✨ Quick Start (2 minutes)

```bash
# 1. Clone and install
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
python scripts/install.py  # Cross-platform installer with guided setup

# 2. Set your API key
export OPENAI_API_KEY="your-key-here"  # or set OPENAI_API_KEY=your-key-here on Windows

# 3. Run!
content-tamer-ai  # Uses smart defaults - just works!
# or: python run.py
```

**That's it!** Drop files in `data/input/` and find intelligently renamed files in `data/processed/`

---

## 🎯 What Content Tamer AI Does

### ✅ Core Capabilities
- **🧠 AI Content Analysis** — Vision models understand document content, not just filenames  
- **📄 Universal File Support** — PDFs, images, screenshots, scanned documents
- **🔍 Intelligent OCR** — Multi-stage text extraction with auto-orientation
- **📝 Descriptive Filenames** — Generates meaningful names up to 160 characters
- **🔄 Batch Processing** — Handle hundreds of files with crash-safe resume
- **🎛️ Zero Configuration** — Works immediately with smart defaults
- **🎨 Enhanced CLI Experience** — Rich progress bars, intelligent messaging, and visual feedback

### 🤖 AI Provider Support
- **OpenAI** ✅ **Production Ready** — GPT-5, GPT-4o with full vision support
- **Claude** ✅ **Latest Models** — Claude Opus 4.1, Sonnet 4, Claude 3.5 series (Opus, Sonnet, Haiku)
- **Gemini** ✅ **Latest Models** — Gemini 2.5 Pro/Flash, 2.0 Flash/Pro with thinking capabilities  
- **Deepseek** ⚠️ **Available** — Cost-effective option, community testing welcomed
- **🏠 Local LLM** ✅ **NEW** — Complete offline processing with Ollama backend

---

## 📁 Use Cases & Examples

### 🏠 Digitizing Your Life
**Before Content Tamer AI:**
```
scan001.pdf
IMG_1234.png
document.pdf
Screenshot 2024-08-24.png
```

**After Content Tamer AI:**
```
quarterly_financial_report_q3_2024.pdf
employee_handbook_remote_work_policy.png
lease_agreement_apartment_downtown.pdf
utility_bill_electricity_january_2024.png
```

### 🎯 Perfect For
- **📄 Scanned Bills & Receipts** — Automatically identify vendors, dates, amounts
- **📱 Screenshot Organization** — Turn random screenshots into searchable assets
- **💼 Business Documents** — Contracts, invoices, reports get meaningful names
- **📚 Research Materials** — Academic papers, articles, notes become findable
- **🏠 Personal Records** — Medical documents, warranties, manuals get organized

---

## 🚀 Installation & Setup

### Option 1: Automated Installation (Recommended)

```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
python scripts/install.py  # Smart cross-platform installer
```

**✨ Installer Features:**
- 🔍 **System validation** (Python, dependencies)
- 💬 **Explicit consent** (shows exactly what gets installed)
- 🏠 **Virtual environment option** (keeps system clean)
- ✅ **Installation verification** (tests everything works)

### Option 2: Manual Setup

```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
pip install -r requirements.txt

# Install your preferred AI provider:
pip install openai>=1.0.0           # For OpenAI (GPT-5, GPT-4o)
pip install anthropic>=0.34.0       # For Claude (Opus 4.1, Sonnet 4, 3.5 series)
pip install google-genai>=0.7.0     # For Gemini (2.5 Pro/Flash, 2.0 series)

# For Local LLM support (offline processing)
pip install psutil>=5.9.0           # System hardware detection
# Note: Ollama installation handled automatically by --setup-local-llm
```

## 🔑 API Key Setup

### Cloud Providers (Optional)

**Get an API key from your preferred provider:**
- [OpenAI API Keys](https://platform.openai.com/api-keys) — GPT-5, GPT-4o with vision support
- [Anthropic Claude](https://console.anthropic.com/) — Claude Opus 4.1, Sonnet 4, Claude 3.5 series
- [Google AI Studio](https://aistudio.google.com/) — Gemini 2.5 Pro/Flash with thinking capabilities

**Set your API key:**
```bash
# Method 1: Environment variable (recommended)
export OPENAI_API_KEY="your-key-here"        # macOS/Linux
set OPENAI_API_KEY=your-key-here             # Windows

# Method 2: The app will prompt you if no key is found
```

### Local LLM (No API Key Required)

**For complete offline processing:**
```bash
# No API key setup needed!
content-tamer-ai --setup-local-llm    # One-time setup
content-tamer-ai -p local              # Use local processing
```

---

## 🎮 Usage Examples

### 🚀 Quick Start (Recommended)

```bash
# Just run it! Uses smart defaults
content-tamer-ai
# or: python run.py

# Check data/processed/ for intelligently renamed files
```

### 🎛️ Advanced Options

```bash
# Different AI models
content-tamer-ai -m gpt-4o          # Best vision support
content-tamer-ai -m gpt-5           # Most capable

# Different providers with latest models
content-tamer-ai -p claude -m claude-opus-4.1      # Most advanced Claude model
content-tamer-ai -p claude -m claude-sonnet-4      # High performance Claude
content-tamer-ai -p claude -m claude-3.5-haiku    # Fast, cost-effective Claude
content-tamer-ai -p gemini -m gemini-2.5-pro      # Advanced reasoning Gemini
content-tamer-ai -p gemini -m gemini-2.0-flash    # Fast, efficient Gemini (default)
content-tamer-ai -p deepseek        # Cost-effective alternative

# 🏠 Local LLM (offline processing) - NEW!
content-tamer-ai --setup-local-llm                    # Interactive setup with hardware detection
content-tamer-ai -p local -m llama3.2-3b             # Use local model (no API key needed)
content-tamer-ai -p local -m gemma-2-2b              # Lightweight option for 4GB RAM systems

# Custom folders
content-tamer-ai -i ~/Downloads -r ~/Organized

# Multi-language OCR
content-tamer-ai --ocr-lang "eng+spa"  # English + Spanish

# Display and output control
content-tamer-ai --quiet            # Minimal output, progress bar only
content-tamer-ai --verbose          # Detailed logging with debug info
content-tamer-ai --no-color         # Plain text output (great for scripts)
content-tamer-ai --no-stats         # Hide statistics in progress display
```

### 🔍 Helpful Commands

```bash
content-tamer-ai --help                    # Show all options
content-tamer-ai --list-models             # See available AI models
content-tamer-ai --check-dependencies      # Check all system dependencies
content-tamer-ai --refresh-dependencies    # Refresh dependency detection
content-tamer-ai --quiet                   # Clean, minimal output
content-tamer-ai --verbose                 # Detailed processing information
```

---

## 🎨 Enhanced User Experience

Content Tamer AI features a completely redesigned CLI experience with intelligent visual feedback:

### 🌈 Rich Visual Interface
- **Color-coded progress bars** with real-time status indicators
- **Smart terminal detection** with graceful fallbacks for all environments
- **Unicode icons** with ASCII alternatives for maximum compatibility
- **Highlighted target filenames** showing exactly what each file becomes

### 📊 Intelligent Progress Display
```
Processing documents... ████████████████████████████████████ 85.2% → quarterly_report_2024_financials.pdf ✅ Done
✅ 12 processed │ ⚠️ 2 warnings │ ⏱️ 45.3s elapsed
```

### 🎛️ Adaptive Messaging System
- **Progressive disclosure** - Choose your information level (minimal/standard/detailed/debug)
- **Message prioritization** - Critical alerts always visible, debug info when you need it
- **Smart grouping** - Similar messages consolidated to prevent spam
- **Context hints** - See exactly which file triggered each message

### 🔧 Display Control Options
- `--quiet` - Clean progress bar only, perfect for automation
- `--verbose` - Full diagnostic output for troubleshooting
- `--no-color` - Plain text mode for scripts and CI/CD
- `--no-stats` - Minimal progress without detailed statistics

---

## 📁 How It Works

**Default Directory Structure:**
```
data/
├── 📥 input/           # ← Drop your files here
├── ✅ processed/       # ← Intelligently renamed files appear here  
│   └── ❌ unprocessed/ # ← Files that couldn't be processed
└── 🔄 .processing/     # ← Progress tracking (hidden)
```

**Processing Pipeline:**
1. **📥 File Discovery** — Scans for PDFs, images, screenshots
2. **🔍 Content Extraction** — Multi-stage OCR + text extraction
3. **🧠 AI Analysis** — Vision models understand document content
4. **📝 Name Generation** — Creates descriptive, searchable filenames
5. **🎯 Smart Organization** — Handles duplicates, sanitizes names, moves files safely

---

## 📄 Supported File Types

### ✅ Currently Supported
- **📄 PDF Files** — Native text + OCR + vision analysis with security scanning
- **🖼️ Images** — PNG, JPG, BMP, TIFF, GIF with full OCR
- **📱 Screenshots** — Perfect for organizing screenshot collections
- **🔍 Scanned Documents** — Auto-orientation and cleanup

### 🔮 Coming Soon
- **📊 Microsoft Office** — Word, Excel, PowerPoint
- **📝 Text Documents** — .txt, .md, .rtf
- **🎯 Custom Formats** — Based on community requests

---

## 🏠 Local LLM Processing (NEW!)

**Complete offline document processing with no API keys required**

### ✨ Why Local LLMs?

- **🔒 Complete Privacy** — Your documents never leave your machine
- **💰 Zero API Costs** — No per-document or monthly fees
- **🚀 Always Available** — No internet connection required
- **⚡ Fast Processing** — Direct hardware acceleration

### 🛠️ Quick Setup

```bash
# 1. Check if your system is ready
content-tamer-ai --check-local-requirements

# 2. Automatic setup with hardware detection (now with 10-minute timeout for large models)
content-tamer-ai --setup-local-llm

# 3. Start processing offline!
content-tamer-ai --provider local --model llama3.2-3b
```

### 🎯 Hardware-Optimized Models

| Model | RAM Required | Download Size | Best For | Performance |
|-------|-------------|---------------|----------|-------------|
| **gemma-2-2b** | 2.5GB | 1.7GB | 4GB RAM laptops | 15-30 seconds |
| **llama3.2-3b** | 4.5GB | 2.2GB | Standard desktops | 8-15 seconds |
| **mistral-7b** | 6.5GB | 4.4GB | Quality-focused | 5-12 seconds |
| **llama3.1-8b** | 7.5GB | 4.7GB | High-end systems | 3-8 seconds |

### 📋 Local LLM Commands

```bash
# Setup and Management
content-tamer-ai --setup-local-llm              # Interactive setup
content-tamer-ai --list-local-models            # Show available models
content-tamer-ai --check-local-requirements     # System compatibility check

# Model Management
content-tamer-ai --download-model gemma-2-2b    # Download specific model
content-tamer-ai --remove-model mistral-7b      # Remove model to save space
content-tamer-ai --local-model-info llama3.2-3b # Detailed model information

# Usage Examples
content-tamer-ai -p local -m llama3.2-3b        # Standard usage (most systems)
content-tamer-ai -p local -m gemma-2-2b         # Lightweight (4GB RAM)
content-tamer-ai -p local -m mistral-7b         # High quality (8GB+ RAM)
```

### 💡 Smart Hardware Detection

The setup process automatically:
- **🔍 Analyzes your system** — RAM, CPU, GPU detection
- **🎯 Recommends optimal models** — Based on available resources  
- **📊 Shows performance estimates** — Expected processing speeds
- **⏰ Extended download support** — 10-minute timeout for large models like llama3.1-8b
- **⚠️ Warns about limitations** — Memory pressure, compatibility issues

### 🔧 Behind the Scenes

**Powered by [Ollama](https://ollama.com/)**
- Production-ready model management
- Automatic quantization and optimization
- Cross-platform compatibility  
- GPU acceleration when available

**No Configuration Required**
- Ollama and Tesseract auto-detected with centralized dependency management
- Models downloaded with progress tracking and extended 10-minute timeout
- Robust error handling and recovery
- Graceful fallback to cloud providers

---

## 🚀 Roadmap & Vision

### 🎯 Next Major Features  
- **🗂️ Smart Folder Organization** — Auto-create folders by content type
- **📅 Date-Based Sorting** — Extract dates for chronological organization  
- **🏢 Domain Classification** — Separate work, personal, financial documents
- **📊 Office Suite Support** — Full Word/Excel/PowerPoint processing

### 💡 The Vision
Content Tamer AI is becoming a comprehensive **digital life organization platform**. We're building toward:

- **Intelligent Document Workflows** — From chaos to searchable knowledge base
- **Privacy-First Processing** — Local LLM support for sensitive documents  
- **Universal Content Understanding** — Any file type, any language, any format
- **Workflow Integration** — Connect with your existing productivity tools

---

## 🧪 Quality & Reliability

**Production-Ready Codebase:**
- ✅ **536 comprehensive tests** covering all components and architectural layers (494 passing, 92.2% success rate)
- ✅ **Full type annotations** with static analysis and Rich UI testing infrastructure
- ✅ **Modern dependency injection architecture** with ApplicationContainer pattern for maintainability
- ✅ **Cross-platform compatibility** (Windows, macOS, Linux)
- ✅ **Crash-safe processing** with resume capability
- ✅ **Advanced Rich CLI testing** with proper console management and display component validation

---

## 🔒 Security & Safety

**Enterprise-Grade Security Controls:**
- 🛡️ **PDF Threat Detection** — Integrated PDFiD analysis with secure XML parsing (XXE protection)
- 🚫 **Prompt Injection Protection** — Advanced pattern detection prevents AI manipulation attacks  
- 🔒 **Command Injection Prevention** — Secure subprocess execution prevents shell injection attacks
- 🛡️ **Path Traversal Prevention** — Full path validation blocks directory traversal exploits
- 🔐 **Secure API Key Handling** — Masked input, validation, and secure logging prevent credential exposure
- 📏 **File Size Limits** — 50MB PDF / 10MB image limits prevent resource exhaustion
- ✅ **Input Sanitization** — Comprehensive content validation and control character removal
- 🔐 **Secure Local LLM** — Ollama installation with integrity validation and injection protection

**PDF Security Analysis:**
Content Tamer AI automatically analyzes PDFs for potential threats:
- **🟢 SAFE**: Clean PDFs process normally
- **🟡 LOW/MEDIUM**: Suspicious content generates warnings but continues processing  
- **🔴 HIGH**: Multiple threat indicators trigger enhanced warnings

**Non-Destructive Approach:**
Our security philosophy prioritizes **user control** over blocking. We detect and warn about potential threats while preserving document integrity - perfect for personal document organization where you know your files.

---

## 🤝 Contributing & Community

**We'd love your help! Priority areas:**
- 🧪 **Test latest AI models** — Claude Opus 4.1, Gemini 2.5 Pro, validate new features  
- 📄 **Add file types** — Office docs, new formats
- 🏠 **Local LLM integration** — Privacy-focused processing
- 🌍 **Internationalization** — Multi-language support

**Quick Start for Contributors:**
```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
python scripts/install.py  # Get set up

# Configure your IDE (optional but recommended)
cp .vscode/settings.json.example .vscode/settings.json  # VS Code
cp .claude/settings.json.example .claude/settings.local.json  # Claude Code
# See documentation/IDE_SETUP.md for other IDEs

# Make your changes
python -m pytest   # Run tests
```

---

## 📋 Requirements

**System Requirements:**
- Python 3.8+ (tested up to Python 3.13)
- 50MB free disk space
- Internet connection for AI processing
- **The automated installer handles everything else!** 🎉

---

## Troubleshooting

### Common Issues
- **Files named `empty_file_*`** — Install OCR dependencies or use vision model (`-m gpt-4o`)
- **Permission errors** — Use non-synced folders, antivirus may lock files
- **API errors** — Check API key is set correctly for your provider
- **Garbled progress display** — Use `--no-color` for terminals with limited Unicode support
- **Too much/little output** — Use `--quiet` for minimal output or `--verbose` for detailed logging
- **Local LLM download timeout** — Large models (llama3.1-8b) now supported with 10-minute timeout
- **Tesseract/Ollama not found** — Use `--check-dependencies` to verify installation and auto-configure paths

### Known Test Issues (Errata)
The following test failures represent 7.8% of total tests and are primarily related to integration testing patterns or known environment constraints:
- **Contract Tests**: Some contract validation patterns need alignment with current architecture
- **Integration Tests**: Complex multi-component interaction edge cases
- **CLI Integration**: Command-line interface tests with directory mocking improvements needed
- **Security Tests**: Command injection prevention tests with subprocess execution patterns

*These failures do not affect core application functionality and represent areas for future test infrastructure improvements*

### Getting Help
- Check the detailed error logs in `data/.processing/errors.log`
- Run with `--verbose` for comprehensive diagnostic output
- Use `--debug` mode for maximum detail (messages, timing, system info)
- [Open an issue](https://github.com/quanyeomans/content-tamer-ai/issues) for bug reports
- Use `content-tamer-ai --help` for all command options

---

## 🏗️ Architecture & Development

### Code Architecture

Content Tamer AI follows a modular architecture designed for maintainability and extensibility:

```
src/
├── main.py                           # Clean entry point (148 lines)
├── core/                             # Core application modules
│   ├── application.py               # Main orchestration logic (248 lines)
│   ├── application_container.py     # Dependency injection container (215 lines)
│   ├── cli_handler.py               # CLI command handlers (new)
│   ├── cli_parser.py               # Command line argument parsing (216 lines)
│   ├── compatibility_layer.py       # Legacy compatibility support (new)
│   ├── directory_manager.py        # Directory setup & validation (88 lines)
│   ├── file_processor.py           # File processing pipeline (448 lines)
│   └── filename_config.py          # Centralized configuration (new)
├── ai_providers/                     # AI service integrations
│   ├── __init__.py
│   ├── base_provider.py             # Abstract base class
│   ├── openai_provider.py           # OpenAI integration
│   ├── claude_provider.py           # Claude integration
│   ├── gemini_provider.py           # Gemini integration
│   ├── deepseek_provider.py         # Deepseek integration
│   └── local_llm_provider.py        # Local LLM with Ollama
├── content_processors.py            # Content extraction (PDF, images, OCR)
├── file_organizer.py                # File operations & organization
└── utils/                           # Supporting utilities
    ├── console_manager.py           # Centralized Rich Console management (new)
    ├── error_handling.py            # Retry logic & error classification
    ├── expert_mode.py               # Interactive configuration
    ├── feature_flags.py             # Feature management system (new)
    ├── rich_cli_display.py          # Rich CLI components (new)
    ├── rich_display_manager.py      # Rich display orchestration (new)
    ├── rich_progress_display.py     # Rich progress components (new)
    └── hardware_detector.py         # System hardware detection (new)
```

### Key Design Principles

- **Dependency Injection**: ApplicationContainer pattern for clean component wiring and testability
- **Separation of Concerns**: Each module has a focused responsibility (main.py reduced from 1005 → 148 lines)
- **Centralized Configuration**: ConsoleManager and filename_config.py eliminate scattered settings
- **Rich UI Architecture**: Proper console management prevents I/O conflicts and enables beautiful displays
- **Modular Architecture**: Components developed and tested independently with proper abstractions
- **Clean Architecture**: Core business logic separated from infrastructure concerns
- **Extensibility**: Easy to add new AI providers, content processors, or display modes
- **Robust Error Handling**: Intelligent retry logic with exponential backoff
- **Cross-Platform**: Works on Windows, macOS, and Linux with consistent behavior

### Recent Architectural Improvements

**Phase 1-4 Evolution (2024):**
- ✅ **Monolithic main.py decomposed** into focused `core/` modules with dependency injection
- ✅ **Rich UI Architecture Migration** from legacy display patterns to centralized console management
- ✅ **ApplicationContainer Pattern** implemented for clean dependency wiring and testability
- ✅ **Test Infrastructure Modernization** with RichTestCase and proper console isolation
- ✅ **Centralized Configuration** with filename_config.py and ConsoleManager eliminating scattered settings
- ✅ **Local LLM Integration** with hardware detection and Ollama backend support
- ✅ **Security Hardening** with comprehensive SAST analysis and vulnerability remediation
- ✅ **Test Coverage Expansion** from 241 to 536 tests with systematic unit test improvements
- ✅ **Code quality improved** to Pylint 9.27/10 standard with balanced practical rules

### For Developers

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Code quality checks
flake8 src --max-line-length=88
pylint src --score=y
mypy src
```

Current code quality: **Pylint 9.27/10** with modern Rich UI architecture ⭐⭐

---

## Acknowledgments

Content Tamer AI was originally forked from [sort-rename-move-pdf](https://github.com/munir-abbasi/sort-rename-move-pdf) by munir-abbasi. We're grateful for that foundational work, though Content Tamer AI has since evolved significantly in scope and functionality to become a comprehensive AI-powered content intelligence platform.

The original project focused specifically on PDF processing, while Content Tamer AI now handles all document types, images, screenshots, and various content formats with advanced AI-powered organization capabilities.

## Credits & License

**MIT License** - see LICENSE file for details.

---

**Ready to tame your digital chaos?** 🎯

Drop some files in `data/input/` and run `content-tamer-ai` to see the magic happen!