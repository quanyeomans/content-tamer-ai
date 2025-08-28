#!/usr/bin/env python3
"""Debug the actual file processing failure now that Rich UI is working."""

import os
import sys
import traceback

# Set environment variables
os.environ['OPENAI_API_KEY'] = 'sk-proj-**********************************************************************************************************QsA'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, 'src')

def debug_file_processing():
    """Debug the actual file processing step by step."""
    try:
        from core.file_processor import process_file_enhanced
        from ai_providers import AIProviderFactory
        from content_processors import ContentProcessorFactory
        from file_organizer import FileOrganizer
        from core.directory_manager import get_api_details
        from utils.error_handling import create_retry_handler
        
        # Test file
        input_path = 'data/input/R2403D-PDF-ENG.PDF'
        filename = 'R2403D-PDF-ENG.PDF'
        unprocessed_folder = 'data/processed/unprocessed'
        renamed_folder = 'data/processed'
        
        print("=== DEBUGGING FILE PROCESSING PIPELINE ===")
        print(f"Input file: {input_path}")
        print(f"File exists: {os.path.exists(input_path)}")
        
        if not os.path.exists(input_path):
            print("ERROR: Test file missing!")
            return False
        
        # Step 1: Test content extraction directly
        print("\n1. Testing content extraction...")
        content_factory = ContentProcessorFactory('eng')
        processor = content_factory.get_processor(input_path)
        
        if not processor:
            print("ERROR: No processor found!")
            return False
            
        text, img_b64 = processor.extract_content(input_path)
        print(f"Content extracted: {len(text)} characters")
        # Safely display first 100 chars, replacing problematic Unicode
        safe_text = text[:100].encode('ascii', 'replace').decode('ascii')
        print(f"First 100 chars (ASCII safe): {safe_text}...")
        
        # Step 2: Test AI client setup
        print("\n2. Testing AI client...")
        provider = 'openai'
        model = 'gpt-5-mini'
        api_key = get_api_details(provider, model)
        ai_client = AIProviderFactory.create(provider, model, api_key)
        print("AI client created successfully")
        
        # Step 3: Test filename generation
        print("\n3. Testing filename generation...")
        try:
            new_filename = ai_client.generate_filename(text[:2000], img_b64)  # Use first 2000 chars
            print(f"Generated filename: '{new_filename}'")
        except Exception as e:
            print(f"Filename generation failed: {e}")
            traceback.print_exc()
            return False
        
        # Step 4: Test file organizer
        print("\n4. Testing file organizer...")
        try:
            organizer = FileOrganizer()  # No arguments required
            print("File organizer created successfully")
            
            # Test filename validation
            clean_filename = organizer.filename_handler.validate_and_trim_filename(new_filename)
            print(f"Validated filename: '{clean_filename}'")
            
            # Test file move operation directly
            try:
                file_extension = os.path.splitext(input_path)[1]
                print(f"File extension: '{file_extension}'")
                
                # Create a copy to test moving
                test_file = input_path.replace('.PDF', '_test.PDF')
                import shutil
                shutil.copy2(input_path, test_file)
                
                moved_filename = organizer.move_file_to_category(
                    test_file, 
                    os.path.basename(test_file),
                    renamed_folder,
                    clean_filename,
                    file_extension
                )
                print(f"File move test successful: '{moved_filename}'")
                
            except Exception as move_e:
                print(f"Direct file move test failed: {move_e}")
                traceback.print_exc()
            
        except Exception as e:
            print(f"File organizer failed: {e}")
            traceback.print_exc()
            return False
        
        # Step 5: Create mock display context first  
        class MockDisplayContext:
            def set_status(self, status, **kwargs): 
                print(f"  Status: {status} {kwargs}")
            def show_warning(self, msg, **kwargs):
                print(f"  Warning: {msg} {kwargs}")
            def show_error(self, msg, **kwargs):
                print(f"  Error: {msg} {kwargs}")
        
        mock_context = MockDisplayContext()
        
        # Test _move_file_only directly
        print("\n6. Testing _move_file_only directly...")
        
        try:
            from core.file_processor import _move_file_only
            
            # Create another test copy
            test_file2 = input_path.replace('.PDF', '_test2.PDF')
            import shutil
            shutil.copy2(input_path, test_file2)
            
            result = _move_file_only(
                test_file2,
                os.path.basename(test_file2),
                renamed_folder,
                new_filename,
                organizer,
                mock_context
            )
            print(f"_move_file_only result: '{result}'")
            
        except Exception as move_only_e:
            print(f"_move_file_only failed: {move_only_e}")
            traceback.print_exc()
        
        # Create progress file
        progress_file_path = os.path.join(unprocessed_folder, '.progress')
        os.makedirs(os.path.dirname(progress_file_path), exist_ok=True)
        
        with open(progress_file_path, 'w', encoding='utf-8') as progress_f:
            retry_handler = create_retry_handler(max_attempts=3)
            
        print("\n7. Testing full process_file_enhanced...")
            
            try:
                print("  Starting process_file_enhanced...")
                success, result_filename = process_file_enhanced(
                    input_path,
                    filename,
                    unprocessed_folder,
                    renamed_folder,
                    progress_f,
                    'eng',
                    ai_client,
                    organizer,
                    mock_context,
                    retry_handler
                )
                
                print(f"  Process result: success={success}, filename='{result_filename}'")
                
                # Check if file was moved or still exists
                print(f"  Original file still exists: {os.path.exists(input_path)}")
                if result_filename:
                    final_path = os.path.join(renamed_folder, result_filename)
                    print(f"  Final file exists: {os.path.exists(final_path)}")
                
                return success
                
            except Exception as e:
                print(f"  process_file_enhanced exception: {e}")
                traceback.print_exc()
                return False
        
    except Exception as e:
        print(f"Debug setup error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Use regular print since we're debugging the core processing, not the display
    try:
        success = debug_file_processing()
        print(f"\n=== DEBUG RESULT: {'SUCCESS' if success else 'FAILURE'} ===")
    except Exception as e:
        print(f"Debug script error: {e}")
        traceback.print_exc()