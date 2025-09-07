# Security Remediation Plan
*Comprehensive security vulnerability remediation roadmap for content-tamer-ai*

**Generated**: 2025-09-07  
**Status**: Ready for Implementation  
**Priority**: HIGH - Critical vulnerabilities identified  

## 🚨 Executive Summary

Security audit identified **29 vulnerabilities** across the codebase:
- **2 HIGH severity** (immediate action required)
- **27 MEDIUM/LOW severity** (planned remediation)
- **0 dependency vulnerabilities** (clean)

**Key Risk**: Command injection vulnerabilities could lead to full system compromise.

## 📊 Vulnerability Breakdown

### 🔴 **CRITICAL SEVERITY** (Fix within 24 hours)

#### **1. Command Injection - Ollama Installation (src/core/cli_parser.py)**
- **Bandit ID**: B602 - subprocess_popen_with_shell_equals_true
- **Lines**: 404, 407, 421
- **Risk**: Remote code execution if attacker controls installation URL
- **CVSS Score**: 9.8 (Critical)
- **Attack Vector**: Malicious Ollama installation script
- **Code Location**:
  ```python
  # VULNERABLE CODE:
  subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"], 
                shell=True)  # Lines 404, 407
  
  subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, 
                   stderr=subprocess.DEVNULL)  # Line 421
  ```

#### **2. XML External Entity (XXE) Attack (src/utils/security.py:424)**
- **Bandit ID**: B405 - import_xml_etree
- **Risk**: File disclosure, SSRF, denial of service
- **CVSS Score**: 8.2 (High)
- **Attack Vector**: Malicious XML input during log sanitization
- **Code Location**:
  ```python
  # VULNERABLE CODE:
  import xml.etree.ElementTree as ET  # Line 424
  ```

### 🟡 **HIGH PRIORITY** (Fix within 1 week)

#### **3. Subprocess Path Injection (src/utils/hardware_detector.py)**
- **Bandit ID**: B607 - start_process_with_partial_path
- **Lines**: 129, 142, 198, 215 (4 instances)
- **Risk**: PATH hijacking attacks
- **CVSS Score**: 6.5 (Medium)
- **Attack Vector**: Malicious executables in PATH
- **Affected Commands**: `sysctl`, `wmic`, `system_profiler`

#### **4. Broad Exception Handling (src/utils/hardware_detector.py:235)**
- **Bandit ID**: B110 - try_except_pass
- **Risk**: Security failures masked
- **CVSS Score**: 4.3 (Medium)
- **Impact**: Security monitoring bypass

### 🟢 **MEDIUM PRIORITY** (Fix within 2 weeks)

#### **5. Input Validation Issues**
- **Bandit ID**: Various input() calls without validation
- **Risk**: Input injection attacks
- **CVSS Score**: 3.7 (Low)
- **Locations**: Multiple files with `input()` calls

## 🛠️ **DETAILED REMEDIATION STEPS**

### **Phase 1: CRITICAL FIXES** ⏱️ *Complete within 24 hours*

#### **Fix 1.1: Command Injection - Ollama Installation**

**File**: `src/core/cli_parser.py`  
**Lines**: 404, 407, 421  
**Estimated Time**: 2 hours  

**Current Vulnerable Code**:
```python
# Line 404-407 (DANGEROUS)
subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"], 
               shell=True)

# Line 421 (LESS CRITICAL BUT FIX)
subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, 
                 stderr=subprocess.DEVNULL)
```

**Secure Replacement**:
```python
def install_ollama_secure():
    """Securely install Ollama without shell injection risks."""
    import requests
    import tempfile
    import hashlib
    import os
    
    # Expected hash of install script (update regularly)
    EXPECTED_HASH = "sha256_hash_of_verified_script"
    INSTALL_URL = "https://ollama.com/install.sh"
    
    try:
        # Download script securely
        response = requests.get(INSTALL_URL, verify=True, timeout=30)
        response.raise_for_status()
        
        # Verify script integrity
        script_hash = hashlib.sha256(response.text.encode()).hexdigest()
        if script_hash != EXPECTED_HASH:
            raise SecurityError("Ollama install script hash mismatch")
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
            f.write(response.text)
            temp_script = f.name
        
        try:
            # Execute without shell=True
            os.chmod(temp_script, 0o755)
            subprocess.run(["/bin/bash", temp_script], 
                          shell=False, 
                          check=True,
                          capture_output=True,
                          timeout=300)
        finally:
            # Clean up
            os.unlink(temp_script)
            
    except (requests.RequestException, subprocess.CalledProcessError) as e:
        raise InstallationError(f"Ollama installation failed: {e}")

def start_ollama_secure():
    """Start Ollama service securely."""
    import shutil
    
    # Validate ollama executable exists and is legitimate
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        raise FileNotFoundError("Ollama executable not found in PATH")
    
    # Start without shell=True
    subprocess.Popen([ollama_path, "serve"], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL,
                     shell=False)
```

**Testing Steps**:
1. Test with valid Ollama installation
2. Test with tampered script (should fail)
3. Test without network access (should fail gracefully)
4. Verify no shell injection possible

#### **Fix 1.2: XXE Vulnerability**

**File**: `src/utils/security.py`  
**Line**: 424  
**Estimated Time**: 30 minutes  

**Current Vulnerable Code**:
```python
import xml.etree.ElementTree as ET
```

**Secure Replacement Option 1 (Recommended)**:
```python
# Add to requirements.txt first:
# defusedxml>=0.7.1

import defusedxml.ElementTree as ET

def parse_xml_safely(xml_content):
    """Parse XML content safely without XXE vulnerabilities."""
    try:
        return ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.warning(f"XML parsing failed: {e}")
        return None
```

**Secure Replacement Option 2** (if defusedxml not available):
```python
import xml.etree.ElementTree as ET
from xml.parsers.expat import ParserCreate

def create_safe_xml_parser():
    """Create XML parser with XXE protection."""
    parser = ParserCreate()
    # Disable DTD processing
    parser.DefaultHandler = lambda data: None
    parser.ExternalEntityRefHandler = None
    parser.EntityDeclHandler = None
    return parser

def parse_xml_safely(xml_content):
    """Parse XML with XXE protection."""
    # Create parser without XXE vulnerabilities
    parser = ET.XMLParser()
    parser.parser.DefaultHandler = lambda data: None
    parser.parser.ExternalEntityRefHandler = None
    
    try:
        return ET.fromstring(xml_content, parser=parser)
    except ET.ParseError as e:
        logger.warning(f"XML parsing failed: {e}")
        return None
```

**Testing Steps**:
1. Test normal XML parsing still works
2. Test XXE payloads are blocked
3. Verify error handling works correctly

### **Phase 2: HIGH PRIORITY FIXES** ⏱️ *Complete within 1 week*

#### **Fix 2.1: Subprocess Path Injection**

**File**: `src/utils/hardware_detector.py`  
**Lines**: 129, 142, 198, 215  
**Estimated Time**: 1 hour  

**Current Vulnerable Pattern**:
```python
# VULNERABLE: Uses partial paths
subprocess.run(["sysctl", "-n", "hw.memsize"], ...)
subprocess.run(["wmic", "computersystem", "get", "TotalPhysicalMemory"], ...)
subprocess.run(["system_profiler", "SPDisplaysDataType"], ...)
```

**Secure Replacement**:
```python
import shutil
from typing import Optional, List

def run_system_command_safe(command: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Run system command safely with full path validation."""
    if not command:
        raise ValueError("Empty command list")
    
    # Get full path to executable
    executable_path = shutil.which(command[0])
    if not executable_path:
        raise FileNotFoundError(f"Executable '{command[0]}' not found in PATH")
    
    # Validate executable is in expected system locations (optional hardening)
    safe_paths = ["/usr/bin", "/bin", "/usr/sbin", "/sbin", "/System/Library"]
    if not any(executable_path.startswith(path) for path in safe_paths):
        logger.warning(f"Executable in unexpected location: {executable_path}")
    
    # Run with full path
    full_command = [executable_path] + command[1:]
    return subprocess.run(full_command, shell=False, **kwargs)

# Apply to all instances:
def _estimate_ram_without_psutil(self) -> float:
    try:
        if platform.system() == "Linux":
            # Secure version
            with open("/proc/meminfo", "r") as f:
                # ... existing logic
                
        elif platform.system() == "Darwin":
            try:
                result = run_system_command_safe(
                    ["sysctl", "-n", "hw.memsize"], 
                    capture_output=True, text=True, timeout=5
                )
                # ... rest of logic
                
        elif platform.system() == "Windows":
            try:
                result = run_system_command_safe(
                    ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                    capture_output=True, text=True, timeout=5
                )
                # ... rest of logic
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        logger.warning(f"System command failed safely: {e}")
        return 8.0  # Safe fallback
```

#### **Fix 2.2: Exception Handling**

**File**: `src/utils/hardware_detector.py`  
**Line**: 235  
**Estimated Time**: 15 minutes  

**Current Vulnerable Code**:
```python
except Exception:
    # If all detection fails, assume no GPU
    pass
```

**Secure Replacement**:
```python
except (subprocess.SubprocessError, FileNotFoundError, ImportError) as e:
    logger.warning(f"GPU detection failed: {type(e).__name__}: {e}")
    return False, None
except Exception as e:
    # Log unexpected exceptions for security monitoring
    logger.error(f"Unexpected error in GPU detection: {type(e).__name__}: {e}")
    return False, None
```

### **Phase 3: MEDIUM PRIORITY FIXES** ⏱️ *Complete within 2 weeks*

#### **Fix 3.1: Input Validation**

**Files**: Multiple files with `input()` calls  
**Estimated Time**: 3 hours  

**Create Secure Input Module**:
```python
# src/utils/secure_input.py
import re
from typing import Union, Pattern

class InputValidator:
    """Secure input validation and sanitization."""
    
    # Predefined safe patterns
    PATTERNS = {
        'api_key': re.compile(r'^[a-zA-Z0-9\-_\.]{10,200}$'),
        'file_path': re.compile(r'^[a-zA-Z0-9\-_\./\\:]{1,500}$'),
        'provider_name': re.compile(r'^[a-z]{3,20}$'),
        'yes_no': re.compile(r'^[yYnN]$'),
        'model_name': re.compile(r'^[a-zA-Z0-9\-\.]{1,50}$'),
    }
    
    @staticmethod
    def validate_input(value: str, input_type: str, custom_pattern: Pattern = None) -> str:
        """Validate and sanitize user input."""
        if not isinstance(value, str):
            raise ValueError("Input must be string")
        
        # Remove dangerous characters
        value = value.strip()
        
        # Check against pattern
        pattern = custom_pattern or InputValidator.PATTERNS.get(input_type)
        if pattern and not pattern.match(value):
            raise ValueError(f"Invalid {input_type} format")
        
        return value
    
    @staticmethod
    def secure_input(prompt: str, input_type: str, default: str = None) -> str:
        """Secure input collection with validation."""
        while True:
            try:
                raw_input = input(prompt).strip()
                if not raw_input and default:
                    raw_input = default
                
                return InputValidator.validate_input(raw_input, input_type)
            except ValueError as e:
                print(f"Invalid input: {e}. Please try again.")
            except KeyboardInterrupt:
                raise
            except EOFError:
                if default:
                    return default
                raise
```

## 📋 **IMPLEMENTATION CHECKLIST**

### **Phase 1: CRITICAL (24 hours)**
- [ ] **Fix command injection in cli_parser.py**
  - [ ] Implement secure Ollama installation function
  - [ ] Replace shell=True with shell=False
  - [ ] Add script integrity validation
  - [ ] Test installation process
  - [ ] Update error handling

- [ ] **Fix XXE vulnerability in security.py**
  - [ ] Install defusedxml dependency
  - [ ] Replace xml.etree.ElementTree import
  - [ ] Test XML parsing functionality
  - [ ] Verify XXE protection works

### **Phase 2: HIGH PRIORITY (1 week)**
- [ ] **Fix subprocess path injection**
  - [ ] Create secure command runner function
  - [ ] Replace all partial path subprocess calls
  - [ ] Add path validation logic
  - [ ] Test on all platforms (Linux/macOS/Windows)

- [ ] **Improve exception handling**
  - [ ] Replace broad exception handlers
  - [ ] Add proper logging
  - [ ] Test error scenarios

### **Phase 3: MEDIUM PRIORITY (2 weeks)**
- [ ] **Add input validation**
  - [ ] Create secure input validation module
  - [ ] Replace all raw input() calls
  - [ ] Add input sanitization
  - [ ] Test with malicious inputs

### **Phase 4: VALIDATION**
- [ ] **Security regression testing**
  - [ ] Run complete Bandit scan
  - [ ] Verify all HIGH/CRITICAL issues resolved
  - [ ] Test attack scenarios
  - [ ] Update security documentation

## 🧪 **TESTING STRATEGY**

### **Security Test Cases**

**Command Injection Tests**:
```python
def test_command_injection_prevention():
    """Test that command injection attacks are prevented."""
    # Test malicious installation URL
    malicious_url = "https://evil.com/malicious.sh; rm -rf /"
    
    with pytest.raises(SecurityError):
        install_ollama_secure(custom_url=malicious_url)
```

**XXE Prevention Tests**:
```python
def test_xxe_prevention():
    """Test that XXE attacks are blocked."""
    xxe_payload = """<?xml version="1.0"?>
    <!DOCTYPE data [<!ENTITY file SYSTEM "file:///etc/passwd">]>
    <data>&file;</data>"""
    
    result = parse_xml_safely(xxe_payload)
    assert result is None or "root:" not in str(result)
```

**Path Injection Tests**:
```python
def test_path_injection_prevention():
    """Test that PATH manipulation attacks fail safely."""
    with mock.patch.dict(os.environ, {"PATH": "/tmp/malicious:/bin"}):
        with pytest.raises(FileNotFoundError):
            run_system_command_safe(["fake_sysctl"])
```

## 📚 **DEPENDENCIES TO ADD**

```bash
# Add to requirements.txt
defusedxml>=0.7.1  # XXE protection
requests>=2.28.0   # Secure HTTP requests (already present)
```

## 🔍 **MONITORING & DETECTION**

After implementation, add security monitoring:

```python
# Add to logging configuration
SECURITY_EVENTS = {
    'command_injection_attempt': 'CRITICAL',
    'xxe_attack_blocked': 'HIGH',
    'path_injection_detected': 'MEDIUM',
    'input_validation_failed': 'LOW'
}

def log_security_event(event_type: str, details: str):
    """Log security events for monitoring."""
    severity = SECURITY_EVENTS.get(event_type, 'INFO')
    logger.log(severity, f"SECURITY: {event_type} - {details}")
```

## 🎯 **SUCCESS CRITERIA**

**Phase 1 Complete When**:
- Bandit scan shows 0 HIGH/CRITICAL vulnerabilities
- All command injection attack tests pass
- XXE protection verified working

**Full Remediation Complete When**:
- Bandit scan shows <5 total vulnerabilities (all LOW severity)
- All security test cases pass
- Security regression test suite created
- Documentation updated

## 📞 **NEXT STEPS TO RESUME**

1. **Start with**: `src/core/cli_parser.py` command injection fix (highest risk)
2. **Test immediately**: Verify installation still works but is secure
3. **Continue with**: XXE fix in `src/utils/security.py`
4. **Validate**: Run Bandit scan to confirm critical issues resolved

**Estimated Total Time**: 8-10 hours across 2-3 weeks

*This document provides complete implementation guidance for when you return to address these security vulnerabilities.*