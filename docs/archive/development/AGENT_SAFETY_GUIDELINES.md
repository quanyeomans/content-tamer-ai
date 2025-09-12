# Agent Safety Guidelines
*Critical rules for parallel agents to prevent breaking production functionality*

## 🚨 **CRITICAL IMPORT ARCHITECTURE RULES**

### **Domain Provider Import Patterns (NEVER CHANGE)**
```python
# ✅ CORRECT: AI providers must use absolute shared imports
from shared.infrastructure.filename_config import get_token_limit_for_provider

# ❌ FORBIDDEN: Relative imports beyond package boundary  
from ....shared.infrastructure.filename_config import get_token_limit_for_provider
# This breaks production and causes "attempted relative import beyond top-level package"
```

### **AI Provider Import Validation**
```bash
# MANDATORY: Test all AI provider imports after any agent changes
python -c "from src.domains.ai_integration.providers.openai_provider import OpenAIProvider; print('✅')"
python -c "from src.domains.ai_integration.providers.claude_provider import ClaudeProvider; print('✅')"  
python -c "from src.domains.ai_integration.providers.gemini_provider import GeminiProvider; print('✅')"
python -c "from src.domains.ai_integration.providers.deepseek_provider import DeepseekProvider; print('✅')"
python -c "from src.domains.ai_integration.providers.local_llm_provider import LocalLLMProvider; print('✅')"
```

## 🔒 **SECURITY CRITICAL PATTERNS**

### **API Key Storage (NEVER CHANGE)**
```python
# ✅ CORRECT: API keys excluded from file storage
if config_dict.get("api_key"):
    config_dict["api_key"] = None
    config_dict["api_key_source"] = "environment_variable_required"

# ❌ FORBIDDEN: API key file persistence
json.dump(config_dict, f)  # Where config_dict contains api_key
```

### **API Key Input (SECURITY CRITICAL)**
```python
# ✅ CORRECT: Masked API key input
api_key = Prompt.ask("Enter API key", password=True)

# ❌ FORBIDDEN: Plain text API key input  
api_key = input("Enter API key")  # Visible in console
```

## 🧪 **MANDATORY VALIDATION PATTERNS**

### **Before Any Agent Deployment**
1. **Identify import patterns** in target files
2. **Document expected behavior** before changes
3. **Test critical functionality** after each agent completes
4. **Validate no regression** in core user workflows

### **After Agent Completion**
1. **Run provider import validation** (commands above)
2. **Test configuration wizard flow** end-to-end
3. **Verify API key security** (no plain text storage)
4. **Run smoke tests** for critical user journeys

## 📋 **Agent Deployment Safety Checklist**

### **Pre-Deployment**
- [ ] **Document current import patterns** in target files
- [ ] **Test AI providers work** before agent changes
- [ ] **Identify security-critical code** that must not be modified
- [ ] **Set success criteria** for agent completion

### **During Deployment**
- [ ] **Monitor agent changes** to import statements
- [ ] **Stop agents** if they modify security-critical patterns
- [ ] **Validate incrementally** don't wait for all agents to complete
- [ ] **Test core functionality** after each critical change

### **Post-Deployment** 
- [ ] **Run complete provider validation** (mandatory)
- [ ] **Test configuration wizard** end-to-end
- [ ] **Verify no API key storage** to files
- [ ] **Run user workflow smoke tests**

## 🚫 **AGENT FORBIDDEN ACTIONS**

### **NEVER Allow Agents To:**
1. **Change import paths** in AI provider files without validation
2. **Modify API key handling** or security-related code
3. **Remove error handling** around external API calls
4. **Change configuration persistence** patterns
5. **Modify domain boundaries** between services

### **REQUIRE MANUAL REVIEW For:**
1. **Any import statement changes** in domain services
2. **Security-related modifications** (API keys, auth, validation)
3. **Configuration management changes**
4. **Provider service modifications**  
5. **Cross-domain dependency changes**

## 🎯 **Lesson from AI Provider Breakage**

**What Happened**: Parallel agents "improved" import statements by making them relative (`....shared`) which broke the Python import system.

**Why It Happened**: Agents didn't understand domain architecture and applied generic "import improvement" patterns.

**How to Prevent**: 
1. **Document architecture constraints** before agent deployment
2. **Test critical functionality** after each agent completion
3. **Use agent specialization** - only deploy agents on code they understand
4. **Validate incrementally** - don't batch validate all agent changes

**Critical Learning**: Agents are powerful but need architectural guardrails to prevent breaking production functionality while "improving" code quality.