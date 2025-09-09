"""
Interface Router and Context Detection

Automatically routes requests to appropriate interface based on context:
- Human interface: Interactive CLI with Rich UI
- Programmatic interface: Headless API for automation
- Protocol interface: MCP server for Claude integration

Provides persona-driven interface selection and consistent experience.
"""

import sys
import os
from typing import Optional, Dict, Any, Union, List
from enum import Enum

from .base_interfaces import HumanInterface, ProgrammaticInterface, ProtocolInterface
from .human.interactive_cli import InteractiveCLI
from .programmatic.library_interface import ContentTamerAPI
from .protocols.mcp_server import MCPServer


class InterfaceType(Enum):
    """Available interface types."""
    HUMAN = "human"
    PROGRAMMATIC = "programmatic"
    PROTOCOL = "protocol"


class ContextDetector:
    """Detects appropriate interface based on execution context."""

    def __init__(self):
        """Initialize context detector."""
        self.context_cache = {}

    def detect_interface_type(self, force_type: Optional[str] = None) -> InterfaceType:
        """Detect appropriate interface type based on context.

        Args:
            force_type: Force specific interface type (for testing)

        Returns:
            Appropriate interface type
        """
        if force_type:
            try:
                return InterfaceType(force_type)
            except ValueError:
                pass

        # Check for MCP/Protocol context
        if self._is_mcp_context():
            return InterfaceType.PROTOCOL

        # Check for programmatic context
        if self._is_programmatic_context():
            return InterfaceType.PROGRAMMATIC

        # Default to human interface
        return InterfaceType.HUMAN

    def _is_mcp_context(self) -> bool:
        """Check if running in MCP context."""
        # Check for MCP-specific environment variables or arguments
        mcp_indicators = [
            os.getenv("MCP_SERVER_MODE"),
            os.getenv("CLAUDE_MCP_SERVER"),
            "--mcp-server" in sys.argv,
            "--protocol-mode" in sys.argv
        ]

        return any(mcp_indicators)

    def _is_programmatic_context(self) -> bool:
        """Check if running in programmatic context."""
        # Check for automation indicators
        automation_indicators = [
            # No TTY (running in CI/automation)
            not sys.stdout.isatty(),
            # Specific environment variables
            os.getenv("CI") == "true",
            os.getenv("AUTOMATED_MODE") == "true",
            os.getenv("CONTENT_TAMER_API_MODE") == "true",
            # Command line flags
            "--headless" in sys.argv,
            "--api-mode" in sys.argv,
            "--no-interaction" in sys.argv,
        ]

        # Check if imported as module (not main execution)
        import_context = __name__ != "__main__" and len(sys.argv) == 1

        return any(automation_indicators) or import_context

    def get_context_info(self) -> Dict[str, Any]:
        """Get detailed context information."""
        return {
            "is_tty": sys.stdout.isatty(),
            "argv_count": len(sys.argv),
            "argv": sys.argv,
            "environment": {
                "CI": os.getenv("CI"),
                "MCP_SERVER_MODE": os.getenv("MCP_SERVER_MODE"),
                "AUTOMATED_MODE": os.getenv("AUTOMATED_MODE"),
                "CONTENT_TAMER_API_MODE": os.getenv("CONTENT_TAMER_API_MODE"),
            },
            "execution_context": __name__
        }


class InterfaceRouter:
    """Routes requests to appropriate interface implementation."""

    def __init__(self):
        """Initialize interface router."""
        self.detector = ContextDetector()
        self._interfaces = {}
        self._current_interface = None
        self._current_type = None

    def get_interface(
        self,
        interface_type: Optional[Union[str, InterfaceType]] = None
    ) -> Union[HumanInterface, ProgrammaticInterface, ProtocolInterface]:
        """Get appropriate interface instance.

        Args:
            interface_type: Force specific interface type

        Returns:
            Appropriate interface instance
        """
        # Determine interface type
        if interface_type is None:
            target_type = self.detector.detect_interface_type()
        elif isinstance(interface_type, str):
            target_type = InterfaceType(interface_type)
        else:
            target_type = interface_type

        # Return cached interface if same type
        if self._current_type == target_type and self._current_interface:
            return self._current_interface

        # Create new interface
        self._current_type = target_type
        self._current_interface = self._create_interface(target_type)

        return self._current_interface

    def _create_interface(
        self,
        interface_type: InterfaceType
    ) -> Union[HumanInterface, ProgrammaticInterface, ProtocolInterface]:
        """Create interface instance of specified type."""
        if interface_type == InterfaceType.HUMAN:
            return InteractiveCLI()
        elif interface_type == InterfaceType.PROGRAMMATIC:
            return ContentTamerAPI()
        elif interface_type == InterfaceType.PROTOCOL:
            return MCPServer()
        else:
            raise ValueError(f"Unknown interface type: {interface_type}")

    def auto_route(self) -> Union[HumanInterface, ProgrammaticInterface, ProtocolInterface]:
        """Automatically route to best interface for current context."""
        return self.get_interface()

    def get_routing_info(self) -> Dict[str, Any]:
        """Get routing decision information."""
        detected_type = self.detector.detect_interface_type()
        context_info = self.detector.get_context_info()

        return {
            "detected_type": detected_type.value,
            "current_type": self._current_type.value if self._current_type else None,
            "context": context_info,
            "routing_reasons": self._get_routing_reasons(detected_type, context_info)
        }

    def _get_routing_reasons(self, interface_type: InterfaceType, context: Dict[str, Any]) -> List[str]:
        """Get human-readable routing decision reasons."""
        reasons = []

        if interface_type == InterfaceType.PROTOCOL:
            if context["environment"]["MCP_SERVER_MODE"]:
                reasons.append("MCP_SERVER_MODE environment variable detected")
            if "--mcp-server" in context["argv"]:
                reasons.append("--mcp-server command line flag detected")

        elif interface_type == InterfaceType.PROGRAMMATIC:
            if not context["is_tty"]:
                reasons.append("No TTY detected (likely automation/CI environment)")
            if context["environment"]["CI"] == "true":
                reasons.append("CI environment detected")
            if context["environment"]["AUTOMATED_MODE"] == "true":
                reasons.append("AUTOMATED_MODE environment variable set")
            if "--headless" in context["argv"]:
                reasons.append("--headless command line flag detected")

        else:  # HUMAN
            if context["is_tty"]:
                reasons.append("TTY detected (interactive terminal)")
            if len(context["argv"]) <= 1:
                reasons.append("No command line arguments (interactive mode)")

        if not reasons:
            reasons.append(f"Default routing to {interface_type.value}")

        return reasons


# Global router instance
_global_router = InterfaceRouter()


def get_interface(interface_type: Optional[str] = None) -> Union[HumanInterface, ProgrammaticInterface, ProtocolInterface]:
    """Get appropriate interface instance (convenience function).

    Args:
        interface_type: Force specific interface type ('human', 'programmatic', 'protocol')

    Returns:
        Appropriate interface instance
    """
    return _global_router.get_interface(interface_type)


def auto_route() -> Union[HumanInterface, ProgrammaticInterface, ProtocolInterface]:
    """Automatically route to best interface for current context."""
    return _global_router.auto_route()


def get_routing_info() -> Dict[str, Any]:
    """Get current routing decision information."""
    return _global_router.get_routing_info()


def detect_persona() -> str:
    """Detect user persona based on context.

    Returns:
        Persona type: 'developer', 'analyst', 'automation', 'integration'
    """
    context = _global_router.detector.get_context_info()
    interface_type = _global_router.detector.detect_interface_type()

    if interface_type == InterfaceType.PROTOCOL:
        return "integration"  # Claude MCP integration
    elif interface_type == InterfaceType.PROGRAMMATIC:
        if context["environment"]["CI"] == "true":
            return "automation"  # CI/CD automation
        else:
            return "developer"  # API/library usage
    else:
        # Human interface - detect based on usage patterns
        if "--expert" in context["argv"] or "--advanced" in context["argv"]:
            return "analyst"  # Power user/analyst
        else:
            return "developer"  # Interactive developer


class PersonaRouter:
    """Routes based on user persona for optimized experience."""

    PERSONA_CONFIGS = {
        "developer": {
            "interface": "human",
            "verbose": True,
            "show_progress": True,
            "confirm_actions": False,
            "default_ml_level": 2
        },
        "analyst": {
            "interface": "human",
            "verbose": True,
            "show_progress": True,
            "confirm_actions": True,
            "default_ml_level": 3
        },
        "automation": {
            "interface": "programmatic",
            "verbose": False,
            "show_progress": False,
            "confirm_actions": False,
            "default_ml_level": 2
        },
        "integration": {
            "interface": "protocol",
            "verbose": True,
            "show_progress": True,
            "confirm_actions": False,
            "default_ml_level": 2
        }
    }

    @classmethod
    def get_persona_config(cls, persona: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration optimized for persona."""
        if persona is None:
            persona = detect_persona()

        return cls.PERSONA_CONFIGS.get(persona, cls.PERSONA_CONFIGS["developer"])

    @classmethod
    def route_for_persona(cls, persona: Optional[str] = None) -> Union[HumanInterface, ProgrammaticInterface, ProtocolInterface]:
        """Route to interface optimized for persona."""
        config = cls.get_persona_config(persona)
        return get_interface(config["interface"])


# Example usage patterns:
"""
# Automatic routing
interface = auto_route()
result = interface.process_documents(config)

# Persona-based routing
interface = PersonaRouter.route_for_persona()
result = interface.process_documents(config)

# Explicit interface selection
human_interface = get_interface("human")
api_interface = get_interface("programmatic")
mcp_interface = get_interface("protocol")

# Routing information
info = get_routing_info()
print(f"Using {info['detected_type']} interface")
print(f"Reasons: {info['routing_reasons']}")
"""
