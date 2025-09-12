# Secure Logging Guide
*Preventing API keys and secrets from appearing in logs*

## 🚨 Critical Security Issue Resolved

**Issue**: API keys and secrets could be exposed in debug logs and error messages.

**Solution**: Implemented automatic secret sanitization for all logging functions.

## ✅ Secure Logging Implementation

### Automatic Secret Sanitization

All API keys are automatically sanitized in log messages:

- **OpenAI keys**: `sk-proj-abc123...` → `sk-proj-abc***`
- **Claude keys**: `sk-ant-abc123...` → `sk-ant***`  
- **Google keys**: `AIzaABC123...` → `AIza***`

### Updated Vulnerable Code

**Fixed in `src/utils/error_handling.py`:**
```python
# Before (VULNERABLE)
logger.debug(f"Attempt {attempt + 1} failed for {filename}: {str(e)}")

# After (SECURE)  
sanitized_error = sanitize_log_message(str(e))
logger.debug(f"Attempt {attempt + 1} failed for {filename}: {sanitized_error}")
```

**Fixed in `src/core/file_processor.py` (2 locations):**
```python
# Before (VULNERABLE)
with open(ERROR_LOG_FILE, mode="a", encoding="utf-8") as log:
    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\\n")

# After (SECURE)
sanitized_error_msg = sanitize_log_message(error_msg)
with open(ERROR_LOG_FILE, mode="a", encoding="utf-8") as log:
    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {sanitized_error_msg}\\n")
```

### Usage for Developers

**Option 1: Use sanitization functions directly**
```python
from utils.security import sanitize_log_message

# Before logging any message that might contain secrets
message = f"API error: {error_with_potential_key}"
sanitized_message = sanitize_log_message(message)
logger.error(sanitized_message)
```

**Option 2: Use secure logging helpers**
```python
from utils.security import secure_log_error, secure_log_debug

# These automatically sanitize messages
secure_log_error(logger, f"Authentication failed with key: {api_key}")
secure_log_debug(logger, f"Processing error: {error_message}")
```

**Option 3: Use SecureLogger class**
```python
from utils.security import SecureLogger

# Create logger that automatically sanitizes all messages
logger = SecureLogger("my_module")
logger.error(f"Failed with key: {api_key}")  # Automatically sanitized
```

## 🔍 Secret Detection Patterns

The sanitization detects and removes:

- API keys from all major providers (OpenAI, Claude, Google, DeepSeek)
- Long alphanumeric strings that might be tokens
- Environment variables containing secret patterns (`*API_KEY`, `*SECRET`, etc.)

## 📋 Security Checklist

- [x] **API key logging vulnerability fixed** in error_handling.py
- [x] **Sanitization functions created** for all logging scenarios
- [x] **Test coverage added** for secret protection
- [x] **Environment variable protection** implemented
- [x] **Exception logging protection** added for stack traces

## 🛡️ Prevention Strategy

**For all new code:**
1. **Use secure logging functions** from `utils.security`
2. **Never log raw error messages** without sanitization
3. **Test logging with fake API keys** to verify sanitization
4. **Review logs before production** to ensure no secrets leak

## ⚠️ Developer Guidelines

**NEVER do this:**
```python
# DANGEROUS - Could log API keys
logger.debug(f"Error details: {str(exception)}")
logger.error(f"Failed request: {api_response}")
```

**ALWAYS do this:**
```python
# SAFE - Sanitizes secrets automatically
from utils.security import sanitize_log_message
logger.debug(f"Error details: {sanitize_log_message(str(exception))}")
logger.error(f"Failed request: {sanitize_log_message(api_response)}")
```

## 🧹 Log Cleanup and Maintenance

### Sanitize Existing Logs
```bash
# Check for and sanitize any existing log files
python scripts/sanitize_logs.py

# Sanitize a specific log file
python scripts/sanitize_logs.py --file data/.processing/errors.log
```

### Set Up Secure Log Rotation
```python
from utils.security import setup_secure_log_rotation, cleanup_old_logs

# Set up rotating log file with automatic sanitization
handler = setup_secure_log_rotation(
    log_file_path="logs/app.log",
    max_size_mb=10,  # Rotate when file reaches 10MB
    backup_count=5   # Keep 5 backup files
)

# Clean up logs older than 30 days
cleanup_old_logs("data/.processing", days_to_keep=30)
```

## 📋 Complete Security Audit Results

- **3 vulnerabilities found and fixed**:
  - `src/utils/error_handling.py:212` - Debug logging of exceptions
  - `src/core/file_processor.py:179` - Direct file logging of errors  
  - `src/core/file_processor.py:533` - Runtime error file logging
- **0 existing log files found** with exposed secrets
- **Automatic sanitization** implemented for all future logging
- **Log cleanup utilities** created for maintenance

*This comprehensive security implementation ensures that API keys never appear in log files, debug output, or error messages, with automatic cleanup processes to maintain security over time.*