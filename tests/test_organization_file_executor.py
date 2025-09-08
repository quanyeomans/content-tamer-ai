#!/usr/bin/env python3
"""
Component Tests for OrganizationFileExecutor

Tests the file execution component that handles physical file operations
for post-processing organization according to TDD principles.
"""

import unittest
import os
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from organization.file_executor import OrganizationFileExecutor
from tests.utils.rich_test_utils import RichTestCase


class TestOrganizationFileExecutorDefaults(unittest.TestCase):
    """Test default behavior and initialization."""
    
    def test_executor_initialization_with_target_folder(self):
        """Test executor initializes correctly with target folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = OrganizationFileExecutor(temp_dir)
            self.assertEqual(executor.target_folder, temp_dir)
            self.assertIsNotNone(executor.file_manager)

    def test_executor_initialization_creates_file_manager(self):
        """Test executor creates FileManager instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = OrganizationFileExecutor(temp_dir)
            # Verify FileManager is properly initialized
            self.assertTrue(hasattr(executor.file_manager, 'safe_move'))


class TestOrganizationFileExecutorValidation(unittest.TestCase):
    """Test plan validation functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = OrganizationFileExecutor(self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass  # Ignore cleanup errors in tests

    def test_validate_organization_plan_with_valid_plan(self):
        """Test validation passes for valid organization plan."""
        # Create test files
        test_file1 = os.path.join(self.temp_dir, "test1.pdf")
        with open(test_file1, 'w') as f:
            f.write("test content")

        valid_plan = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': [{
                    'filename': 'test1.pdf',
                    'current_path': test_file1,
                    'target_folder': 'Documents',
                    'category': 'documents'
                }]
            }
        }
        
        result = self.executor.validate_organization_plan(valid_plan)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['issues']), 0)

    def test_validate_organization_plan_with_failed_plan(self):
        """Test validation fails for failed organization plan."""
        invalid_plan = {
            'success': False,
            'error': 'Organization failed'
        }
        
        result = self.executor.validate_organization_plan(invalid_plan)
        self.assertFalse(result['valid'])
        self.assertIn('Organization plan failed to generate', result['issues'])

    def test_validate_organization_plan_with_missing_files(self):
        """Test validation warns about missing source files."""
        plan_with_missing_files = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': [{
                    'filename': 'missing.pdf',
                    'current_path': '/nonexistent/missing.pdf',
                    'target_folder': 'Documents',
                    'category': 'documents'
                }]
            }
        }
        
        result = self.executor.validate_organization_plan(plan_with_missing_files)
        self.assertTrue(result['valid'])  # Still valid, just warnings
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn('missing.pdf', str(result['warnings']))


class TestOrganizationFileExecutorFolderCreation(unittest.TestCase):
    """Test folder structure creation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = OrganizationFileExecutor(self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_create_folder_structure_single_level(self):
        """Test creation of single-level folder structure."""
        organization_structure = {
            'folders': {
                'Documents': {'type': 'category'},
                'Images': {'type': 'category'}
            }
        }
        
        result = self.executor._create_folder_structure(organization_structure)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['folders_created']), 2)
        self.assertIn('Documents', result['folders_created'])
        self.assertIn('Images', result['folders_created'])
        
        # Verify folders actually exist
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Documents')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Images')))

    def test_create_folder_structure_with_subfolders(self):
        """Test creation of nested folder structure."""
        organization_structure = {
            'folders': {
                'Documents': {
                    'type': 'category',
                    'subfolders': {
                        '2024': {'type': 'time'},
                        '2023': {'type': 'time'}
                    }
                }
            }
        }
        
        result = self.executor._create_folder_structure(organization_structure)
        
        self.assertTrue(result['success'])
        self.assertIn('Documents', result['folders_created'])
        self.assertIn('Documents/2024', result['folders_created'])
        self.assertIn('Documents/2023', result['folders_created'])
        
        # Verify nested folders exist
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Documents', '2024')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Documents', '2023')))


class TestOrganizationFileExecutorFileMovement(unittest.TestCase):
    """Test file movement operations."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = OrganizationFileExecutor(self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_move_single_file_success(self):
        """Test successful single file move."""
        # Create source file
        source_file = os.path.join(self.temp_dir, "test_doc.pdf")
        with open(source_file, 'w') as f:
            f.write("test content")
        
        # Execute move
        result = self.executor._move_single_file(
            current_path=source_file,
            target_folder="Documents",
            filename="test_doc.pdf",
            category="documents"
        )
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['filename'], "test_doc.pdf")
        self.assertEqual(result['target_folder'], "Documents")
        self.assertEqual(result['category'], "documents")
        
        # Verify file was actually moved
        target_path = os.path.join(self.temp_dir, "Documents", "test_doc.pdf")
        self.assertTrue(os.path.exists(target_path))
        self.assertFalse(os.path.exists(source_file))

    def test_move_single_file_with_collision_handling(self):
        """Test file move with filename collision resolution."""
        # Create source files
        source_file1 = os.path.join(self.temp_dir, "document.pdf")
        source_file2 = os.path.join(self.temp_dir, "document_copy.pdf")
        
        with open(source_file1, 'w') as f:
            f.write("content 1")
        with open(source_file2, 'w') as f:
            f.write("content 2")
        
        # Create target directory and existing file
        target_dir = os.path.join(self.temp_dir, "Documents")
        os.makedirs(target_dir)
        existing_file = os.path.join(target_dir, "document.pdf")
        with open(existing_file, 'w') as f:
            f.write("existing content")
        
        # Move second file (should handle collision)
        result = self.executor._move_single_file(
            current_path=source_file2,
            target_folder="Documents",
            filename="document.pdf",  # Same name as existing
            category="documents"
        )
        
        # Verify collision was handled
        self.assertTrue(result['success'])
        self.assertNotEqual(result['final_filename'], "document.pdf")  # Should be renamed
        self.assertIn("document", result['final_filename'])  # Should contain base name
        
        # Verify both files exist
        self.assertTrue(os.path.exists(existing_file))  # Original unchanged
        self.assertTrue(os.path.exists(os.path.join(target_dir, result['final_filename'])))

    def test_move_single_file_missing_source(self):
        """Test file move with missing source file."""
        result = self.executor._move_single_file(
            current_path="/nonexistent/file.pdf",
            target_folder="Documents",
            filename="file.pdf",
            category="documents"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('does not exist', result['error'])

    def test_execute_file_moves_batch(self):
        """Test batch file movement execution."""
        # Create multiple source files
        source_files = []
        file_assignments = []
        
        for i in range(3):
            filename = f"doc_{i}.pdf"
            source_path = os.path.join(self.temp_dir, filename)
            with open(source_path, 'w') as f:
                f.write(f"content {i}")
            source_files.append(source_path)
            
            file_assignments.append({
                'filename': filename,
                'current_path': source_path,
                'target_folder': 'Documents',
                'category': 'documents'
            })
        
        # Execute batch move
        result = self.executor._execute_file_moves(file_assignments)
        
        # Verify all moves succeeded
        self.assertEqual(result['successful_moves'], 3)
        self.assertEqual(result['failed_moves'], 0)
        self.assertEqual(result['total_moves'], 3)
        self.assertEqual(len(result['move_details']), 3)
        
        # Verify files were moved
        for i in range(3):
            target_path = os.path.join(self.temp_dir, "Documents", f"doc_{i}.pdf")
            self.assertTrue(os.path.exists(target_path))
            self.assertFalse(os.path.exists(source_files[i]))


class TestOrganizationFileExecutorEndToEnd(unittest.TestCase):
    """Test complete organization plan execution."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = OrganizationFileExecutor(self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_execute_complete_organization_plan(self):
        """Test execution of complete organization plan."""
        # Create test files
        test_files = []
        file_assignments = []
        
        file_data = [
            ("invoice_2024.pdf", "Invoices", "invoices"),
            ("contract_legal.pdf", "Legal", "contracts"),
            ("receipt_office.pdf", "Invoices", "invoices")
        ]
        
        for filename, target_folder, category in file_data:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"Content for {filename}")
            
            file_assignments.append({
                'filename': filename,
                'current_path': file_path,
                'target_folder': target_folder,
                'category': category
            })
        
        # Create organization plan
        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {
                    'Invoices': {'type': 'category'},
                    'Legal': {'type': 'category'}
                },
                'file_assignments': file_assignments
            }
        }
        
        # Execute plan
        result = self.executor.execute_organization_plan(organization_plan)
        
        # Verify execution success
        self.assertTrue(result['success'])
        self.assertEqual(result['files_moved'], 3)
        self.assertEqual(result['files_failed'], 0)
        self.assertEqual(result['total_files'], 3)
        self.assertEqual(len(result['folders_created']), 2)
        
        # Verify folder structure
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Invoices')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Legal')))
        
        # Verify files are in correct locations
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Invoices', 'invoice_2024.pdf')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Invoices', 'receipt_office.pdf')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Legal', 'contract_legal.pdf')))
        
        # Verify execution summary
        summary = result['execution_summary']
        self.assertEqual(summary['total_files_processed'], 3)
        self.assertEqual(summary['files_successfully_moved'], 3)
        self.assertEqual(summary['files_failed_to_move'], 0)
        self.assertEqual(summary['success_rate'], 1.0)
        self.assertTrue(summary['overall_success'])

    def test_execute_organization_plan_with_failures(self):
        """Test execution handles partial failures gracefully."""
        file_assignments = [
            {
                'filename': 'existing.pdf',
                'current_path': os.path.join(self.temp_dir, 'existing.pdf'),
                'target_folder': 'Documents',
                'category': 'documents'
            },
            {
                'filename': 'missing.pdf',
                'current_path': '/nonexistent/missing.pdf',  # Will fail
                'target_folder': 'Documents', 
                'category': 'documents'
            }
        ]
        
        # Create only one of the files
        with open(file_assignments[0]['current_path'], 'w') as f:
            f.write("content")
        
        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': file_assignments
            }
        }
        
        # Execute plan
        result = self.executor.execute_organization_plan(organization_plan)
        
        # Verify partial success
        self.assertTrue(result['success'])  # Still considered success if some files moved
        self.assertEqual(result['files_moved'], 1)
        self.assertEqual(result['files_failed'], 1)
        self.assertEqual(result['total_files'], 2)
        self.assertIn('warnings', result)
        
        # Verify successful file was moved
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'Documents', 'existing.pdf')))


class TestOrganizationFileExecutorUtilities(unittest.TestCase):
    """Test utility functions and edge cases."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = OrganizationFileExecutor(self.temp_dir)
        
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_get_current_organization_state_empty_folder(self):
        """Test organization state detection in empty folder."""
        result = self.executor.get_current_organization_state()
        
        self.assertFalse(result['organized'])
        self.assertEqual(len(result['organized_folders']), 0)
        self.assertEqual(result['files_in_root'], 0)

    def test_get_current_organization_state_with_organization(self):
        """Test organization state detection with existing structure."""
        # Create organized structure
        os.makedirs(os.path.join(self.temp_dir, 'Documents'))
        os.makedirs(os.path.join(self.temp_dir, 'Images'))
        
        # Add some files
        with open(os.path.join(self.temp_dir, 'Documents', 'test.pdf'), 'w') as f:
            f.write("content")
        with open(os.path.join(self.temp_dir, 'root_file.txt'), 'w') as f:
            f.write("root content")
        
        result = self.executor.get_current_organization_state()
        
        self.assertTrue(result['organized'])
        self.assertEqual(result['total_organized_folders'], 2)
        self.assertEqual(result['files_in_root'], 1)
        
        # Check folder details
        folder_names = [folder['name'] for folder in result['organized_folders']]
        self.assertIn('Documents', folder_names)
        self.assertIn('Images', folder_names)

    def test_execute_organization_plan_empty_assignments(self):
        """Test execution with empty file assignments."""
        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {},
                'file_assignments': []
            }
        }
        
        result = self.executor.execute_organization_plan(organization_plan)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['files_moved'], 0)
        self.assertEqual(result['reason'], 'No files to organize')


if __name__ == '__main__':
    unittest.main(verbosity=2)