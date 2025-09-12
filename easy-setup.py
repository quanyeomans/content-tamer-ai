#!/usr/bin/env python3
"""
Simple setup script for Content Tamer AI.

This is the easiest way to get started. Just run:
    python easy-setup.py

It will handle everything automatically.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main setup function - handles everything automatically."""
    print("Content Tamer AI - Easy Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/main.py").exists():
        print("[ERROR] Please run this from the content-tamer-ai directory")
        print("   cd content-tamer-ai")
        print("   python easy-setup.py")
        return False
    
    print("Installing Installing dependencies...")
    try:
        # Install core dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("[OK] Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print("[ERROR] Failed to install dependencies")
        print(f"   Error: {e}")
        return False
    
    # Download spaCy model
    print("Setting up Setting up language model...")
    try:
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                      check=True, capture_output=True)
        print("[OK] Language model installed")
    except subprocess.CalledProcessError:
        print("[WARNING]  Language model download failed (will continue without it)")
    
    # Create data directories
    print("Creating Creating directories...")
    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    print("[OK] Directories created")
    
    print("\n[SUCCESS] Setup Complete!")
    print("\nNext Steps: Next Steps:")
    print("   1. Choose your AI provider:")
    print("      • OpenAI: export OPENAI_API_KEY='your-key'")  
    print("      • Claude: export ANTHROPIC_API_KEY='your-key'")
    print("      • Local (no key needed): python src/main.py --setup-local-llm")
    print("\n   2. Add files to process:")
    print("      • Drop PDFs and images in: data/input/")
    print("\n   3. Run Content Tamer AI:")
    print("      • python src/main.py")
    print("\n   4. Find your organized files in: data/processed/")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)