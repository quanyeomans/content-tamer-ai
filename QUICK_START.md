# 🚀 Content Tamer AI - Quick Start

**Get running in under 2 minutes!**

## 1. Install

```bash
# Clone the project
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai

# Run the smart installer (handles everything automatically)
python install.py
```

The installer will:
- ✅ Check your Python version
- ✅ Verify dependencies  
- ✅ Ask permission before installing anything
- ✅ Set up a virtual environment (recommended)
- ✅ Test that everything works

## 2. Set API Key

```bash
# Option 1: Environment variable (recommended)
export OPENAI_API_KEY="your-key-here"        # macOS/Linux
set OPENAI_API_KEY=your-key-here             # Windows

# Option 2: The app will prompt you if no key is found
```

**Get your API key:** [OpenAI API Keys](https://platform.openai.com/api-keys)

## 3. Run It!

```bash
# Just run it - uses smart defaults
content-tamer-ai
# or: python run.py

# That's it! 🎉
```

## 📁 What Happens

1. **Input folder created:** `documents/input/` 
2. **Drop your files there:** PDFs, images, screenshots
3. **Run the command:** `python run.py`
4. **Check results:** `documents/processed/`

## 🎯 Example Results

**Before:**
```
scan001.pdf
IMG_1234.png  
document.pdf
```

**After:**
```
quarterly_financial_report_q3_2024.pdf
employee_handbook_remote_work_policy.png
meeting_notes_project_kickoff_january.pdf
```

## 🆘 Need Help?

```bash
content-tamer-ai --help          # Show all options
content-tamer-ai --list-models   # See available AI models
```

**Problems?** Check the full [README.md](README.md) for detailed troubleshooting.

---

**That's it!** You're ready to organize your documents with AI. 🤖✨