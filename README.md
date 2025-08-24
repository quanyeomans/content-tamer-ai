# AI-Powered Document Organization System

Intelligent document processing with AI-generated filenames. Supports PDFs, images, and screenshots with multi-provider AI integration and extensible file type support.

---

## Features

### Current Capabilities
- **Multi-file type support** — PDFs, images (PNG, JPG, BMP, TIFF, GIF), screenshots
- **OpenAI integration** — GPT-5, GPT-4o with vision support via Responses API ✅ **Tested & Working**
- **Advanced OCR pipeline** — PyMuPDF → PyPDF2 → Tesseract fallback with auto-orientation
- **Intelligent content extraction** — Text + image rendering for vision-capable models
- **Robust file operations** — Safe moves with retry logic, cross-platform file locking
- **Resumable processing** — Progress tracking with `.progress` file and `--reset-progress` flag
- **Modular architecture** — Extensible design for new file types and AI providers

### AI Provider Status
- **OpenAI**: ✅ **Fully tested and working** (GPT-5, GPT-4o, vision support)
- **Claude**: ⚠️ **Needs testing** (API integration complete, requires validation)
- **Gemini**: ⚠️ **Needs testing** (API integration complete, requires validation) 
- **Deepseek**: ⚠️ **Needs testing** (API integration complete, requires validation)

---

## Requirements

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
Install based on your preferred provider:

```bash
# OpenAI (recommended - fully tested)
pip install openai

# Claude (requires testing)
pip install anthropic

# Gemini (requires testing)
pip install google-genai

# Deepseek uses requests (no extra dependencies)
```

### OCR Dependencies
For image processing and scanned document support:
```bash
pip install pymupdf pillow pytesseract
```

**Tesseract binary installation:**
- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

---

## Installation

```bash
git clone https://github.com/yourusername/sort-rename-move-pdf.git
cd sort-rename-move-pdf
pip install -r requirements.txt  # Install core dependencies
```

---

## API Keys

Set environment variables or use `--api-key` flag:
- **OpenAI**: `OPENAI_API_KEY` (recommended)
- **Claude**: `CLAUDE_API_KEY` 
- **Gemini**: `GEMINI_API_KEY`
- **Deepseek**: `DEEPSEEK_API_KEY`

---

## Usage

### Basic Usage
```bash
python sortrenamemovepdf.py \
  -i /path/to/input/files \
  -c /path/to/corrupted \
  -r /path/to/renamed
```

### OpenAI Models (Recommended)
```bash
# GPT-5 mini (default, fastest)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-5-mini

# GPT-5 (more capable)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-5

# GPT-4o (excellent vision support)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-4o
```

### Other Providers (Experimental)
```bash
# Claude (needs testing)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p claude -m claude-3-sonnet

# Gemini (needs testing)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p gemini
```

### Advanced Options
```bash
# Multi-language OCR
python sortrenamemovepdf.py ... --ocr-lang "eng+deu"

# Reset progress and reprocess all files
python sortrenamemovepdf.py ... --reset-progress

# List all available models
python sortrenamemovepdf.py --list-models
```

### Command-line Arguments
```bash
-i, --input         Input folder containing files to process
-c, --corrupted     Output folder for corrupted/unreadable files  
-r, --renamed       Output folder for successfully processed files
-p, --provider      AI provider (openai, claude, gemini, deepseek)
-m, --model         Model to use for the selected provider
-k, --api-key       API key for the selected provider
-l, --list-models   List all available models by provider and exit
--ocr-lang          Tesseract OCR language (default: "eng")
--reset-progress    Delete .progress and reprocess all files
```

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

### Architecture
```
sortrenamemovepdf.py     # Main orchestration
├── ai_providers.py      # OpenAI, Claude, Gemini, Deepseek clients
├── content_processors.py # PDF + Image extraction with OCR pipeline
├── file_organizer.py    # File ops, progress tracking, future organization
└── utils/text_utils.py  # Token management and text processing
```

---

## Supported File Types

### Currently Supported
- **PDFs**: Native text, OCR fallback, image rendering
- **Images**: PNG, JPG, JPEG, BMP, TIFF, GIF with OCR

### Planned Support
- **Microsoft Office**: Word (.docx), Excel (.xlsx), PowerPoint (.pptx)
- **Text documents**: .txt, .md, .rtf
- **Additional formats**: Based on community needs

---

## Future Features Backlog

### Planned Features
- **Local LLM Integration** — Run entirely offline with Ollama, GPT4All
- **Advanced Organization** — Content-based folder structures (invoices, contracts, reports)
- **Temporal Organization** — Date-based folder creation from document content
- **Domain Classification** — Financial, personal, work document categorization
- **Batch Organization Tools** — Post-processing organization of renamed files
- **Office Document Support** — Word, Excel, PowerPoint processing
- **Enhanced Vision Processing** — Multi-page image analysis, table extraction
- **AI-Powered Organization Suggestions** — Analyze content patterns for optimal folder structures

### Technical Improvements
- **Provider API Updates** — Test and validate Claude, Gemini, Deepseek integrations
- **Enhanced Error Recovery** — Better handling of corrupted files and API failures
- **Performance Optimization** — Parallel processing for large batches
- **Configuration Management** — YAML/JSON config files for advanced settings
- **Plugin Architecture** — Easy addition of new file types and AI providers

---

## Troubleshooting

### Common Issues
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

## Development Status

### Current State
- ✅ **Refactored Architecture** — Modular, extensible design
- ✅ **OpenAI Integration** — Fully tested and working
- ✅ **Multi-file Support** — PDFs and images supported
- ✅ **Advanced OCR Pipeline** — Multiple extraction methods with fallbacks
- ⚠️ **Other AI Providers** — Need testing and potential API updates

### Next Priorities
1. **Validate non-OpenAI providers** — Test Claude, Gemini, Deepseek integrations
2. **Local LLM support** — Privacy-first document processing
3. **Office document support** — Word, Excel, PowerPoint processing
4. **Enhanced organization features** — Content-based folder structures

---

## Contributing

Contributions welcome! Priority areas:
- **AI Provider Testing** — Validate Claude, Gemini, Deepseek functionality
- **New File Types** — Office documents, additional image formats
- **Local LLM Integration** — Ollama, GPT4All support
- **Organization Features** — Advanced folder structuring based on content
- **Test Coverage** — Unit tests and integration test fixtures

---

## Credits

Originally forked from [munir-abbasi/sort-rename-move-pdf](https://github.com/munir-abbasi/sort-rename-move-pdf). Significantly refactored and enhanced with multi-file support, modular architecture, and advanced AI integration.

---

## License

MIT License - see LICENSE file for details.

---