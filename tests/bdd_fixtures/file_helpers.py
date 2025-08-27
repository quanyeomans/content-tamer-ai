"""BDD test helpers for file operations with minimal mocking."""

import os
import shutil
import tempfile
from typing import Any, Dict, List
from unittest.mock import Mock, patch


class BDDTestContext:
    """Context object for BDD tests with real file operations."""

    def __init__(self):
        self.temp_dir = None
        self.input_dir = None
        self.processed_dir = None
        self.unprocessed_dir = None
        self.test_files: List[str] = []
        self.processing_result = None
        self.display_output = None
        self.ai_mock_responses: Dict[str, str] = {}

    def setup_directories(self):
        """Create clean test directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.processed_dir = os.path.join(self.temp_dir, "processed")
        self.unprocessed_dir = os.path.join(self.temp_dir, "unprocessed")

        for directory in [self.input_dir, self.processed_dir, self.unprocessed_dir]:
            os.makedirs(directory)

    def cleanup_directories(self):
        """Clean up test directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_pdf_file(
        self, filename: str, content: str = "Test document content"
    ) -> str:
        """Create a realistic PDF file for testing."""
        filepath = os.path.join(self.input_dir, filename)
        pdf_content = f"%PDF-1.4\n{content}\n%EOF"
        with open(filepath, "wb") as f:
            f.write(pdf_content.encode("utf-8"))
        self.test_files.append(filepath)
        return filepath

    def create_png_file(self, filename: str) -> str:
        """Create a realistic PNG file for testing."""
        filepath = os.path.join(self.input_dir, filename)
        # Simple PNG file header + minimal data
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$\x00\x00\x00\nIDAT\x08\x1dc\xf8\x00\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
        with open(filepath, "wb") as f:
            f.write(png_content)
        self.test_files.append(filepath)
        return filepath

    def create_txt_file(
        self, filename: str, content: str = "Plain text content"
    ) -> str:
        """Create a text file for testing."""
        filepath = os.path.join(self.input_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        self.test_files.append(filepath)
        return filepath

    def create_corrupted_file(self, filename: str) -> str:
        """Create a corrupted file that will fail processing."""
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
            filename_hint.replace(".pdf", "").replace(".png", "").replace(".txt", "")
            if filename_hint
            else "document"
        )
        return f"ai_generated_{base_name}"

    def lock_file_temporarily(self, filepath: str):
        """Mock a file being temporarily locked (for retry scenarios)."""
        # In real implementation, this would involve OS-level file locking
        # For BDD tests, we'll simulate this behavior in step definitions
        pass


def create_test_context() -> BDDTestContext:
    """Create a new BDD test context with clean state."""
    return BDDTestContext()
