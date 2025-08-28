#!/usr/bin/env python3
"""Debug file detection issue."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

def debug_file_detection():
    """Debug why PDF files aren't being detected."""
    try:
        from content_processors import ContentProcessorFactory
        
        # Test file path - use absolute path
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        test_file = os.path.join(current_dir, "data", "input", "R2403D-PDF-ENG.PDF")
        
        print(f"Testing file: {test_file}")
        print(f"File exists: {os.path.exists(test_file)}")
        print(f"File extension: {os.path.splitext(test_file)[1]}")
        print(f"Lower extension: {os.path.splitext(test_file)[1].lower()}")
        
        # Test content factory
        factory = ContentProcessorFactory()
        print(f"Supported extensions: {factory.get_supported_extensions()}")
        
        # Test processor lookup
        processor = factory.get_processor(test_file)
        print(f"Processor for file: {processor}")
        
        if processor:
            print(f"Processor type: {type(processor)}")
            print(f"Can process: {processor.can_process(test_file)}")
        
        # Test PDF processor directly
        from content_processors import PDFProcessor
        pdf_processor = PDFProcessor()
        print(f"PDF processor can handle: {pdf_processor.can_process(test_file)}")
        print(f"PDF processor extension: {pdf_processor.get_file_extension()}")
        
        return True
        
    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_file_detection()