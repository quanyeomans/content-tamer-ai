"""
This module handles the sorting, renaming, and moving of PDF files.
"""

import os
import shutil
import re
import time
import sys
import argparse
import json
import unicodedata
import platform
import base64
import io
import datetime as dt
import PyPDF2
from PyPDF2.errors import PdfReadError
import tiktoken
from openai import OpenAI, APIError
from tqdm import tqdm
import requests
from typing import Any, Optional, List, Tuple


# -----------------------------
# Optional dependencies for OCR / rendering
# -----------------------------
HAVE_PYMUPDF = False
HAVE_TESSERACT = False
try:
    import fitz  # PyMuPDF

    HAVE_PYMUPDF = True
except ImportError:
    HAVE_PYMUPDF = False

try:
    from PIL import Image
    import pytesseract

    HAVE_TESSERACT = True
except ImportError:
    HAVE_TESSERACT = False

# These settings can be adjusted to change OCR behavior.
OCR_LANG = "eng"  # Language for OCR (e.g., "eng" for English, "eng+ind" for English and Indonesian).
OCR_PAGES = 4  # Process the first N pages of a PDF for OCR.
OCR_ZOOM = 3.5  # Zoom factor for rendering PDF pages as images. Higher values create larger images.
OCR_USE_OSD = (
    True  # Enable Tesseract's orientation and script detection to auto-rotate images.
)


def _print_capabilities(ocr_lang: str):
    """Prints the status of optional dependencies."""
    pymupdf_status = "yes" if HAVE_PYMUPDF else "no"
    tesseract_status = "yes" if HAVE_TESSERACT else "no"
    print(
        f"OCR deps → PyMuPDF: {pymupdf_status}, Tesseract: {tesseract_status}; "
        f"OCR_LANG={ocr_lang}, OCR_PAGES={OCR_PAGES}, OCR_ZOOM={OCR_ZOOM}"
    )


# Platform-specific imports for file locking
if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl  # pylint: disable=import-error
# fcntl is imported dynamically where needed for non-Windows systems.

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
    """Prevents multiple processes from writing to the same file at once."""
    if platform.system() == "Windows":
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl  # pylint: disable=import-error

        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)


def unlock_file(file_obj):
    """Releases the lock, allowing other processes to access the file."""
    if platform.system() == "Windows":
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl  # pylint: disable=import-error

        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)


# -----------------------------
# Global constants
# -----------------------------
ENCODING = tiktoken.get_encoding("cl100k_base")
MAX_LENGTH = 15000
MAX_RETRIES = 3
RETRY_DELAY = 2

ERROR_LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pdf_processing_errors.log"
)

# Available AI providers / models
AI_PROVIDERS = {
    "openai": [
        # Current recommended models
        "gpt-5",
        "gpt-5-mini",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4-turbo",
        # Legacy/compat
        "gpt-3.5-turbo",
        # Vision-capable (naming left for compatibility)
        "gpt-4-vision-preview",
        "gpt-4o-vision",
    ],
    "gemini": ["gemini-pro"],
    "claude": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
    "deepseek": ["deepseek-chat"],
}

# This is a dictionary of default prompts that instruct the AI on how to generate a filename.
# Each AI provider gets a specific prompt tailored to its expected format.
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

# This allows for custom prompts to be used if defined. Otherwise, it falls back to the defaults.
SYSTEM_PROMPTS = DEFAULT_SYSTEM_PROMPTS


def get_system_prompt(provider: str) -> str:
    """Gets the system prompt for a given AI provider, with a fallback to the default."""
    try:
        if isinstance(SYSTEM_PROMPTS, dict) and provider in SYSTEM_PROMPTS:
            return SYSTEM_PROMPTS[provider]
    except Exception:
        pass
    return DEFAULT_SYSTEM_PROMPTS[provider]


# This dictionary sets the default AI model to use for each provider.
DEFAULT_MODELS = {
    "openai": "gpt-5-mini",
    "gemini": "gemini-pro",
    "claude": "claude-3-haiku",
    "deepseek": "deepseek-chat",
}

# This tells Tesseract which language to look for in the document.
OCR_LANG = "eng"

# This will hold the AI client instance once it's initialized.
AI_CLIENT = None

# -----------------------------
# OCR and Image Rendering Functions
# -----------------------------


def _detect_osd_angle(img):
    """Uses Tesseract's Orientation and Script Detection (OSD) to find out if an image is rotated."""
    if not HAVE_TESSERACT or not OCR_USE_OSD:
        return 0
    try:
        osd = pytesseract.image_to_osd(img)
        m = re.search(r"Rotate:\s*(\d+)", osd)
        return (int(m.group(1)) % 360) if m else 0
    except pytesseract.TesseractError:
        return 0


def _rotate_image(img, angle):
    if not angle:
        return img
    # Tesseract's angle is clockwise, but the Python Imaging Library (PIL) rotates counter-clockwise, so we invert the angle.
    return img.rotate(360 - angle, expand=True)


def _fitz_text(pdf_path: str, max_pages: int = 5) -> str:
    """Extracts text from a PDF using the PyMuPDF library (fitz), which is fast and efficient."""
    if not HAVE_PYMUPDF:
        return ""
    try:
        doc = fitz.open(pdf_path)
        chunks: List[str] = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            # Using "text" mode helps maintain the original reading order of the document.
            chunks.append(page.get_text("text") or "")
        return "\n".join(chunks).strip()
    except RuntimeError:
        return ""


def _fitz_render_png_b64(
    pdf_path: str, page_index: int = 0, zoom: float = OCR_ZOOM, auto_orient: bool = True
) -> Optional[str]:
    if not HAVE_PYMUPDF:
        return None
    try:
        doc = fitz.open(pdf_path)
        if page_index >= len(doc):
            return None
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        png_bytes = pix.tobytes("png")

        # If Tesseract is installed, we can automatically detect and correct the image's orientation before processing.
        if HAVE_TESSERACT and auto_orient:
            try:
                img = Image.open(io.BytesIO(png_bytes))
                angle = _detect_osd_angle(img)
                img = _rotate_image(img, angle)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                png_bytes = buf.getvalue()
            except (IOError, ValueError):
                pass

        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except RuntimeError:
        return None


def _ocr_tesseract_from_pdf(
    pdf_path: str, pages: int = OCR_PAGES, zoom: float = OCR_ZOOM, lang: str = OCR_LANG
) -> str:
    if not (HAVE_PYMUPDF and HAVE_TESSERACT):
        return ""
    try:
        doc = fitz.open(pdf_path)
    except RuntimeError:
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
        except (RuntimeError, IOError, ValueError, pytesseract.TesseractError):
            continue
    return "\n".join(out).strip()


def _pypdf2_text(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """Extracts text from a PDF's text layer using the PyPDF2 library. This is a fallback method."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                return "Error: PDF is encrypted and cannot be processed without a password."

            total_pages = len(reader.pages)
            if max_pages is None and total_pages > 100:
                max_pages = 100
                print(
                    f"Warning: PDF has {total_pages} pages. Limiting to first {max_pages} pages for performance."
                )

            pages_to_process = (
                reader.pages
                if not max_pages or total_pages <= max_pages
                else reader.pages[:max_pages]
            )

            content = []
            for page in pages_to_process:
                try:
                    page_text = page.extract_text() or ""
                    content.append(page_text)
                except (TypeError, KeyError, ValueError) as e:
                    print(
                        f"Warning: Could not extract text from a page due to malformed content: {str(e)}"
                    )

            joined = (" ".join(content)).strip()
            if not joined:
                return ""
            return truncate_content_to_token_limit(joined, MAX_LENGTH)
    except (IOError, OSError) as e:
        return f"Error opening PDF: {str(e)}"
    except PdfReadError as e:
        return f"Error reading PDF: {str(e)}"


def extract_text_and_image(
    pdf_path: str, min_len: int = 40, ocr_lang: str = OCR_LANG
) -> Tuple[str, Optional[str]]:
    """
    Extracts all possible content from a PDF, including text and images.
    It tries multiple methods to ensure the best possible result.
    Returns the extracted text and the first page rendered as an image.
    """
    # 1. Try to get text using PyMuPDF, which is fast.
    text = _fitz_text(pdf_path) if HAVE_PYMUPDF else ""

    # 2. If PyMuPDF fails, try PyPDF2 as a fallback.
    if not text:
        pypdf2_text = _pypdf2_text(pdf_path)
        # If PyPDF2 returns an error (e.g., encrypted PDF), stop and return the error.
        if pypdf2_text.startswith("Error"):
            return pypdf2_text, None
        text = pypdf2_text or ""

    # 3. Render the first page as an image, to be used by vision-capable AI models.
    img_b64 = (
        _fitz_render_png_b64(pdf_path, 0, OCR_ZOOM, auto_orient=True)
        if HAVE_PYMUPDF
        else None
    )

    # 4. If the extracted text is very short, it might be a scanned PDF. Try OCR.
    if len(text) < min_len:
        ocr_text = _ocr_tesseract_from_pdf(pdf_path, lang=ocr_lang)
        if len(ocr_text) > len(text):
            text = ocr_text

    return text.strip(), img_b64


# -----------------------------
# AI Client and Provider-Specific Code
# -----------------------------


class AIClient:
    """A factory class that creates the appropriate AI client based on the selected provider."""

    @staticmethod
    def create(provider: str, model: str, api_key: str) -> Any:
        """Creates and returns an instance of an AI client."""
        if provider == "openai":
            return OpenAIClient(api_key, model)
        elif provider == "gemini":
            if not HAVE_GEMINI:
                raise ImportError(
                    "Please install Google Generative AI: pip install google-genai"
                )
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
    """Handles communication with the OpenAI API."""

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        try:
            client = self.client.with_options(timeout=90)

            parts = []
            if content:
                parts.append(
                    {
                        "type": "input_text",
                        "text": (
                            "You are a document analyst. Create a concise, human-readable filename "
                            "for this PDF based on its visible content. Use underscores between words. "
                            "Return ONLY the filename. 4–8 words, 60 chars max.\n\n"
                            f"---\nEXTRACTED_TEXT_START\n{content[:8000]}\nEXTRACTED_TEXT_END\n"
                        ),
                    }
                )
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

            # First attempt to get a filename.
            try:
                resp = _call(base)
                raw = (resp.output_text or "").strip()
            except APIError as e:
                msg = str(e).lower()
                # If the model doesn't support images, try again without the image.
                if "image" in msg:
                    noimg = dict(base)
                    noimg["input"] = [
                        {
                            "role": "user",
                            "content": [
                                c for c in parts if c.get("type") != "input_image"
                            ],
                        }
                    ]
                    noimg.pop("reasoning", None)
                    noimg["temperature"] = 0.1
                    noimg["top_p"] = 0.9
                    resp = _call(noimg)
                    raw = (resp.output_text or "").strip()
                else:
                    raise

            # If we still don't have a name and an image was provided, try a vision-capable model as a fallback.
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
    """Handles communication with the Google Gemini API."""

    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generates a filename using the Gemini API. Note: This client does not use images."""
        try:
            response = self.model.generate_content(
                [get_system_prompt("gemini"), content or ""],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=60,
                    temperature=0.2,
                ),
            )
            if not hasattr(response, "text"):
                raise AttributeError("Unexpected response format from Gemini API")
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}") from e


class ClaudeClient:
    """Handles communication with the Anthropic Claude API."""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        """Generates a filename using the Claude API. Note: This client does not use images."""
        try:
            message = self.client.messages.create(
                model=self.model,
                system=get_system_prompt("claude"),
                max_tokens=60,
                messages=[{"role": "user", "content": content or ""}],
            )
            if (
                hasattr(message, "content")
                and isinstance(message.content, list)
                and len(message.content) > 0
            ):
                first = message.content[0]
                if hasattr(first, "text"):
                    return first.text
            if hasattr(message, "content"):
                if isinstance(message.content, str):
                    return message.content
                elif isinstance(message.content, dict) and "text" in message.content:
                    return message.content["text"]
            raise ValueError("Unable to extract text from Claude API response")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}") from e


class DeepseekClient:
    """Handles communication with the Deepseek API via direct HTTP requests."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    def generate_filename(self, content: str, image_b64: Optional[str] = None) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
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
            response = requests.post(
                self.base_url, headers=headers, json=data, timeout=30
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise RuntimeError(f"Deepseek API request error: {str(e)}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Deepseek API response parsing error: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Deepseek API error: {str(e)}") from e


# -----------------------------
# Core Logic and File Operations
# -----------------------------


def get_api_details(provider: str, model: str):
    """Gets the API key from environment variables or prompts the user for it."""
    if provider not in AI_PROVIDERS:
        available_providers = ", ".join(AI_PROVIDERS.keys())
        raise ValueError(
            f"Unsupported provider '{provider}'. Available providers: {available_providers}"
        )

    env_var_name = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    if not api_key:
        api_key = input(f"Please enter your {provider.capitalize()} API key: ").strip()
        if not api_key:
            raise ValueError(f"{provider.capitalize()} API key is required.")

    if model not in AI_PROVIDERS.get(provider, []):
        available_models = ", ".join(
            AI_PROVIDERS.get(provider, ["No models available"])
        )
        raise ValueError(
            f"Invalid model '{model}' for provider '{provider}'. Available models: {available_models}"
        )

    return api_key


def sort_and_rename_pdfs(
    input_dir,
    corrupted_dir,
    renamed_dir,
    provider="openai",
    model=None,
    reset_progress: bool = False,
    ocr_lang: str = "eng",
):
    """The main function that orchestrates the PDF processing workflow."""
    if not os.path.exists(input_dir):
        print(f"Error: Input folder '{input_dir}' does not exist.")
        return False

    if model is None:
        model = DEFAULT_MODELS.get(provider, AI_PROVIDERS[provider][0])

    try:
        api_key = get_api_details(provider, model)
        ai_client = AIClient.create(provider, model, api_key)
    except (ValueError, ImportError) as e:
        print(f"Error setting up AI client: {e}")
        return False

    os.makedirs(corrupted_dir, exist_ok=True)
    os.makedirs(renamed_dir, exist_ok=True)

    pdf_files = []
    for f in os.listdir(input_dir):
        # Skip any files that are not PDFs, are hidden, or are system files.
        if not f.lower().endswith(".pdf") or f.startswith(".") or f.startswith("._"):
            continue
        full_path = os.path.join(input_dir, f)
        if not os.path.isfile(full_path):
            continue
        pdf_files.append(f)

    total_files = len(pdf_files)
    if total_files == 0:
        print(f"No PDF files found in {input_dir}")
        return True

    progress_file = os.path.join(renamed_dir, ".progress")
    processed_files = load_progress(progress_file, input_dir, reset_progress)

    try:
        with open(progress_file, "a", encoding="utf-8") as progress_f, tqdm(
            total=total_files, desc="Processing PDFs", unit="file"
        ) as pbar:
            for filename in pdf_files:
                if filename in processed_files:
                    pbar.update(1)
                    continue

                input_path = os.path.normpath(os.path.join(input_dir, filename))
                if not os.path.exists(input_path):
                    print(f"\nWarning: File {filename} no longer exists, skipping.")
                    pbar.update(1)
                    continue

                process_pdf(
                    input_path,
                    filename,
                    corrupted_dir,
                    renamed_dir,
                    pbar,
                    progress_f,
                    ocr_lang,
                    ai_client,
                )
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Progress has been saved.")
    except IOError as e:
        print(f"\nError writing to progress file: {e}")
        return False

    return True


def load_progress(
    progress_file: str, input_dir: str, reset_progress: bool = False
) -> set:
    """Loads the set of processed files from the progress file."""
    if reset_progress and os.path.exists(progress_file):
        try:
            os.remove(progress_file)
            print("Resetting progress: existing .progress file removed.")
        except OSError as e:
            print(f"Warning: Could not delete progress file: {e}")

    processed_files = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                processed_files = {line.strip() for line in f}
            # Make sure we only skip files that have actually been moved out of the input folder.
            processed_files = {
                name
                for name in processed_files
                if not os.path.exists(os.path.join(input_dir, name))
            }
        except (IOError, OSError) as e:
            print(f"Warning: Could not read progress file: {e}")
    return processed_files


def safe_move(src: str, dst: str, attempts: int = 3, delay: float = 0.75) -> None:
    """A more reliable way to move files, with retries and a fallback to copy-then-delete."""
    last_err = None
    for i in range(attempts):
        try:
            shutil.move(src, dst)
            return
        except OSError as e:
            last_err = e
            time.sleep(delay * (i + 1))
    # If moving the file fails, try copying it and then deleting the original.
    shutil.copy2(src, dst)
    try:
        os.remove(src)
    except OSError as e:
        # If the delete fails, raise the error that caused the original move to fail.
        raise e if e else last_err
        raise e if e else last_err


def process_pdf(
    input_path,
    filename,
    corrupted_folder,
    renamed_folder,
    pbar,
    progress_f,
    ocr_lang: str,
    ai_client: Any,
):
    """Processes a single PDF: extracts content, gets a new name, and moves the file."""
    try:
        if not os.path.isfile(input_path):
            pass

        # Extract text and a potential image from the PDF.
        text, img_b64 = extract_text_and_image(input_path, ocr_lang=ocr_lang)

        # If the extractor returned an error message, treat it as a corrupted file.
        if text.startswith("Error"):
            raise PdfReadError(text)

        # If the PDF is empty (no text or image), give it a generic name.
        if not text and not img_b64:
            timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"empty_file_{timestamp}"
        else:
            # Get a new filename from the AI, with retries in case of network issues.
            new_file_name = get_new_filename_with_retry(ai_client, text, img_b64)
            new_file_name = validate_and_trim_filename(new_file_name)

        # Check if a file with the new name already exists and add a number if it does.
        new_file_name = handle_duplicate_filename(new_file_name, renamed_folder)

        # Move the file to the 'renamed' folder.
        new_filepath = os.path.join(renamed_folder, new_file_name + ".pdf")
        safe_move(input_path, new_filepath)
        pbar.set_postfix({"Status": "Renamed", "New Name": new_file_name})

        # Record that this file has been processed.
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
    except RuntimeError as e:
        error_msg = f"Unexpected error with file {filename}: {str(e)}"
        print(f"\n{error_msg}")
        try:
            with open(ERROR_LOG_FILE, mode="a", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\n")
        except (IOError, OSError) as log_error:
            print(f"Warning: Could not write to error log: {str(log_error)}")
        pbar.set_postfix({"Status": "Error", "Message": "Unexpected error"})

    pbar.update(1)


def get_new_filename_with_retry(
    ai_client: Any,
    pdf_content: str,
    image_b64: Optional[str] = None,
    max_retries: int = MAX_RETRIES,
) -> str:
    """Calls the AI to get a filename, and retries if it fails."""
    timeout_count = 0
    for attempt in range(max_retries):
        try:
            return get_filename_from_ai(ai_client, pdf_content, image_b64)
        except RuntimeError as e:
            error_str = str(e).lower()
            is_timeout = any(
                t in error_str
                for t in ["timeout", "timed out", "connection", "network"]
            )
            if is_timeout:
                timeout_count += 1
                wait_time = RETRY_DELAY * (
                    2**timeout_count
                )  # Use exponential backoff for network issues.
                print(
                    f"\nAPI timeout/network error: {str(e)}. Retrying in {wait_time} seconds..."
                )
            else:
                wait_time = RETRY_DELAY * (
                    attempt + 1
                )  # Use linear backoff for other errors.
                print(f"\nAPI error: {str(e)}. Retrying in {wait_time} seconds...")

            time.sleep(wait_time)

            if attempt == max_retries - 1:
                print(
                    f"\nFailed to get filename from API after {max_retries} attempts."
                )
                timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                if timeout_count > 0:
                    return f"network_error_{timestamp}"
                else:
                    return f"untitled_document_{timestamp}"


def get_filename_from_ai(
    ai_client: Any, pdf_content: str, image_b64: Optional[str] = None
) -> str:
    if ai_client is None:
        raise RuntimeError(
            "AI client not initialized. Call sort_and_rename_pdfs first."
        )
    return ai_client.generate_filename(pdf_content, image_b64)


def validate_and_trim_filename(initial_filename: str) -> str:
    if not initial_filename or initial_filename.isspace():
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        return f"empty_file_{timestamp}"

    # Normalize unicode characters to their closest ASCII equivalent.
    normalized = (
        unicodedata.normalize("NFKD", initial_filename)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    # Remove any characters that are not letters, numbers, or underscores.
    cleaned_filename = re.sub(r"[^a-zA-Z0-9_]", "", normalized)

    if not cleaned_filename:
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        return f"invalid_name_{timestamp}"

    return cleaned_filename[:160]


def handle_duplicate_filename(filename: str, folder: str) -> str:
    """If a file with the same name already exists, this adds a number to the end (e.g., file_1.pdf)."""
    base_filename = filename
    counter = 1
    while os.path.exists(os.path.join(folder, f"{filename}.pdf")):
        filename = f"{base_filename}_{counter}"
        counter += 1
    return filename


def pdfs_to_text_string(filepath: str, max_pages: Optional[int] = None) -> str:
    """A legacy function for extracting text, kept for compatibility. It uses the PyPDF2 method."""
    return _pypdf2_text(filepath, max_pages)


def truncate_content_to_token_limit(content: str, max_tokens: int) -> str:
    """Ensures the text sent to the AI does not exceed its maximum token limit."""
    try:
        token_count = len(ENCODING.encode(content))
        if token_count <= max_tokens:
            return content

        # For very long content, make a rough initial cut to speed up the process.
        if token_count > max_tokens * 2:
            bytes_per_token = len(content.encode("utf-8")) / token_count
            target_bytes = int(max_tokens * bytes_per_token * 0.9)
            content = content[:target_bytes]
            token_count = len(ENCODING.encode(content))

        # Fine-tune the truncation to get as close to the token limit as possible.
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
    except (ValueError, TypeError) as e:
        print(f"Warning: Error during content truncation: {str(e)}")
        return content[: int(max_tokens * 3)]


def list_available_models():
    """Prints a list of all AI models supported by the script, grouped by provider."""
    print("Available AI models by provider:")
    for provider, models in AI_PROVIDERS.items():
        print(f"\n{provider.capitalize()}:")
        for model in models:
            print(f"  - {model}")


def parse_arguments():
    """Sets up and parses the command-line arguments that the script accepts."""
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
""",
    )
    parser.add_argument("--input", "-i", help="Input folder containing PDF files")
    parser.add_argument("--corrupted", "-c", help="Folder for corrupted PDF files")
    parser.add_argument("--renamed", "-r", help="Folder for renamed PDF files")
    parser.add_argument(
        "--provider",
        "-p",
        help=f"AI provider (options: {', '.join(AI_PROVIDERS.keys())})",
        default="openai",
        choices=AI_PROVIDERS.keys(),
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Model to use for the selected provider (run with --list-models to see options)",
    )
    parser.add_argument("--api-key", "-k", help="API key for the selected provider")
    parser.add_argument(
        "--list-models",
        "-l",
        action="store_true",
        help="List all available models by provider and exit",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="Tesseract OCR language hint (e.g., 'eng', 'eng+ind')",
    )
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Ignore and delete existing .progress file before run",
    )
    return parser.parse_args()

def main():
    """Main function to parse arguments and run the PDF processing."""
    try:
        # This block runs when the script is executed directly from the command line.
        args = parse_arguments()
        # Set the OCR language from the command-line argument.
        _print_capabilities(args.ocr_lang)

        # If the user just wants to see the available models, print them and exit.
        if args.list_models:
            list_available_models()
            sys.exit(0)

        # Temporarily set the API key from the command line if provided.
        original_env = None
        api_key_set = False

        try:
            if args.api_key:
                env_var = f"{args.provider.upper()}_API_KEY"
                original_env = (env_var, os.environ.get(env_var))
                os.environ[env_var] = args.api_key
                api_key_set = True
                print(f"Using provided {args.provider.capitalize()} API key")

            # Get the folder paths from the arguments, or ask the user if not provided.
            input_dir = args.input or input("Enter the input folder path: ")
            corrupted_dir = args.corrupted or input(
                "Enter the corrupted PDFs folder path: "
            )
            renamed_dir = args.renamed or input("Enter the renamed PDFs folder path: ")

            # Start the main PDF processing task.
            success = sort_and_rename_pdfs(
                input_dir,
                corrupted_dir,
                renamed_dir,
                args.provider,
                args.model,
                reset_progress=args.reset_progress,
                ocr_lang=args.ocr_lang,
            )

            if not success:
                print("PDF sorting and renaming failed.")
                return 1
        finally:
            # Restore the original API key environment variable if it was changed.
            if api_key_set and original_env:
                try:
                    env_var, original_value = original_env
                    if original_value is None:
                        os.environ.pop(env_var, None)
                    else:
                        os.environ[env_var] = original_value
                except (KeyError, TypeError):
                    print("Warning: Could not restore original API key environment.")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        return 130  # Standard exit code for a process stopped with Ctrl+C.
    except (ValueError, ImportError) as e:
        print(f"\nConfiguration error: {e}")
        return 1
    except Exception as e:
        print(f"\nCritical error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())