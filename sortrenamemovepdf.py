import os
import shutil
import PyPDF2
from PyPDF2.errors import PdfReadError
import tiktoken
from openai import OpenAI
import re
import time
import sys
from tqdm import tqdm
import argparse
import json
import requests
from typing import Dict, Any, Optional, List, Tuple
import unicodedata
import platform
import base64
import io
import datetime as dt

# -----------------------------
# Optional dependencies for OCR / rendering
# -----------------------------
HAVE_PYMUPDF = False
HAVE_TESSERACT = False
try:
    import fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except Exception:
    HAVE_PYMUPDF = False

try:
    from PIL import Image
    import pytesseract
    HAVE_TESSERACT = True
except Exception:
    HAVE_TESSERACT = False

# OCR config (tunable)
OCR_LANG = "eng"           # e.g., "eng+ind"
OCR_PAGES = 4               # first N pages to OCR
OCR_ZOOM = 3.5              # 72 * zoom ≈ DPI (3.5 ≈ 252 DPI)
OCR_USE_OSD = True          # try Tesseract orientation detection

def _print_capabilities():
    print(
        f"OCR deps → PyMuPDF: {'yes' if HAVE_PYMUPDF else 'no'}, "
        f"Tesseract: {'yes' if HAVE_TESSERACT else 'no'}; "
        f"OCR_LANG={OCR_LANG}, OCR_PAGES={OCR_PAGES}, OCR_ZOOM={OCR_ZOOM}"
    )

# Platform-specific imports for file locking
if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl
if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl

# Import API clients conditionally to avoid hard dependencies
try:
    import google.genai as genai
    HAVE_GEMINI = True
except ImportError:
    HAVE_GEMINI = False

try:
    import anthropic
    HAVE_CLAUDE = True
except ImportError:
    HAVE_CLAUDE = False

# No need for try/except for Deepseek since we're using requests
HAVE_DEEPSEEK = True

# -----------------------------
# Cross-platform file locking
# -----------------------------

def lock_file(file_obj):
    """Apply a file lock appropriate for the platform"""
    if platform.system() == "Windows":
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
    else:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)

def unlock_file(file_obj):
    """Release a file lock appropriate for the platform"""
    if platform.system() == "Windows":
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)

# -----------------------------
# Global constants
# -----------------------------
ENCODING = tiktoken.get_encoding("cl100k_base")
MAX_LENGTH = 15000
MAX_RETRIES = 3
RETRY_DELAY = 2

ERROR_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_processing_errors.log")

# Available AI providers / models
AI_PROVIDERS = {
    "openai": [
        # Current recommended models
        "gpt-5", "gpt-5-mini", "gpt-4.1-mini", "gpt-4o", "gpt-4-turbo",
        # Legacy/compat
        "gpt-3.5-turbo",
        # Vision-capable (naming left for compatibility)
        "gpt-4-vision-preview", "gpt-4o-vision"
    ],
    "gemini": ["gemini-pro"],
    "claude": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
    "deepseek": ["deepseek-chat"],
}

# Default (fallback) prompts per provider
DEFAULT_SYSTEM_PROMPTS = {
    "openai": (
        "Generate a descriptive filename based on the document content. "
        "Return ONLY the filename text, no quotes or code blocks. "
        "Use English letters, numbers, and underscores only. 50 characters max."
    ),
    "gemini": "Generate a descriptive filename based on the document content. Use only English letters, numbers, and underscores. Keep it under 50 characters.",
    "claude": "Generate a descriptive filename based on the document content. Use only English letters, numbers, and underscores. Keep it under 50 characters.",
    "deepseek": "Generate a descriptive filename based on the document content. Use only English letters, numbers, and underscores. Keep it under 50 characters.",
}

# Optional override map; if not present at runtime, fall back to defaults
SYSTEM_PROMPTS = DEFAULT_SYSTEM_PROMPTS


def get_system_prompt(provider: str) -> str:
    """Safe accessor that tolerates missing/overridden SYSTEM_PROMPTS."""
    try:
        if isinstance(SYSTEM_PROMPTS, dict) and provider in SYSTEM_PROMPTS:
            return SYSTEM_PROMPTS[provider]
    except Exception:
        pass
    return DEFAULT_SYSTEM_PROMPTS[provider]

DEFAULT_MODELS = {
    "openai": "gpt-5-mini",  # modern, cheap default
    "gemini": "gemini-pro",
    "claude": "claude-3-haiku",
    "deepseek": "deepseek-chat",
}

# OCR language hint for Tesseract (e.g., "eng", "eng+ind")
OCR_LANG = "eng"

# Global variable for AI client
ai_client = None

# -----------------------------
# OCR / Rendering helpers
# -----------------------------

def _detect_osd_angle(img):
    """Use Tesseract OSD to estimate rotation angle (0/90/180/270)."""
    if not HAVE_TESSERACT or not OCR_USE_OSD:
        return 0
    try:
        osd = pytesseract.image_to_osd(img)
        m = re.search(r"Rotate:\s*(\d+)", osd)
        return (int(m.group(1)) % 360) if m else 0
    except Exception:
        return 0

def _rotate_image(img, angle):
    if not angle:
        return img
    # tesseract OSD angle is clockwise; PIL rotate is counter-clockwise → invert
    return img.rotate(360 - angle, expand=True)

def _fitz_text(pdf_path: str, max_pages: int = 5) -> str:
    """Text extraction via PyMuPDF if available."""
    if not HAVE_PYMUPDF:
        return ""
    try:
        doc = fitz.open(pdf_path)
        chunks: List[str] = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            # "text" mode keeps reading order better for simple pages
            chunks.append(page.get_text("text") or "")
        return "\n".join(chunks).strip()
    except Exception:
        return ""

def _fitz_render_png_b64(pdf_path: str, page_index: int = 0, zoom: float = OCR_ZOOM, auto_orient: bool = True) -> Optional[str]:
    if not HAVE_PYMUPDF:
        return None
    try:
        doc = fitz.open(pdf_path)
        if page_index >= len(doc):
            return None
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        png_bytes = pix.tobytes("png")

        # If Tesseract is available, use OSD to orient the image before sending to the LLM
        if HAVE_TESSERACT and auto_orient:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(png_bytes))
                angle = _detect_osd_angle(img)
                img = _rotate_image(img, angle)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                png_bytes = buf.getvalue()
            except Exception:
                pass

        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None

def _ocr_tesseract_from_pdf(pdf_path: str, pages: int = OCR_PAGES, zoom: float = OCR_ZOOM, lang: str = OCR_LANG) -> str:
    if not (HAVE_PYMUPDF and HAVE_TESSERACT):
        return ""
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return ""
    out = []
    for i, page in enumerate(doc):
        if i >= pages:
            break
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            angle = _detect_osd_angle(img)
            img = _rotate_image(img, angle)
            text = pytesseract.image_to_string(img, lang=lang, config="--psm 6 --oem 1")
            out.append(text or "")
        except Exception:
            continue
    return "\n".join(out).strip()

def _pypdf2_text(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """Fallback text extraction using PyPDF2 (text layer only)."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                return "Error: PDF is encrypted and cannot be processed without a password."

            total_pages = len(reader.pages)
            if max_pages is None and total_pages > 100:
                max_pages = 100
                print(f"Warning: PDF has {total_pages} pages. Limiting to first {max_pages} pages for performance.")

            pages_to_process = reader.pages if not max_pages or total_pages <= max_pages else reader.pages[:max_pages]

            content = []
            for page in pages_to_process:
                try:
                    page_text = page.extract_text() or ""
                    content.append(page_text)
                except Exception as e:
                    print(f"Warning: Could not extract text from a page: {str(e)}")

            joined = (" ".join(content)).strip()
            if not joined:
                return ""
            return truncate_content_to_token_limit(joined, MAX_LENGTH)
    except (IOError, OSError) as e:
        return f"Error opening PDF: {str(e)}"
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_and_image(pdf_path: str, min_len: int = 40) -> Tuple[str, Optional[str]]:
    """
    Best-effort content extraction for image-based + digital PDFs.
    Returns (text, first_page_image_data_url).
    """
    # 1) Try PyMuPDF text (fast if a text layer exists)
    text = _fitz_text(pdf_path) if HAVE_PYMUPDF else ""

    # 2) Fallback: PyPDF2 text (detect encryption or errors)
    if not text:
        pypdf2_text = _pypdf2_text(pdf_path)
        # Propagate explicit errors from PyPDF2
        if pypdf2_text.startswith("Error"):
            return pypdf2_text, None
        text = pypdf2_text or ""

    # 3) Render first page image for vision models
    img_b64 = _fitz_render_png_b64(pdf_path, 0, OCR_ZOOM, auto_orient=True) if HAVE_PYMUPDF else None

    # 4) If text is too short, try Tesseract OCR on first few pages
    if len(text) < min_len:
        ocr_text = _ocr_tesseract_from_pdf(pdf_path, lang=OCR_LANG)
        if len(ocr_text) > len(text):
            text = ocr_text

    return text.strip(), img_b64

# -----------------------------
# AI client factory and providers
# -----------------------------

class AIClient:
    """Factory class for different AI clients"""

    @staticmethod
    def create(provider: str, model: str, api_key: str) -> Any:
        """Create an AI client based on the provider"""
        if provider == "openai":
            return OpenAIClient(api_key, model)
        elif provider == "gemini":
            if not HAVE_GEMINI:
                raise ImportError("Please install Google Generative AI: pip install google-genai")
            return GeminiClient(api_key, model)
        elif provider == "claude":
            if not HAVE_CLAUDE:
                raise ImportError("Please install Anthropic: pip install anthropic")
            return ClaudeClient(api_key, model)
        elif provider == "deepseek":
            return DeepseekClient(api_key, model)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")


class OpenAIClient:
    """OpenAI API client (Responses API; GPT-5-safe)."""

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        try:
            client = self.client.with_options(timeout=90)

            parts = []
            if content:
                parts.append({
                    "type": "input_text",
                    "text": (
                        "You are a document analyst. Create a concise, human-readable filename "
                        "for this PDF based on its visible content. Use underscores between words. "
                        "Return ONLY the filename. 4–8 words, 60 chars max.\n\n"
                        f"---\nEXTRACTED_TEXT_START\n{content[:8000]}\nEXTRACTED_TEXT_END\n"
                    )
                })
            if image_b64:
                parts.append({"type": "input_image", "image_url": image_b64})

            base = {
                "model": self.model,
                "instructions": get_system_prompt("openai"),
                "input": [{"role": "user", "content": parts}],
                "max_output_tokens": 64,
            }
            model_lc = (self.model or "").lower()
            if "gpt-5" in model_lc:
                base["reasoning"] = {"effort": "low"}
            else:
                base["temperature"] = 0.1
                base["top_p"] = 0.9

            def _call(payload):
                return client.responses.create(**payload)

            # First attempt
            try:
                resp = _call(base)
                raw = (resp.output_text or "").strip()
            except Exception as e:
                msg = str(e)
                # If GPT-5 complains about image inputs, retry without image
                if "image_url" in msg or "image" in msg:
                    noimg = dict(base)
                    noimg["input"] = [{"role": "user", "content": [c for c in parts if c.get("type") != "input_image"]}]
                    noimg.pop("reasoning", None)
                    noimg["temperature"] = 0.1
                    noimg["top_p"] = 0.9
                    resp = _call(noimg)
                    raw = (resp.output_text or "").strip()
                else:
                    raise

            # If we still have nothing and we have an image, try a vision-friendly fallback model
            if not raw and image_b64:
                fallback_model = "gpt-4o"
                fb = dict(base)
                fb["model"] = fallback_model
                fb.pop("reasoning", None)
                fb["temperature"] = 0.1
                fb["top_p"] = 0.9
                try:
                    resp = _call(fb)
                    raw = (resp.output_text or "").strip()
                except Exception:
                    pass

            return raw
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class GeminiClient:
    """Google Gemini API client (text-only here)."""

    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generate a filename using Gemini API (ignores image)."""
        try:
            response = self.model.generate_content(
                [get_system_prompt("gemini"), content or ""],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=60,
                    temperature=0.2,
                ),
            )
            if not hasattr(response, 'text'):
                raise AttributeError("Unexpected response format from Gemini API")
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


class ClaudeClient:
    """Anthropic Claude API client (text-only here)."""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generate a filename using Claude API (ignores image)."""
        try:
            message = self.client.messages.create(
                model=self.model,
                system=get_system_prompt("claude"),
                max_tokens=60,
                messages=[{"role": "user", "content": content or ""}],
            )
            if hasattr(message, 'content') and isinstance(message.content, list) and len(message.content) > 0:
                first = message.content[0]
                if hasattr(first, 'text'):
                    return first.text
            if hasattr(message, 'content'):
                if isinstance(message.content, str):
                    return message.content
                elif isinstance(message.content, dict) and 'text' in message.content:
                    return message.content['text']
            raise ValueError("Unable to extract text from Claude API response")
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")


class DeepseekClient:
    """Deepseek API client using direct HTTP requests (text-only)."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": get_system_prompt("deepseek")},
                {"role": "user", "content": content or ""},
            ],
            "max_tokens": 60,
            "temperature": 0.2,
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}, Response: {response.text}")
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise Exception(f"Deepseek API request error: {str(e)}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"Deepseek API response parsing error: {str(e)}")
        except Exception as e:
            raise Exception(f"Deepseek API error: {str(e)}")

# -----------------------------
# Utilities & core workflow
# -----------------------------

def get_api_details(provider: str, model: str):
    """Get API key and check if it's valid for the given provider"""
    if provider not in AI_PROVIDERS:
        available_providers = ", ".join(AI_PROVIDERS.keys())
        raise ValueError(f"Unsupported provider '{provider}'. Available providers: {available_providers}")

    env_var_name = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    if not api_key:
        api_key = input(f"Please enter your {provider.capitalize()} API key: ").strip()
        if not api_key:
            raise ValueError(f"{provider.capitalize()} API key is required.")

    if model not in AI_PROVIDERS.get(provider, []):
        available_models = ", ".join(AI_PROVIDERS.get(provider, ["No models available"]))
        raise ValueError(f"Invalid model '{model}' for provider '{provider}'. Available models: {available_models}")

    return api_key


def sort_and_rename_pdfs(input_folder, corrupted_folder, renamed_folder, provider="openai", model=None, reset_progress: bool = False):
    """Sort and rename PDF files based on their content."""
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return False

    if model is None:
        model = DEFAULT_MODELS.get(provider, AI_PROVIDERS[provider][0])

    api_key = get_api_details(provider, model)
    global ai_client
    ai_client = AIClient.create(provider, model, api_key)

    os.makedirs(corrupted_folder, exist_ok=True)
    os.makedirs(renamed_folder, exist_ok=True)

    pdf_files = []
    for f in os.listdir(input_folder):
        # Skip non-PDFs, hidden files, and AppleDouble resource forks
        if not f.lower().endswith('.pdf'):
            continue
        if f.startswith('.') or f.startswith('._'):
            # Hidden / AppleDouble file (e.g., ._scan.pdf) – skip
            continue
        full_path = os.path.join(input_folder, f)
        if not os.path.isfile(full_path):
            continue
        pdf_files.append(f)
    total_files = len(pdf_files)
    if total_files == 0:
        print(f"No PDF files found in {input_folder}")
        return True

    progress_file = os.path.join(renamed_folder, ".progress")
    # Optionally reset progress file if user requested
    if reset_progress and os.path.exists(progress_file):
        try:
            os.remove(progress_file)
            print("Resetting progress: existing .progress file removed.")
        except Exception as e:
            print(f"Warning: Could not delete progress file: {str(e)}")

    processed_files = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as f:
                processed_files = set(line.strip() for line in f)
            # Reconcile: only treat as processed if the file is NOT in the input folder anymore
            processed_files = {name for name in processed_files if not os.path.exists(os.path.join(input_folder, name))}
        except Exception as e:
            print(f"Warning: Could not read progress file: {str(e)}")

    try:
        with open(progress_file, "a") as progress_f:
            with tqdm(total=total_files, desc="Processing PDFs", unit="file") as pbar:
                for filename in pdf_files:
                    if filename in processed_files:
                        pbar.update(1)
                        continue

                    input_path = os.path.normpath(os.path.join(input_folder, filename))
                    if not os.path.exists(input_path):
                        print(f"\nWarning: File {filename} no longer exists, skipping.")
                        pbar.update(1)
                        continue

                    process_pdf(input_path, filename, corrupted_folder, renamed_folder, pbar, progress_f)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Progress has been saved.")
        return True
    except Exception as e:
        print(f"\nError during processing: {str(e)}")
        return False

    return True


def safe_move(src: str, dst: str, attempts: int = 3, delay: float = 0.75) -> None:
    """Robust move with retries; falls back to copy+delete on stubborn permission errors."""
    last_err = None
    for i in range(attempts):
        try:
            shutil.move(src, dst)
            return
        except Exception as e:
            last_err = e
            time.sleep(delay * (i + 1))
    # Fallback: copy then remove
    shutil.copy2(src, dst)
    try:
        os.remove(src)
    except Exception as e:
        # If delete fails, surface the last meaningful error
        raise e if e else last_err


def process_pdf(input_path, filename, corrupted_folder, renamed_folder, pbar, progress_f):
    """Process a single PDF file with error handling."""
    try:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"File not found or not accessible: {input_path}")

        # New: robust extraction including OCR + first page image
        text, img_b64 = extract_text_and_image(input_path)

        # If explicit error from PyPDF2 (encryption, open/read issues)
        if text.startswith("Error"):
            raise PdfReadError(text)

        # Guard: if still empty (no text and no image), mark as empty
        if not text and not img_b64:
            timestamp = dt.datetime.now().strftime('%Y%m%d%H%M%S')
            new_file_name = f"empty_file_{timestamp}"
        else:
            # Get new filename with retries; pass image to models that support it
            new_file_name = get_new_filename_with_retry(text, img_b64)
            new_file_name = validate_and_trim_filename(new_file_name)

        # Handle duplicate filenames with sequential numbering
        new_file_name = handle_duplicate_filename(new_file_name, renamed_folder)

        # Move file to renamed folder
        new_filepath = os.path.join(renamed_folder, new_file_name + ".pdf")
        safe_move(input_path, new_filepath)
        pbar.set_postfix({"Status": "Renamed", "New Name": new_file_name})

        # Record progress
        try:
            lock_file(progress_f)
            progress_f.write(f"{filename}\n")
            progress_f.flush()
        finally:
            unlock_file(progress_f)

    except (PdfReadError, OSError, FileNotFoundError) as e:
        error_msg = f"Error with file {filename}: {str(e)}"
        print(f"\n{error_msg}")
        try:
            if os.path.exists(input_path):
                corrupted_path = os.path.join(corrupted_folder, filename)
                safe_move(input_path, corrupted_path)
                pbar.set_postfix({"Status": "Corrupted", "Moved to": corrupted_folder})
            else:
                pbar.set_postfix({"Status": "Error", "Message": "File not found"})

            try:
                lock_file(progress_f)
                progress_f.write(f"{filename}\n")
                progress_f.flush()
            finally:
                unlock_file(progress_f)
        except OSError as move_error:
            pbar.set_postfix({"Status": "Error", "Message": str(move_error)})
    except Exception as e:
        error_msg = f"Unexpected error with file {filename}: {str(e)}"
        print(f"\n{error_msg}")
        try:
            with open(ERROR_LOG_FILE, "a") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\n")
        except Exception as log_error:
            print(f"Warning: Could not write to error log: {str(log_error)}")
        pbar.set_postfix({"Status": "Error", "Message": "Unexpected error"})

    pbar.update(1)


def get_new_filename_with_retry(pdf_content: str, image_b64: Optional[str] = None, max_retries: int = MAX_RETRIES) -> str:
    """Get new filename with retry mechanism for API failures."""
    timeout_count = 0
    for attempt in range(max_retries):
        try:
            return get_filename_from_ai(pdf_content, image_b64)
        except Exception as e:
            error_str = str(e).lower()
            is_timeout = any(t in error_str for t in ["timeout", "timed out", "connection", "network"])

            if is_timeout:
                timeout_count += 1
                wait_time = RETRY_DELAY * (2 ** timeout_count)  # Exponential backoff
                print(f"\nAPI timeout/network error: {str(e)}. Retrying in {wait_time} seconds...")
            else:
                wait_time = RETRY_DELAY * (attempt + 1)  # Linear backoff
                print(f"\nAPI error: {str(e)}. Retrying in {wait_time} seconds...")

            time.sleep(wait_time)

            if attempt == max_retries - 1:
                print(f"\nFailed to get filename from API after {max_retries} attempts.")
                timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())
                if timeout_count > 0:
                    return f"network_error_{timestamp}"
                else:
                    return f"untitled_document_{timestamp}"


def get_filename_from_ai(pdf_content: str, image_b64: Optional[str] = None) -> str:
    """Get a filename suggestion from the selected AI model"""
    if ai_client is None:
        raise RuntimeError("AI client not initialized. Call sort_and_rename_pdfs first.")
    return ai_client.generate_filename(pdf_content, image_b64)


def validate_and_trim_filename(initial_filename: str) -> str:
    """Clean and validate a filename."""
    if not initial_filename or initial_filename.isspace():
        timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        return f'empty_file_{timestamp}'

    # Normalize unicode, encode to ASCII ignoring errors, then decode
    normalized = unicodedata.normalize('NFKD', initial_filename).encode('ascii', 'ignore').decode('ascii')
    # Keep only [A-Za-z0-9_]
    cleaned_filename = re.sub(r'[^a-zA-Z0-9_]', '', normalized)

    if not cleaned_filename:
        timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        return f'invalid_name_{timestamp}'

    return cleaned_filename[:160]


def handle_duplicate_filename(filename: str, folder: str) -> str:
    """Handle duplicate filenames by adding a sequential number."""
    base_filename = filename
    counter = 1
    while os.path.exists(os.path.join(folder, f"{filename}.pdf")):
        filename = f"{base_filename}_{counter}"
        counter += 1
    return filename


# Legacy function (still used by some fallbacks). Retained for completeness.
def pdfs_to_text_string(filepath: str, max_pages: Optional[int] = None) -> str:
    """Extract text from a PDF file (PyPDF2 path), handling errors."""
    return _pypdf2_text(filepath, max_pages)


def truncate_content_to_token_limit(content: str, max_tokens: int) -> str:
    """Truncate content to fit within token limit in a safe and efficient way."""
    try:
        token_count = len(ENCODING.encode(content))
        if token_count <= max_tokens:
            return content

        if token_count > max_tokens * 2:
            bytes_per_token = len(content.encode('utf-8')) / token_count
            target_bytes = int(max_tokens * bytes_per_token * 0.9)
            content = content[:target_bytes]
            token_count = len(ENCODING.encode(content))

        if token_count > max_tokens:
            low, high = 0, len(content)
            while high - low > 100:
                mid = (low + high) // 2
                if len(ENCODING.encode(content[:mid])) <= max_tokens:
                    low = mid
                else:
                    high = mid
            content = content[:low]
        return content
    except Exception as e:
        print(f"Warning: Error during content truncation: {str(e)}")
        return content[: int(max_tokens * 3)]


def list_available_models():
    """List all available AI models by provider"""
    print("Available AI models by provider:")
    for provider, models in AI_PROVIDERS.items():
        print(f"\n{provider.capitalize()}:")
        for model in models:
            print(f"  - {model}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Sort and rename PDF files based on their content",
        epilog="""
Examples:
  # Use default OpenAI model
  python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed

  # Use GPT-4o
  python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p openai -m gpt-4o
  
  # Use Claude
  python sortrenamemovepdf.py -i ./input -c ./corrupted -r ./renamed -p claude -m claude-3-sonnet
  
  # List all available models
  python sortrenamemovepdf.py --list-models
"""
    )
    parser.add_argument("--input", "-i", help="Input folder containing PDF files")
    parser.add_argument("--corrupted", "-c", help="Folder for corrupted PDF files")
    parser.add_argument("--renamed", "-r", help="Folder for renamed PDF files")
    parser.add_argument("--provider", "-p", help=f"AI provider (options: {', '.join(AI_PROVIDERS.keys())})",
                        default="openai", choices=AI_PROVIDERS.keys())
    parser.add_argument("--model", "-m", help="Model to use for the selected provider (run with --list-models to see options)")
    parser.add_argument("--api-key", "-k", help="API key for the selected provider")
    parser.add_argument("--list-models", "-l", action="store_true", help="List all available models by provider and exit")
    parser.add_argument("--ocr-lang", default="eng", help="Tesseract OCR language hint (e.g., 'eng', 'eng+ind')")
    parser.add_argument("--reset-progress", action="store_true", help="Ignore and delete existing .progress file before run")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_arguments()
        # Apply OCR language hint
        OCR_LANG = args.ocr_lang
        _print_capabilities()

        # List available models if requested
        if args.list_models:
            list_available_models()
            sys.exit(0)

        # Save original env var state if using command-line key
        original_env = None
        api_key_set = False

        try:
            if args.api_key:
                env_var = f"{args.provider.upper()}_API_KEY"
                original_env = (env_var, os.environ.get(env_var))
                os.environ[env_var] = args.api_key
                api_key_set = True
                print(f"Using provided {args.provider.capitalize()} API key")

            # Get folder paths from arguments or prompt user
            input_folder = args.input or input("Enter the input folder path: ")
            corrupted_folder = args.corrupted or input("Enter the corrupted PDFs folder path: ")
            renamed_folder = args.renamed or input("Enter the renamed PDFs folder path: ")

            # Process PDFs
            success = sort_and_rename_pdfs(input_folder, corrupted_folder, renamed_folder, args.provider, args.model, reset_progress=args.reset_progress)

            if success:
                print("PDF sorting and renaming completed successfully.")
                return_code = 0
            else:
                print("PDF sorting and renaming failed.")
                return_code = 1
        finally:
            # Restore original environment if modified
            if api_key_set and original_env:
                try:
                    env_var, original_value = original_env
                    if original_value is None:
                        os.environ.pop(env_var, None)
                    else:
                        os.environ[env_var] = original_value
                except Exception as e:
                    print(f"Warning: Could not restore original API key environment: {str(e)}")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        return_code = 130  # Standard return code for SIGINT
    except Exception as e:
        print(f"\nCritical error: {str(e)}")
        return_code = 1

    # Exit with appropriate code
    sys.exit(return_code)
