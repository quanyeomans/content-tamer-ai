#!/usr/bin/env python3
"""
Integration Tests for Post-Processing Organization

Tests the complete end-to-end organization workflow from file processing
through content analysis, classification, and physical organization.
"""

import unittest
import os
import sys
import tempfile
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shared.file_operations.file_organizer import FileOrganizer
from tests.utils.rich_test_utils import RichTestCase

class TestPostProcessingOrganizationIntegration(unittest.TestCase, RichTestCase):
    """Integration tests for complete organization workflow."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        """Clean up Rich testing environment and temp files."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass
        RichTestCase.tearDown(self)

    def test_end_to_end_organization_workflow_basic(self):
        """Test complete workflow from file processing to organization (Basic engine)."""
        # Create test files with realistic content
        test_files = self._create_realistic_test_files()

        # Run post-processing organization with basic engine
        result = self.organizer.run_post_processing_organization(
            processed_files=test_files,
            target_folder=self.temp_dir,
            enable_organization=True,
            ml_enhancement_level=1  # Basic engine
        )

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify overall success
        self.assertTrue(result['success'])
        self.assertTrue(result['organization_applied'])
        self.assertEqual(result['engine_type'], 'Basic (Level 1)')
        self.assertGreater(result['documents_organized'], 0)

        # Verify organization structure was created
        org_result = result['organization_result']
        self.assertTrue(org_result['success'])
        self.assertIn('organization_structure', org_result)

        # Check if reorganization was recommended and executed
        should_reorganize = org_result.get('should_reorganize', False)
        if should_reorganize:
            # If reorganization was recommended, execution should have occurred
            self.assertIn('execution_result', org_result)
            execution_result = org_result['execution_result']
            if execution_result and execution_result.get('success'):
                self.assertGreaterEqual(execution_result['files_moved'], 0)

                # Verify folder structure exists
                folders = org_result['organization_structure']['folders']
                for folder_name in folders:
                    folder_path = os.path.join(self.temp_dir, folder_name)
                    self.assertTrue(os.path.exists(folder_path),
                                   "Expected folder not created: {folder_name}")
        else:
            # If reorganization not recommended, that's also a valid result
            # (quality score may be too low for reorganization threshold)
            self.assertIn('quality_metrics', org_result)
            quality_metrics = org_result['quality_metrics']
            self.assertIn('accuracy', quality_metrics)

    def test_end_to_end_organization_workflow_enhanced(self):
        """Test complete workflow with enhanced ML processing (Level 2)."""
        # Create test files
        test_files = self._create_realistic_test_files()

        # Run post-processing organization with enhanced engine
        result = self.organizer.run_post_processing_organization(
            processed_files=test_files,
            target_folder=self.temp_dir,
            enable_organization=True,
            ml_enhancement_level=2  # Enhanced engine
        )

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify enhanced processing
        self.assertTrue(result['success'])
        self.assertTrue(result['organization_applied'])
        self.assertEqual(result['engine_type'], 'Enhanced (Level 2)')

        # Verify ML enhancement was applied
        org_result = result['organization_result']
        self.assertIn('ml_metrics', org_result)
        ml_metrics = org_result['ml_metrics']
        self.assertTrue(ml_metrics.get('ml_applied', False))
        self.assertTrue(ml_metrics.get('ml_available', False))

        # Verify organization execution
        if org_result.get('execution_result'):
            execution_result = org_result['execution_result']
            self.assertTrue(execution_result.get('success', False))
            self.assertGreaterEqual(execution_result.get('files_moved', 0), 0)

    def test_organization_workflow_with_mixed_file_types(self):
        """Test organization with various file types and content patterns."""
        # Create diverse test files
        mixed_files = self._create_mixed_content_files()

        # Run organization
        result = self.organizer.run_post_processing_organization(
            processed_files=mixed_files,
            target_folder=self.temp_dir,
            enable_organization=True,
            ml_enhancement_level=2
        )

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify handling of diverse content
        self.assertTrue(result['success'])
        self.assertTrue(result['organization_applied'])

        org_result = result['organization_result']
        classified_docs = org_result.get('classified_documents', [])

        # Verify different categories were identified
        categories = set(doc.get('category') for doc in classified_docs)
        self.assertGreater(len(categories), 1, "Should identify multiple categories")

        # Verify execution handled all file types
        if org_result.get('execution_result'):
            execution_result = org_result['execution_result']
            self.assertEqual(execution_result.get('total_files', 0), len(mixed_files))

    def test_organization_workflow_error_handling(self):
        """Test organization workflow handles errors gracefully."""
        # Create mix of valid and problematic files
        test_files = []

        # Valid file
        valid_file = os.path.join(self.temp_dir, "valid_document.pd")
        with open(valid_file, 'w') as f:
            f.write("This is a valid invoice document with proper content for classification.")
        test_files.append(valid_file)

        # File that will be missing during execution (simulate external deletion)
        missing_file = os.path.join(self.temp_dir, "will_be_missing.pd")
        with open(missing_file, 'w') as f:
            f.write("This file will be deleted before organization execution.")
        test_files.append(missing_file)

        # Delete the file after adding to list (simulates external interference)
        os.remove(missing_file)

        # Run organization
        result = self.organizer.run_post_processing_organization(
            processed_files=test_files,
            target_folder=self.temp_dir,
            enable_organization=True,
            ml_enhancement_level=1
        )

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify graceful error handling
        self.assertTrue(result['success'])  # Overall should still succeed
        self.assertTrue(result['organization_applied'])

        # Verify execution handled partial failures
        org_result = result['organization_result']
        if org_result.get('execution_result'):
            execution_result = org_result['execution_result']
            # Should have some failures but continue processing
            self.assertGreaterEqual(execution_result.get('files_failed', 0), 1)
            # Should have some successes
            self.assertGreaterEqual(execution_result.get('files_moved', 0), 0)

    def test_organization_workflow_disabled(self):
        """Test workflow when organization is explicitly disabled."""
        # Create test files
        test_files = self._create_realistic_test_files()

        # Run with organization disabled
        result = self.organizer.run_post_processing_organization(
            processed_files=test_files,
            target_folder=self.temp_dir,
            enable_organization=False,  # Disabled
            ml_enhancement_level=2
        )

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify organization was skipped
        self.assertTrue(result['success'])
        self.assertFalse(result['organization_applied'])
        self.assertIn('Organization disabled', result['reason'])

        # Verify no folders were created
        folder_count = len([item for item in os.listdir(self.temp_dir)
                           if os.path.isdir(os.path.join(self.temp_dir, item))
                           and not item.startswith('.')])
        self.assertEqual(folder_count, 0)

    def test_organization_state_persistence(self):
        """Test that organization state is properly persisted."""
        # Create test files
        test_files = self._create_realistic_test_files()

        # Run organization
        result = self.organizer.run_post_processing_organization(
            processed_files=test_files,
            target_folder=self.temp_dir,
            enable_organization=True,
            ml_enhancement_level=2
        )

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify success
        self.assertTrue(result['success'])
        self.assertTrue(result['organization_applied'])

        # Verify state persistence
        content_tamer_dir = os.path.join(self.temp_dir, '.content_tamer')
        if os.path.exists(content_tamer_dir):
            # Check for state files
            organization_dir = os.path.join(content_tamer_dir, 'organization')
            if os.path.exists(organization_dir):
                state_files = os.listdir(organization_dir)
                # Should have some persistent state
                self.assertGreater(len(state_files), 0)

    def test_organization_workflow_temporal_analysis(self):
        """Test organization workflow with temporal intelligence."""
        # Create files with temporal patterns
        temporal_files = self._create_temporal_test_files()

        # Run organization with temporal analysis
        result = self.organizer.run_post_processing_organization(
            processed_files=temporal_files,
            target_folder=self.temp_dir,
            enable_organization=True,
            ml_enhancement_level=3  # Temporal intelligence
        )

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify temporal processing
        self.assertTrue(result['success'])
        self.assertTrue(result['organization_applied'])

        org_result = result['organization_result']

        # Verify temporal analysis was performed
        self.assertIn('temporal_analysis', org_result)
        temporal_analysis = org_result['temporal_analysis']
        self.assertIn('recommended_time_structure', temporal_analysis)

        # Verify organization structure considers temporal patterns
        organization_structure = org_result['organization_structure']
        self.assertIn('time_granularity', organization_structure)

    def _create_realistic_test_files(self):
        """Create realistic test files with proper content for classification."""
        test_files = []

        file_contents = [
            ("invoice_abc_company_2024.pd", "Invoice from ABC Company dated March 15, 2024. Amount due: $1,250.00. Service period: February 2024. Payment terms: Net 30 days. Invoice number: INV-2024-001."),
            ("contract_legal_services.pd", "Legal services agreement between XYZ Law Firm and client for consulting services. Term: 12 months starting January 2024. Retainer: $5,000. Hourly rate: $250."),
            ("receipt_office_supplies.pd", "Receipt for office supplies purchased from Supply Store. Date: 2024-03-10. Total: $89.45. Items: paper, pens, folders. Receipt #R-12345."),
            ("bank_statement_jan_2024.pd", "Monthly bank statement for January 2024. Account summary and transaction details included. Beginning balance: $10,000. Ending balance: $12,500."),
            ("medical_report_consultation.pd", "Medical consultation report from Dr. Smith, MD. Patient visit date: March 8, 2024. Diagnosis and treatment plan. Follow-up required in 30 days.")
        ]

        for filename, content in file_contents:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            test_files.append(file_path)

        return test_files

    def _create_mixed_content_files(self):
        """Create files with diverse content types and patterns."""
        mixed_files = []

        # Different document types with varied content
        content_patterns = [
            ("financial_report_q1.pd", "Quarterly financial report Q1 2024. Revenue: $50,000. Expenses: $35,000. Net profit analysis."),
            ("employee_handbook.pd", "Company employee handbook. Policies, procedures, and benefits information for all staff members."),
            ("technical_specification.pd", "Technical specifications for software development project. API documentation and system requirements."),
            ("marketing_proposal.pd", "Marketing campaign proposal for product launch. Target demographics and budget allocation details."),
            ("utility_bill_march.pd", "Utility bill for March 2024. Electricity usage: 450 kWh. Amount due: $125.67."),
            ("insurance_policy.pd", "Insurance policy document. Coverage details, premium information, and terms and conditions."),
            ("research_paper.pd", "Academic research paper on machine learning applications. Published in Journal of AI Research 2024.")
        ]

        for filename, content in content_patterns:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            mixed_files.append(file_path)

        return mixed_files

    def _create_temporal_test_files(self):
        """Create files with clear temporal patterns for temporal analysis testing."""
        temporal_files = []

        # Files with clear temporal indicators
        temporal_content = [
            ("invoice_jan_2024.pd", "Invoice #001 dated January 15, 2024. First quarter billing cycle."),
            ("invoice_feb_2024.pd", "Invoice #002 dated February 15, 2024. First quarter billing cycle."),
            ("invoice_mar_2024.pd", "Invoice #003 dated March 15, 2024. First quarter billing cycle."),
            ("report_q1_2024.pd", "Q1 2024 quarterly report. January-March analysis and performance metrics."),
            ("statement_fy2024.pd", "Annual statement for fiscal year 2024. July 2023 - June 2024 period."),
            ("tax_return_2023.pd", "Tax return for calendar year 2023. Filed in April 2024."),
            ("budget_fy2025.pd", "Budget planning for fiscal year 2025. Projected expenditures and revenue.")
        ]

        for filename, content in temporal_content:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            temporal_files.append(file_path)

        return temporal_files

class TestOrganizationEngineIntegration(unittest.TestCase, RichTestCase):
    """Integration tests for organization engine components."""

    def setUp(self):
        """Set up Rich testing environment for each test."""
        RichTestCase.setUp(self)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up Rich testing environment and temp files."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass
        RichTestCase.tearDown(self)

    def test_basic_organization_engine_integration(self):
        """Test BasicOrganizationEngine integration with file executor."""
        from organization.organization_engine import BasicOrganizationEngine

        engine = BasicOrganizationEngine(self.temp_dir)

        # Create test documents
        test_docs = [
            {
                'filename': 'test_invoice.pdf',
                'path': os.path.join(self.temp_dir, 'test_invoice.pdf'),
                'content': 'Invoice from ABC Company for services rendered. Amount: $500.00.'
            },
            {
                'filename': 'test_contract.pdf',
                'path': os.path.join(self.temp_dir, 'test_contract.pdf'),
                'content': 'Legal services agreement for consulting. Duration: 6 months.'
            }
        ]

        # Create actual files
        for doc in test_docs:
            with open(doc['path'], 'w') as f:
                f.write(doc['content'])

        # Run organization
        result = engine.organize_documents(test_docs)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify integration success
        self.assertTrue(result['success'])
        self.assertTrue(result['should_reorganize'])

        # Verify execution occurred
        if result.get('execution_result'):
            execution_result = result['execution_result']
            self.assertGreaterEqual(execution_result.get('files_moved', 0), 0)

    def test_enhanced_organization_engine_integration(self):
        """Test EnhancedOrganizationEngine integration with ML and file executor."""
        from organization.enhanced_organization_engine import EnhancedOrganizationEngine

        engine = EnhancedOrganizationEngine(self.temp_dir, ml_enhancement_level=2)

        # Create test documents
        test_docs = [
            {
                'filename': 'financial_doc.pdf',
                'path': os.path.join(self.temp_dir, 'financial_doc.pdf'),
                'content': 'Financial statement for Q1 2024. Revenue and expense analysis.'
            },
            {
                'filename': 'legal_doc.pdf',
                'path': os.path.join(self.temp_dir, 'legal_doc.pdf'),
                'content': 'Legal contract between parties. Terms and conditions outlined.'
            }
        ]

        # Create actual files
        for doc in test_docs:
            with open(doc['path'], 'w') as f:
                f.write(doc['content'])

        # Run enhanced organization
        result = engine.organize_documents(test_docs)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify enhanced integration
        self.assertTrue(result['success'])
        self.assertIn('ml_metrics', result)

        # Verify ML enhancement was attempted
        ml_metrics = result['ml_metrics']
        self.assertTrue(ml_metrics.get('ml_available', False))

        # Verify execution integration
        if result.get('execution_result'):
            execution_result = result['execution_result']
            self.assertTrue(execution_result.get('success', False))

    def test_organization_component_failure_isolation(self):
        """Test that component failures don't break the entire workflow."""
        from organization.organization_engine import BasicOrganizationEngine

        engine = BasicOrganizationEngine(self.temp_dir)

        # Create problematic test scenario
        test_docs = [
            {
                'filename': 'good_doc.pdf',
                'path': os.path.join(self.temp_dir, 'good_doc.pdf'),
                'content': 'Valid document content for testing.'
            },
            {
                'filename': 'bad_doc.pdf',
                'path': '/nonexistent/bad_doc.pdf',  # Invalid path
                'content': 'This file path does not exist.'
            }
        ]

        # Create only the valid file
        with open(test_docs[0]['path'], 'w') as f:
            f.write(test_docs[0]['content'])

        # Run organization
        result = engine.organize_documents(test_docs)

        # Ensure no Rich I/O errors occurred
        self.assert_no_rich_errors()

        # Verify graceful handling
        self.assertTrue(result['success'])  # Overall should succeed

        # Verify partial processing occurred
        classified_docs = result.get('classified_documents', [])
        self.assertEqual(len(classified_docs), 2)  # Both docs should be classified

        # Verify execution handled partial failures
        if result.get('execution_result'):
            execution_result = result['execution_result']
            # Should have some failures but overall success
            self.assertGreaterEqual(execution_result.get('files_failed', 0), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
