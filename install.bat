@echo off
REM Cross-platform installation script for AI-Powered Document Organization System
REM Windows Batch version

setlocal enabledelayedexpansion

echo.
echo ======================================================================
echo   AI-Powered Document Organization System
echo   Windows Installation Script
echo ======================================================================
echo.

REM Step 1: Check Python version
echo [Step 1] Checking Python Version

python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found
    echo   Install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected

REM Step 2: Check pip availability
echo.
echo [Step 2] Checking Package Manager

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [X] pip not found
    echo   Install pip: https://pip.pypa.io/en/stable/installation/
    pause
    exit /b 1
)

echo [OK] pip package manager detected

REM Step 3: Check Tesseract (optional)
echo.
echo [Step 3] Checking OCR Dependencies

tesseract --version >nul 2>&1
if errorlevel 1 (
    echo [!] Tesseract OCR not found (optional for full OCR support^)
    echo   Installation instructions:
    echo     Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
    echo     Add installation directory to PATH
    set TESSERACT_AVAILABLE=0
) else (
    for /f "tokens=1,2" %%i in ('tesseract --version 2^>^&1') do (
        if "%%i"=="tesseract" (
            echo [OK] Tesseract OCR found: %%i %%j
            set TESSERACT_AVAILABLE=1
            goto :tesseract_done
        )
    )
    :tesseract_done
)

REM Step 4: AI Provider Selection
echo.
echo [Step 4] AI Provider Selection
echo.
echo Available AI providers:
echo.
echo   1. OpenAI - GPT models (recommended - fully tested^) [OK] Tested ^& Working
echo   2. Claude - Anthropic Claude models [!] Needs Testing
echo   3. Gemini - Google Gemini models [!] Needs Testing
echo   4. Dev - Development and testing tools [*] Optional
echo   0. Skip AI provider installation (install manually later^)
echo.

set /p AI_CHOICE="Select providers to install [1,2,3,4 or 0 to skip]: "

set AI_PACKAGES=
if "%AI_CHOICE%"=="1" set AI_PACKAGES=openai^>=1.0.0
if "%AI_CHOICE%"=="2" set AI_PACKAGES=anthropic^>=0.3.0
if "%AI_CHOICE%"=="3" set AI_PACKAGES=google-genai^>=0.3.0
if "%AI_CHOICE%"=="4" set AI_PACKAGES=pytest^>=8.4.1
if "%AI_CHOICE%"=="1,2" set AI_PACKAGES=openai^>=1.0.0 anthropic^>=0.3.0
if "%AI_CHOICE%"=="1,3" set AI_PACKAGES=openai^>=1.0.0 google-genai^>=0.3.0
if "%AI_CHOICE%"=="1,4" set AI_PACKAGES=openai^>=1.0.0 pytest^>=8.4.1
if "%AI_CHOICE%"=="2,3" set AI_PACKAGES=anthropic^>=0.3.0 google-genai^>=0.3.0
if "%AI_CHOICE%"=="1,2,3" set AI_PACKAGES=openai^>=1.0.0 anthropic^>=0.3.0 google-genai^>=0.3.0
if "%AI_CHOICE%"=="1,2,4" set AI_PACKAGES=openai^>=1.0.0 anthropic^>=0.3.0 pytest^>=8.4.1
if "%AI_CHOICE%"=="1,3,4" set AI_PACKAGES=openai^>=1.0.0 google-genai^>=0.3.0 pytest^>=8.4.1
if "%AI_CHOICE%"=="2,3,4" set AI_PACKAGES=anthropic^>=0.3.0 google-genai^>=0.3.0 pytest^>=8.4.1
if "%AI_CHOICE%"=="1,2,3,4" set AI_PACKAGES=openai^>=1.0.0 anthropic^>=0.3.0 google-genai^>=0.3.0 pytest^>=8.4.1

if "%AI_CHOICE%"=="0" (
    echo [i] Skipping AI provider installation
) else if "%AI_PACKAGES%"=="" (
    echo [!] Invalid selection, skipping AI provider installation
)

REM Step 5: Virtual Environment (simplified for batch)
echo.
echo [Step 5] Virtual Environment (Recommended^)
echo.
if defined VIRTUAL_ENV (
    echo [i] Already running in virtual environment: %VIRTUAL_ENV%
    goto :skip_venv
)

echo It's recommended to install packages in a virtual environment to avoid conflicts.
echo.
echo Virtual environment benefits:
echo   • Isolates project dependencies
echo   • Prevents system-wide package conflicts
echo   • Easy to remove/recreate if needed
echo.

set /p VENV_CHOICE="Create virtual environment? [Y/n]: "

if /i "%VENV_CHOICE%"=="n" (
    echo [!] Proceeding without virtual environment
    goto :skip_venv
)

if exist venv (
    echo [!] Directory 'venv' already exists
    set /p USE_EXISTING="Use existing directory? [Y/n]: "
    if /i "!USE_EXISTING!"=="n" (
        echo [X] Virtual environment creation cancelled
        pause
        exit /b 1
    )
) else (
    echo Creating virtual environment in 'venv'...
    python -m venv venv
    if errorlevel 1 (
        echo [X] Failed to create virtual environment
        echo Continuing with system Python installation...
        goto :skip_venv
    )
    echo [OK] Virtual environment created successfully
)

echo.
echo Next steps:
echo   1. Activate: venv\Scripts\activate.bat
echo   2. Rerun installer: install.bat
echo.
echo The installer will detect the active virtual environment automatically.
pause
exit /b 0

:skip_venv

REM Core dependencies
set CORE_PACKAGES=pypdf^>=6.0.0 tiktoken^>=0.11.0 tqdm^>=4.67.1 requests^>=2.32.5 pymupdf^>=1.26.3 pillow^>=11.3.0 pytesseract^>=0.3.13

REM Request consent for core packages
echo.
echo Installation Consent Required
echo The following core dependencies will be installed:
echo.
for %%p in (%CORE_PACKAGES%) do echo   • %%p
echo.
echo These packages will be installed using pip from the Python Package Index (PyPI^).
echo Installation requires internet connection and may take several minutes.
echo.

set /p CORE_CONSENT="Do you consent to install these packages? [y/N]: "

if /i not "%CORE_CONSENT%"=="y" (
    echo [i] Installation cancelled by user
    pause
    exit /b 1
)

REM Install core packages
echo.
echo Installing core dependencies...
echo   Command: python -m pip install %CORE_PACKAGES%
echo.

python -m pip install %CORE_PACKAGES%
if errorlevel 1 (
    echo [X] Failed to install core dependencies
    pause
    exit /b 1
)

echo [OK] Core dependencies installed successfully

REM Install AI provider packages if selected
if not "%AI_PACKAGES%"=="" (
    echo.
    echo Installation Consent Required
    echo The following AI provider packages will be installed:
    echo.
    for %%p in (%AI_PACKAGES%) do echo   • %%p
    echo.
    
    set /p AI_CONSENT="Do you consent to install these packages? [y/N]: "
    
    if /i "!AI_CONSENT!"=="y" (
        echo.
        echo Installing AI provider packages...
        echo   Command: python -m pip install %AI_PACKAGES%
        echo.
        
        python -m pip install %AI_PACKAGES%
        if errorlevel 1 (
            echo [!] AI provider installation failed, but core system should work
        ) else (
            echo [OK] AI provider packages installed successfully
        )
    ) else (
        echo [i] Skipped AI provider installation
    )
)

REM Step 6: Verify installation
echo.
echo [Step 6] Verifying Installation

python -c "import pypdf" 2>nul && echo [OK] pypdf imported successfully || echo [X] Failed to import pypdf
python -c "import tiktoken" 2>nul && echo [OK] tiktoken imported successfully || echo [X] Failed to import tiktoken
python -c "import tqdm" 2>nul && echo [OK] tqdm imported successfully || echo [X] Failed to import tqdm
python -c "import requests" 2>nul && echo [OK] requests imported successfully || echo [X] Failed to import requests
python -c "import fitz" 2>nul && echo [OK] pymupdf imported successfully || echo [X] Failed to import pymupdf
python -c "import PIL" 2>nul && echo [OK] pillow imported successfully || echo [X] Failed to import pillow
python -c "import pytesseract" 2>nul && echo [OK] pytesseract imported successfully || echo [X] Failed to import pytesseract

echo.
echo Installation Complete!
echo.
echo What's installed:
echo [OK] Core Python dependencies
echo [OK] PDF processing capabilities
echo [OK] Image processing support

if "%TESSERACT_AVAILABLE%"=="1" (
    echo [OK] Full OCR capabilities (Tesseract^)
) else (
    echo [!] Limited OCR (Tesseract binary not found^)
)

echo.
echo Next steps:
echo   1. Set up API key: set OPENAI_API_KEY=your-key-here
echo   2. Run the application: python run.py
echo   3. Place files in: documents\input\
echo   4. Find results in: documents\processed\
echo.
echo Documentation:
echo   • README.md - Complete usage guide
echo   • Run tests: python -m pytest tests\ -v
echo   • List models: python run.py --list-models

echo.
pause