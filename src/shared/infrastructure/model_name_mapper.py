"""
Model Name Mapper

Provides centralized mapping between internal model names and Ollama model names.
This solves the systemic issue of inconsistent model naming conventions.

Internal format: modelname-size (e.g., llama3.1-8b)
Ollama format: modelname:size (e.g., llama3.1:8b)
"""

from typing import Dict, Optional


class ModelNameMapper:
    """Maps between internal model names and Ollama model names."""
    
    # Comprehensive mapping of all model name variations
    MODEL_NAME_MAP: Dict[str, str] = {
        # Internal name -> Ollama name
        "gemma-2-2b": "gemma2:2b",
        "gemma2-2b": "gemma2:2b",
        "llama3.2-3b": "llama3.2:3b",
        "llama3.2-1b": "llama3.2:1b",
        "mistral-7b": "mistral:7b",
        "mistral-nemo": "mistral-nemo:latest",
        "llama3.1-8b": "llama3.1:8b",
        "llama3.1-70b": "llama3.1:70b",
        "llama3-8b": "llama3:8b",
        "llama3-70b": "llama3:70b",
        "phi3-mini": "phi3:mini",
        "phi3-medium": "phi3:medium",
        "qwen2-7b": "qwen2:7b",
        "qwen2.5-7b": "qwen2.5:7b",
        "codellama-7b": "codellama:7b",
        "codellama-13b": "codellama:13b",
        # Already correct format (passthrough)
        "gemma2:2b": "gemma2:2b",
        "llama3.2:3b": "llama3.2:3b",
        "llama3.2:1b": "llama3.2:1b",
        "mistral:7b": "mistral:7b",
        "llama3.1:8b": "llama3.1:8b",
        "llama3.1:70b": "llama3.1:70b",
        "llama3:8b": "llama3:8b",
        "llama3:70b": "llama3:70b",
    }
    
    # Reverse mapping for display/configuration
    OLLAMA_TO_INTERNAL: Dict[str, str] = {
        "gemma2:2b": "gemma2-2b",
        "llama3.2:3b": "llama3.2-3b",
        "llama3.2:1b": "llama3.2-1b",
        "mistral:7b": "mistral-7b",
        "mistral-nemo:latest": "mistral-nemo",
        "llama3.1:8b": "llama3.1-8b",
        "llama3.1:70b": "llama3.1-70b",
        "llama3:8b": "llama3-8b",
        "llama3:70b": "llama3-70b",
        "phi3:mini": "phi3-mini",
        "phi3:medium": "phi3-medium",
        "qwen2:7b": "qwen2-7b",
        "qwen2.5:7b": "qwen2.5-7b",
        "codellama:7b": "codellama-7b",
        "codellama:13b": "codellama-13b",
    }
    
    @classmethod
    def to_ollama_format(cls, model_name: str) -> str:
        """Convert internal model name to Ollama format.
        
        Args:
            model_name: Internal model name (e.g., "llama3.1-8b")
            
        Returns:
            Ollama model name (e.g., "llama3.1:8b")
        """
        if not model_name:
            return model_name
            
        # Check if already in correct format or in mapping
        if model_name in cls.MODEL_NAME_MAP:
            return cls.MODEL_NAME_MAP[model_name]
        
        # Try automatic conversion for unknown models
        # Convert hyphen before size to colon
        if '-' in model_name:
            parts = model_name.rsplit('-', 1)
            if len(parts) == 2 and parts[1] and (parts[1][0].isdigit() or parts[1] == 'latest'):
                return f"{parts[0]}:{parts[1]}"
        
        # Return as-is if no conversion needed
        return model_name
    
    @classmethod
    def to_internal_format(cls, ollama_name: str) -> str:
        """Convert Ollama model name to internal format.
        
        Args:
            ollama_name: Ollama model name (e.g., "llama3.1:8b")
            
        Returns:
            Internal model name (e.g., "llama3.1-8b")
        """
        if not ollama_name:
            return ollama_name
            
        # Check reverse mapping
        if ollama_name in cls.OLLAMA_TO_INTERNAL:
            return cls.OLLAMA_TO_INTERNAL[ollama_name]
        
        # Try automatic conversion
        if ':' in ollama_name:
            parts = ollama_name.split(':', 1)
            if len(parts) == 2:
                return f"{parts[0]}-{parts[1]}"
        
        # Return as-is if no conversion needed
        return ollama_name
    
    @classmethod
    def normalize_model_name(cls, model_name: str, target_format: str = "ollama") -> str:
        """Normalize model name to specified format.
        
        Args:
            model_name: Model name in any format
            target_format: "ollama" or "internal"
            
        Returns:
            Normalized model name
        """
        if target_format == "ollama":
            return cls.to_ollama_format(model_name)
        elif target_format == "internal":
            return cls.to_internal_format(model_name)
        else:
            raise ValueError(f"Unknown target format: {target_format}")
    
    @classmethod
    def is_valid_model(cls, model_name: str) -> bool:
        """Check if model name is recognized.
        
        Args:
            model_name: Model name to check
            
        Returns:
            True if model is recognized
        """
        # Check both formats
        return (
            model_name in cls.MODEL_NAME_MAP or
            model_name in cls.OLLAMA_TO_INTERNAL or
            cls.to_ollama_format(model_name) in cls.OLLAMA_TO_INTERNAL.keys()
        )
    
    @classmethod
    def get_display_name(cls, model_name: str) -> str:
        """Get user-friendly display name for model.
        
        Args:
            model_name: Model name in any format
            
        Returns:
            Display-friendly name
        """
        # Normalize to internal format for consistent display
        internal_name = cls.to_internal_format(cls.to_ollama_format(model_name))
        
        # Create readable name
        display_map = {
            "gemma2-2b": "Gemma 2 (2B)",
            "llama3.2-3b": "Llama 3.2 (3B)",
            "llama3.2-1b": "Llama 3.2 (1B)",
            "mistral-7b": "Mistral (7B)",
            "mistral-nemo": "Mistral Nemo",
            "llama3.1-8b": "Llama 3.1 (8B)",
            "llama3.1-70b": "Llama 3.1 (70B)",
            "llama3-8b": "Llama 3 (8B)",
            "llama3-70b": "Llama 3 (70B)",
            "phi3-mini": "Phi-3 Mini",
            "phi3-medium": "Phi-3 Medium",
            "qwen2-7b": "Qwen 2 (7B)",
            "qwen2.5-7b": "Qwen 2.5 (7B)",
            "codellama-7b": "Code Llama (7B)",
            "codellama-13b": "Code Llama (13B)",
        }
        
        return display_map.get(internal_name, internal_name)