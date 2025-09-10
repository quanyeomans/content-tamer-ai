"""BDD test helpers for file operations with pytest tmp_path integration."""

import os
import shutil
from pathlib import Path
from typing import Dict, Union

from tests.utils.pytest_file_utils import create_processing_directories


class BDDTestContext:
    """Context for BDD tests using pytest tmp_path fixtures."""

    def __init__(self, tmp_path: Union[Path, str] = None):
        """Initialize context with pytest tmp_path."""
        if tmp_path is None:
            # For backward compatibility - will be deprecated
            import tempfile
            tmp_path = tempfile.mkdtemp()
            self._legacy_mode = True
        else:
            self._legacy_mode = False
            
        if isinstance(tmp_path, str):
            tmp_path = Path(tmp_path)
            
        self.tmp_path = tmp_path
        self.temp_dir = str(tmp_path)  # For backward compatibility
        self.input_dir = None
        self.processed_dir = None
        self.unprocessed_dir = None
        self.test_files = []
        self.ai_mock_responses: Dict[str, str] = {}
        self.processing_result = None
        self.processing_error = None
        self.display_output = None
        self._directories_created = False

    def setup_directories(self):
        """Create clean test directories using pytest tmp_path."""
        if not self._directories_created:
            directories = create_processing_directories(self.tmp_path)
            self.input_dir = str(directories["input"])
            self.processed_dir = str(directories["processed"])
            self.unprocessed_dir = str(directories["unprocessed"])
            self._directories_created = True

    def cleanup_directories(self):
        """Clean up test directories (no-op with pytest tmp_path)."""
        # No manual cleanup needed - pytest tmp_path handles it
        if self._legacy_mode and self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_pdf_file(self, filename: str, content: str = "Test document content") -> str:
        """Create a realistic PDF file for testing by copying from fixtures."""
        if not self._directories_created:
            self.setup_directories()
            
        filepath = os.path.join(self.input_dir, filename)

        # Use real PDF from fixtures instead of fake PDF
        fixture_pdf = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "fixtures", "sample.pd"
        )

        if os.path.exists(fixture_pdf):
            shutil.copy2(fixture_pdf, filepath)
        else:
            # Fallback to minimal valid PDF if fixture not found
            # This creates a minimal but valid PDF that PyMuPDF can parse
            pdf_content = b"""%PDF-1.4
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
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000010 00000 n
0000000053 00000 n
0000000110 00000 n
0000000205 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
295
%%EOF"""
            with open(filepath, "wb") as f:
                f.write(pdf_content)

        self.test_files.append(filepath)
        return filepath

    def create_png_file(self, filename: str) -> str:
        """Create a realistic PNG file for testing."""
        if not self._directories_created:
            self.setup_directories()
            
        filepath = os.path.join(self.input_dir, filename)
        # Simple PNG file header + minimal data
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$\x00\x00\x00\nIDAT\x08\x1dc\xf8\x00\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
        with open(filepath, "wb") as f:
            f.write(png_content)
        self.test_files.append(filepath)
        return filepath

    def create_txt_file(self, filename: str, content: str = "Plain text content") -> str:
        """Create a text file for testing."""
        if not self._directories_created:
            self.setup_directories()
            
        filepath = os.path.join(self.input_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        self.test_files.append(filepath)
        return filepath

    def create_corrupted_file(self, filename: str) -> str:
        """Create a corrupted file that will fail processing."""
        if not self._directories_created:
            self.setup_directories()
            
        filepath = os.path.join(self.input_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b"corrupted file content that will fail processing")
        self.test_files.append(filepath)
        return filepath

    def set_ai_mock_response(self, filename: str, response: str):
        """Set the AI mock response for a specific file."""
        self.ai_mock_responses[filename] = response

    def get_ai_mock_response(self, content: str, filename_hint: str = "") -> str:
        """Get AI mock response based on content or filename hint."""
        # Try to find response by filename hint first
        for filename, response in self.ai_mock_responses.items():
            if filename_hint and filename in filename_hint:
                return response

        # Default AI response pattern
        base_name = (
            filename_hint.replace(".pd", "").replace(".png", "").replace(".txt", "")
            if filename_hint
            else "document"
        )
        return f"ai_generated_{base_name}"

    def lock_file_temporarily(self, filepath: str):
        """Mock a file being temporarily locked (for retry scenarios)."""
        # In real implementation, this would involve OS-level file locking
        # For BDD tests, we'll simulate this behavior in step definitions
        pass

    # New methods for pytest tmp_path integration
    def get_path(self, directory: str) -> Path:
        """Get pathlib.Path for a directory."""
        if not self._directories_created:
            self.setup_directories()
            
        if directory == "input":
            return Path(self.input_dir)
        elif directory == "processed":
            return Path(self.processed_dir)
        elif directory == "unprocessed":
            return Path(self.unprocessed_dir)
        elif directory == "temp":
            return self.tmp_path
        else:
            return self.tmp_path / directory

    def create_file_with_path(self, path: Union[Path, str], content: Union[str, bytes]) -> str:
        """Create file using pathlib.Path API."""
        if isinstance(path, str):
            path = Path(path)
            
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
            
        filepath = str(path)
        if filepath not in self.test_files:
            self.test_files.append(filepath)
        return filepath


def create_test_context(tmp_path: Union[Path, str] = None) -> BDDTestContext:
    """Create a new BDD test context with pytest tmp_path integration."""
    return BDDTestContext(tmp_path)


# Backward compatibility function
def create_legacy_test_context() -> BDDTestContext:
    """Create a legacy BDD test context without tmp_path (deprecated)."""
    return BDDTestContext()