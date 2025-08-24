# AI-Powered Document Organization System

🚀 **Transform your document chaos into organized intelligence**

Automatically rename and organize your PDF files, images, and screenshots using AI analysis. Get descriptive, meaningful filenames based on actual document content - no more `scan001.pdf` or `IMG_1234.png`!

## ✨ Quick Start (2 minutes)

```bash
# 1. Clone and install
git clone https://github.com/yourusername/sort-rename-move-pdf.git
cd sort-rename-move-pdf
python install.py  # Cross-platform installer with guided setup

# 2. Set your API key
export OPENAI_API_KEY="your-key-here"  # or set OPENAI_API_KEY=your-key-here on Windows

# 3. Run!
python run.py  # Uses smart defaults - just works!
```

**That's it!** Drop files in `documents/input/` and find renamed files in `documents/processed/`

---

## 🎯 Features

### ✅ What It Does
- **🤖 AI-Generated Filenames** — Creates descriptive names from document content
- **📄 Multi-Format Support** — PDFs, images (PNG, JPG, BMP, TIFF, GIF), screenshots
- **🔍 Smart Content Extraction** — Advanced OCR pipeline with auto-orientation
- **⚡ Vision Model Support** — Processes scanned documents and images
- **🔄 Resumable Processing** — Crash-safe with progress tracking
- **🎛️ Zero Configuration** — Works out-of-the-box with sensible defaults
- **🔧 Developer Friendly** — Modern Python, full test coverage, extensible architecture

### 🤖 AI Provider Support
- **OpenAI** ✅ **Production Ready** — GPT-5, GPT-4o with full vision support
- **Claude** ⚠️ **Available** — Integration complete, community testing welcomed
- **Gemini** ⚠️ **Available** — Integration complete, community testing welcomed
- **Deepseek** ⚠️ **Available** — Cost-effective option, community testing welcomed

---

## 📋 Requirements

**System Requirements:**
- Python 3.8+ (tested up to Python 3.13)
- 50MB free disk space
- Internet connection for AI processing

**The automated installer handles everything else!** 🎉

<details>
<summary>📦 Manual Installation Details (Advanced Users)</summary>

### Core Dependencies
```bash
python >= 3.8
PyPDF2 >= 6.0.0
tiktoken >= 0.11.0
tqdm >= 4.67.1
requests >= 2.32.5
pymupdf >= 1.26.3
pillow >= 11.3.0
pytesseract >= 0.3.13
```

### AI Provider Dependencies
```bash
# Choose your preferred provider
pip install openai        # OpenAI (recommended)
pip install anthropic     # Claude
pip install google-genai  # Gemini
# Deepseek works with requests (included)
```

### OCR Enhancement (Optional)
**Tesseract binary for enhanced OCR:**
- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`  
- **Windows**: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

</details>

---

## 🚀 Installation

### Option 1: Automated Installation (Recommended)

**One-command setup with guided installation:**

```bash
# All platforms
git clone https://github.com/yourusername/sort-rename-move-pdf.git
cd sort-rename-move-pdf
python install.py  # Smart cross-platform installer
```

**✨ Installer Features:**
- 🔍 **Automatic system checks** (Python, pip, dependencies)
- 💬 **User consent required** (tells you exactly what gets installed)
- 🏠 **Virtual environment option** (keeps your system clean)
- 🌐 **Cross-platform** (Windows, macOS, Linux)
- ✅ **Installation verification** (tests everything works)

### Option 2: Developer Quick Start

```bash
# For developers who want control
git clone https://github.com/yourusername/sort-rename-move-pdf.git
cd sort-rename-move-pdf
make dev-setup  # Installs everything + development tools
```

<details>
<summary>🔧 Manual Installation (If You Prefer Control)</summary>

```bash
# Basic manual setup
git clone https://github.com/yourusername/sort-rename-move-pdf.git
cd sort-rename-move-pdf
pip install -r requirements.txt
pip install openai  # or your preferred AI provider

# Test it works
python run.py --help
```

**Choose Your AI Provider:**
```bash
pip install openai        # OpenAI (recommended)
pip install anthropic     # Claude  
pip install google-genai  # Gemini
# Deepseek works out of the box
```

</details>

## 🔑 API Key Setup

**Choose one method:**

```bash
# Method 1: Environment variable (recommended)
export OPENAI_API_KEY="your-key-here"        # macOS/Linux
set OPENAI_API_KEY=your-key-here             # Windows

# Method 2: Command line flag
python run.py --api-key your-key-here

# Method 3: The app will prompt you if no key is found
```

**Supported Providers:**
- `OPENAI_API_KEY` — GPT-5, GPT-4o (recommended)
- `CLAUDE_API_KEY` — Claude 3 models
- `GEMINI_API_KEY` — Google Gemini
- `DEEPSEEK_API_KEY` — Cost-effective option

---

## 📁 How It Works

**Default "Just Works" Mode:**

```
documents/
├── 📥 input/           # ← Drop your files here
├── ✅ processed/       # ← Renamed files appear here  
│   └── ❌ unprocessed/ # ← Files that couldn't be processed
└── 🔄 .processing/     # ← Progress tracking (hidden)
    ├── .progress       # Resume after crashes
    └── errors.log      # Detailed error information
```

**Three-Step Process:**
1. **📥 Drop files** → Place PDFs/images in `documents/input/`
2. **🚀 Run command** → `python run.py`
3. **✨ Get results** → Check `documents/processed/` for renamed files

**Example Results:**
```
Before: scan001.pdf, IMG_1234.png, document.pdf
After:  quarterly_financial_report_q3_2024.pdf
        employee_handbook_remote_work_policy.png
        meeting_notes_project_kickoff_january.pdf
```

---

## 🎮 Usage Examples

### 🚀 Quick Start (Recommended)

```bash
# Just run it! Uses smart defaults
python run.py

# That's it! Check documents/processed/ for results
```

### 🎛️ Common Options

```bash
# Different AI models
python run.py -m gpt-4o          # Best vision support
python run.py -m gpt-5           # Most capable
python run.py -m gpt-5-mini      # Fastest (default)

# Different providers  
python run.py -p claude -m claude-3-sonnet
python run.py -p gemini
python run.py -p deepseek        # Cost-effective

# Custom folders
python run.py -i ~/Downloads -r ~/Organized

# Multi-language OCR
python run.py --ocr-lang "eng+spa"  # English + Spanish

# Start fresh (ignore previous progress)
python run.py --reset-progress
```

### 🔍 Helpful Commands

```bash
python run.py --help          # Show all options
python run.py --list-models   # See available AI models
```

### 📖 All Command Options

| Option | Description | Example |
|--------|-------------|----------|
| `-i, --input` | Input folder | `-i ~/Documents` |
| `-r, --renamed` | Success output folder | `-r ~/Organized` |
| `-u, --unprocessed` | Failed files folder | `-u ~/Failed` |
| `-p, --provider` | AI provider | `-p openai` |
| `-m, --model` | Specific model | `-m gpt-4o` |
| `-k, --api-key` | API key | `-k sk-...` |
| `--ocr-lang` | OCR language | `--ocr-lang eng+fra` |
| `--reset-progress` | Start fresh | `--reset-progress` |
| `--list-models` | Show available models | `--list-models` |

---

## How It Works

### Processing Pipeline
1. **File Discovery** — Scans input folder for supported file types (PDFs, images)
2. **Content Extraction**:
   - **PDFs**: PyMuPDF → PyPDF2 → Tesseract OCR fallback
   - **Images**: Direct OCR + base64 encoding for vision models
   - **Auto-orientation**: Tesseract OSD for rotated documents
3. **AI Processing** — Sends content + image to AI for filename generation
4. **File Organization** — Sanitizes names, handles duplicates, safely moves files
5. **Progress Tracking** — Resumable processing with collision-safe logging

### Project Structure
```
sort-rename-move-pdf/
├── run.py               # Simple entry point - just run this!
├── requirements.txt     # Dependencies list
├── setup.py            # Python package setup
├── src/                # Source code (organized for developers)
│   ├── main.py         # Main orchestration logic
│   ├── ai_providers.py # OpenAI, Claude, Gemini, Deepseek clients
│   ├── content_processors.py # PDF + Image extraction with OCR
│   ├── file_organizer.py # File ops, progress tracking
│   └── utils/          # Utilities and helper functions
├── documents/          # Default working directory (auto-created)
│   ├── input/          # Place your files here
│   ├── processed/      # Renamed files appear here
│   └── .processing/    # Progress tracking and logs
├── examples/           # Sample files and getting started guide
└── tests/             # Comprehensive test suite
```

---

## 📄 Supported File Types

### ✅ Currently Supported
- **📄 PDF Files** — Native text extraction + OCR fallback + image rendering
- **🖼️ Images** — PNG, JPG, JPEG, BMP, TIFF, GIF with full OCR support
- **📱 Screenshots** — Perfect for organizing screenshot collections
- **🔍 Scanned Documents** — Advanced OCR with auto-orientation

### 🔮 Coming Soon
- **📊 Microsoft Office** — Word (.docx), Excel (.xlsx), PowerPoint (.pptx)
- **📝 Text Documents** — .txt, .md, .rtf
- **🎯 Custom Formats** — Based on community requests

---

## 🚀 Roadmap

### 🎯 Next Major Features
- **🏠 Local LLM Support** — Process documents offline with Ollama/GPT4All
- **🗂️ Smart Organization** — Auto-create folders by content type (invoices, contracts, etc.)
- **📅 Date-Based Sorting** — Extract dates for chronological organization
- **🏢 Domain Classification** — Separate work, personal, financial documents
- **📊 Office Suite Support** — Word, Excel, PowerPoint processing

### 🔧 Technical Enhancements
- **⚡ Performance** — Parallel processing for large document batches
- **🛠️ Plugin System** — Easy addition of new file types and AI providers
- **⚙️ Configuration** — Advanced settings via config files
- **📈 Analytics** — Processing statistics and insights

*Want a feature? [Open an issue](https://github.com/yourusername/sort-rename-move-pdf/issues) — community input drives development!*

---

## Troubleshooting

### Installation Issues
- **"Python 3.8+ required" error**
  - Update Python from [python.org](https://python.org) or your system package manager
  - Verify version: `python --version` (Windows) or `python3 --version` (Linux/macOS)

- **"pip not found" error**
  - Install pip: [pip.pypa.io/en/stable/installation](https://pip.pypa.io/en/stable/installation/)
  - Or use system package manager: `sudo apt install python3-pip` (Ubuntu)

- **Installation fails with "Permission denied"**
  - Use virtual environment (recommended by installer)
  - Or install with user flag: `pip install --user -r requirements.txt`

- **Tesseract not found warnings**
  - **Windows**: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki), add to PATH
  - **macOS**: `brew install tesseract`
  - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
  - OCR will use basic methods without Tesseract (reduced quality)

### Runtime Issues
- **Files named `empty_file_*`**
  - Ensure OCR dependencies are installed: `pymupdf`, `pillow`, `pytesseract`, and Tesseract binary
  - Try vision-capable model: `-m gpt-4o`
  - Check file isn't zero-byte or purely image without OCR

- **"Permission denied" errors**
  - Cloud sync/antivirus may lock files. Use non-synced folders or retry
  - Script attempts copy-then-delete fallback automatically

- **Non-OpenAI providers failing**
  - Currently only OpenAI is fully tested. Other providers need validation
  - Check API key environment variables are set correctly

- **Rate limiting / network errors**
  - Script retries with intelligent backoff (exponential for timeouts, linear for others)
  - Check `pdf_processing_errors.log` for detailed error information

### Performance Notes
- Large PDFs auto-limited to first 100 pages for text extraction
- Content truncated via `tiktoken` with binary-search optimization
- Progress tracking prevents reprocessing on interruption

---

## 🧪 Quality & Testing

**Production-Ready Codebase:**
- ✅ **66 comprehensive tests** covering all components
- ✅ **Full type annotations** with Pyright validation  
- ✅ **PEP8 compliant** with Black formatting
- ✅ **Modular architecture** for easy extension
- ✅ **Cross-platform compatibility** (Windows, macOS, Linux)

**Development Tools Available:**
```bash
make test           # Run test suite
make lint           # Check code quality  
make format         # Auto-format code
make type-check     # Static type checking
make dev-setup      # Complete dev environment
```

**For Contributors:**
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

## 📊 Project Status

### ✅ Stable & Ready
- **🏗️ Modern Architecture** — Modular, extensible, well-tested
- **🤖 OpenAI Integration** — Production-ready with full vision support
- **📄 Multi-Format Support** — PDFs, images, screenshots
- **🔍 Advanced OCR** — Multiple extraction methods with intelligent fallbacks
- **🧪 Comprehensive Testing** — 66 tests, full type coverage
- **🌐 Cross-Platform** — Windows, macOS, Linux support

### 🚧 Beta Features
- **Claude, Gemini, Deepseek** — API integrations complete, community testing needed

### 🎯 Coming Next
- **Local LLM support** for privacy-focused users
- **Office document processing**
- **Advanced organization features**

---

## 🤝 Contributing

**We'd love your help!** Priority areas:

- 🧪 **Test AI providers** — Help validate Claude, Gemini, Deepseek
- 📄 **Add file types** — Office docs, new image formats
- 🏠 **Local LLM integration** — Ollama, GPT4All support
- 🎨 **UI improvements** — Better user experience
- 🌍 **Internationalization** — Multi-language support

**Quick Start for Contributors:**
```bash
git clone https://github.com/yourusername/sort-rename-move-pdf.git
cd sort-rename-move-pdf
make dev-setup     # Installs everything + dev tools
make test          # Ensure everything works
# Make your changes
make check-all     # Run all quality checks
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Credits

Originally forked from [munir-abbasi/sort-rename-move-pdf](https://github.com/munir-abbasi/sort-rename-move-pdf). Significantly refactored and enhanced with multi-file support, modular architecture, and advanced AI integration.

---

## License

MIT License - see LICENSE file for details.

---