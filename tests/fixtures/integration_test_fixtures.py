"""
Centralized Integration Test Fixtures and Data Management

Provides consistent test data, directory structures, and mock configurations
for high-quality integration testing across components.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional
from unittest.mock import MagicMock, Mock
from dataclasses import dataclass


@dataclass
class TestFileData:
    """Standard test file configuration."""
    filename: str
    content: bytes
    expected_content: str
    file_type: str


@dataclass
class IntegrationTestEnvironment:
    """Complete test environment with directories and files."""
    temp_dir: str
    input_dir: str
    processed_dir: str
    unprocessed_dir: str
    test_files: List[TestFileData]
    
    def cleanup(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class IntegrationTestDataFactory:
    """Factory for creating standardized integration test data."""
    
    # Standard test file data
    STANDARD_TEST_FILES = [
        TestFileData(
            filename="financial_report.pdf",
            content=b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/Contents 4 0 R>>endobj\n4 0 obj<</Length 44>>stream\nBT\n/F1 12 Tf\n100 700 Td\n(Q4 Financial Report 2024) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000174 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n267\n%%EOF",
            expected_content="Q4 Financial Report 2024",
            file_type="pdf"
        ),
        TestFileData(
            filename="meeting_notes.txt", 
            content=b"Team meeting notes from March 15, 2024\n\nAgenda:\n1. Project status update\n2. Budget review\n3. Next quarter planning\n\nAction items:\n- Complete Q1 report by March 30\n- Schedule Q2 planning session",
            expected_content="Team meeting notes from March 15, 2024\n\nAgenda:\n1. Project status update\n2. Budget review\n3. Next quarter planning\n\nAction items:\n- Complete Q1 report by March 30\n- Schedule Q2 planning session",
            file_type="txt"
        ),
        TestFileData(
            filename="invoice_scan.png",
            content=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x1diTXtComment\x00\x00\x00\x00\x00Created with sample data\x18\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82",
            expected_content="Invoice #12345 - Company ABC - $1,250.00 - Due: 2024-03-30",
            file_type="png"
        )
    ]
    
    def create_test_environment(self, include_files: bool = True) -> IntegrationTestEnvironment:
        """Create complete integration test environment."""
        temp_dir = tempfile.mkdtemp(prefix="integration_test_")
        
        # Create directory structure
        input_dir = os.path.join(temp_dir, "input")
        processed_dir = os.path.join(temp_dir, "processed") 
        unprocessed_dir = os.path.join(processed_dir, "unprocessed")
        
        for dir_path in [input_dir, processed_dir, unprocessed_dir]:
            os.makedirs(dir_path, exist_ok=True)
            
        test_files = []
        if include_files:
            # Create test files
            for file_data in self.STANDARD_TEST_FILES:
                file_path = os.path.join(input_dir, file_data.filename)
                with open(file_path, "wb") as f:
                    f.write(file_data.content)
                test_files.append(file_data)
        
        return IntegrationTestEnvironment(
            temp_dir=temp_dir,
            input_dir=input_dir,
            processed_dir=processed_dir,
            unprocessed_dir=unprocessed_dir,
            test_files=test_files
        )
        
    def create_large_test_environment(self, file_count: int = 20) -> IntegrationTestEnvironment:
        """Create test environment with many files for performance testing."""
        env = self.create_test_environment(include_files=False)
        
        # Create many test files for performance testing
        test_files = []
        for i in range(file_count):
            file_data = TestFileData(
                filename=f"test_document_{i:03d}.pdf",
                content=f"%PDF-1.4\nTest document {i} content\n%EOF".encode(),
                expected_content=f"Test document {i} content",
                file_type="pdf"
            )
            
            file_path = os.path.join(env.input_dir, file_data.filename)
            with open(file_path, "wb") as f:
                f.write(file_data.content)
            test_files.append(file_data)
            
        env.test_files = test_files
        return env


class IntegrationMockFactory:
    """Factory for creating standardized mocks for integration testing."""
    
    @staticmethod
    def create_minimal_ai_mock(success_rate: float = 1.0) -> Mock:
        """Create AI client mock with configurable success rate."""
        mock_ai = Mock()
        
        def generate_filename_with_failure(content):
            """AI mock that sometimes fails based on success_rate."""
            import random
            if random.random() <= success_rate:
                # Success case - generate reasonable filename
                if "financial" in content.lower():
                    return "q4_financial_report_2024"
                elif "meeting" in content.lower():
                    return "team_meeting_notes_march_2024"
                elif "invoice" in content.lower():
                    return "invoice_12345_company_abc_march_2024"
                else:
                    return "ai_generated_document_name"
            else:
                # Failure case
                raise Exception("AI service temporarily unavailable")
        
        mock_ai.generate_filename.side_effect = generate_filename_with_failure
        return mock_ai
    
    @staticmethod
    def create_content_processor_mock(extraction_success_rate: float = 1.0) -> Mock:
        """Create content processor mock with configurable extraction success."""
        mock_processor = Mock()
        
        def extract_with_failure(file_path):
            """Content extraction that sometimes fails."""
            import random
            if random.random() <= extraction_success_rate:
                # Success case - return expected content based on filename
                filename = os.path.basename(file_path).lower()
                if "financial" in filename:
                    return ("Q4 Financial Report 2024", None)
                elif "meeting" in filename:
                    return ("Team meeting notes from March 15, 2024", None)
                elif "invoice" in filename:
                    return ("Invoice #12345 - Company ABC - $1,250.00", None)
                else:
                    return ("Generic document content", None)
            else:
                # Failure case
                return ("", "Content extraction failed")
        
        mock_processor.extract_content.side_effect = extract_with_failure
        mock_processor.can_process.return_value = True
        return mock_processor
    
    @staticmethod 
    def create_realistic_file_organizer_mock() -> Mock:
        """Create file organizer mock that performs real file operations."""
        mock_organizer = Mock()
        
        def realistic_move_file(input_path, filename, target_dir, new_name, extension):
            """Actually move files for realistic integration testing."""
            if os.path.exists(input_path):
                target_path = os.path.join(target_dir, new_name + extension)
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(input_path, target_path)
                return new_name
            else:
                raise FileNotFoundError(f"Source file not found: {input_path}")
        
        mock_organizer.move_file_to_category.side_effect = realistic_move_file
        mock_organizer.filename_handler.validate_and_trim_filename.side_effect = lambda x: x[:160]  # Realistic trimming
        mock_organizer.progress_tracker.record_progress.return_value = None
        mock_organizer.progress_tracker.load_progress.return_value = set()
        
        return mock_organizer


class PerformanceTestFixtures:
    """Fixtures for performance regression testing."""
    
    @staticmethod
    def create_performance_baseline() -> Dict[str, float]:
        """Define performance baselines for regression testing."""
        return {
            "single_file_processing_max_seconds": 2.0,
            "batch_10_files_max_seconds": 15.0,
            "memory_usage_max_mb": 100.0,
            "ai_call_timeout_seconds": 30.0,
        }
    
    @staticmethod
    def create_stress_test_data(file_count: int = 100) -> List[TestFileData]:
        """Create large dataset for stress testing."""
        stress_files = []
        for i in range(file_count):
            # Create files of varying sizes
            content_size = min(1000 + (i * 50), 10000)  # 1KB to 10KB range
            content = f"Large test document {i}\n" + ("Sample content line.\n" * (content_size // 20))
            
            stress_files.append(TestFileData(
                filename=f"stress_test_{i:04d}.txt",
                content=content.encode(),
                expected_content=content[:100] + "...",  # Truncated for testing
                file_type="txt"
            ))
        
        return stress_files


class FailureScenarioFixtures:
    """Fixtures for testing failure propagation across components."""
    
    @staticmethod
    def create_ai_failure_scenario():
        """Create scenario where AI consistently fails."""
        return IntegrationMockFactory.create_minimal_ai_mock(success_rate=0.0)
    
    @staticmethod
    def create_content_extraction_failure_scenario():
        """Create scenario where content extraction fails."""
        return IntegrationMockFactory.create_content_processor_mock(extraction_success_rate=0.0)
    
    @staticmethod
    def create_file_system_failure_scenario(temp_dir: str):
        """Create scenario where file operations fail (permissions, disk full, etc)."""
        # Make directory read-only to simulate permission failures
        os.chmod(temp_dir, 0o444)
        return temp_dir
    
    @staticmethod
    def create_intermittent_failure_scenario():
        """Create scenario with intermittent failures (50% success rate)."""
        return {
            'ai_mock': IntegrationMockFactory.create_minimal_ai_mock(success_rate=0.5),
            'content_mock': IntegrationMockFactory.create_content_processor_mock(extraction_success_rate=0.5)
        }


# Convenience factory instance
integration_fixtures = IntegrationTestDataFactory()
performance_fixtures = PerformanceTestFixtures()
failure_fixtures = FailureScenarioFixtures()