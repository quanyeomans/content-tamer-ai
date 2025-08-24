# 🤖 Content Tamer AI

**Transform digital chaos into organized, searchable assets**

When you digitize your life - scanning bills, taking screenshots, saving documents - you end up with thousands of files with meaningless names like `IMG_2074.jpg` or `Screenshot 2024-08-24.png`. Content Tamer AI uses vision-capable AI models to understand what your documents actually contain and generates intelligent, descriptive filenames that make everything instantly searchable and workflow-ready.

## ✨ Quick Start (2 minutes)

```bash
# 1. Clone and install
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
python install.py  # Cross-platform installer with guided setup

# 2. Set your API key
export OPENAI_API_KEY="your-key-here"  # or set OPENAI_API_KEY=your-key-here on Windows

# 3. Run!
content-tamer-ai  # Uses smart defaults - just works!
# or: python run.py
```

**That's it!** Drop files in `documents/input/` and find intelligently renamed files in `documents/processed/`

---

## 🎯 What Content Tamer AI Does

### ✅ Core Capabilities
- **🧠 AI Content Analysis** — Vision models understand document content, not just filenames  
- **📄 Universal File Support** — PDFs, images, screenshots, scanned documents
- **🔍 Intelligent OCR** — Multi-stage text extraction with auto-orientation
- **📝 Descriptive Filenames** — Generates meaningful names up to 160 characters
- **🔄 Batch Processing** — Handle hundreds of files with crash-safe resume
- **🎛️ Zero Configuration** — Works immediately with smart defaults

### 🤖 AI Provider Support
- **OpenAI** ✅ **Production Ready** — GPT-5, GPT-4o with full vision support
- **Claude** ⚠️ **Available** — Integration complete, community testing welcomed
- **Gemini** ⚠️ **Available** — Integration complete, community testing welcomed  
- **Deepseek** ⚠️ **Available** — Cost-effective option, community testing welcomed

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
python install.py  # Smart cross-platform installer
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
pip install openai  # or your preferred AI provider
```

## 🔑 API Key Setup

**Get an API key from your preferred provider:**
- [OpenAI API Keys](https://platform.openai.com/api-keys) (recommended)
- [Anthropic Claude](https://console.anthropic.com/) 
- [Google AI Studio](https://aistudio.google.com/)

**Set your API key:**
```bash
# Method 1: Environment variable (recommended)
export OPENAI_API_KEY="your-key-here"        # macOS/Linux
set OPENAI_API_KEY=your-key-here             # Windows

# Method 2: The app will prompt you if no key is found
```

---

## 🎮 Usage Examples

### 🚀 Quick Start (Recommended)

```bash
# Just run it! Uses smart defaults
content-tamer-ai
# or: python run.py

# Check documents/processed/ for intelligently renamed files
```

### 🎛️ Advanced Options

```bash
# Different AI models
content-tamer-ai -m gpt-4o          # Best vision support
content-tamer-ai -m gpt-5           # Most capable

# Different providers  
content-tamer-ai -p claude -m claude-3-sonnet
content-tamer-ai -p gemini
content-tamer-ai -p deepseek        # Cost-effective

# Custom folders
content-tamer-ai -i ~/Downloads -r ~/Organized

# Multi-language OCR
content-tamer-ai --ocr-lang "eng+spa"  # English + Spanish
```

### 🔍 Helpful Commands

```bash
content-tamer-ai --help          # Show all options
content-tamer-ai --list-models   # See available AI models
```

---

## 📁 How It Works

**Default Directory Structure:**
```
documents/
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
- **📄 PDF Files** — Native text + OCR + vision analysis
- **🖼️ Images** — PNG, JPG, BMP, TIFF, GIF with full OCR
- **📱 Screenshots** — Perfect for organizing screenshot collections
- **🔍 Scanned Documents** — Auto-orientation and cleanup

### 🔮 Coming Soon
- **📊 Microsoft Office** — Word, Excel, PowerPoint
- **📝 Text Documents** — .txt, .md, .rtf
- **🎯 Custom Formats** — Based on community requests

---

## 🚀 Roadmap & Vision

### 🎯 Next Major Features
- **🏠 Local LLM Support** — Process documents offline with Ollama/GPT4All
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
- ✅ **66 comprehensive tests** covering all components
- ✅ **Full type annotations** with static analysis
- ✅ **Modular architecture** for easy extension
- ✅ **Cross-platform compatibility** (Windows, macOS, Linux)
- ✅ **Crash-safe processing** with resume capability

---

## 🤝 Contributing & Community

**We'd love your help! Priority areas:**
- 🧪 **Test AI providers** — Validate Claude, Gemini, Deepseek
- 📄 **Add file types** — Office docs, new formats
- 🏠 **Local LLM integration** — Privacy-focused processing
- 🌍 **Internationalization** — Multi-language support

**Quick Start for Contributors:**
```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
python install.py  # Get set up
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

### Getting Help
- Check the detailed error logs in `documents/.processing/errors.log`
- [Open an issue](https://github.com/quanyeomans/content-tamer-ai/issues) for bug reports
- Use `content-tamer-ai --help` for all command options

---

## Credits & License

Originally inspired by document organization needs, completely rebuilt as a modern AI-powered platform.

**MIT License** - see LICENSE file for details.

---

**Ready to tame your digital chaos?** 🎯

Drop some files in `documents/input/` and run `content-tamer-ai` to see the magic happen!