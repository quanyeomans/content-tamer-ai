"""
Organization Execution Contracts
================================

CONTRACT AGREEMENTS TESTED:
1. Files are physically moved according to organization plan
2. Target folder structure is created as specified
3. File collision handling preserves all files safely
4. Execution provides accurate success/failure reporting
5. Partial failures are handled gracefully without data loss
"""

import os
import sys
import unittest
import tempfile

import pytest

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from shared.file_operations.file_organizer import FileOrganizer
from tests.utils.rich_test_utils import RichTestCase

class TestOrganizationExecutionContracts(unittest.TestCase, RichTestCase):
    """Contracts ensuring reliable organization execution behavior."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)
        self.temp_dir = tempfile.mkdtemp()
        self.executor = OrganizationFileExecutor(self.temp_dir)

    def tearDown(self):
        """Clean up Rich testing environment and temp files."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass
        RichTestCase.tearDown(self)

    @pytest.mark.contract
    @pytest.mark.critical
    def test_physical_file_movement_contract(self):
        """CONTRACT: Files must be physically moved to target locations according to plan."""
        # Create source files
        source_files = []
        for i in range(3):
            filename = f"test_doc_{i}.pdf"
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Test content {i}")
            source_files.append(file_path)

        # Create organization plan
        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': [
                    {
                        'filename': f'test_doc_{i}.pdf',
                        'current_path': source_files[i],
                        'target_folder': 'Documents',
                        'category': 'documents'
                    } for i in range(3)
                ]
            }
        }

        # Execute organization
        result = self.executor.execute_organization_plan(organization_plan)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Contract: All files must be physically moved
        self.assertTrue(result['success'])
        self.assertEqual(result['files_moved'], 3)
        self.assertEqual(result['files_failed'], 0)

        # Contract: Files must exist in target locations
        for i in range(3):
            target_path = os.path.join(self.temp_dir, 'Documents', 'test_doc_{i}.pdf')
            self.assertTrue(os.path.exists(target_path),
                           "File test_doc_{i}.pdf not found in target location")

            # Contract: Files must be removed from source locations
            self.assertFalse(os.path.exists(source_files[i]),
                           "File test_doc_{i}.pdf still exists in source location")

    @pytest.mark.contract
    @pytest.mark.critical
    def test_folder_structure_creation_contract(self):
        """CONTRACT: Target folder structure must be created exactly as specified in plan."""
        # Create complex organization plan with nested structure
        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {
                    'Documents': {
                        'type': 'category',
                        'subfolders': {
                            '2024': {'type': 'time'},
                            '2023': {'type': 'time'}
                        }
                    },
                    'Images': {'type': 'category'},
                    'Archives': {
                        'type': 'category',
                        'subfolders': {
                            'Legal': {'type': 'subcategory'}
                        }
                    }
                },
                'file_assignments': []  # No files, just testing structure creation
            }
        }

        # Execute organization
        result = self.executor.execute_organization_plan(organization_plan)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Contract: All specified folders must be created
        expected_folders = [
            'Documents',
            'Images',
            'Archives',
            'Documents/2024',
            'Documents/2023',
            'Archives/Legal'
        ]

        for folder in expected_folders:
            folder_path = os.path.join(self.temp_dir, folder)
            self.assertTrue(os.path.exists(folder_path),
                           "Expected folder not created: {folder}")

        # Contract: Execution must report successful folder creation
        self.assertTrue(result['success'])
        self.assertEqual(result['files_moved'], 0)  # No files to move
        self.assertGreater(len(result['folders_created']), 0)

    @pytest.mark.contract
    @pytest.mark.critical
    def test_file_collision_safety_contract(self):
        """CONTRACT: File collisions must be handled safely without data loss."""
        # Create source file
        source_file = os.path.join(self.temp_dir, "document.pd")
        with open(source_file, 'w') as f:
            f.write("New document content")

        # Create existing file in target location
        target_dir = os.path.join(self.temp_dir, "Documents")
        os.makedirs(target_dir)
        existing_file = os.path.join(target_dir, "document.pd")
        with open(existing_file, 'w') as f:
            f.write("Existing document content")

        # Create organization plan that will cause collision
        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': [{
                    'filename': 'document.pdf',
                    'current_path': source_file,
                    'target_folder': 'Documents',
                    'category': 'documents'
                }]
            }
        }

        # Execute organization
        result = self.executor.execute_organization_plan(organization_plan)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Contract: Collision must be handled successfully
        self.assertTrue(result['success'])
        self.assertEqual(result['files_moved'], 1)
        self.assertEqual(result['files_failed'], 0)

        # Contract: Both files must exist (no data loss)
        self.assertTrue(os.path.exists(existing_file),
                       "Original file was lost during collision handling")

        # Contract: New file must exist with different name
        moved_file_name = result['move_details'][0]['final_filename']
        moved_file_path = os.path.join(target_dir, moved_file_name)
        self.assertTrue(os.path.exists(moved_file_path),
                       "Moved file not found at {moved_file_path}")
        self.assertNotEqual(moved_file_name, "document.pd",
                           "Collision not handled - filename not changed")

        # Contract: Contents must be preserved correctly
        with open(existing_file, 'r') as f:
            existing_content = f.read()
        with open(moved_file_path, 'r') as f:
            moved_content = f.read()

        self.assertEqual(existing_content, "Existing document content")
        self.assertEqual(moved_content, "New document content")

    @pytest.mark.contract
    @pytest.mark.critical
    def test_execution_reporting_accuracy_contract(self):
        """CONTRACT: Execution results must accurately report success/failure statistics."""
        # Create mix of valid and invalid file assignments
        valid_file = os.path.join(self.temp_dir, "valid.pd")
        with open(valid_file, 'w') as f:
            f.write("valid content")

        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': [
                    {
                        'filename': 'valid.pdf',
                        'current_path': valid_file,
                        'target_folder': 'Documents',
                        'category': 'documents'
                    },
                    {
                        'filename': 'invalid.pdf',
                        'current_path': '/nonexistent/invalid.pdf',  # Will fail
                        'target_folder': 'Documents',
                        'category': 'documents'
                    }
                ]
            }
        }

        # Execute organization
        result = self.executor.execute_organization_plan(organization_plan)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Contract: Statistics must be accurate
        self.assertEqual(result['files_moved'], 1)
        self.assertEqual(result['files_failed'], 1)
        self.assertEqual(result['total_files'], 2)

        # Contract: Success rate must be calculated correctly
        execution_summary = result['execution_summary']
        self.assertEqual(execution_summary['files_successfully_moved'], 1)
        self.assertEqual(execution_summary['files_failed_to_move'], 1)
        self.assertEqual(execution_summary['success_rate'], 0.5)  # 1/2 = 50%

        # Contract: Move details must contain accurate information
        self.assertEqual(len(result['move_details']), 2)

        successful_moves = [detail for detail in result['move_details'] if detail['success']]
        failed_moves = [detail for detail in result['move_details'] if not detail['success']]

        self.assertEqual(len(successful_moves), 1)
        self.assertEqual(len(failed_moves), 1)

        # Contract: Failed moves must include error information
        self.assertIn('error', failed_moves[0])
        self.assertIn('does not exist', failed_moves[0]['error'])

    @pytest.mark.contract
    @pytest.mark.critical
    def test_partial_failure_graceful_handling_contract(self):
        """CONTRACT: Partial failures must be handled gracefully without stopping execution."""
        # Create multiple files with mix of conditions
        source_files = []
        file_assignments = []

        # Valid files
        for i in range(3):
            filename = "valid_{i}.pdf"
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("content {i}")
            source_files.append(file_path)

            file_assignments.append({
                'filename': filename,
                'current_path': file_path,
                'target_folder': 'Documents',
                'category': 'documents'
            })

        # Invalid files (will fail)
        for i in range(2):
            file_assignments.append({
                'filename': 'invalid_{i}.pdf',
                'current_path': f'/nonexistent/invalid_{i}.pdf',
                'target_folder': 'Documents',
                'category': 'documents'
            })

        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': file_assignments
            }
        }

        # Execute organization
        result = self.executor.execute_organization_plan(organization_plan)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Contract: Execution must continue despite failures
        self.assertTrue(result['success'])  # Overall still successful
        self.assertEqual(result['files_moved'], 3)  # All valid files moved
        self.assertEqual(result['files_failed'], 2)  # All invalid files failed
        self.assertEqual(result['total_files'], 5)

        # Contract: All valid files must be moved successfully
        for i in range(3):
            target_path = os.path.join(self.temp_dir, 'Documents', 'valid_{i}.pdf')
            self.assertTrue(os.path.exists(target_path),
                           "Valid file {i} was not moved despite partial failures")

        # Contract: Warnings must be provided for failures
        self.assertIn('warnings', result)
        self.assertIn('2 files failed', result['warnings'])

    @pytest.mark.contract
    @pytest.mark.critical
    def test_plan_validation_requirement_contract(self):
        """CONTRACT: Invalid plans must be rejected before execution."""
        # Test with failed organization plan
        invalid_plan = {
            'success': False,
            'error': 'Classification failed'
        }

        result = self.executor.execute_organization_plan(invalid_plan)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Contract: Invalid plans must be rejected
        self.assertFalse(result['success'])
        self.assertIn('Cannot execute failed organization plan', result['reason'])
        self.assertEqual(result['files_moved'], 0)

        # Contract: No file operations must occur for invalid plans
        # Verify no folders were created
        folder_count = len([item for item in os.listdir(self.temp_dir)
                           if os.path.isdir(os.path.join(self.temp_dir, item))
                           and not item.startswith('.')])
        self.assertEqual(folder_count, 0)

    @pytest.mark.contract
    @pytest.mark.critical
    def test_atomic_operation_consistency_contract(self):
        """CONTRACT: Each file operation must be atomic - either fully succeed or fully fail."""
        # Create source file
        source_file = os.path.join(self.temp_dir, "atomic_test.pd")
        with open(source_file, 'w') as f:
            f.write("atomic test content")

        organization_plan = {
            'success': True,
            'organization_structure': {
                'folders': {'Documents': {'type': 'category'}},
                'file_assignments': [{
                    'filename': 'atomic_test.pdf',
                    'current_path': source_file,
                    'target_folder': 'Documents',
                    'category': 'documents'
                }]
            }
        }

        # Execute organization
        result = self.executor.execute_organization_plan(organization_plan)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Contract: Operation must be fully complete or fully failed
        if result['files_moved'] > 0:
            # If reported as moved, file must exist in target and not in source
            target_path = os.path.join(self.temp_dir, 'Documents', 'atomic_test.pd')
            self.assertTrue(os.path.exists(target_path),
                           "File reported as moved but not found in target location")
            self.assertFalse(os.path.exists(source_file),
                           "File reported as moved but still exists in source location")
        else:
            # If reported as failed, file must remain in source location
            self.assertTrue(os.path.exists(source_file),
                           "File reported as failed but removed from source location")

if __name__ == '__main__':
    unittest.main()
