# Security Testing Strategy
*Specialized testing approach for security-critical functionality*

## 🛡️ **Security Testing Principles**

### 1. **Negative Requirements Testing**
**Test what should NOT happen, not just what should happen**

```python
def test_api_key_never_appears_in_logs(self):
    """
    SECURITY TEST: Verify API key never appears in any log output.
    This is more important than testing exact sanitization format.
    """
    api_key = "sk-proj-real-api-key-for-testing"
    
    # Test all logging scenarios
    logger.debug(f"Auth failed: {api_key}")
    logger.error(f"Invalid key: {api_key}")
    
    # The key requirement: original key MUST NOT appear anywhere
    all_logs = get_all_log_outputs()
    self.assertNotIn(api_key, all_logs, "SECURITY FAILURE: API key found in logs")
```

### 2. **Adversarial Testing**
**Test like an attacker trying to extract secrets**

```python
def test_api_key_extraction_attempts(self):
    """Test various ways an attacker might try to extract API keys."""
    api_key = "sk-proj-test123456789"
    
    attack_vectors = [
        f"Debug info: {api_key}",           # Direct logging
        f"Error: Authentication failed with key {api_key}",  # Error messages
        {"api_key": api_key, "status": "failed"},  # Dictionary logging
        Exception(f"Invalid key: {api_key}"),      # Exception messages
    ]
    
    for attack_vector in attack_vectors:
        with self.subTest(vector=str(attack_vector)[:20]):
            sanitized = sanitize_log_message(str(attack_vector))
            self.assertNotIn(api_key, sanitized, 
                           f"API key leaked through: {type(attack_vector)}")
```

### 3. **Integration Security Testing**
**Test complete workflows for secret exposure**

```python
def test_end_to_end_secret_protection(self):
    """Test entire processing workflow for secret leakage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up fake API key in environment
        fake_key = "sk-proj-integration-test-key"
        os.environ["OPENAI_API_KEY"] = fake_key
        
        try:
            # Run complete file processing workflow
            result = process_files_with_ai(temp_dir, provider="openai")
            
            # Check all possible output locations
            log_files = glob.glob(f"{temp_dir}/**/*.log", recursive=True)
            console_output = capture_console_output()
            error_files = glob.glob(f"{temp_dir}/**/errors.*", recursive=True)
            
            # Verify key appears nowhere
            all_outputs = [console_output] + [read_file(f) for f in log_files + error_files]
            for output in all_outputs:
                self.assertNotIn(fake_key, output, "API key found in system output")
                
        finally:
            del os.environ["OPENAI_API_KEY"]
```

## 🎯 **Security Test Categories**

### **Category 1: Input Sanitization Tests**
- Test all user input paths for secret injection
- Test environment variable handling
- Test configuration file parsing

### **Category 2: Output Sanitization Tests** 
- Test all logging functions
- Test error message generation
- Test file output operations
- Test console/terminal output

### **Category 3: Storage Security Tests**
- Test temporary file creation
- Test persistent storage
- Test memory cleanup

### **Category 4: Error Condition Security Tests**
- Test exception handling with secrets
- Test timeout/failure scenarios
- Test resource exhaustion conditions

## 📋 **Security Test Checklist**

For every security-critical feature:

- [ ] **Boundary Value Tests**: Test with minimum/maximum length secrets
- [ ] **Format Variation Tests**: Test different API key formats  
- [ ] **Encoding Tests**: Test with different character encodings
- [ ] **Injection Tests**: Test with malicious input patterns
- [ ] **Performance Tests**: Verify sanitization doesn't cause performance issues
- [ ] **Memory Tests**: Verify secrets are cleared from memory
- [ ] **Concurrency Tests**: Test sanitization under concurrent access

## 🔍 **Security Test Data Management**

### **Safe Test API Keys**
```python
# Use predictable test keys that are safe to include in tests
TEST_API_KEYS = {
    "openai_test": "sk-proj-test123456789abcdef",
    "claude_test": "sk-ant-test123456789abcdef", 
    "invalid_test": "not-a-real-key-12345",
}

# Never use real API keys in tests
# Never commit real API keys to repository
```

### **Test Environment Isolation**
- Use temporary directories for all file operations
- Clear environment variables after tests
- Mock external API calls to prevent real key usage
- Use test-specific loggers to capture output

*This strategy ensures security features are thoroughly tested from an adversarial perspective.*