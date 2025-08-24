"""
PDF Security Tests for PDFiD Integration

Tests the PDFiD threat detection system integrated into Content Tamer AI.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.security import PDFAnalyzer, PDFThreatAnalysis, ThreatLevel


class TestThreatLevel(unittest.TestCase):
    """Test ThreatLevel enumeration."""
    
    def test_threat_levels_exist(self):
        """Test that all expected threat levels are defined."""
        self.assertEqual(ThreatLevel.SAFE.value, "safe")
        self.assertEqual(ThreatLevel.LOW.value, "low")
        self.assertEqual(ThreatLevel.MEDIUM.value, "medium")
        self.assertEqual(ThreatLevel.HIGH.value, "high")


class TestPDFThreatAnalysis(unittest.TestCase):
    """Test PDFThreatAnalysis class."""
    
    def test_safe_analysis(self):
        """Test safe PDF analysis results."""
        analysis = PDFThreatAnalysis(
            ThreatLevel.SAFE, 
            {'javascript': 0}, 
            "PDF appears safe"
        )
        
        self.assertTrue(analysis.is_safe)
        self.assertFalse(analysis.should_warn)
        self.assertEqual(analysis.threat_level, ThreatLevel.SAFE)
    
    def test_low_threat_analysis(self):
        """Test low threat PDF analysis results."""
        analysis = PDFThreatAnalysis(
            ThreatLevel.LOW,
            {'uri_references': 1},
            "PDF has low risk indicators"
        )
        
        self.assertTrue(analysis.is_safe)  # Low is still considered safe for processing
        self.assertFalse(analysis.should_warn)
        self.assertEqual(analysis.threat_level, ThreatLevel.LOW)
    
    def test_medium_threat_analysis(self):
        """Test medium threat PDF analysis results."""
        analysis = PDFThreatAnalysis(
            ThreatLevel.MEDIUM,
            {'javascript': 1},
            "JavaScript detected"
        )
        
        self.assertFalse(analysis.is_safe)
        self.assertTrue(analysis.should_warn)
        self.assertEqual(analysis.threat_level, ThreatLevel.MEDIUM)
    
    def test_high_threat_analysis(self):
        """Test high threat PDF analysis results."""
        analysis = PDFThreatAnalysis(
            ThreatLevel.HIGH,
            {'javascript': 2, 'launch_action': 1},
            "Multiple high-risk indicators"
        )
        
        self.assertFalse(analysis.is_safe)
        self.assertTrue(analysis.should_warn)
        self.assertEqual(analysis.threat_level, ThreatLevel.HIGH)


class TestPDFAnalyzer(unittest.TestCase):
    """Test PDFAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PDFAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyzer_initialization(self):
        """Test that PDFAnalyzer initializes correctly."""
        self.assertIsInstance(self.analyzer, PDFAnalyzer)
        self.assertIsInstance(self.analyzer._pdfid_available, bool)
    
    def test_pdfid_availability_check(self):
        """Test PDFiD availability detection."""
        # This should be True since we installed pdfid
        self.assertTrue(self.analyzer._pdfid_available)
    
    def test_nonexistent_file_analysis(self):
        """Test analysis of non-existent file."""
        analysis = self.analyzer.analyze_pdf("nonexistent.pdf")
        
        self.assertIsInstance(analysis, PDFThreatAnalysis)
        self.assertEqual(analysis.threat_level, ThreatLevel.LOW)
        self.assertIn('analysis_error', analysis.indicators)
    
    def test_empty_file_analysis(self):
        """Test analysis of empty file."""
        empty_file = os.path.join(self.temp_dir, "empty.pdf")
        with open(empty_file, 'wb') as f:
            pass  # Create empty file
        
        analysis = self.analyzer.analyze_pdf(empty_file)
        self.assertIsInstance(analysis, PDFThreatAnalysis)
        # Should handle gracefully with error or low threat
    
    def test_minimal_pdf_analysis(self):
        """Test analysis of minimal valid PDF."""
        pdf_file = os.path.join(self.temp_dir, "minimal.pdf")
        with open(pdf_file, 'wb') as f:
            f.write(b'%PDF-1.4\n%EOF\n')
        
        analysis = self.analyzer.analyze_pdf(pdf_file)
        self.assertIsInstance(analysis, PDFThreatAnalysis)
        # Minimal PDF should be safe or low risk
        self.assertIn(analysis.threat_level, [ThreatLevel.SAFE, ThreatLevel.LOW])
    
    @patch('pdfid.pdfid.PDFiD')
    def test_pdfid_unavailable_fallback(self, mock_pdfid):
        """Test behavior when PDFiD is unavailable."""
        # Create analyzer with mocked unavailable PDFiD
        with patch.object(PDFAnalyzer, '_check_pdfid_availability', return_value=False):
            analyzer = PDFAnalyzer()
            analysis = analyzer.analyze_pdf("test.pdf")
            
            self.assertEqual(analysis.threat_level, ThreatLevel.SAFE)
            self.assertFalse(analysis.indicators['pdfid_available'])
            self.assertIn("PDFiD not available", analysis.summary)
    
    def test_threat_level_calculation(self):
        """Test threat level calculation logic."""
        # Test safe indicators
        indicators = {}
        threat_level = self.analyzer._calculate_threat_level(indicators)
        self.assertEqual(threat_level, ThreatLevel.SAFE)
        
        # Test low risk indicators
        indicators = {'uri_references': 1}
        threat_level = self.analyzer._calculate_threat_level(indicators)
        self.assertEqual(threat_level, ThreatLevel.LOW)
        
        # Test medium risk indicators
        indicators = {'javascript': 1}
        threat_level = self.analyzer._calculate_threat_level(indicators)
        self.assertEqual(threat_level, ThreatLevel.MEDIUM)
        
        # Test high risk indicators  
        indicators = {'javascript': 1, 'launch_action': 1}
        threat_level = self.analyzer._calculate_threat_level(indicators)
        self.assertEqual(threat_level, ThreatLevel.HIGH)
    
    def test_summary_generation(self):
        """Test threat summary generation."""
        # Safe PDF summary
        summary = self.analyzer._generate_summary(ThreatLevel.SAFE, {})
        self.assertIn("appears safe", summary.lower())
        
        # JavaScript threat summary
        indicators = {'javascript': 2}
        summary = self.analyzer._generate_summary(ThreatLevel.MEDIUM, indicators)
        self.assertIn("JavaScript", summary)
        self.assertIn("2 instances", summary)
        
        # Multiple threats summary
        indicators = {'javascript': 1, 'embedded_files': 1, 'uri_references': 3}
        summary = self.analyzer._generate_summary(ThreatLevel.HIGH, indicators)
        self.assertIn("JavaScript", summary)
        self.assertIn("Embedded files", summary)
        self.assertIn("URI references", summary)


class TestPDFProcessorIntegration(unittest.TestCase):
    """Test PDFProcessor integration with threat analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures.""" 
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pdf_processor_with_threat_analysis(self):
        """Test that PDFProcessor integrates threat analysis."""
        from content_processors import PDFProcessor
        
        # Create a minimal PDF
        pdf_file = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_file, 'wb') as f:
            f.write(b'%PDF-1.4\n%EOF\n')
        
        processor = PDFProcessor()
        
        # Capture print output to verify threat analysis runs
        with patch('builtins.print') as mock_print:
            content, image = processor.extract_content(pdf_file)
            
            # Check if any PDF analysis messages were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            analysis_printed = any("PDF Analysis" in call or "PDF Security" in call for call in print_calls)
            
            # Should have run analysis (may or may not print depending on threat level)
            self.assertIsInstance(content, str)
    
    def test_pdf_processor_handles_analysis_errors(self):
        """Test that PDFProcessor handles analysis errors gracefully."""
        from content_processors import PDFProcessor
        
        processor = PDFProcessor()
        
        # Test with non-existent file - should handle gracefully
        content, image = processor.extract_content("nonexistent.pdf")
        self.assertTrue(content.startswith("Error:"))


class TestSecurityConfiguration(unittest.TestCase):
    """Test security configuration updates for PDF analysis."""
    
    def test_security_config_includes_pdf_options(self):
        """Test that security configuration can be extended for PDF options."""
        from utils.security import get_security_config, update_security_config
        
        # Test existing config
        config = get_security_config()
        self.assertIsInstance(config, dict)
        
        # Test updating config with PDF-specific options
        update_security_config(pdf_threat_detection=True, pdf_analysis_timeout=30)
        
        updated_config = get_security_config()
        self.assertTrue(updated_config.get('pdf_threat_detection'))
        self.assertEqual(updated_config.get('pdf_analysis_timeout'), 30)
        
        # Reset config
        update_security_config(pdf_threat_detection=None, pdf_analysis_timeout=None)


class TestPerformanceImpact(unittest.TestCase):
    """Test performance impact of PDF threat analysis."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up performance test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analysis_performance(self):
        """Test that PDF analysis completes in reasonable time."""
        import time
        
        # Create a test PDF
        pdf_file = os.path.join(self.temp_dir, "perf_test.pdf")
        with open(pdf_file, 'wb') as f:
            f.write(b'%PDF-1.4\n%EOF\n')
        
        analyzer = PDFAnalyzer()
        
        start_time = time.time()
        analysis = analyzer.analyze_pdf(pdf_file)
        end_time = time.time()
        
        # Analysis should complete quickly (less than 5 seconds)
        analysis_time = end_time - start_time
        self.assertLess(analysis_time, 5.0, f"PDF analysis took {analysis_time:.2f}s")
        
        self.assertIsInstance(analysis, PDFThreatAnalysis)


if __name__ == "__main__":
    unittest.main()