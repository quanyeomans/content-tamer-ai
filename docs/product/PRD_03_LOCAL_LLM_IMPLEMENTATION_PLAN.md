# Local LLM Feature - Implementation Plan
*Following PRE-CODE_CHECKLIST and IMPLEMENTATION_WORKFLOW*

## 🛡️ PRE-CODE CHECKLIST COMPLETION

### ✅ Gate 1: Strategy Alignment
- [x] **Test approach planned**: Extend `tests/test_ai_providers.py` for LocalLLMProvider tests
- [x] **Security implications assessed**: Local model verification, no API key exposure, data isolation  
- [x] **Backward compatibility considered**: Zero breaking changes - new provider follows existing pattern
- [x] **Minimal scope defined**: Core LocalLLMProvider + ModelManager + CLI integration

### ✅ Gate 2: TodoWrite Planning  
- [x] **Todo list created**: Implementation tasks broken down and tracked
- [x] **Test files identified**: `tests/test_ai_providers.py`, `tests/test_integration.py`
- [x] **Security checks planned**: Model verification, checksum validation, secure storage
- [x] **Completion criteria defined**: Working local LLM provider with 4 model options

### ✅ Gate 3: Test-First Commitment
- [x] **Test file identified**: `tests/test_ai_providers.py` - will extend existing AI provider tests
- [x] **Test behavior defined**: LocalLLMProvider generates filenames following same interface
- [x] **Mock strategy planned**: Mock Ollama HTTP client, use real file operations with tempdir
- [x] **Edge cases considered**: Model download failures, OOM conditions, Ollama service down

### ✅ Gate 4: Security Review
- [x] **API key safety**: No API keys needed for local models - completely eliminated
- [x] **Path validation**: Model storage in secure app directory, validate downloaded files
- [x] **Input sanitization**: Reuse existing filename validation and sanitization  
- [x] **Error message safety**: No sensitive paths or model details in user-facing errors

## 📋 IMPLEMENTATION WORKFLOW

### Phase 1: Foundation (Tests First)
```python
# Tests to write FIRST in tests/test_ai_providers.py

class TestLocalLLMProvider(unittest.TestCase):
    def test_local_provider_creation(self):
        """Test LocalLLMProvider can be created with model name."""
        
    def test_filename_generation_success(self):
        """Test successful filename generation via mocked Ollama."""
        
    def test_filename_generation_failure(self):
        """Test graceful failure when Ollama is unavailable."""
        
    def test_model_validation(self):
        """Test model validation and checksum verification."""
```

### Phase 2: Core Implementation
1. **LocalLLMProvider class** (`src/ai_providers.py`)
2. **ModelManager class** (`src/utils/model_manager.py`) 
3. **HardwareDetector class** (`src/utils/hardware_detector.py`)
4. **CLI integration** (`src/core/cli_parser.py`)

### Phase 3: Integration & Testing
1. **Provider factory integration**
2. **End-to-end testing with real models**
3. **Performance validation across memory tiers**
4. **Error handling and fallback testing**

## 🔧 DETAILED IMPLEMENTATION TASKS

### Task 1: Test Infrastructure Setup
**File**: `tests/test_ai_providers.py`
**Estimated time**: 2-3 hours

```python
# Mock Ollama client for testing
@patch('requests.post')
def test_ollama_communication(self, mock_post):
    mock_post.return_value.json.return_value = {
        'response': 'document_analysis_report'
    }
    provider = LocalLLMProvider('gemma-2-2b')
    result = provider.generate_filename("test content", None)
    self.assertEqual(result, 'document_analysis_report')
```

### Task 2: LocalLLMProvider Implementation  
**File**: `src/ai_providers.py`
**Estimated time**: 3-4 hours

```python
class LocalLLMProvider(BaseProvider):
    def __init__(self, model_name: str, host: str = "localhost:11434"):
        self.model_name = model_name
        self.host = host
        self.client = requests.Session()
    
    def generate_filename(self, text: str, image_b64: str = None) -> str:
        prompt = get_secure_filename_prompt_template("local")
        # Implementation with error handling and validation
```

### Task 3: ModelManager Implementation
**File**: `src/utils/model_manager.py` 
**Estimated time**: 4-5 hours

```python  
class ModelManager:
    def __init__(self, ollama_host: str = "localhost:11434"):
        self.host = ollama_host
        self.models_dir = self._get_models_directory()
    
    async def download_model(self, model_name: str) -> bool:
        # Download with progress tracking and verification
    
    def verify_model(self, model_name: str) -> bool:
        # Checksum verification and integrity check
```

### Task 4: HardwareDetector Implementation
**File**: `src/utils/hardware_detector.py`
**Estimated time**: 2-3 hours

```python
class HardwareDetector:
    def detect_system_tier(self) -> Tuple[str, List[str]]:
        available_ram = psutil.virtual_memory().available
        # Logic to determine hardware tier and recommend models
```

### Task 5: CLI Integration
**File**: `src/core/cli_parser.py`
**Estimated time**: 2-3 hours

```python  
# Add new CLI arguments
parser.add_argument('--setup-local-llm', action='store_true')
parser.add_argument('--list-local-models', action='store_true') 
parser.add_argument('--check-local-requirements', action='store_true')
```

### Task 6: Provider Factory Integration
**File**: `src/ai_providers.py`
**Estimated time**: 1-2 hours

```python
AI_PROVIDERS["local"] = [
    "gemma-2-2b", "llama3.2-3b", "mistral-7b", "llama3.1-8b"
]

# Update factory method to handle local provider
```

## 🧪 TESTING STRATEGY

### Unit Tests
- **LocalLLMProvider**: Mock Ollama responses, test error handling
- **ModelManager**: Mock downloads, test verification logic  
- **HardwareDetector**: Mock system resources, test tier detection
- **CLI integration**: Test argument parsing and help text

### Integration Tests  
- **End-to-end filename generation**: With mocked Ollama responses
- **Model download simulation**: Using test models or mocked downloads
- **Hardware detection**: Across different simulated system configurations
- **Error scenarios**: Ollama down, insufficient memory, corrupted models

### System Tests
- **Real model testing**: Download and test with actual small models
- **Performance validation**: Measure inference times across tiers
- **Resource monitoring**: Validate memory usage predictions
- **Cross-platform**: Test on Linux, macOS, Windows (where possible)

## 🔒 SECURITY VALIDATION CHECKLIST

### Model Security
- [ ] **Checksum verification**: All downloaded models verified against known checksums
- [ ] **Secure storage**: Models stored in protected application directory  
- [ ] **Access controls**: Appropriate file permissions on model directory
- [ ] **Update security**: Secure mechanism for model updates with rollback

### Data Security
- [ ] **Local processing**: Verify no data leaves the system during processing
- [ ] **Temporary files**: Secure handling of temporary processing files
- [ ] **Memory protection**: No sensitive data in swap/hibernation files
- [ ] **Error logging**: No sensitive data in logs or error messages

### System Security  
- [ ] **Service isolation**: Ollama runs with minimal required permissions
- [ ] **Network security**: Ollama only listens on localhost
- [ ] **Resource limits**: Prevent DoS through memory/CPU exhaustion
- [ ] **Input validation**: Sanitize all inputs to prevent injection attacks

## 📐 USER EXPERIENCE DESIGN

### Setup Flow
```bash
# Auto-detect and setup recommended model
$ content-tamer-ai --setup-local-llm
> Detecting system capabilities...
> Recommended model: Llama 3.2 3B (6GB RAM required)
> Download size: 2.2GB
> Continue? [Y/n]: Y
> Downloading model... [████████████████] 100%
> Verifying model integrity... ✓
> Setup complete! Try: content-tamer-ai --provider local

# Manual model selection
$ content-tamer-ai --list-local-models  
Available models:
  gemma-2-2b     (2.5GB RAM, 1.7GB download) - Ultra-lightweight
  llama3.2-3b    (4-5GB RAM, 2.2GB download) - Recommended for your system
  mistral-7b     (6-7GB RAM, 4.4GB download) - High quality
  llama3.1-8b    (7-8GB RAM, 4.7GB download) - Maximum performance
```

### Runtime Experience
```bash
# Standard usage with local model
$ content-tamer-ai --provider local --model llama3.2-3b
> Loading model (first run may take 60 seconds)... ✓
> Processing documents...
> Generated: "Q3_Financial_Report_Analysis_2024.pdf"

# Mixed usage (some local, some cloud)
$ content-tamer-ai --provider local --model gemma-2-2b --fallback-provider openai
> Using local model with cloud fallback for failures
```

### Error Handling UX
```bash
# Insufficient memory
$ content-tamer-ai --provider local --model mistral-7b
⚠️  Warning: Insufficient memory for Mistral 7B (requires 6GB, 4GB available)
💡 Recommended: Use 'llama3.2-3b' or increase available memory
🔄 Auto-switching to Llama 3.2 3B...

# Model not downloaded
$ content-tamer-ai --provider local --model mistral-7b
❌ Model 'mistral-7b' not found locally
💡 Download with: content-tamer-ai --setup-local-llm --model mistral-7b
```

## 📊 SUCCESS CRITERIA & METRICS

### Functional Success
- [ ] **Core functionality**: Local LLM provider generates filenames successfully
- [ ] **Model management**: Download, verify, load, and unload models reliably  
- [ ] **Hardware detection**: Accurately detect system capabilities and recommend models
- [ ] **CLI integration**: All new CLI commands work as specified
- [ ] **Error handling**: Graceful failure with helpful error messages

### Performance Success
- [ ] **Tier 1 (4GB)**: <30 second filename generation
- [ ] **Tier 2 (6GB)**: <15 second filename generation
- [ ] **Tier 3 (8GB)**: <12 second filename generation
- [ ] **Tier 4 (10GB)**: <8 second filename generation
- [ ] **Memory efficiency**: <20% overhead above theoretical requirements

### Quality Success  
- [ ] **Filename quality**: >80% user satisfaction vs cloud models
- [ ] **Setup success**: >95% successful model downloads and configuration
- [ ] **Reliability**: >99% successful filename generations after setup
- [ ] **Security**: Pass all security validation checks

### User Experience Success
- [ ] **Ease of setup**: Non-technical users can set up local models
- [ ] **Clear documentation**: Comprehensive user guide and troubleshooting
- [ ] **Helpful errors**: Error messages include actionable next steps
- [ ] **Performance feedback**: Users understand resource usage and limitations

## 🚀 IMPLEMENTATION TIMELINE

### Week 1: Foundation
- Complete test infrastructure setup
- Implement LocalLLMProvider core functionality  
- Basic ModelManager with download capability

### Week 2: Integration
- HardwareDetector implementation
- CLI integration and argument parsing
- Provider factory integration

### Week 3: Testing & Polish
- Comprehensive testing with mocked models
- Error handling and edge cases
- Documentation and user experience

### Week 4: Validation  
- Real model testing and performance validation
- Security audit and validation
- Final integration testing and deployment

## ⚠️ RISKS & MITIGATIONS

### Technical Risks
- **Ollama dependency**: Mitigate with clear installation instructions and fallback
- **Memory pressure**: Implement monitoring and graceful degradation
- **Model quality**: Extensive testing and user feedback collection
- **Cross-platform compatibility**: Test on multiple platforms during development

### User Experience Risks  
- **Complex setup**: Mitigate with automatic hardware detection and recommendations
- **Poor performance on low-end hardware**: Clear expectations and tier guidelines  
- **Storage requirements**: Warn users about disk space requirements upfront
- **Confusion with existing providers**: Clear documentation and CLI help

*This implementation plan follows our established Ways of Working and provides a comprehensive roadmap for adding local LLM capabilities to Content Tamer AI.*