# Getting Started with AI-Powered Document Organization

This directory contains sample files to help you get started quickly.

## Quick Start

1. **Set up your API key** (OpenAI recommended):
   ```bash
   # Windows
   set OPENAI_API_KEY=your_api_key_here
   
   # Linux/macOS  
   export OPENAI_API_KEY=your_api_key_here
   ```

2. **Copy sample files to input directory**:
   ```bash
   # Copy the provided samples
   cp examples/sample.pdf documents/input/
   cp examples/sample_image.png documents/input/
   
   # Or add your own PDF files and images
   ```

3. **Run the system**:
   ```bash
   python run.py
   # You'll see a rich progress bar with real-time updates!
   ```

4. **Check results**:
   - Renamed files: `documents/processed/`
   - Failed files: `documents/processed/unprocessed/`
   - Processing logs: `documents/.processing/`

## Sample Files Included

- **`sample.pdf`** - A test PDF file for processing
- **`sample_image.png`** - A test image file with text for OCR

## What to Expect

**Rich Visual Interface:**
```
Processing documents... ████████████████████ 100% → meeting_notes_q4_planning.pdf ✅ Done
✅ 2 processed │ ⏱️ 12.3s elapsed
```

**Processing Flow:**
- The system will extract text from your documents
- Send the content to AI for intelligent filename generation
- Move successfully processed files to the `processed` folder
- Place unprocessable files in the `unprocessed` subfolder

## Troubleshooting

- **"No API key"** → Set your `OPENAI_API_KEY` environment variable
- **"Empty filename"** → File may be corrupted or unsupported format
- **"Permission denied"** → Files may be locked by another application

## Next Steps

1. Try processing your own documents
2. Experiment with different AI models: `python run.py --list-models`
3. Try different display modes:
   - `python run.py --quiet` (minimal output)
   - `python run.py --verbose` (detailed logging)
   - `python run.py --no-color` (plain text)
4. Customize processing with advanced options: `python run.py --help`

For detailed documentation, see the main README.md file.