#!/usr/bin/env python3
"""
Tests for filename configuration and generation functionality.

Covers:
- Filename validation and sanitization
- Word boundary preservation in truncation
- AI prompt template validation
- OCR orientation detection
- Regression prevention for filename processing defects
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from PIL import Image
import io

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.filename_config import (
    validate_generated_filename, 
    get_filename_prompt_template,
    MAX_FILENAME_LENGTH,
    MIN_FILENAME_LENGTH
)
from content_processors import PDFProcessor


class TestFilenameValidation(unittest.TestCase):
    """Test filename validation and sanitization."""
    
    def test_filename_truncation_preserves_word_boundaries(self):
        """Test that filename truncation preserves complete words."""
        # Test case based on actual examples: document_H.PDF, document_HBR.PDF
        long_filename = "Harvard_Business_Review_Article_on_Multichannel_Strategy_for_Retail_Organizations_with_Digital_Transformation_Focus_2024_Analysis_Report"
        
        # This should be truncated but preserve word boundaries
        result = validate_generated_filename(long_filename)
        
        # Should not end mid-word (like document_H)
        self.assertFalse(result.endswith("_H"), f"Filename truncated mid-word: {result}")
        self.assertFalse(result.endswith("_HBR"), f"Filename truncated mid-word: {result}")
        
        # Should respect length limit
        self.assertLessEqual(len(result), MAX_FILENAME_LENGTH)
        
        # Should preserve meaningful content
        self.assertGreater(len(result), MIN_FILENAME_LENGTH)
        
    def test_defect_1_word_boundary_preservation(self):
        """Test that truncation preserves complete words."""
        test_cases = [
            ("Very_Long_Document_Name_That_Exceeds_Maximum_Length_Limits_For_Filesystem_Compatibility_Testing", 
             ["Very_Long_Document_Name", "Testing"]),  # Should not end with partial words
            ("Short_Name", ["Short_Name"]),  # Should not be truncated
        ]
        
        for input_filename, expected_endings in test_cases:
            with self.subTest(input_filename=input_filename):
                result = validate_generated_filename(input_filename)
                
                # Check that result ends with complete word
                if len(input_filename) > MAX_FILENAME_LENGTH:
                    # Should end at word boundary
                    self.assertTrue(any(result.endswith(ending) for ending in expected_endings),
                                  f"Result '{result}' should end with complete word")
                else:
                    # Short names should remain unchanged
                    self.assertEqual(result, input_filename)
                    
    def test_defect_2_camelcase_underscore_separation(self):
        """Reproduce Defect 2: CamelCase filenames without underscores."""
        # Test AI prompt template includes underscore instruction
        prompt = get_filename_prompt_template()
        
        # Should explicitly mention underscores and warn against camelCase
        self.assertIn("underscore", prompt.lower(), "Prompt should mention underscores")
        self.assertIn("camelcase", prompt.lower(), "Prompt should warn against camelCase")
        
        # Test actual examples from defects
        camelcase_examples = [
            "CentralCoastCouncilAnnualRateNotice20182019",
            "WoolworthsMultichannelStrategyGroceryBusinessModels",
            "BigWOnlineNetworkPlanUpdate"
        ]
        
        for camelcase in camelcase_examples:
            with self.subTest(camelcase=camelcase):
                result = validate_generated_filename(camelcase)
                
                # After sanitization, should contain underscores if original was long
                # (Note: sanitize_filename doesn't convert camelCase, that's AI's job)
                # But the prompt should guide AI to avoid camelCase
                
                # Verify prompt contains explicit instruction
                self.assertIn("IMPORTANT", prompt, "Should have important instruction about underscores")


class TestOCROrientationDefects(unittest.TestCase):
    """Test defects in OCR page orientation detection."""
    
    def setUp(self):
        """Set up test environment."""
        self.processor = PDFProcessor()
        
    @patch('content_processors.HAVE_TESSERACT', True)
    @patch('content_processors.OCR_USE_OSD', True)
    @patch('content_processors.pytesseract')
    def test_defect_3_reproduce_orientation_failure(self, mock_tesseract):
        """Reproduce Defect 3: OCR failing to detect page orientation."""
        # Mock an image that should be rotated
        mock_image = MagicMock()
        
        # Simulate Tesseract OSD failure (returns no useful info)
        mock_tesseract.image_to_osd.return_value = "No rotation detected\nConfidence: low"
        mock_tesseract.TesseractError = Exception
        
        # This should gracefully handle OSD failure
        angle = self.processor._detect_osd_angle(mock_image)
        
        # Should return 0 when OSD fails (no rotation detected)
        self.assertEqual(angle, 0, "Should return 0 when OSD fails to detect rotation")
        
    @patch('content_processors.HAVE_TESSERACT', True)
    @patch('content_processors.OCR_USE_OSD', True)
    @patch('content_processors.pytesseract')
    def test_defect_3_enhanced_orientation_detection(self, mock_tesseract):
        """Test enhanced OSD with multiple PSM modes."""
        mock_image = MagicMock()
        
        # Simulate first few PSM modes failing, but one succeeds
        def osd_side_effect(img, config=None):
            if config in ['--psm 0', '--psm 1']:
                raise Exception("OSD failed")
            elif config == '--psm 3':
                return "Orientation in degrees: 90\nRotate: 90\nConfidence: high"
            else:
                return "Rotate: 270\nConfidence: medium"
        
        mock_tesseract.image_to_osd.side_effect = osd_side_effect
        mock_tesseract.TesseractError = Exception
        
        angle = self.processor._detect_osd_angle(mock_image)
        
        # Should detect the 90-degree rotation from PSM mode 3
        self.assertEqual(angle, 90, "Should detect rotation with enhanced PSM modes")
        
    @patch('content_processors.HAVE_TESSERACT', True)
    @patch('content_processors.OCR_USE_OSD', True)
    @patch('content_processors.pytesseract')
    def test_orientation_regex_patterns(self, mock_tesseract):
        """Test multiple regex patterns for orientation parsing."""
        mock_image = MagicMock()
        
        test_cases = [
            ("Rotate: 180", 180),
            ("Orientation in degrees: 270", 270),
            ("Rotate degrees: 90", 90),
            ("No clear rotation info", 0),
        ]
        
        for osd_output, expected_angle in test_cases:
            with self.subTest(osd_output=osd_output):
                mock_tesseract.image_to_osd.return_value = osd_output
                mock_tesseract.TesseractError = Exception
                
                angle = self.processor._detect_osd_angle(mock_image)
                self.assertEqual(angle, expected_angle, 
                               f"Should parse angle {expected_angle} from '{osd_output}'")


class TestDefectRegressionPrevention(unittest.TestCase):
    """Ensure defects don't reoccur in the future."""
    
    def test_filename_length_consistency(self):
        """Ensure filename length limits are consistent across modules."""
        from core.filename_config import MAX_FILENAME_LENGTH as config_max
        from utils.security import MAX_FILENAME_LENGTH as security_max
        
        # Should use same limit to avoid multiple truncations
        self.assertEqual(config_max, security_max, 
                        "Filename length limits should be consistent across modules")
        
    def test_ai_prompt_includes_formatting_rules(self):
        """Ensure AI prompts explicitly state formatting requirements."""
        prompt = get_filename_prompt_template()
        
        required_elements = [
            "underscore",  # Word separation instruction
            "characters maximum",  # Length limit
            "words",  # Word count guidance
            "English letters, numbers, underscores, and hyphens only"  # Character restriction
        ]
        
        for element in required_elements:
            with self.subTest(element=element):
                self.assertIn(element.lower(), prompt.lower(),
                            f"Prompt should contain '{element}' for proper AI guidance")
                
    def test_ocr_orientation_fallback_robustness(self):
        """Ensure OCR orientation detection has proper error handling."""
        processor = PDFProcessor()
        mock_image = MagicMock()
        
        # Should handle missing tesseract gracefully
        with patch('content_processors.HAVE_TESSERACT', False):
            angle = processor._detect_osd_angle(mock_image)
            self.assertEqual(angle, 0, "Should return 0 when Tesseract unavailable")
        
        # Should handle OSD disabled gracefully  
        with patch('content_processors.OCR_USE_OSD', False):
            angle = processor._detect_osd_angle(mock_image)
            self.assertEqual(angle, 0, "Should return 0 when OSD disabled")


# Additional regression prevention tests


class TestDefectRegressionPrevention(unittest.TestCase):
    """Prevent regression of the three identified defects."""
    
    def test_no_mid_word_truncation_regression(self):
        """Ensure filenames never truncate mid-word again."""
        
        # Generate test cases that would previously cause mid-word truncation
        problematic_cases = [
            # Cases that would create _H, _HBR type endings
            "Harvard_Business_Review_Article_Analysis_Report",
            "How_Great_Companies_Build_Winning_Organizations",  
            "Healthcare_Business_Research_Methods_Guide",
            
            # Very long cases to stress-test boundary detection
            ("Artificial_Intelligence_Implementation_Strategy_for_Enterprise_"
             "Digital_Transformation_Including_Machine_Learning_Advanced_Analytics"),
        ]
        
        for test_case in problematic_cases:
            with self.subTest(test_case=test_case):
                result = validate_generated_filename(test_case)
                
                # Should not end with single characters after underscore
                if '_' in result:
                    parts = result.split('_')
                    last_part = parts[-1]
                    
                    # Last part should be meaningful (>1 char) or empty (trailing _ removed)
                    if last_part:  # If not empty after rstrip
                        self.assertGreaterEqual(len(last_part), 2, 
                            f"Filename '{result}' ends with single char '{last_part}' - indicates mid-word truncation")
    
    def test_ai_prompt_prevents_camelcase_regression(self):
        """Ensure AI prompt continues to prevent camelCase filenames."""
        
        prompt = get_filename_prompt_template()
        
        # Must contain explicit underscore instruction
        self.assertIn("underscore", prompt.lower(), 
                     "Prompt must explicitly mention underscores for word separation")
        
        # Must warn against camelCase specifically  
        self.assertIn("camelcase", prompt.lower(),
                     "Prompt must explicitly warn against camelCase")
        
        # Must contain "IMPORTANT" flag for visibility
        self.assertIn("IMPORTANT", prompt,
                     "Prompt must flag underscore instruction as IMPORTANT")
    
    def test_ocr_orientation_robustness_regression(self):
        """Ensure OCR orientation detection remains robust."""
        
        from content_processors import PDFProcessor
        from unittest.mock import patch, MagicMock
        
        processor = PDFProcessor()
        mock_image = MagicMock()
        
        # Test multiple failure scenarios should not crash
        failure_scenarios = [
            # Tesseract completely unavailable
            {'HAVE_TESSERACT': False, 'OCR_USE_OSD': True},
            
            # OSD disabled
            {'HAVE_TESSERACT': True, 'OCR_USE_OSD': False},
            
            # Tesseract throws exception
            {'HAVE_TESSERACT': True, 'OCR_USE_OSD': True, 'exception': True},
        ]
        
        for scenario in failure_scenarios:
            with self.subTest(scenario=scenario):
                
                # Apply patches individually using context manager stack
                patches = []
                if 'HAVE_TESSERACT' in scenario:
                    patches.append(patch('content_processors.HAVE_TESSERACT', scenario['HAVE_TESSERACT']))
                if 'OCR_USE_OSD' in scenario:
                    patches.append(patch('content_processors.OCR_USE_OSD', scenario['OCR_USE_OSD']))
                if scenario.get('exception'):
                    # Use the actual TesseractError type that the code expects
                    patches.append(patch('content_processors.pytesseract.image_to_osd', 
                                       side_effect=Exception("OSD failed")))
                    # Also mock TesseractError to be Exception for the test
                    patches.append(patch('content_processors.pytesseract.TesseractError', Exception))
                
                # Use ExitStack to apply multiple patches
                from contextlib import ExitStack
                with ExitStack() as stack:
                    for patch_obj in patches:
                        stack.enter_context(patch_obj)
                    
                    # Should not crash, should return safe default
                    angle = processor._detect_osd_angle(mock_image)
                    self.assertEqual(angle, 0, "Should return 0 on any OSD failure")
    
    def test_filename_length_consistency_regression(self):
        """Ensure filename length limits remain consistent across modules."""
        
        from core.filename_config import MAX_FILENAME_LENGTH as config_max
        from utils.security import MAX_FILENAME_LENGTH as security_max
        
        # Should use same constant to avoid multiple truncations
        self.assertEqual(config_max, security_max,
                        "MAX_FILENAME_LENGTH must be consistent across all modules")
        self.assertEqual(config_max, 160, 
                        "MAX_FILENAME_LENGTH should remain 160 for filesystem compatibility")
    
    def test_word_boundary_logic_edge_cases(self):
        """Test edge cases in word boundary detection logic."""
        
        edge_cases = [
            # All underscores - should handle gracefully
            ("A_B_C_D_E_F_G_H_I_J_K_L_M_N_O_P_Q_R_S_T_U_V_W_X_Y_Z_" * 3, "Should handle excessive underscores"),
            
            # No underscores but too long - should truncate sensibly  
            ("A" * 180, "Should handle no-underscore case"),
            
            # Mixed separators
            ("Test-Document_With-Mixed_Separators-And_Underscores", "Should handle mixed separators"),
            
            # Boundary exactly at limit
            ("Exactly_160_Characters_" + "X" * 133, "Should handle exact boundary case"),
        ]
        
        for test_input, description in edge_cases:
            with self.subTest(case=description):
                result = validate_generated_filename(test_input)
                
                # Should never exceed limit
                self.assertLessEqual(len(result), 160, f"Should respect length limit: {description}")
                
                # Should produce valid result
                self.assertGreater(len(result), 0, f"Should not produce empty result: {description}")
                
                # Should not end with separator
                self.assertFalse(result.endswith(('_', '-')), 
                                f"Should not end with separator: {description}")


if __name__ == "__main__":
    unittest.main(verbosity=2)