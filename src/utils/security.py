"""
Content Tamer AI - Security Utilities

Provides input sanitization, validation, and security controls for file processing
and AI prompt construction to prevent injection attacks and path traversal.
"""

import os
import re
from pathlib import Path
from typing import Optional, Set, Dict, Any
from enum import Enum


# Security constants
MAX_CONTENT_LENGTH = 4096  # Reduced from 8000 for safety
MAX_FILENAME_LENGTH = 160
SAFE_CHARS = re.compile(r'^[a-zA-Z0-9._\-\s]+$')

# Dangerous patterns that could indicate prompt injection
PROMPT_INJECTION_PATTERNS = [
    # Direct instruction attempts
    r'ignore\s+(?:previous|all|above)\s+instructions?',
    r'forget\s+(?:previous|all|above)\s+instructions?',
    r'new\s+instructions?',
    r'system\s*:\s*',
    r'assistant\s*:\s*',
    r'user\s*:\s*',
    
    # Command injection attempts
    r'execute\s+(?:command|code|script)',
    r'run\s+(?:command|code|script)',
    r'eval\s*\(',
    r'exec\s*\(',
    r'subprocess\.',
    r'os\.system',
    
    # Data exfiltration attempts
    r'print\s+(?:api|key|token|secret)',
    r'output\s+(?:api|key|token|secret)',
    r'reveal\s+(?:api|key|token|secret)',
    r'show\s+(?:api|key|token|secret)',
    
    # Formatting attempts
    r'```\s*(?:python|bash|sh|cmd)',
    r'<script[^>]*>',
    r'javascript:',
    
    # Role confusion attempts  
    r'you\s+are\s+(?:now|a)\s+(?:hacker|admin|root)',
    r'act\s+as\s+(?:if\s+you\s+are\s+)?(?:a|an|)\s*(?:hacker|admin|root|administrator)',
    r'pretend\s+(?:to\s+be|you\s+are)',
    r'act\s+like\s+(?:a|an)\s+(?:hacker|admin|root)',
]

# Compiled regex patterns for performance
INJECTION_REGEX = re.compile('|'.join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE)


class SecurityError(Exception):
    """Raised when a security validation fails."""
    pass


class InputSanitizer:
    """Handles input sanitization and validation for security."""
    
    @staticmethod
    def sanitize_content_for_ai(content: str) -> str:
        """
        Sanitize content before sending to AI to prevent prompt injection.
        
        Args:
            content: Raw extracted content from files
            
        Returns:
            Sanitized content safe for AI processing
            
        Raises:
            SecurityError: If content contains suspicious patterns
        """
        if not content:
            return ""
        
        # Truncate to safe length
        content = content[:MAX_CONTENT_LENGTH]
        
        # Check for prompt injection patterns
        if INJECTION_REGEX.search(content):
            # Log the attempt but don't include the actual content in the error
            raise SecurityError(
                "Suspicious content patterns detected. File may contain prompt injection attempts."
            )
        
        # Remove/escape potential control characters
        content = InputSanitizer._remove_control_characters(content)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    @staticmethod
    def _remove_control_characters(text: str) -> str:
        """Remove or escape control characters that could be dangerous."""
        # Remove non-printable characters except newlines and tabs
        cleaned = ''.join(
            char for char in text 
            if char.isprintable() or char in '\n\t'
        )
        
        # Limit consecutive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize filename for security.
        
        Args:
            filename: Proposed filename
            
        Returns:
            Sanitized filename
            
        Raises:
            SecurityError: If filename is unsafe
        """
        if not filename:
            raise SecurityError("Filename cannot be empty")
        
        # Check length
        if len(filename) > MAX_FILENAME_LENGTH:
            filename = filename[:MAX_FILENAME_LENGTH]
        
        # Check for dangerous characters
        if not SAFE_CHARS.match(filename):
            # Remove unsafe characters
            filename = re.sub(r'[^a-zA-Z0-9._\-\s]', '', filename)
        
        # Remove dangerous patterns
        dangerous_names = {'.', '..', 'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 
                          'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                          'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 
                          'LPT8', 'LPT9'}
        
        if filename.upper() in dangerous_names:
            raise SecurityError(f"Filename '{filename}' is reserved/dangerous")
        
        # Ensure it doesn't start/end with dangerous characters
        filename = filename.strip('. ')
        
        if not filename:
            raise SecurityError("Filename became empty after sanitization")
        
        return filename


class PathValidator:
    """Handles path validation and traversal protection."""
    
    @staticmethod
    def validate_file_path(file_path: str, base_dirs: Set[str]) -> str:
        """
        Validate file path to prevent directory traversal attacks.
        
        Args:
            file_path: Path to validate
            base_dirs: Set of allowed base directories
            
        Returns:
            Resolved absolute path if safe
            
        Raises:
            SecurityError: If path is unsafe or outside allowed directories
        """
        if not file_path:
            raise SecurityError("File path cannot be empty")
        
        try:
            # Resolve path to handle symlinks and relative components
            resolved_path = Path(file_path).resolve()
            abs_path = str(resolved_path)
            
            # Check if path is within any allowed base directory
            path_is_safe = False
            for base_dir in base_dirs:
                base_resolved = Path(base_dir).resolve()
                try:
                    # Check if file_path is within base_dir
                    resolved_path.relative_to(base_resolved)
                    path_is_safe = True
                    break
                except ValueError:
                    continue
            
            if not path_is_safe:
                raise SecurityError(
                    f"Path '{file_path}' is outside allowed directories"
                )
            
            return abs_path
            
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid file path: {e}") from e
    
    @staticmethod
    def validate_directory(dir_path: str) -> str:
        """
        Validate directory path for safety.
        
        Args:
            dir_path: Directory path to validate
            
        Returns:
            Absolute directory path
            
        Raises:
            SecurityError: If directory path is unsafe
        """
        try:
            resolved_dir = Path(dir_path).resolve()
            
            # Check for suspicious patterns
            path_str = str(resolved_dir)
            if '..' in path_str.split(os.sep):
                raise SecurityError("Directory path contains traversal attempts")
            
            return str(resolved_dir)
            
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid directory path: {e}") from e


class ContentValidator:
    """Validates content extracted from files."""
    
    @staticmethod
    def validate_extracted_content(content: str, source_file: str) -> str:
        """
        Validate content extracted from files before AI processing.
        
        Args:
            content: Extracted content
            source_file: Source file path for context
            
        Returns:
            Validated content
            
        Raises:
            SecurityError: If content appears malicious
        """
        if not content:
            return ""
        
        # Basic length check
        if len(content) > MAX_CONTENT_LENGTH * 2:  # Allow some overhead before truncation
            content = content[:MAX_CONTENT_LENGTH * 2]
        
        # Check for embedded scripts or commands
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        combined_pattern = re.compile('|'.join(script_patterns), re.IGNORECASE | re.DOTALL)
        if combined_pattern.search(content):
            raise SecurityError(
                f"File '{source_file}' contains potentially malicious embedded scripts"
            )
        
        return content


# Security configuration
SECURITY_CONFIG = {
    'max_content_length': MAX_CONTENT_LENGTH,
    'max_filename_length': MAX_FILENAME_LENGTH,
    'enable_injection_detection': True,
    'strict_path_validation': True,
}


def get_security_config() -> dict:
    """Get current security configuration."""
    return SECURITY_CONFIG.copy()


def update_security_config(**kwargs) -> None:
    """Update security configuration (for testing only)."""
    SECURITY_CONFIG.update(kwargs)


# PDF Threat Detection
class ThreatLevel(Enum):
    """PDF threat level classifications."""
    SAFE = "safe"
    LOW = "low" 
    MEDIUM = "medium"
    HIGH = "high"


class PDFThreatAnalysis:
    """Results from PDF threat analysis."""
    
    def __init__(self, threat_level: ThreatLevel, indicators: Dict[str, Any], summary: str):
        self.threat_level = threat_level
        self.indicators = indicators
        self.summary = summary
    
    @property
    def is_safe(self) -> bool:
        """Check if PDF is considered safe for processing."""
        return self.threat_level in [ThreatLevel.SAFE, ThreatLevel.LOW]
    
    @property
    def should_warn(self) -> bool:
        """Check if user should be warned about this PDF."""
        return self.threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]


class PDFAnalyzer:
    """Analyzes PDF files for potential security threats using PDFiD."""
    
    def __init__(self):
        self._pdfid_available = self._check_pdfid_availability()
    
    def _check_pdfid_availability(self) -> bool:
        """Check if PDFiD is available for use."""
        try:
            from pdfid.pdfid import PDFiD
            return True
        except ImportError:
            return False
    
    def analyze_pdf(self, file_path: str) -> PDFThreatAnalysis:
        """
        Analyze PDF file for potential security threats.
        
        Args:
            file_path: Path to PDF file to analyze
            
        Returns:
            PDFThreatAnalysis with threat level and details
        """
        if not self._pdfid_available:
            return PDFThreatAnalysis(
                threat_level=ThreatLevel.SAFE,
                indicators={'pdfid_available': False},
                summary="PDFiD not available - basic processing only"
            )
        
        try:
            return self._run_pdfid_analysis(file_path)
        except Exception as e:
            return PDFThreatAnalysis(
                threat_level=ThreatLevel.LOW,
                indicators={'analysis_error': str(e)},
                summary=f"Analysis failed: {str(e)}"
            )
    
    def _run_pdfid_analysis(self, file_path: str) -> PDFThreatAnalysis:
        """Run PDFiD analysis on the PDF file."""
        from pdfid.pdfid import PDFiD
        
        # Pre-check file existence to avoid PDFiD calling sys.exit()
        if not os.path.isfile(file_path):
            raise Exception(f"File not found: {file_path}")
        
        # Run PDFiD analysis
        try:
            xmldoc = PDFiD(file_path, allNames=False, extraData=False, disarm=False, force=False)
            
            # Extract key indicators
            indicators = self._extract_indicators(xmldoc)
            
            # Calculate threat level
            threat_level = self._calculate_threat_level(indicators)
            
            # Generate summary
            summary = self._generate_summary(threat_level, indicators)
            
            return PDFThreatAnalysis(threat_level, indicators, summary)
            
        except SystemExit:
            # PDFiD calls sys.exit() on various errors
            raise Exception("PDFiD encountered a fatal error during analysis")
        except Exception as e:
            raise Exception(f"PDFiD analysis failed: {str(e)}")
    
    def _extract_indicators(self, xmldoc) -> Dict[str, Any]:
        """Extract threat indicators from PDFiD XML output."""
        indicators = {}
        
        # Parse the XML structure - PDFiD returns specific format
        import xml.etree.ElementTree as ET
        
        try:
            # Get the root element 
            if hasattr(xmldoc, 'getroot'):
                root = xmldoc.getroot() if callable(xmldoc.getroot) else xmldoc.getroot
            else:
                # Handle string output
                root = ET.fromstring(str(xmldoc))
            
            # Extract key threat indicators
            for keyword in root.findall('.//Keyword'):
                name = keyword.get('Name', '')
                count = int(keyword.get('Count', 0))
                
                if name == '/JS' or name == '/JavaScript':
                    indicators['javascript'] = count
                elif name == '/OpenAction':
                    indicators['open_action'] = count
                elif name == '/AA':  # Additional Actions
                    indicators['additional_actions'] = count
                elif name == '/EmbeddedFile':
                    indicators['embedded_files'] = count
                elif name == '/XFA':  # XML Forms Architecture
                    indicators['xfa_forms'] = count
                elif name == '/URI':
                    indicators['uri_references'] = count
                elif name == '/SubmitForm':
                    indicators['submit_form'] = count
                elif name == '/Launch':
                    indicators['launch_action'] = count
                
        except Exception as e:
            indicators['parse_error'] = str(e)
        
        return indicators
    
    def _calculate_threat_level(self, indicators: Dict[str, Any]) -> ThreatLevel:
        """Calculate overall threat level based on indicators."""
        if 'parse_error' in indicators:
            return ThreatLevel.LOW
        
        # High threat indicators
        high_risk_count = 0
        if indicators.get('javascript', 0) > 0:
            high_risk_count += 1
        if indicators.get('launch_action', 0) > 0:
            high_risk_count += 2  # Launch actions are very suspicious
        if indicators.get('embedded_files', 0) > 0:
            high_risk_count += 1
        
        # Medium threat indicators  
        medium_risk_count = 0
        if indicators.get('open_action', 0) > 0:
            medium_risk_count += 1
        if indicators.get('additional_actions', 0) > 0:
            medium_risk_count += 1
        if indicators.get('uri_references', 0) > 0:
            medium_risk_count += 1
        if indicators.get('submit_form', 0) > 0:
            medium_risk_count += 1
        if indicators.get('xfa_forms', 0) > 0:
            medium_risk_count += 1
        
        # Determine threat level
        if high_risk_count >= 2:
            return ThreatLevel.HIGH
        elif high_risk_count >= 1:
            return ThreatLevel.MEDIUM
        elif medium_risk_count >= 3:
            return ThreatLevel.MEDIUM
        elif medium_risk_count >= 1:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.SAFE
    
    def _generate_summary(self, threat_level: ThreatLevel, indicators: Dict[str, Any]) -> str:
        """Generate human-readable summary of threats detected."""
        if threat_level == ThreatLevel.SAFE:
            return "PDF appears safe - no suspicious indicators detected"
        
        threats = []
        
        if indicators.get('javascript', 0) > 0:
            threats.append(f"JavaScript code ({indicators['javascript']} instances)")
        if indicators.get('launch_action', 0) > 0:
            threats.append(f"Launch actions ({indicators['launch_action']} instances)")  
        if indicators.get('embedded_files', 0) > 0:
            threats.append(f"Embedded files ({indicators['embedded_files']} instances)")
        if indicators.get('open_action', 0) > 0:
            threats.append(f"Auto-open actions ({indicators['open_action']} instances)")
        if indicators.get('uri_references', 0) > 0:
            threats.append(f"External URI references ({indicators['uri_references']} instances)")
        if indicators.get('submit_form', 0) > 0:
            threats.append(f"Form submissions ({indicators['submit_form']} instances)")
        
        if threats:
            return f"Potential threats detected: {', '.join(threats)}"
        else:
            return f"PDF has {threat_level.value} risk indicators"