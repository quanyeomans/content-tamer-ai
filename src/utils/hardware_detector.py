"""
Hardware Detection for Local LLM Operations

Detects system capabilities including RAM, CPU, and GPU to recommend
appropriate local LLM models and configurations.
"""

import platform
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    import psutil

    HAVE_PSUTIL = True
except ImportError:
    psutil = None  # type: ignore
    HAVE_PSUTIL = False


@dataclass
class SystemInfo:
    """System hardware information."""

    total_ram_gb: float
    available_ram_gb: float
    cpu_count: int
    platform_system: str
    platform_machine: str
    has_gpu: bool = False
    gpu_info: Optional[str] = None


@dataclass
class ModelRecommendation:
    """Model recommendation with reasoning."""

    model_name: str
    confidence: str  # "high", "medium", "low"
    reason: str
    alternative_models: List[str]


class HardwareDetector:
    """Detects system hardware capabilities for local LLM recommendations."""

    # Model requirements (matching ModelManager specs)
    MODEL_REQUIREMENTS = {
        "gemma-2-2b": {
            "min_ram_gb": 2.5,
            "optimal_ram_gb": 4.0,
            "description": "Ultra-lightweight for 4GB RAM systems",
        },
        "llama3.2-3b": {
            "min_ram_gb": 4.5,
            "optimal_ram_gb": 6.0,
            "description": "Balanced performance for 6GB RAM systems",
        },
        "mistral-7b": {
            "min_ram_gb": 6.5,
            "optimal_ram_gb": 8.0,
            "description": "High-quality for 8GB RAM systems",
        },
        "llama3.1-8b": {
            "min_ram_gb": 7.5,
            "optimal_ram_gb": 10.0,
            "description": "Premium for 10GB+ RAM systems",
        },
    }

    def __init__(self):
        """Initialize hardware detector."""
        self._system_info = None

    def detect_system_info(self) -> SystemInfo:
        """Detect system hardware information."""
        if self._system_info is not None:
            return self._system_info

        # Get RAM information
        if HAVE_PSUTIL:
            memory = psutil.virtual_memory()
            total_ram_gb = memory.total / (1024**3)
            available_ram_gb = memory.available / (1024**3)
            cpu_count = psutil.cpu_count(logical=True)
        else:
            # Fallback without psutil
            total_ram_gb = self._estimate_ram_without_psutil()
            available_ram_gb = total_ram_gb * 0.7  # Estimate 70% available
            cpu_count = os.cpu_count() or 4  # Default to 4 if unknown

        # Get platform information
        platform_system = platform.system()
        platform_machine = platform.machine()

        # Detect GPU (basic detection)
        has_gpu, gpu_info = self._detect_gpu()

        self._system_info = SystemInfo(
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            cpu_count=cpu_count,
            platform_system=platform_system,
            platform_machine=platform_machine,
            has_gpu=has_gpu,
            gpu_info=gpu_info,
        )

        return self._system_info

    def _estimate_ram_without_psutil(self) -> float:
        """Estimate RAM without psutil (fallback method)."""
        try:
            # Try different platform-specific methods
            if platform.system() == "Linux":
                # Try /proc/meminfo
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            # Extract KB and convert to GB
                            kb = int(line.split()[1])
                            return kb / (1024**2)
            elif platform.system() == "Darwin":  # macOS
                # Try sysctl (if available)
                try:
                    import subprocess

                    result = subprocess.run(
                        ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        bytes_ram = int(result.stdout.strip())
                        return bytes_ram / (1024**3)
                except (subprocess.SubprocessError, ValueError, FileNotFoundError):
                    pass
            elif platform.system() == "Windows":
                # Try wmic (if available)
                try:
                    import subprocess

                    result = subprocess.run(
                        ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split("\n")
                        for line in lines:
                            if line.strip() and not "TotalPhysicalMemory" in line:
                                bytes_ram = int(line.strip())
                                return bytes_ram / (1024**3)
                except (subprocess.SubprocessError, ValueError, FileNotFoundError):
                    pass
        except (IOError, OSError, ValueError):
            pass

        # Ultimate fallback - assume 8GB
        return 8.0

    def _detect_gpu(self) -> Tuple[bool, Optional[str]]:
        """Detect GPU availability (basic detection)."""
        gpu_info = None
        has_gpu = False

        try:
            # Try nvidia-ml-py if available (for NVIDIA GPUs)
            try:
                import GPUtil

                gpus = GPUtil.getGPUs()
                if gpus:
                    has_gpu = True
                    gpu_info = f"NVIDIA {gpus[0].name}"
                    return has_gpu, gpu_info
            except ImportError:
                pass

            # Try platform-specific detection
            if platform.system() == "Linux":
                # Check for GPU devices
                gpu_paths = ["/proc/driver/nvidia/version", "/dev/dri"]
                for path in gpu_paths:
                    if os.path.exists(path):
                        has_gpu = True
                        if "nvidia" in path.lower():
                            gpu_info = "NVIDIA GPU (detected)"
                        else:
                            gpu_info = "GPU (detected)"
                        break

            elif platform.system() == "Darwin":  # macOS
                # macOS always has integrated graphics, check for discrete
                try:
                    import subprocess

                    result = subprocess.run(
                        ["system_profiler", "SPDisplaysDataType"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0 and "GPU" in result.stdout:
                        has_gpu = True
                        gpu_info = "macOS GPU (detected)"
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

            elif platform.system() == "Windows":
                # Check for common GPU registry entries or wmic
                try:
                    import subprocess

                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "name"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split("\n")
                        for line in lines:
                            if (
                                line.strip()
                                and "Name" not in line
                                and "Microsoft Basic" not in line
                            ):
                                has_gpu = True
                                gpu_info = line.strip()
                                break
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

        except Exception:
            # If all detection fails, assume no GPU
            pass

        return has_gpu, gpu_info

    def get_recommended_models(self) -> List[ModelRecommendation]:
        """Get recommended models based on detected hardware."""
        system_info = self.detect_system_info()
        recommendations = []

        # Use available RAM for recommendations (more conservative than total)
        available_ram = system_info.available_ram_gb

        # Find all models that can run on this system
        compatible_models = []
        for model_name, requirements in self.MODEL_REQUIREMENTS.items():
            if available_ram >= requirements["min_ram_gb"]:
                compatible_models.append((model_name, requirements))

        if not compatible_models:
            # System has insufficient RAM for any model
            return [
                ModelRecommendation(
                    model_name="none",
                    confidence="high",
                    reason=f"Insufficient RAM ({available_ram:.1f}GB available). Minimum 2.5GB required.",
                    alternative_models=[],
                )
            ]

        # Sort by memory requirement (highest first)
        compatible_models.sort(key=lambda x: x[1]["min_ram_gb"], reverse=True)

        # Primary recommendation: highest model that fits comfortably
        primary_model, primary_req = compatible_models[0]

        # Determine confidence based on how much headroom we have
        headroom = available_ram - primary_req["min_ram_gb"]
        if headroom >= 2.0:
            confidence = "high"
            reason = f"Excellent fit: {available_ram:.1f}GB RAM available, {primary_req['min_ram_gb']}GB required"
        elif headroom >= 1.0:
            confidence = "medium"
            reason = f"Good fit: {available_ram:.1f}GB RAM available, {primary_req['min_ram_gb']}GB required"
        else:
            confidence = "low"
            reason = f"Tight fit: {available_ram:.1f}GB RAM available, {primary_req['min_ram_gb']}GB required"

        # Alternative models (smaller ones that would also work)
        alternatives = [model for model, _ in compatible_models[1:3]]  # Top 2 alternatives

        primary_recommendation = ModelRecommendation(
            model_name=primary_model,
            confidence=confidence,
            reason=reason,
            alternative_models=alternatives,
        )
        recommendations.append(primary_recommendation)

        return recommendations

    def get_system_tier(self) -> str:
        """Get system hardware tier classification."""
        system_info = self.detect_system_info()
        available_ram = system_info.available_ram_gb

        if available_ram >= 10.0:
            return "premium"
        elif available_ram >= 8.0:
            return "enhanced"
        elif available_ram >= 6.0:
            return "standard"
        else:
            return "ultra_lightweight"

    def check_ollama_compatibility(self) -> Dict[str, bool]:
        """Check system compatibility with Ollama."""
        system_info = self.detect_system_info()

        compatibility = {
            "supported_platform": system_info.platform_system in ["Linux", "Darwin", "Windows"],
            "sufficient_ram": system_info.available_ram_gb >= 2.0,
            "supported_architecture": system_info.platform_machine
            in ["x86_64", "AMD64", "arm64", "aarch64"],
            "recommended_ram": system_info.available_ram_gb >= 4.0,
        }

        compatibility["overall_compatible"] = all(
            [
                compatibility["supported_platform"],
                compatibility["sufficient_ram"],
                compatibility["supported_architecture"],
            ]
        )

        return compatibility

    def get_performance_estimate(self, model_name: str) -> Dict[str, str]:
        """Estimate performance characteristics for a model on this system."""
        if model_name not in self.MODEL_REQUIREMENTS:
            return {"error": "Unknown model"}

        system_info = self.detect_system_info()
        requirements = self.MODEL_REQUIREMENTS[model_name]

        # Estimate inference speed based on RAM headroom and CPU
        available_ram = system_info.available_ram_gb
        required_ram = requirements["min_ram_gb"]

        if available_ram < required_ram:
            return {
                "inference_speed": "Not supported",
                "memory_status": "Insufficient RAM",
                "recommendation": "Choose a smaller model",
            }

        headroom_ratio = available_ram / required_ram
        cpu_factor = min(system_info.cpu_count / 4.0, 2.0)  # Normalize to 4 cores, cap at 2x

        # Rough performance estimates
        if headroom_ratio > 2.0 and cpu_factor > 1.5:
            speed = "Fast (5-15 seconds)"
            memory_status = "Comfortable"
        elif headroom_ratio > 1.5 and cpu_factor > 1.0:
            speed = "Medium (10-30 seconds)"
            memory_status = "Good"
        else:
            speed = "Slow (30+ seconds)"
            memory_status = "Tight"

        return {
            "inference_speed": speed,
            "memory_status": memory_status,
            "recommendation": (
                "Good choice for your system"
                if headroom_ratio > 1.3
                else "Consider a smaller model for better performance"
            ),
        }

    def get_system_summary(self) -> Dict:
        """Get a comprehensive system summary."""
        system_info = self.detect_system_info()
        compatibility = self.check_ollama_compatibility()
        recommendations = self.get_recommended_models()

        return {
            "hardware": {
                "total_ram_gb": round(system_info.total_ram_gb, 1),
                "available_ram_gb": round(system_info.available_ram_gb, 1),
                "cpu_count": system_info.cpu_count,
                "platform": f"{system_info.platform_system} {system_info.platform_machine}",
                "gpu": system_info.gpu_info if system_info.has_gpu else "Not detected",
            },
            "compatibility": compatibility,
            "tier": self.get_system_tier(),
            "recommendations": [
                {
                    "model": rec.model_name,
                    "confidence": rec.confidence,
                    "reason": rec.reason,
                    "alternatives": rec.alternative_models,
                }
                for rec in recommendations
            ],
        }
