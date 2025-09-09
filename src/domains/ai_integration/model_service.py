"""
Model Service

Hardware detection and model selection service for AI integration.
Consolidates model management logic from scattered utilities.
"""

import logging
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

import psutil

# Optional imports
try:
    import wmi  # type: ignore
    HAVE_WMI = True
except ImportError:
    wmi = None  # type: ignore
    HAVE_WMI = False


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
    provider: str = "local"
    capabilities: Optional[List[str]] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["text_generation"]


@dataclass
class HardwareTier:
    """Hardware tier definition."""

    name: str
    min_ram_gb: int
    max_ram_gb: int
    recommended_models: List[str]
    description: str
    performance_level: str


@dataclass
class SystemCapabilities:
    """System hardware capabilities."""

    total_ram_gb: float
    available_ram_gb: float
    cpu_count: int
    cpu_brand: str
    platform: str
    gpu_available: bool
    gpu_memory_gb: Optional[float] = None
    gpu_brand: Optional[str] = None


class ModelService:
    """Hardware detection and model selection service."""

    def __init__(self):
        """Initialize model service."""
        self.logger = logging.getLogger(__name__)
        self._system_capabilities: Optional[SystemCapabilities] = None
        self._model_catalog: Dict[str, ModelInfo] = {}
        self._hardware_tiers: List[HardwareTier] = []
        self._initialize_model_catalog()
        self._initialize_hardware_tiers()

    def get_system_capabilities(self) -> SystemCapabilities:
        """Get system hardware capabilities."""
        if self._system_capabilities is None:
            self._system_capabilities = self._detect_system_capabilities()
        return self._system_capabilities

    def _detect_system_capabilities(self) -> SystemCapabilities:
        """Detect system hardware capabilities."""
        # Memory information
        memory = psutil.virtual_memory()
        total_ram_gb = memory.total / (1024**3)
        available_ram_gb = memory.available / (1024**3)

        # CPU information
        cpu_count = psutil.cpu_count(logical=True) or 1  # Fallback to 1 if None
        cpu_brand = self._get_cpu_brand()

        # Platform information
        system_platform = platform.system()

        # GPU detection (basic)
        gpu_available, gpu_memory_gb, gpu_brand = self._detect_gpu()

        return SystemCapabilities(
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            cpu_count=cpu_count,
            cpu_brand=cpu_brand,
            platform=system_platform,
            gpu_available=gpu_available,
            gpu_memory_gb=gpu_memory_gb,
            gpu_brand=gpu_brand,
        )

    def _get_cpu_brand(self) -> str:
        """Get CPU brand information."""
        try:
            if platform.system() == "Windows":
                if HAVE_WMI and wmi is not None:
                    try:
                        c = wmi.WMI()
                        for processor in c.Win32_Processor():
                            return processor.Name.strip()
                    except Exception:
                        # wmi call failed, continue to fallback
                        pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, check=False
                )
                return result.stdout.strip()
            else:  # Linux
                with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("model name"):
                            return line.split(":")[1].strip()
        except Exception:
            pass

        return "Unknown CPU"

    def _detect_gpu(self) -> Tuple[bool, Optional[float], Optional[str]]:
        """Detect GPU capabilities."""
        try:
            # Try NVIDIA GPU detection
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total,name", "--format=csv,noheader,nounits"],
                capture_output=True, check=False,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines and lines[0]:
                    parts = lines[0].split(", ")
                    if len(parts) >= 2:
                        memory_mb = float(parts[0])
                        gpu_name = parts[1]
                        return True, memory_mb / 1024, gpu_name  # Convert MB to GB
        except Exception:
            pass

        # Try AMD GPU detection (basic) - safe subprocess call
        try:
            if platform.system() == "Linux":
                # Use shell=False for security - pipe operations done in Python
                try:
                    lspci_result = subprocess.run(
                        ["lspci"], capture_output=True, text=True, shell=False, timeout=5, check=False
                    )
                    if lspci_result.returncode == 0:
                        # Filter for AMD in Python instead of shell
                        lspci_lines = lspci_result.stdout.lower()
                        if "amd" in lspci_lines and (
                            "vga" in lspci_lines or "display" in lspci_lines
                        ):
                            return True, None, "AMD GPU"
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass  # lspci not available or timeout
        except Exception:
            pass

        return False, None, None

    def _initialize_hardware_tiers(self) -> None:
        """Initialize hardware tier definitions."""
        self._hardware_tiers = [
            HardwareTier(
                name="minimal",
                min_ram_gb=4,
                max_ram_gb=8,
                recommended_models=["gemma2:2b"],
                description="Minimal systems with limited resources",
                performance_level="basic",
            ),
            HardwareTier(
                name="standard",
                min_ram_gb=8,
                max_ram_gb=16,
                recommended_models=["llama3.2:3b", "gemma2:2b"],
                description="Standard desktop/laptop systems",
                performance_level="good",
            ),
            HardwareTier(
                name="performance",
                min_ram_gb=16,
                max_ram_gb=32,
                recommended_models=["mistral:7b", "llama3.2:3b"],
                description="High-performance systems",
                performance_level="excellent",
            ),
            HardwareTier(
                name="workstation",
                min_ram_gb=32,
                max_ram_gb=64,
                recommended_models=["llama3.1:8b", "mistral:7b"],
                description="Workstation-class systems",
                performance_level="exceptional",
            ),
            HardwareTier(
                name="server",
                min_ram_gb=64,
                max_ram_gb=999,
                recommended_models=["llama3.1:8b", "llama3.1:70b"],
                description="Server-class systems with extensive resources",
                performance_level="maximum",
            ),
        ]

    def _initialize_model_catalog(self) -> None:
        """Initialize model catalog with available models."""
        self._model_catalog = {
            "gemma2:2b": ModelInfo(
                name="gemma2:2b",
                size_gb=1.6,
                memory_requirement_gb=3.0,
                description="Gemma 2 2B - Very efficient small model",
                provider="local",
                capabilities=["text_generation", "fast_inference"],
            ),
            "llama3.2:3b": ModelInfo(
                name="llama3.2:3b",
                size_gb=2.0,
                memory_requirement_gb=5.0,
                description="Llama 3.2 3B - Balanced performance model",
                provider="local",
                capabilities=["text_generation", "good_quality"],
            ),
            "mistral:7b": ModelInfo(
                name="mistral:7b",
                size_gb=4.1,
                memory_requirement_gb=8.0,
                description="Mistral 7B - High quality general purpose",
                provider="local",
                capabilities=["text_generation", "high_quality"],
            ),
            "llama3.1:8b": ModelInfo(
                name="llama3.1:8b",
                size_gb=4.7,
                memory_requirement_gb=10.0,
                description="Llama 3.1 8B - High capability model",
                provider="local",
                capabilities=["text_generation", "high_quality", "reasoning"],
            ),
        }

    def get_recommended_models_for_system(
        self, system: Optional[SystemCapabilities] = None
    ) -> List[str]:
        """Get recommended models for the current or specified system."""
        if system is None:
            system = self.get_system_capabilities()

        # Find appropriate hardware tier
        tier = self._get_hardware_tier(system.total_ram_gb)
        if tier:
            return tier.recommended_models

        # Fallback to minimal models
        return ["gemma2:2b"]

    def _get_hardware_tier(self, ram_gb: float) -> Optional[HardwareTier]:
        """Get appropriate hardware tier for RAM amount."""
        for tier in self._hardware_tiers:
            if tier.min_ram_gb <= ram_gb <= tier.max_ram_gb:
                return tier

        # If RAM exceeds all tiers, return the highest tier
        if ram_gb > self._hardware_tiers[-1].max_ram_gb:
            return self._hardware_tiers[-1]

        # If RAM is below all tiers, return the lowest tier
        return self._hardware_tiers[0]

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        return self._model_catalog.get(model_name)

    def get_all_models(self) -> Dict[str, ModelInfo]:
        """Get information about all available models."""
        return self._model_catalog.copy()

    def validate_model_compatibility(
        self, model_name: str, system: Optional[SystemCapabilities] = None
    ) -> Dict[str, Any]:
        """Validate if a model is compatible with the system."""
        if system is None:
            system = self.get_system_capabilities()

        model_info = self.get_model_info(model_name)
        if not model_info:
            return {
                "compatible": False,
                "reason": f"Unknown model: {model_name}",
                "recommendation": "Choose from available models",
            }

        # Check memory requirements
        if model_info.memory_requirement_gb > system.available_ram_gb:
            return {
                "compatible": False,
                "reason": f"Insufficient RAM: requires {model_info.memory_requirement_gb}GB, available {system.available_ram_gb:.1f}GB",
                "recommendation": f"Consider smaller models like {self.get_recommended_models_for_system(system)[0]}",
            }

        # Check performance expectations
        tier = self._get_hardware_tier(system.total_ram_gb)
        performance_level = "unknown"
        if tier:
            if model_name in tier.recommended_models:
                performance_level = "optimal"
            elif model_info.memory_requirement_gb <= system.total_ram_gb * 0.3:
                performance_level = "good"
            elif model_info.memory_requirement_gb <= system.total_ram_gb * 0.5:
                performance_level = "acceptable"
            else:
                performance_level = "slow"

        return {
            "compatible": True,
            "performance_level": performance_level,
            "memory_usage": f"{model_info.memory_requirement_gb}GB of {system.total_ram_gb:.1f}GB",
            "tier": tier.name if tier else "unknown",
        }

    def get_performance_estimate(
        self, model_name: str, system: Optional[SystemCapabilities] = None
    ) -> Dict[str, Any]:
        """Get performance estimate for a model on the system."""
        if system is None:
            system = self.get_system_capabilities()

        compatibility = self.validate_model_compatibility(model_name, system)
        if not compatibility["compatible"]:
            return {
                "error": compatibility["reason"],
                "recommendation": compatibility["recommendation"],
            }

        model_info = self.get_model_info(model_name)
        if not model_info:
            return {"error": f"Unknown model: {model_name}"}

        # Estimate inference speed based on model size and system capabilities
        base_tokens_per_second = 10  # Conservative baseline

        # Adjust based on model size (smaller = faster)
        if model_info.memory_requirement_gb <= 4:
            speed_multiplier = 2.0  # Small models are much faster
        elif model_info.memory_requirement_gb <= 8:
            speed_multiplier = 1.5
        else:
            speed_multiplier = 1.0

        # Adjust based on available memory (more headroom = better performance)
        memory_ratio = system.available_ram_gb / model_info.memory_requirement_gb
        if memory_ratio > 3:
            memory_multiplier = 1.5
        elif memory_ratio > 2:
            memory_multiplier = 1.2
        elif memory_ratio > 1.5:
            memory_multiplier = 1.0
        else:
            memory_multiplier = 0.7  # Tight memory = slower

        # Adjust based on CPU
        cpu_multiplier = min(2.0, system.cpu_count / 4.0)  # More cores help up to a point

        estimated_speed = (
            base_tokens_per_second * speed_multiplier * memory_multiplier * cpu_multiplier
        )

        # Categorize speed
        if estimated_speed >= 25:
            speed_category = "Very Fast (25+ tokens/sec)"
        elif estimated_speed >= 15:
            speed_category = "Fast (15+ tokens/sec)"
        elif estimated_speed >= 8:
            speed_category = "Moderate (8+ tokens/sec)"
        else:
            speed_category = "Slow (<8 tokens/sec)"

        # Memory status
        memory_usage_percent = (model_info.memory_requirement_gb / system.total_ram_gb) * 100
        if memory_usage_percent <= 20:
            memory_status = "Excellent (<20% RAM)"
        elif memory_usage_percent <= 40:
            memory_status = "Good (<40% RAM)"
        elif memory_usage_percent <= 60:
            memory_status = "Acceptable (<60% RAM)"
        else:
            memory_status = "Tight (>60% RAM)"

        # Overall recommendation
        if compatibility["performance_level"] == "optimal":
            recommendation = f"Excellent choice for your {compatibility['tier']} system"
        elif compatibility["performance_level"] == "good":
            recommendation = "Good performance expected"
        elif compatibility["performance_level"] == "acceptable":
            recommendation = "Usable but consider smaller models for better performance"
        else:
            recommendation = "Consider switching to a smaller model for better experience"

        return {
            "inference_speed": speed_category,
            "estimated_tokens_per_second": f"{estimated_speed:.1f}",
            "memory_status": memory_status,
            "memory_usage_percent": f"{memory_usage_percent:.1f}%",
            "recommendation": recommendation,
            "performance_level": compatibility["performance_level"],
        }

    def get_system_summary(self) -> Dict[str, Any]:
        """Get comprehensive system capability summary."""
        system = self.get_system_capabilities()
        tier = self._get_hardware_tier(system.total_ram_gb)
        recommended_models = self.get_recommended_models_for_system(system)

        return {
            "hardware": {
                "ram_total": f"{system.total_ram_gb:.1f}GB",
                "ram_available": f"{system.available_ram_gb:.1f}GB",
                "cpu_count": system.cpu_count,
                "cpu_brand": system.cpu_brand,
                "platform": system.platform,
                "gpu_available": system.gpu_available,
                "gpu_brand": system.gpu_brand or "None",
            },
            "tier": {
                "name": tier.name if tier else "unknown",
                "description": tier.description if tier else "Unknown tier",
                "performance_level": tier.performance_level if tier else "unknown",
            },
            "recommendations": {
                "models": recommended_models,
                "primary_model": recommended_models[0] if recommended_models else "gemma2:2b",
            },
        }
