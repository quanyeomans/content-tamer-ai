Welcome to AI-Powered Document Organization!

Getting Started:
1. Place your PDF files or images in this folder (documents/input/)
2. Run: python sortrenamemovepdf.py
3. Your renamed files will appear in: documents/processed/
4. Files that couldn't be processed will be in: documents/processed/unprocessed/

Supported File Types:
- PDF files (.pdf)
- Images: PNG, JPG, JPEG, BMP, TIFF, GIF

Requirements:
- Set OPENAI_API_KEY environment variable, or use --api-key flag
- For images: Install Tesseract OCR binary (see README.md)

Examples:
- Basic usage: python sortrenamemovepdf.py
- With specific model: python sortrenamemovepdf.py -p openai -m gpt-4o  
- Custom folders: python sortrenamemovepdf.py -i /my/files -r /my/output

Need help? Check the main README.md file or run:
python sortrenamemovepdf.py --help

Remove this file once you've added your own documents to process.