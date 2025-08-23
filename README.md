# PDF Sort, Rename & Move Utility

Organise PDFs with AI. The tool extracts content (text + OCR for scans), asks an AI model for a descriptive filename, and moves files into the right folder.

---

## Features
- **OpenAI (default) via Responses API** — GPT-5 / GPT-5-mini supported; sends a first-page image when available  
- **OCR for scanned PDFs** — PyMuPDF render + Tesseract fallback (first N pages) with language hints  
- **Filename hygiene** — underscores only, safe characters, de-dupe handling  
- **Resumable runs** — `.progress` file with a `--reset-progress` flag  
- **Sturdier file ops** — skips hidden/AppleDouble files, retries moves with copy-then-delete fallback  
- **Multi-provider** — OpenAI, Claude, Gemini, Deepseek (OpenAI path is the most current)

---

## Requirements

### Core Dependencies
```bash
python >= 3.8
PyPDF >= 6.0.0
tiktoken >= 0.11.0
tqdm >= 4.67.1
requests >= 2.32.5
pymupdf >= 1.26.3
pillow >= 11.3.0
pytesseract >= 0.3.13
```

### Provider-Specific Dependencies
Install only what you need based on your preferred AI provider:

```bash
# For OpenAI (default)
pip install openai

# For Claude
pip install anthropic

# For Gemini
pip install google-genai
```

### OCR
Recommended for scanning PDFs which may contain images rather than text
```bash
pip install pymupdf pillow pytesseract
```

And install the Tesseract binary:
- macOS: `brew install tesseract`
- Debian/Ubuntu: `sudo apt-get install tesseract-ocr`
- Windows: install Tesseract (UB Mannheim builds are common)

---

## Installation
```bash
git clone https://github.com/yourusername/sort-rename-move-pdf.git
cd sort-rename-move-pdf
# then install deps as above
```

--- 

## API Keys

Set an env var or pass `--api-key`:
- **OpenAI**: `OPENAI_API_KEY`
- **Claude**: `CLAUDE_API_KEY`
- **Gemini**: `GEMINI_API_KEY`
- **Deepseek**: `DEEPSEEK_API_KEY`

--- 

## Usage

### Basic
```bash
python sortrenamemovepdf.py \
  -i /path/to/pdfs \
  -c /path/to/corrupted \
  -r /path/to/renamed
```

### OpenAI models
```bash
# GPT-5 mini (default if not set)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-5-mini
# GPT-5 (full)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-5
# GPT-4o (vision-friendly)
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-4o
```

### Other providers
```bash
# Claude
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p claude -m claude-3-sonnet
# Gemini
python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p gemini
```

### OCR language hint (default: English)
```bash
python sortrenamemovepdf.py ... --ocr-lang "eng"
# examples: "eng+deu", "eng+ind"
```

### Reset progress tracking
```bash
python sortrenamemovepdf.py ... --reset-progress
```

### List available models
```bash
python sortrenamemovepdf.py --list-models
```

### Command-line arguments
```bash
-i, --input         Input folder containing PDF files
-c, --corrupted     Folder for corrupted PDF files
-r, --renamed       Folder for renamed PDF files
-p, --provider      AI provider (openai, claude, gemini, deepseek)
-m, --model         Model to use for the selected provider
-k, --api-key       API key for the selected provider
-l, --list-models   List all available models by provider and exit
--ocr-lang          Tesseract OCR language hint (default: "eng")
--reset-progress    Delete .progress and process all files from scratch
```

---

## How it works

1. Finds PDFs in the input folder (skips hidden/AppleDouble files like `._scan.pdf`).
2. Extracts content:
    - Native text via PyMuPDF / PyPDF2
    - If too little text, OCR first N pages with Tesseract
    - Renders the first page to an image for AI vision context
3. Calls the selected AI model to propose a filename.
4. Sanitises and de-dupes; moves the file to the renamed folder.
5. Corrupted/encrypted PDFs are moved to the corrupted folder.
6. Progress is tracked so runs can resume.

---

## Troubleshooting

- **All files named `empty_file_*`**
    - Ensure `pymupdf`, `pillow`, `pytesseract` are installed **and** the Tesseract binary is installed.
    - Try a vision-capable model (`-m gpt-4o`).
    - Check that your PDFs aren’t zero-byte or image-only without OCR tooling.
- **“Permission denied” on moves**
    - Cloud sync/AV tools can lock files. Use a non-synced target folder or retry; the script will attempt copy-then-delete.
- **Malformed PDFs like `._scan.pdf`**
    - These are macOS resource forks; they’re skipped.
- **Rate limiting / network blips**
    - The script retries with exponential backoff; see `pdf_processing_errors.log`.

---

## Performance

- Very large PDFs: auto-limit to first 100 pages for text extraction.
- Token handling: truncation via `tiktoken` with binary-search trimming.
- Per-file progress is written; reset with `--reset-progress`.

---

## Status & roadmap

- **OpenAI** path is the most current (Responses API, vision inputs).
- **Anthropic/Gemini** paths are functional but may need SDK updates to match the latest APIs and add vision support.
- Tests will be added in a future revision (unit + integration with fixture PDFs).

---

## Credit

Forked from **[munir-abbasi/sort-rename-move-pdf](https://github.com/munir-abbasi/sort-rename-move-pdf)** — thanks to the original author for the foundation. 

---

## License

MIT

---

## Contributing

PRs welcome — especially for provider SDK updates, test fixtures, and vision/auto-rotation improvements.

---