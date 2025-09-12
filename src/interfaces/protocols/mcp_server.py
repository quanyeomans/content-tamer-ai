"""
MCP (Model Context Protocol) Server Foundation

Provides foundation for Claude MCP integration with Content Tamer AI.
This enables Content Tamer AI to be used as an MCP server in Claude Desktop.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional

from ..base_interfaces import ProcessingResult, ProtocolInterface
from ..programmatic.library_interface import ContentTamerAPI


@dataclass
class MCPTool:
    """MCP tool definition."""

    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPResource:
    """MCP resource definition."""

    uri: str
    name: str
    description: str
    mime_type: Optional[str] = None


class MCPServer(ProtocolInterface):
    """Foundation MCP server for Content Tamer AI integration."""

    def __init__(self):
        """Initialize MCP server with Content Tamer API integration."""
        self.logger = logging.getLogger(__name__)
        self.api = ContentTamerAPI()
        self.tools = self._define_tools()
        self.resources = self._define_resources()

        # Server state
        self._running = False
        self._request_handlers: Dict[str, Callable] = {}

        # Register request handlers
        self._register_handlers()

    def _define_tools(self) -> List[MCPTool]:
        """Define available MCP tools."""
        return [
            MCPTool(
                name="process_documents",
                description="Process documents with AI-powered organization and intelligent naming",
                input_schema={
                    "type": "object",
                    "properties": {
                        "input_dir": {
                            "type": "string",
                            "description": "Directory containing documents to process",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory where organized documents will be saved",
                        },
                        "provider": {
                            "type": "string",
                            "enum": ["openai", "claude", "gemini", "deepseek", "local"],
                            "description": "AI provider to use for processing",
                            "default": "openai",
                        },
                        "api_key": {
                            "type": "string",
                            "description": "API key for the AI provider (optional if set in environment)",
                        },
                        "organization_enabled": {
                            "type": "boolean",
                            "description": "Enable intelligent document organization",
                            "default": True,
                        },
                        "ml_level": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 3,
                            "description": "ML enhancement level (1=basic, 2=balanced, 3=comprehensive)",
                            "default": 2,
                        },
                    },
                    "required": ["input_dir", "output_dir"],
                },
            ),
            MCPTool(
                name="validate_setup",
                description="Validate configuration and setup before processing",
                input_schema={
                    "type": "object",
                    "properties": {
                        "input_dir": {
                            "type": "string",
                            "description": "Input directory to validate",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Output directory to validate",
                        },
                        "provider": {
                            "type": "string",
                            "enum": ["openai", "claude", "gemini", "deepseek", "local"],
                            "description": "AI provider to validate",
                        },
                        "api_key": {"type": "string", "description": "API key to validate"},
                    },
                    "required": ["input_dir", "output_dir"],
                },
            ),
            MCPTool(
                name="get_provider_info",
                description="Get information about supported AI providers and models",
                input_schema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "description": "Specific provider to get info for (optional)",
                        }
                    },
                },
            ),
        ]

    def _define_resources(self) -> List[MCPResource]:
        """Define available MCP resources."""
        return [
            MCPResource(
                uri="content-tamer://docs/api",
                name="Content Tamer AI API Documentation",
                description="Complete API documentation for Content Tamer AI",
                mime_type="text/markdown",
            ),
            MCPResource(
                uri="content-tamer://config/current",
                name="Current Configuration",
                description="Current Content Tamer AI configuration",
                mime_type="application/json",
            ),
            MCPResource(
                uri="content-tamer://status/system",
                name="System Status",
                description="Current system status and capabilities",
                mime_type="application/json",
            ),
        ]

    def _register_handlers(self) -> None:
        """Register MCP request handlers."""
        self._request_handlers = {
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
        }

    async def start_server(self, host: str = "localhost", port: int = 8000) -> None:
        """Start the MCP server (foundation implementation)."""
        self.logger.info("Starting MCP server on %s:%s", host, port)
        self._running = True

        # This is a foundation implementation
        # In a full MCP implementation, this would set up the actual server
        # For now, we just log that the server would start
        self.logger.info("MCP server foundation ready - full implementation pending")

    async def stop_server(self) -> None:
        """Stop the MCP server."""
        self.logger.info("Stopping MCP server")
        self._running = False

    def initialize_protocol(self, config: Dict[str, Any]) -> bool:
        """Initialize the protocol handler."""
        try:
            self.logger.info("Initializing MCP protocol")
            # Initialize any protocol-specific configuration
            return True
        except Exception as e:
            self.logger.error("Failed to initialize MCP protocol: %s", e)
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        """Return protocol capabilities description."""
        return {
            "protocol": "MCP",
            "version": "1.0",
            "capabilities": {"tools": True, "resources": True, "async_processing": True},
            "tools": [tool.name for tool in self.tools],
            "resources": [resource.uri for resource in self.resources],
            "supported_methods": list(self._request_handlers.keys()),
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})

        if method in self._request_handlers:
            try:
                return await self._request_handlers[method](params)
            except Exception as e:
                self.logger.error("Error handling %s: %s", method, e)
                return {"error": {"code": -32000, "message": str(e)}}
        else:
            return {"error": {"code": -32601, "message": f"Method not found: {method}"}}

    async def _handle_tools_list(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:  # pylint: disable=unused-argument
        """Handle tools list request."""
        return {"tools": [asdict(tool) for tool in self.tools]}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request."""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name == "process_documents":
            return await self._call_process_documents(arguments)
        elif name == "validate_setup":
            return await self._call_validate_setup(arguments)
        elif name == "get_provider_info":
            return await self._call_get_provider_info(arguments)
        else:
            return {"error": {"code": -32000, "message": f"Unknown tool: {name}"}}

    async def _handle_resources_list(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:  # pylint: disable=unused-argument
        """Handle resources list request."""
        return {"resources": [asdict(resource) for resource in self.resources]}

    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read request."""
        uri = params.get("uri")

        if uri == "content-tamer://docs/api":
            return await self._get_api_documentation()
        elif uri == "content-tamer://config/current":
            return await self._get_current_config()
        elif uri == "content-tamer://status/system":
            return await self._get_system_status()
        else:
            return {"error": {"code": -32000, "message": f"Resource not found: {uri}"}}

    async def _call_process_documents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document processing through API."""
        try:
            # Run processing in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.api.process_documents, arguments)

            return {"content": [{"type": "text", "text": self._format_processing_result(result)}]}

        except Exception as e:
            return {"error": {"code": -32000, "message": f"Processing failed: {e}"}}

    async def _call_validate_setup(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate setup configuration."""
        try:
            from ..programmatic.library_interface import validate_setup

            errors = validate_setup(**arguments)

            if errors:
                message = "Configuration validation failed:\n" + "\n".join(
                    f"• {error}" for error in errors
                )
            else:
                message = "✅ Configuration is valid and ready for processing"

            return {"content": [{"type": "text", "text": message}]}

        except Exception as e:
            return {"error": {"code": -32000, "message": f"Validation failed: {e}"}}

    async def _call_get_provider_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI provider information."""
        try:
            from ..programmatic.library_interface import get_provider_info

            provider = arguments.get("provider")
            info = get_provider_info(provider)

            return {"content": [{"type": "text", "text": json.dumps(info, indent=2)}]}

        except Exception as e:
            return {"error": {"code": -32000, "message": f"Provider info failed: {e}"}}

    async def _get_api_documentation(self) -> Dict[str, Any]:
        """Get API documentation resource."""
        docs = """
# Content Tamer AI API Documentation

## Overview
Content Tamer AI provides intelligent document processing with AI-powered organization and naming.

## Available Tools

### process_documents
Process documents with AI-powered organization and intelligent naming.

**Parameters:**
- `input_dir` (required): Directory containing documents to process
- `output_dir` (required): Directory where organized documents will be saved
- `provider` (optional): AI provider (openai, claude, gemini, deepseek, local)
- `api_key` (optional): API key for the provider
- `organization_enabled` (optional): Enable intelligent organization
- `ml_level` (optional): ML enhancement level (1-3)

### validate_setup
Validate configuration before processing.

### get_provider_info
Get information about supported AI providers and models.
        """

        return {
            "contents": [
                {
                    "uri": "content-tamer://docs/api",
                    "mimeType": "text/markdown",
                    "text": docs.strip(),
                }
            ]
        }

    async def _get_current_config(self) -> Dict[str, Any]:
        """Get current configuration resource."""
        config = self.api.config_manager.load_configuration()
        config_dict = {
            "input_dir": config.input_dir,
            "output_dir": config.output_dir,
            "provider": config.provider,
            "model": config.model,
            "organization_enabled": config.organization_enabled,
            "ml_level": config.ml_level,
            "has_api_key": bool(config.api_key),
        }

        return {
            "contents": [
                {
                    "uri": "content-tamer://config/current",
                    "mimeType": "application/json",
                    "text": json.dumps(config_dict, indent=2),
                }
            ]
        }

    async def _get_system_status(self) -> Dict[str, Any]:
        """Get system status resource."""
        status = {
            "server_running": self._running,
            "supported_providers": self.api.get_supported_providers(),
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
        }

        return {
            "contents": [
                {
                    "uri": "content-tamer://status/system",
                    "mimeType": "application/json",
                    "text": json.dumps(status, indent=2),
                }
            ]
        }

    def _format_processing_result(self, result: ProcessingResult) -> str:
        """Format processing result for display."""
        if result.success:
            message = f"✅ Processing completed successfully!\n\n"
            message += f"Files processed: {result.files_processed}\n"
            message += f"Output directory: {result.output_directory}\n"

            if result.files_failed > 0:
                message += f"Files failed: {result.files_failed}\n"

            if result.warnings:
                message += f"\nWarnings:\n"
                for warning in result.warnings:
                    message += f"• {warning}\n"

        else:
            message = f"❌ Processing failed\n\n"
            message += f"Errors:\n"
            for error in result.errors:
                message += f"• {error}\n"

        return message

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running


# MCP Server Factory Function
def create_mcp_server() -> MCPServer:
    """Create and return MCP server instance."""
    return MCPServer()


# Async context manager for MCP server
class MCPServerContext:
    """Context manager for MCP server lifecycle."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize context manager."""
        self.host = host
        self.port = port
        self.server = None

    async def __aenter__(self) -> MCPServer:
        """Enter context and start server."""
        self.server = create_mcp_server()
        await self.server.start_server(self.host, self.port)
        return self.server

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and stop server."""
        if self.server:
            await self.server.stop_server()
        return False


# Example usage:
"""
# Basic usage
server = create_mcp_server()
await server.start_server()

# With context manager
async with MCPServerContext() as server:
    # Server is running
    response = await server.handle_request({
        "method": "tools/call",
        "params": {
            "name": "process_documents",
            "arguments": {
                "input_dir": "./documents",
                "output_dir": "./organized"
            }
        }
    })
    print(response)
"""
