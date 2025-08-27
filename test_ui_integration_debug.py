#!/usr/bin/env python3
"""
Integration test to debug the UI issues reported by user.

This test replicates the exact scenario: files that are successfully processed
and renamed but still show as "Failed" in the UI.
"""

import os
import tempfile
import shutil
import sys
from unittest.mock import MagicMock, patch

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.file_processor import process_file_enhanced_core
from utils.display_manager import DisplayManager, DisplayOptions, ProcessingContext
from utils.progress_display import ProgressDisplay
from file_organizer import FileOrganizer

def test_file_processing_success_vs_failure():
    """Test to debug why successfully processed files show as failed."""
    print("=== UI Integration Debug Test ===")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        input_dir = os.path.join(temp_dir, "input")
        processed_dir = os.path.join(temp_dir, "processed") 
        unprocessed_dir = os.path.join(temp_dir, "unprocessed")
        
        os.makedirs(input_dir)
        os.makedirs(processed_dir)
        os.makedirs(unprocessed_dir)
        
        # Create a test PDF file with proper content
        test_file = os.path.join(input_dir, "test_document.pdf")
        # Create a minimal valid PDF
        pdf_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000173 00000 n 
0000000301 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
398
%%EOF"""
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(pdf_content)
        
        print(f"Created test file: {test_file}")
        print(f"File exists: {os.path.exists(test_file)}")
        
        # Setup mocks for AI and file organizer
        mock_ai_client = MagicMock()
        mock_ai_client.generate_filename.return_value = "AI_Generated_Test_Document"
        
        # Setup real file organizer
        organizer = FileOrganizer()
        
        # Create display manager - force no color and no unicode
        display_options = DisplayOptions(no_color=True, verbose=True)
        display_manager = DisplayManager(display_options)
        
        # Create display context
        display_context = ProcessingContext(display_manager)
        
        # Create mock progress file that doesn't throw file errors
        progress_f = MagicMock()
        progress_f.write = MagicMock()
        progress_f.flush = MagicMock() 
        progress_f.fileno = MagicMock(return_value=1)
        
        print("\n=== Testing Core File Processing ===")
        
        try:
            # First, test without the display system to isolate the core logic issue
            print("Testing file processing core logic without display...")
            
            # Mock the display context more thoroughly
            display_context.set_status = MagicMock()
            display_context.show_warning = MagicMock()
            
            # Test the core processing function directly
            success, result = process_file_enhanced_core(
                input_path=test_file,
                filename="test_document.pdf",
                unprocessed_folder=unprocessed_dir,
                renamed_folder=processed_dir,
                progress_f=progress_f,
                ocr_lang="eng",
                ai_client=mock_ai_client,
                organizer=organizer,
                display_context=display_context
            )
            
            print(f"Core processing result: success={success}, result={result}")
            
            # Test content extraction separately if main processing failed
            if not success:
                print("Processing failed - testing individual components...")
                
                # Test if it's a content extraction issue
                try:
                    from content_processors import PDFProcessor
                    processor = PDFProcessor()
                    if processor.can_process(test_file):
                        text, img_b64 = processor.extract_content(test_file)
                        print(f"Direct PDF extraction: text_length={len(text) if text else 0}, has_image={bool(img_b64)}")
                    else:
                        print("PDF processor cannot process this file")
                except Exception as e:
                    print(f"Direct PDF extraction failed: {e}")
                
                # Test filename generation with simple content
                try:
                    from core.file_processor import _generate_filename
                    # Mock display context for filename generation
                    mock_display = MagicMock()
                    mock_display.set_status = MagicMock()
                    new_name = _generate_filename("test content", None, mock_ai_client, organizer, mock_display, filename="test_document.pdf")
                    print(f"Filename generation test: {new_name}")
                except Exception as e:
                    print(f"Filename generation failed: {e}")
            
            # Check what actually happened to the file
            print(f"Original file exists: {os.path.exists(test_file)}")
            
            # Check processed directory
            processed_files = os.listdir(processed_dir) if os.path.exists(processed_dir) else []
            print(f"Files in processed dir: {processed_files}")
            
            # Check unprocessed directory  
            unprocessed_files = os.listdir(unprocessed_dir) if os.path.exists(unprocessed_dir) else []
            print(f"Files in unprocessed dir: {unprocessed_files}")
            
            # This should help us understand the disconnect
            if processed_files and not success:
                print("!! ISSUE FOUND: File was moved to processed directory but success=False!")
                print("This explains why UI shows 'Failed' for successfully processed files")
            elif not processed_files and success:
                print("!! ISSUE FOUND: Success=True but file not in processed directory!")
            elif processed_files and success:
                print("SUCCESS: File processed correctly and success=True")
            else:
                print("FAILURE: File not processed and success=False") 
                
        except Exception as e:
            print(f"Exception during processing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_file_processing_success_vs_failure()