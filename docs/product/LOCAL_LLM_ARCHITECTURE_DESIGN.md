# Local LLM Integration - Architecture Design
*Self-contained AI processing for Content Tamer AI*

## Overview

This document defines the architecture for integrating local LLM capabilities into Content Tamer AI, enabling completely offline operation without external API dependencies.

## Architecture Decision: Ollama Backend

### Selected Framework: Ollama
**Rationale:**
- **Production-ready**: Battle-tested with robust model management
- **Seamless integration**: HTTP API aligns with existing provider pattern
- **Automatic optimization**: Handles quantization, model lifecycle, cross-platform issues
- **Minimal complexity**: Reduces integration overhead while maximizing reliability

### Alternative Frameworks Considered
- **llama.cpp**: Maximum control but complex integration and platform-specific builds
- **Transformers**: Familiar but higher memory overhead and slower inference
- **Decision**: Ollama provides the best balance of capability and implementation simplicity

## Model Portfolio (4 Recommended Models)

### Hardware-Based Model Tiers

#### Tier 1: Ultra-Lightweight (4GB RAM)
**Model**: Gemma 2 2B (Q4_K_M)
- **Memory requirement**: ~2.5GB
- **Download size**: 1.7GB
- **Inference time**: 15-30 seconds
- **Use case**: Laptops, older hardware, battery-powered devices

#### Tier 2: Standard (6GB RAM) 
**Model**: Llama 3.2 3B (Q4_K_M)
- **Memory requirement**: ~4-5GB
- **Download size**: 2.2GB
- **Inference time**: 8-15 seconds
- **Use case**: Most desktop systems, good price/performance ratio

#### Tier 3: Enhanced (8GB RAM)
**Model**: Mistral 7B (Q4_K_M)
- **Memory requirement**: ~6-7GB
- **Download size**: 4.4GB
- **Inference time**: 5-12 seconds
- **Use case**: Quality-focused users, systems with adequate RAM

#### Tier 4: Premium (10GB+ RAM)
**Model**: Llama 3.1 8B (Q4_K_M)
- **Memory requirement**: ~7-8GB
- **Download size**: 4.7GB
- **Inference time**: 3-8 seconds
- **Use case**: High-end systems, cloud-quality results

## System Architecture

### Core Components

#### 1. LocalLLMProvider
```python
class LocalLLMProvider(BaseProvider):
    """Ollama-based local LLM provider implementation."""
    
    def __init__(self, model_name: str, ollama_host: str = "localhost:11434"):
        self.model_name = model_name
        self.client = OllamaClient(host=ollama_host)
    
    def generate_filename(self, text: str, image_b64: str = None) -> str:
        """Generate filename using local model."""
        prompt = get_secure_filename_prompt_template("local")
        response = self.client.generate(self.model_name, prompt + text)
        return validate_generated_filename(response.text)
```

#### 2. ModelManager
```python
class ModelManager:
    """Handles model lifecycle operations."""
    
    async def download_model(self, model_name: str) -> bool
    async def verify_model(self, model_name: str) -> bool
    async def load_model(self, model_name: str) -> bool
    async def unload_model(self, model_name: str) -> bool
    def list_available_models() -> List[ModelInfo]
    def get_model_status(self, model_name: str) -> ModelStatus
```

#### 3. HardwareDetector
```python
class HardwareDetector:
    """Detects system capabilities and recommends models."""
    
    def detect_system_tier(self) -> Tuple[str, List[str]]
    def get_available_memory(self) -> int
    def check_gpu_acceleration(self) -> bool
    def recommend_models(self) -> List[ModelRecommendation]
```

#### 4. ResourceMonitor
```python
class ResourceMonitor:
    """Monitors resource usage during inference."""
    
    def track_memory_usage(self) -> MemoryStats
    def check_memory_pressure(self) -> bool
    def trigger_cleanup_if_needed(self) -> None
```

### Integration Points

#### Provider Factory Extension
```python
# In ai_providers.py
AI_PROVIDERS["local"] = [
    "gemma-2-2b",
    "llama3.2-3b", 
    "mistral-7b",
    "llama3.1-8b"
]

class AIProviderFactory:
    @staticmethod
    def create(provider: str, model: str, api_key: str = None):
        if provider == "local":
            return LocalLLMProvider(model)
        # ... existing providers
```

#### CLI Integration
```bash
# New CLI options
content-tamer-ai --provider local --model gemma-2-2b
content-tamer-ai --setup-local-llm
content-tamer-ai --list-local-models
content-tamer-ai --check-local-requirements
```

## User Experience Flow

### Initial Setup
1. **Hardware detection**: Automatic system analysis
2. **Model recommendation**: Present 1-2 optimal models
3. **Informed choice**: Display memory requirements, download sizes, performance
4. **One-click setup**: Download and configure selected model
5. **Verification**: Test model with sample document

### Runtime Operation
1. **Model loading**: Automatic loading on first use (with progress indicator)
2. **Processing**: Standard filename generation workflow
3. **Resource monitoring**: Background memory/CPU tracking
4. **Graceful degradation**: Fallback to simpler models or timestamp naming

## Security & Privacy

### Data Isolation
- All processing occurs locally
- No data transmission to external services
- Models stored in protected application directory

### Model Verification
- Checksum validation for downloaded models
- Signature verification where available
- Corruption detection and automatic redownload

### Secure Configuration
- Local model settings stored in application config
- No API keys required or stored
- Secure model update mechanism with rollback

## Performance Characteristics

### Memory Usage Patterns
```
Model Load Time    Inference Time    Peak Memory
Gemma 2B    30-45s         15-30s           2.5GB
Llama 3.2   45-60s          8-15s           4-5GB
Mistral 7B  60-90s          5-12s           6-7GB
Llama 3.1   90-120s         3-8s            7-8GB
```

### Optimization Strategies
- **Model caching**: Keep loaded model in memory between files
- **Batch processing**: Process multiple files in sequence
- **Memory management**: Monitor and warn at 80% memory usage
- **CPU optimization**: Utilize available cores for inference acceleration

## Error Handling & Fallbacks

### Failure Scenarios
- **Model download failure**: Resume capability, clear error messages
- **Memory exhaustion**: Automatic fallback to smaller model
- **Model corruption**: Detection and redownload
- **Inference failure**: Fallback to timestamp naming with user notification

### Recovery Mechanisms
- **Automatic model repair**: Detect and fix corrupted models
- **Memory pressure handling**: Unload models when memory is needed
- **Graceful degradation**: Maintain core functionality even with model failures

## Quality & Performance Targets

### Functional Requirements
- **Setup success rate**: >95% successful installations
- **Inference reliability**: >99% successful filename generations
- **Quality retention**: >80% quality score vs cloud models

### Performance Requirements
- **Tier 1**: Filename generation <30 seconds
- **Tier 2**: Filename generation <15 seconds  
- **Tier 3**: Filename generation <12 seconds
- **Tier 4**: Filename generation <8 seconds

### Resource Efficiency
- **Memory overhead**: <20% above theoretical model requirements
- **CPU utilization**: Efficient multi-core usage
- **Storage efficiency**: Compressed model storage

## Implementation Phases

### Phase 1: Core Integration
- LocalLLMProvider implementation
- Basic ModelManager functionality
- Hardware detection and model recommendation
- CLI integration for model management

### Phase 2: Enhanced Features  
- Resource monitoring and optimization
- Advanced error handling and recovery
- Performance tuning and caching
- User experience improvements

### Phase 3: Production Readiness
- Comprehensive testing across hardware tiers
- Documentation and user guides
- Performance optimization
- Long-term model management (updates, migrations)

## Dependencies

### Required
- **Ollama**: Model runtime and management
- **requests**: HTTP communication with Ollama
- **psutil**: System resource monitoring

### Optional
- **GPUtil**: GPU detection and monitoring (if available)
- **py-cpuinfo**: Detailed CPU capability detection

## Backward Compatibility

### Zero Breaking Changes
- Existing cloud provider functionality unchanged
- Current configuration files remain valid
- All existing CLI options continue to work

### Migration Support
- Smooth transition for existing users
- Optional local model setup
- Hybrid operation support (mix local and cloud providers)

*This architecture provides a robust foundation for local LLM integration while maintaining the simplicity and reliability of the existing Content Tamer AI system.*