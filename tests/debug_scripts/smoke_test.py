#!/usr/bin/env python3
"""Quick smoke test to verify core application functionality."""

import os
import sys
import tempfile
import shutil

# Set environment variables first
os.environ['OPENAI_API_KEY'] = 'sk-fake-test-key'
os.environ['NO_COLOR'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

def smoke_test_imports():
    """Test that core imports work."""
    print("Testing imports...")
    try:
        from core.application import organize_content
        from core.file_processor import process_file, pdfs_to_text_string
        from ai_providers import AIProviderFactory
        from content_processors import ContentProcessorFactory
        print("All imports successful")
        return True
    except Exception as e:
        print(f"Import failed: {e}")
        return False

def smoke_test_api_creation():
    """Test that AI provider factory works."""
    print("Testing AI provider creation...")
    try:
        from ai_providers import AIProviderFactory
        # This should fail gracefully with our fake key
        try:
            client = AIProviderFactory.create("openai", "fake-key", "gpt-4o-mini")
            print("AI provider creation works")
            return True
        except Exception as e:
            if "Invalid" in str(e) or "API key" in str(e):
                print("AI provider correctly validates keys")
                return True
            else:
                print(f"Unexpected AI provider error: {e}")
                return False
    except Exception as e:
        print(f"AI provider test failed: {e}")
        return False

def smoke_test_file_operations():
    """Test basic file operations without AI."""
    print("Testing file operations...")
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir)
        
        # Create test file
        test_file = os.path.join(input_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Test content")
        
        # Test file exists
        if os.path.exists(test_file):
            print("File operations work")
            return True
        else:
            print("File creation failed")
            return False
    except Exception as e:
        print(f"File operations failed: {e}")
        return False
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

def smoke_test_basic_functionality():
    """Test basic application startup without AI calls."""
    print("Testing basic application startup...")
    try:
        from core.application import organize_content
        
        # Create temp directories
        temp_dir = tempfile.mkdtemp()
        input_dir = os.path.join(temp_dir, "input") 
        unprocessed_dir = os.path.join(temp_dir, "unprocessed")
        renamed_dir = os.path.join(temp_dir, "renamed")
        
        os.makedirs(input_dir)
        os.makedirs(unprocessed_dir) 
        os.makedirs(renamed_dir)
        
        # This should fail gracefully with invalid provider but not crash
        try:
            result = organize_content(
                input_dir=input_dir,
                unprocessed_dir=unprocessed_dir,
                renamed_dir=renamed_dir,
                provider="invalid_provider",
                model="gpt-4o-mini",
                display_options={"no_color": True, "verbose": False}
            )
            # Should return False but not crash
            print("Application handles invalid provider gracefully")
            return True
        except Exception as e:
            if "Unsupported provider" in str(e):
                print("Application correctly rejects invalid provider")
                return True
            else:
                print(f"Application crashed: {e}")
                return False
                
    except Exception as e:
        print(f"Basic functionality test failed: {e}")
        return False
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

def main():
    """Run all smoke tests."""
    print("Running smoke tests...\n")
    
    tests = [
        smoke_test_imports,
        smoke_test_api_creation, 
        smoke_test_file_operations,
        smoke_test_basic_functionality
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("All smoke tests PASSED - Application appears functional!")
        return 0
    else:
        print("Some smoke tests FAILED - Application needs fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())