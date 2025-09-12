# Security Operations

## 🚨 Security Response SLA

### Severity Levels
```bash
CRITICAL - Exploit in wild, data exposure         → Fix in 4 hours
HIGH     - Exploitable vulnerability, no PoC yet  → Fix in 24 hours  
MEDIUM   - Requires specific conditions           → Fix in 1 week
LOW      - Defense in depth, minor issue          → Next release
```

## 🔒 Automated Security Gates

### Pre-Commit Hooks
```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
  - id: security-scan
    name: Bandit Security Scan
    entry: bandit -r src/ -ll
    language: system
    types: [python]
  
  - id: no-secrets
    name: Check for Secrets
    entry: git diff --cached | grep -E "(api_key|secret|token|password)" 
    language: system
```

### CI/CD Pipeline
```yaml
# GitHub Actions / GitLab CI
security-scan:
  script:
    - bandit -r src/ -f json > bandit.json
    - safety check --json > safety.json
    - grep -r "api_key\|secret" src/ && exit 1 || true
  artifacts:
    reports:
      sast: bandit.json
```

### Runtime Monitoring
```python
# Log sanitization middleware
class SecurityMiddleware:
    def process_log(self, message: str) -> str:
        # Redact patterns that look like secrets
        patterns = [
            (r'sk-[a-zA-Z0-9]{48}', '[API_KEY]'),
            (r'key["\']?\s*[:=]\s*["\'][^"\']+', '[REDACTED]'),
            (r'[a-f0-9]{64}', '[HASH]'),  # SHA256
        ]
        for pattern, replacement in patterns:
            message = re.sub(pattern, replacement, message)
        return message
```

## 🛡️ Security Checklist

### For Every Commit
```markdown
- [ ] No API keys in code (grep check)
- [ ] No secrets in logs (sanitization active)
- [ ] Paths validated (no traversal)
- [ ] Input sanitized (no injection)
- [ ] Errors sanitized (no info leak)
```

### Weekly Security Audit
```bash
# Full security audit script
#!/bin/bash
echo "=== Security Audit $(date) ==="

# 1. SAST Scan
bandit -r src/ -f txt

# 2. Dependency Check
safety check
pip list --outdated

# 3. Secret Scanning
git log --oneline -100 | grep -i "api\|key\|secret" || echo "Git history clean"
grep -r "api_key\|secret\|password" src/ || echo "No hardcoded secrets"

# 4. File Permissions
find . -type f -perm 0777 | head -20

# 5. Log Analysis
grep -r "logger.*f\"" src/ | head -20  # f-string in logging
```

## 🔐 Vulnerability Response Playbook

### 1. Discovery
```bash
# Immediate assessment
bandit -r src/ -ll | grep HIGH
safety check | grep -i vulnerable
```

### 2. Containment
```python
# Immediate mitigation
if vulnerability == "api_key_exposure":
    # Rotate keys immediately
    # Add to .env: NEW_API_KEY=xxx
    # Update code to use env var
    os.environ['API_KEY']
```

### 3. Remediation
```python
# Fix pattern examples

# SQL Injection → Parameterized queries
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# Path Traversal → Validate paths
safe_path = os.path.join(base_dir, os.path.basename(user_input))

# XSS → Escape output
from html import escape
safe_output = escape(user_input)
```

### 4. Validation
```bash
# Verify fix
bandit -r src/ -ll | grep -c HIGH  # Should be 0
python -m pytest tests/security/ -v  # Security tests pass
```

## 🔍 Security Patterns

### API Key Management
```python
# NEVER hardcode
api_key = "sk-abc123"  # FORBIDDEN

# ALWAYS use environment
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise ValueError("API key not configured")
```

### Input Validation
```python
def validate_filename(filename: str) -> str:
    """Sanitize filename for security."""
    # Remove path components
    filename = os.path.basename(filename)
    # Remove suspicious patterns
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Limit length
    return filename[:255]
```

### Error Handling
```python
def secure_error_handler(error: Exception) -> str:
    """Sanitize error messages."""
    # Log full error internally
    logger.error("Full error: %s", str(error), exc_info=True)
    
    # Return safe message to user
    if isinstance(error, ValidationError):
        return f"Invalid input: {error.field}"
    else:
        return "Operation failed. Contact support with ID: " + request_id
```

## 📊 Security Metrics

### Track Monthly
- Vulnerabilities found: ___ HIGH, ___ MEDIUM
- Mean time to remediation: ___ hours
- Dependencies updated: ___/___
- Security tests added: ___

### Security Debt
```bash
# Count security TODOs
grep -r "TODO.*security\|FIXME.*security" src/ | wc -l

# Count suppressed warnings
grep -r "nosec\|pylint.*disable" src/ | wc -l
```

## 🚀 Quick Commands

### One-Line Security Check
```bash
bandit -r src/ -ll && safety check && echo "✓ Security OK"
```

### Find Potential Secrets
```bash
grep -r "api\|key\|secret\|token\|password" src/ --include="*.py" | grep -v "^#"
```

### Check Recent Commits
```bash
git diff HEAD~10 | grep "^+" | grep -i "api_key\|secret\|password"
```