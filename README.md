# 🤖 Content Tamer AI
**Transform your digital chaos into organized, searchable files**

Stop losing time hunting through hundreds of files named `IMG_1234.jpg` and `Screenshot 2024-08-24.png`. Content Tamer AI reads your documents and gives them intelligent, descriptive names so you can find what you need instantly.

## ✨ What It Does

**Before Content Tamer AI:**
```
scan001.pdf              ← What's this?
IMG_1234.png             ← No clue
document.pdf             ← Could be anything
Screenshot_20240824.png  ← Screenshot of what?
```

**After Content Tamer AI:**
```
Electricity_Bill_January_2024.pdf           ← Instantly clear
Employee_Handbook_Remote_Work_Policy.png    ← Easy to find
Lease_Agreement_Downtown_Apartment.pdf      ← Perfectly organized
Quarterly_Financial_Report_Q3_2024.png      ← Makes sense
```

## 🚀 Quick Start (3 minutes)

### Step 1: Get Content Tamer AI
```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
python easy-setup.py
```

### Step 2: Choose Your AI
**Option A: Use Cloud AI** (most accurate, requires internet)
```bash
# For OpenAI (most popular)
export OPENAI_API_KEY="your-openai-key"

# For Claude (high quality)  
export ANTHROPIC_API_KEY="your-claude-key"
```

**Option B: Use Local AI** (completely private, no internet needed)
```bash
python src/main.py --setup-local-llm
```

### Step 3: Process Your Files
```bash
# Put your messy files in data/input/
# Then run:
python src/main.py
```

**That's it!** Your organized files appear in `data/processed/` with intelligent names.

---

## 💡 Perfect For

### 🏠 **Personal Life**
- **Bills & Receipts** → `Electricity_Bill_January_2024.pdf`
- **Medical Records** → `Blood_Test_Results_Annual_Checkup.pdf` 
- **Screenshots** → `Zoom_Meeting_Notes_Project_Planning.png`
- **Warranties** → `TV_Warranty_Samsung_65_Inch_QLED.pdf`

### 💼 **Work & Business**  
- **Contracts** → `Service_Agreement_Marketing_Agency.pdf`
- **Invoices** → `Invoice_12345_Web_Development_Services.pdf`
- **Reports** → `Monthly_Sales_Report_December_2024.pdf`
- **Presentations** → `Product_Launch_Presentation_Q1_2025.pdf`

### 📚 **Research & Study**
- **Academic Papers** → `Machine_Learning_Research_Paper_Stanford.pdf`
- **Notes** → `Meeting_Notes_Budget_Planning_Session.pdf`
- **Articles** → `Climate_Change_Impact_Report_UN_2024.pdf`

---

## 🛡️ Privacy & Security

### ✅ **Your Data Stays Safe**
- **Local Processing**: All file analysis happens on your computer
- **No File Uploads**: Your documents never leave your machine  
- **Secure AI Calls**: Only text content (not files) sent to AI providers
- **Open Source**: Full transparency - inspect the code yourself
- **Offline Option**: Complete privacy with Local AI mode

### 🔒 **What Gets Sent to AI?**
- ✅ **Text extracted from your documents** (for smart naming)
- ❌ **Never your actual files**
- ❌ **Never personal information** (automatically filtered)
- ❌ **Never file paths or locations**

---

## 🔧 Features That Matter

### 🧠 **Smart Document Understanding**
- Reads PDFs, images, screenshots, and scanned documents
- Understands content, not just filenames  
- Handles multiple languages and formats
- Works with poor quality scans

### 📁 **Intelligent Organization** 
- Groups related documents automatically
- Creates logical folder structures
- Learns from your preferences over time
- Handles any volume of files

### 🎯 **Zero Learning Curve**
- Works immediately with smart defaults
- Beautiful progress bars and feedback
- Clear error messages with solutions
- Resume processing if interrupted

---

## 💰 Cost & AI Options

### **OpenAI** (Most Popular)
- **Cost**: ~$0.01 per document
- **Quality**: Excellent
- **Speed**: Fast
- **Best for**: General use, mixed document types

### **Claude** (Highest Quality)  
- **Cost**: ~$0.015 per document
- **Quality**: Outstanding
- **Speed**: Fast
- **Best for**: Complex documents, contracts, reports

### **Local AI** (Completely Free)
- **Cost**: $0 (runs on your computer)
- **Quality**: Very good
- **Speed**: Depends on your hardware
- **Best for**: Privacy-focused users, high volumes

---

## 📋 Installation Options

### Option 1: Easy Setup (Recommended)
```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai  
python easy-setup.py  # Handles everything automatically
```

### Option 2: Advanced Setup
```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
python scripts/install.py  # Detailed setup with options
```

### Option 3: Manual Setup
```bash
git clone https://github.com/quanyeomans/content-tamer-ai.git
cd content-tamer-ai
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## 🆘 Help & Support

### **Common Issues**

**"No API key found"**
```bash
# Set your API key (replace with your actual key)
export OPENAI_API_KEY="sk-your-actual-key-here"
```

**"OCR not working"**  
```bash
# Install Tesseract for reading scanned documents
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Mac: brew install tesseract  
# Linux: sudo apt-get install tesseract-ocr
```

**"Local AI too slow"**
```bash
# Check system requirements and available models
python src/main.py --check-local-requirements
python src/main.py --list-local-models
```

### **Getting Better Results**

- **Use high-quality scans** (300+ DPI) for best OCR results
- **Process similar documents together** for better organization
- **Check results regularly** and provide feedback to improve accuracy
- **Use descriptive folder names** when organizing large collections

---

## 🌟 Why Content Tamer AI?

- ✅ **Saves Hours**: Stop searching through endless files
- ✅ **Works Everywhere**: Windows, Mac, Linux support  
- ✅ **Completely Secure**: Your files never leave your computer
- ✅ **Privacy First**: Local AI option needs no internet
- ✅ **Always Improving**: Regular updates with new features
- ✅ **Open Source**: Free forever, no hidden costs

---

**Ready to tame your digital chaos?** Get started in 3 minutes! ⬆️