"""
Model Manager for Local LLM Operations

Handles model lifecycle including downloading, verification, loading, and management
of local LLM models through Ollama backend.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import requests


class ModelStatus(Enum):
    """Status of a model in the system."""

    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    AVAILABLE = "available"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class ModelInfo:
    """Information about a model."""

    name: str
    size_gb: float
    memory_requirement_gb: float
    description: str
    status: ModelStatus = ModelStatus.NOT_DOWNLOADED
    download_progress: float = 0.0
    error_message: Optional[str] = None


@dataclass
class HardwareTier:
    """Hardware tier definition."""

    name: str
    min_ram_gb: int
    max_ram_gb: int
    recommended_models: List[str]
    description: str


class ModelManager:
    """Manages local LLM model lifecycle operations."""

    # Model specifications based on our research
    MODEL_SPECS = {
        "gemma-2-2b": ModelInfo(
            name="gemma-2-2b",
            size_gb=1.7,
            memory_requirement_gb=2.5,
            description="Ultra-lightweight model for 4GB RAM systems",
        ),
        "llama3.2-3b": ModelInfo(
            name="llama3.2-3b",
            size_gb=2.2,
            memory_requirement_gb=4.5,
            description="Balanced performance model for 6GB RAM systems",
        ),
        "mistral-7b": ModelInfo(
            name="mistral-7b",
            size_gb=4.4,
            memory_requirement_gb=6.5,
            description="High-quality model for 8GB RAM systems",
        ),
        "llama3.1-8b": ModelInfo(
            name="llama3.1-8b",
            size_gb=4.7,
            memory_requirement_gb=7.5,
            description="Premium model for 10GB+ RAM systems",
        ),
    }

    # Hardware tier definitions
    HARDWARE_TIERS = [
        HardwareTier(
            "ultra_lightweight", 4, 6, ["gemma-2-2b"], "Laptops, older hardware"
        ),
        HardwareTier("standard", 6, 8, ["llama3.2-3b"], "Most desktop systems"),
        HardwareTier("enhanced", 8, 10, ["mistral-7b"], "Quality-focused users"),
        HardwareTier("premium", 10, 32, ["llama3.1-8b"], "High-end systems"),
    ]

    def __init__(self, ollama_host: str = "localhost:11434"):
        """Initialize ModelManager with Ollama connection."""
        self.host = ollama_host
        self.base_url = f"http://{ollama_host}"
        self.session = requests.Session()

        # Try to create models directory in user's home
        self.models_dir = self._get_models_directory()
        os.makedirs(self.models_dir, exist_ok=True)

    def _get_models_directory(self) -> str:
        """Get the models storage directory."""
        # Use user's home directory for model storage
        home_dir = os.path.expanduser("~")
        models_dir = os.path.join(home_dir, ".content-tamer-ai", "models")
        return models_dir

    def is_ollama_running(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def list_available_models(self) -> List[ModelInfo]:
        """Get list of available models with their specifications."""
        models = []

        for name, spec in self.MODEL_SPECS.items():
            model_info = ModelInfo(
                name=spec.name,
                size_gb=spec.size_gb,
                memory_requirement_gb=spec.memory_requirement_gb,
                description=spec.description,
                status=self._get_model_status(spec.name),
            )
            models.append(model_info)

        return models

    def _get_model_status(self, model_name: str) -> ModelStatus:
        """Get the current status of a model."""
        if not self.is_ollama_running():
            return ModelStatus.ERROR

        try:
            # Check if model is available in Ollama
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()

            ollama_models = response.json().get("models", [])
            model_names = [
                model.get("name", "").split(":")[0] for model in ollama_models
            ]

            if model_name in model_names:
                return ModelStatus.AVAILABLE
            else:
                return ModelStatus.NOT_DOWNLOADED

        except requests.RequestException:
            return ModelStatus.ERROR

    def download_model(self, model_name: str, progress_callback=None) -> bool:
        """Download a model through Ollama."""
        if model_name not in self.MODEL_SPECS:
            raise ValueError(f"Unknown model: {model_name}")

        if not self.is_ollama_running():
            raise RuntimeError(
                f"Ollama is not running on {self.host}. "
                "Please start Ollama first: ollama serve"
            )

        try:
            # Start model download
            data = {"name": model_name}
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=data,
                stream=True,
                timeout=None,  # No timeout for downloads
            )
            response.raise_for_status()

            # Process streaming response for progress
            total_size = 0
            completed_size = 0

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        status_data = json.loads(line)

                        if "total" in status_data and "completed" in status_data:
                            total_size = status_data["total"]
                            completed_size = status_data["completed"]

                            if total_size > 0:
                                progress = (completed_size / total_size) * 100
                                if progress_callback:
                                    progress_callback(progress)

                        # Check for completion
                        if status_data.get("status") == "success":
                            if progress_callback:
                                progress_callback(100.0)
                            return True

                    except json.JSONDecodeError:
                        continue  # Skip malformed JSON lines

            return True

        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to download model {model_name}: {str(e)}"
            ) from e

    def verify_model(self, model_name: str) -> bool:
        """Verify that a model is properly installed and functional."""
        if not self.is_ollama_running():
            return False

        try:
            # Try a simple generation to verify the model works
            test_data = {
                "model": model_name,
                "prompt": "Test",
                "stream": False,
                "options": {"num_predict": 1},
            }

            response = self.session.post(
                f"{self.base_url}/api/generate", json=test_data, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return "response" in result

        except requests.RequestException:
            return False

    def remove_model(self, model_name: str) -> bool:
        """Remove a model from Ollama."""
        if not self.is_ollama_running():
            raise RuntimeError("Ollama is not running")

        try:
            data = {"name": model_name}
            response = self.session.delete(
                f"{self.base_url}/api/delete", json=data, timeout=30
            )
            response.raise_for_status()
            return True

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to remove model {model_name}: {str(e)}") from e

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get detailed information about a specific model."""
        if model_name not in self.MODEL_SPECS:
            return None

        spec = self.MODEL_SPECS[model_name]
        return ModelInfo(
            name=spec.name,
            size_gb=spec.size_gb,
            memory_requirement_gb=spec.memory_requirement_gb,
            description=spec.description,
            status=self._get_model_status(spec.name),
        )

    def get_recommended_model_for_system(
        self, available_ram_gb: float
    ) -> Optional[str]:
        """Get recommended model based on available system RAM."""
        # Find the best model that fits in available RAM
        suitable_models = []

        for name, spec in self.MODEL_SPECS.items():
            if spec.memory_requirement_gb <= available_ram_gb:
                suitable_models.append((name, spec.memory_requirement_gb))

        if not suitable_models:
            return None

        # Return the model with highest memory requirement that still fits
        suitable_models.sort(key=lambda x: x[1], reverse=True)
        return suitable_models[0][0]

    def get_hardware_tier_for_system(
        self, available_ram_gb: float
    ) -> Optional[HardwareTier]:
        """Get hardware tier based on available system RAM."""
        for tier in reversed(self.HARDWARE_TIERS):  # Check from highest to lowest
            if available_ram_gb >= tier.min_ram_gb:
                return tier
        return None

    def estimate_download_time(
        self, model_name: str, bandwidth_mbps: float = 10.0
    ) -> float:
        """Estimate download time for a model in seconds."""
        if model_name not in self.MODEL_SPECS:
            return 0.0

        model_size_mb = self.MODEL_SPECS[model_name].size_gb * 1024
        return (
            model_size_mb * 8
        ) / bandwidth_mbps  # Convert to bits and divide by bandwidth

    def get_system_status(self) -> Dict:
        """Get overall system status."""
        return {
            "ollama_running": self.is_ollama_running(),
            "ollama_host": self.host,
            "models_directory": self.models_dir,
            "available_models": len(
                [
                    m
                    for m in self.list_available_models()
                    if m.status == ModelStatus.AVAILABLE
                ]
            ),
            "total_models": len(self.MODEL_SPECS),
        }
