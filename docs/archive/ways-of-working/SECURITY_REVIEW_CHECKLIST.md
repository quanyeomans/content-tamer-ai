# Security Review Checklist
*Secure-by-design checks for every change*

## API Key Security

### Environment Variables Only
- [ ] **No hardcoded keys**: API keys never appear in source code
- [ ] **No logging**: API keys never logged, printed, or written to files
- [ ] **Environment check**: Code reads from `os.environ.get()` only
- [ ] **Memory clearing**: API keys cleared from memory after use where possible

### User Input Security
- [ ] **Secure input**: Use `getpass()` or similar for API key entry
- [ ] **Display protection**: Only show partial key for user verification (first 10, last 4 chars)
- [ ] **Screen clearing**: Clear terminal after API key entry to remove visibility

### Error Message Security
- [ ] **No key leakage**: Error messages never include actual API keys
- [ ] **Partial display only**: Show `sk-proj-abc...xyz` format in errors
- [ ] **Safe logging**: Log events without sensitive data

## File System Security

### Path Validation
- [ ] **Directory traversal check**: All paths validated against `../` attacks
- [ ] **Absolute paths**: Resolve relative paths to absolute before processing
- [ ] **Sandbox enforcement**: Files only processed within allowed directories
- [ ] **Permission checks**: Verify read/write permissions before file operations

### File Content Security
- [ ] **Magic number check**: Validate file type by content, not just extension
- [ ] **Size limits**: Enforce reasonable file size limits (prevent resource exhaustion)
- [ ] **Content sanitization**: Remove potentially dangerous patterns before AI processing
- [ ] **Encoding validation**: Validate character encoding to prevent injection

### Temporary Files
- [ ] **Secure creation**: Use `tempfile.NamedTemporaryFile()` with appropriate permissions
- [ ] **Automatic cleanup**: Ensure temporary files deleted after processing
- [ ] **Restricted access**: Temporary files only readable by current user

## Input Validation

### User Inputs
- [ ] **Type checking**: Validate all user inputs match expected types
- [ ] **Length limits**: Enforce reasonable input length limits
- [ ] **Character whitelist**: Allow only safe characters in filenames/paths
- [ ] **Format validation**: Validate formats (emails, URLs, etc.) with proper regex

### Content Processing
- [ ] **Text extraction**: Sanitize extracted text before sending to AI
- [ ] **Content length**: Enforce token/character limits for AI processing  
- [ ] **Injection prevention**: Remove/escape potentially dangerous content patterns
- [ ] **Unicode safety**: Handle Unicode characters safely across platforms

## Network Security

### AI Provider Communication
- [ ] **HTTPS only**: All external API calls use encrypted connections
- [ ] **Certificate validation**: Don't disable SSL/TLS verification
- [ ] **Timeout handling**: Implement reasonable timeouts for network requests
- [ ] **Rate limiting**: Respect provider rate limits to avoid blocking

### Error Handling
- [ ] **Information disclosure**: Error messages don't leak internal system details
- [ ] **Stack trace filtering**: Production errors don't expose code internals
- [ ] **Safe defaults**: Error handling fails securely (deny by default)

## Data Protection

### User Content
- [ ] **Local processing**: Files processed locally, only content sent to AI
- [ ] **No storage**: User content never stored on external systems
- [ ] **Content-only transmission**: Never send actual files to AI providers
- [ ] **Encryption in transit**: All AI API calls encrypted

### Memory Management
- [ ] **Sensitive data clearing**: Clear sensitive data from memory after use
- [ ] **Resource cleanup**: Properly close file handles and network connections
- [ ] **Memory limits**: Prevent memory exhaustion from large files

## Security Testing

### Validation Tests
- [ ] **Path traversal test**: Verify directory traversal attacks fail safely
- [ ] **Malicious input test**: Test with potentially dangerous inputs
- [ ] **API key leak test**: Verify keys don't appear in logs/outputs
- [ ] **File validation test**: Test with malformed files and wrong extensions

### Error Condition Tests
- [ ] **Permission denied test**: Verify graceful handling of permission errors
- [ ] **Network failure test**: Test behavior when AI APIs unavailable
- [ ] **Resource exhaustion test**: Test with very large files
- [ ] **Invalid input test**: Test with malformed/malicious inputs

## Common Vulnerabilities to Avoid

### Path Traversal
```python
# BAD: Vulnerable to directory traversal
file_path = os.path.join(base_dir, user_filename)

# GOOD: Validate and resolve path safely
file_path = os.path.realpath(os.path.join(base_dir, user_filename))
if not file_path.startswith(os.path.realpath(base_dir)):
    raise ValueError("Invalid file path")
```

### Information Disclosure
```python
# BAD: Leaks internal system details
except Exception as e:
    return f"Database error: {str(e)}"

# GOOD: Safe error message
except Exception as e:
    logger.error(f"Database error: {str(e)}")  # Log details
    return "An internal error occurred. Please try again."  # User message
```

### Injection Prevention
```python
# BAD: Potential injection risk
query = f"SELECT * FROM files WHERE name='{user_input}'"

# GOOD: Parameterized/validated input
if not re.match(r'^[a-zA-Z0-9._-]+$', user_input):
    raise ValueError("Invalid filename characters")
```

## Red Flags: High Security Risk

**Stop immediately if:**
- [ ] API keys being logged or displayed
- [ ] File paths not validated for directory traversal
- [ ] User input used directly in file operations
- [ ] External API calls without encryption
- [ ] Error messages exposing system internals
- [ ] Temporary files not cleaned up
- [ ] File operations without permission checks

*Based on SECURITY_STANDARDS.md - Secure by design, not as an afterthought*