"""
Interface Layer Tests

Comprehensive testing for all interface layer components:
- Human Interface (InteractiveCLI, RichConsoleManager)
- Programmatic Interface (ContentTamerAPI, library functions)
- Protocol Interface (MCP Server)
- Interface Routing and Context Detection

Uses RichTestCase framework for proper console isolation.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch

# Import test framework
from tests.utils.rich_test_utils import RichTestCase

# Import interfaces to test
from src.interfaces.human.interactive_cli import InteractiveCLI
from src.interfaces.human.rich_console_manager import RichConsoleManager
from src.interfaces.programmatic.library_interface import (
    ContentTamerAPI, process_documents_simple, validate_setup, get_provider_info
)
from src.interfaces.protocols.mcp_server import MCPServer, create_mcp_server
from src.interfaces.interface_router import (
    InterfaceRouter, ContextDetector, InterfaceType,
    get_interface, auto_route, detect_persona, PersonaRouter
)
from src.interfaces.base_interfaces import ProcessingResult

class TestHumanInterface(unittest.TestCase, RichTestCase):
    """Test human interface components."""

    def setUp(self):
        """Set up test environment."""
        RichTestCase.setUp(self)
        self.cli = InteractiveCLI()

    def test_console_initialization(self):
        """Test console manager initialization."""
        console_manager = RichConsoleManager()
        self.assertIsNotNone(console_manager.console)
        self.assertTrue(console_manager._initialized)

    def test_console_singleton_pattern(self):
        """Test console manager singleton behavior."""
        manager1 = RichConsoleManager()
        manager2 = RichConsoleManager()
        self.assertIs(manager1, manager2)
        self.assertIs(manager1.console, manager2.console)

    def test_smart_emoji_handling(self):
        """Test cross-platform emoji handling."""
        console_manager = RichConsoleManager()

        # Should not raise exception regardless of terminal capability
        console_manager.show_status("Test message", "success")
        console_manager.show_loading("Test loading")

        output = self.get_console_output()
        self.assertIn("Test message", output)
        self.assertIn("Test loading", output)

    def test_display_panel_methods(self):
        """Test panel display methods."""
        console_manager = RichConsoleManager()

        # Test different panel types
        console_manager.show_info_panel("Info", "Test info content")
        console_manager.show_error_panel("Error", "Test error", ["Suggestion 1", "Suggestion 2"])
        console_manager.show_success_panel("Success", "Test success", {"Key": "Value"})

        output = self.get_console_output()
        self.assertIn("Test info content", output)
        self.assertIn("Test error", output)
        self.assertIn("Test success", output)
        self.assertIn("Suggestion 1", output)
        self.assertIn("Key", output)

    def test_configuration_table_display(self):
        """Test configuration table formatting."""
        console_manager = RichConsoleManager()

        config = {
            "Provider": "openai",
            "Enabled": True,
            "API Key": None,
            "Count": 42
        }

        console_manager.show_configuration_table(config, "Test Configuration")

        output = self.get_console_output()
        self.assertIn("Test Configuration", output)
        self.assertIn("Provider", output)
        self.assertIn("openai", output)
        self.assertIn("Yes", output)  # Boolean formatting
        self.assertIn("Not set", output)  # None formatting

    def test_interactive_cli_initialization(self):
        """Test InteractiveCLI initialization with all dependencies."""
        cli = InteractiveCLI()

        self.assertIsNotNone(cli.console_manager)
        self.assertIsNotNone(cli.parser)
        self.assertIsNotNone(cli.config_manager)
        self.assertIsNotNone(cli.wizard)
        self.assertIsNotNone(cli.display_manager)
        self.assertIsNotNone(cli._console)

    def test_error_handling_with_suggestions(self):
        """Test error handling with context-specific suggestions."""
        cli = InteractiveCLI()

        # Test API key error
        api_error = Exception("API key not found")
        cli.handle_error(api_error, {"provider": "openai"})

        output = self.get_console_output()
        self.assertIn("API key", output)
        self.assertIn("OPENAI_API_KEY", output)

        # Test permission error
        perm_error = Exception("Permission denied")
        cli.handle_error(perm_error, {})

        output = self.get_console_output()
        self.assertIn("Permission", output)
        self.assertIn("permissions", output)

    def test_processing_result_display(self):
        """Test processing result formatting."""
        cli = InteractiveCLI()

        # Success result
        success_result = ProcessingResult(
            success=True,
            files_processed=5,
            files_failed=1,
            output_directory="/test/output",
            errors=[],
            warnings=["Warning 1"],
            metadata={"processing_time": "10 seconds"}
        )

        cli.show_results(success_result)

        output = self.get_console_output()
        self.assertIn("Processing Complete", output)
        self.assertIn("5", output)  # files processed
        self.assertIn("Warning 1", output)

        # Clear output
        self.reset_console()

        # Failure result
        failure_result = ProcessingResult(
            success=False,
            files_processed=0,
            files_failed=5,
            output_directory="",
            errors=["Error 1", "Error 2"],
            warnings=[],
            metadata={}
        )

        cli.show_results(failure_result)

        output = self.get_console_output()
        self.assertIn("Processing Failed", output)
        self.assertIn("Error 1", output)

class TestProgrammaticInterface(unittest.TestCase):
    """Test programmatic interface components."""

    def test_content_tamer_api_initialization(self):
        """Test API initialization with default configuration."""
        api = ContentTamerAPI()

        self.assertIsNotNone(api.config_manager)
        self.assertIsNotNone(api.config)

    def test_supported_providers_list(self):
        """Test getting supported providers."""
        api = ContentTamerAPI()
        providers = api.get_supported_providers()

        self.assertIsInstance(providers, list)
        self.assertIn("openai", providers)
        self.assertIn("claude", providers)
        self.assertIn("local", providers)

    def test_provider_models_retrieval(self):
        """Test getting models for specific providers."""
        api = ContentTamerAPI()

        openai_models = api.get_supported_models("openai")
        self.assertIsInstance(openai_models, list)
        self.assertTrue(any("gpt" in model for model in openai_models))

        claude_models = api.get_supported_models("claude")
        self.assertIsInstance(claude_models, list)
        self.assertTrue(any("claude" in model for model in claude_models))

    def test_api_key_validation(self):
        """Test API key validation."""
        api = ContentTamerAPI()

        # Valid key format
        self.assertTrue(api.validate_api_key("openai", "sk-test-key"))

        # Empty key
        self.assertFalse(api.validate_api_key("openai", ""))
        self.assertFalse(api.validate_api_key("openai", "   "))

    def test_configuration_validation(self):
        """Test configuration validation."""
        api = ContentTamerAPI()

        # Valid basic configuration
        valid_config = {
            "input_dir": ".",
            "output_dir": "./output",
            "provider": "openai"
        }

        errors = api.validate_configuration(valid_config)
        # Should have API key error but no structural errors
        self.assertIsInstance(errors, list)

    @patch('src.interfaces.programmatic.library_interface.ContentTamerAPI')
    def test_simple_processing_function(self, mock_api_class):
        """Test simple processing convenience function."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        mock_result = ProcessingResult(
            success=True,
            files_processed=3,
            files_failed=0,
            output_directory="./output",
            errors=[],
            warnings=[],
            metadata={}
        )
        mock_api.process_documents.return_value = mock_result

        result = process_documents_simple(
            input_dir="./input",
            output_dir="./output",
            api_key="test-key"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.files_processed, 3)
        mock_api.process_documents.assert_called_once()

    def test_setup_validation_function(self):
        """Test setup validation convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(input_dir)

            errors = validate_setup(input_dir, output_dir)

            # Should have API key error but no directory errors
            self.assertIsInstance(errors, list)
            self.assertTrue(any("API key" in error for error in errors))

    def test_provider_info_function(self):
        """Test provider info convenience function."""
        # All providers
        all_info = get_provider_info()
        self.assertIn("supported_providers", all_info)
        self.assertIn("provider_models", all_info)

        # Specific provider
        openai_info = get_provider_info("openai")
        self.assertIn("provider", openai_info)
        self.assertIn("models", openai_info)
        self.assertEqual(openai_info["provider"], "openai")

class TestProtocolInterface(unittest.TestCase):
    """Test protocol interface components."""

    def setUp(self):
        """Set up test environment."""
        self.server = create_mcp_server()

    def test_mcp_server_creation(self):
        """Test MCP server creation and initialization."""
        server = create_mcp_server()

        self.assertIsInstance(server, MCPServer)
        self.assertIsNotNone(server.api)
        self.assertIsInstance(server.tools, list)
        self.assertIsInstance(server.resources, list)
        self.assertGreater(len(server.tools), 0)
        self.assertGreater(len(server.resources), 0)

    def test_mcp_tools_definition(self):
        """Test MCP tools are properly defined."""
        tools = self.server.tools

        tool_names = [tool.name for tool in tools]
        self.assertIn("process_documents", tool_names)
        self.assertIn("validate_setup", tool_names)
        self.assertIn("get_provider_info", tool_names)

        # Check tool schemas
        process_tool = next(t for t in tools if t.name == "process_documents")
        self.assertIn("input_dir", process_tool.input_schema["properties"])
        self.assertIn("output_dir", process_tool.input_schema["properties"])

    def test_mcp_resources_definition(self):
        """Test MCP resources are properly defined."""
        resources = self.server.resources

        resource_uris = [resource.uri for resource in resources]
        self.assertIn("content-tamer://docs/api", resource_uris)
        self.assertIn("content-tamer://config/current", resource_uris)
        self.assertIn("content-tamer://status/system", resource_uris)

    async def test_mcp_request_handling(self):
        """Test MCP request handling."""
        # Test tools list request
        tools_response = await self.server.handle_request({
            "method": "tools/list",
            "params": {}
        })

        self.assertIn("tools", tools_response)
        self.assertIsInstance(tools_response["tools"], list)

        # Test resources list request
        resources_response = await self.server.handle_request({
            "method": "resources/list",
            "params": {}
        })

        self.assertIn("resources", resources_response)
        self.assertIsInstance(resources_response["resources"], list)

        # Test unknown method
        error_response = await self.server.handle_request({
            "method": "unknown/method",
            "params": {}
        })

        self.assertIn("error", error_response)
        self.assertEqual(error_response["error"]["code"], -32601)

    async def test_mcp_tool_execution(self):
        """Test MCP tool execution."""
        # Test validate_setup tool
        response = await self.server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "validate_setup",
                "arguments": {
                    "input_dir": "./nonexistent",
                    "output_dir": "./test_output"
                }
            }
        })

        self.assertIn("content", response)
        content_text = response["content"][0]["text"]
        self.assertIn("validation failed", content_text.lower())

        # Test get_provider_info tool
        provider_response = await self.server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "get_provider_info",
                "arguments": {}
            }
        })

        self.assertIn("content", provider_response)
        content_text = provider_response["content"][0]["text"]
        provider_data = json.loads(content_text)
        self.assertIn("supported_providers", provider_data)

    async def test_mcp_resource_reading(self):
        """Test MCP resource reading."""
        # Test API documentation
        docs_response = await self.server.handle_request({
            "method": "resources/read",
            "params": {
                "uri": "content-tamer://docs/api"
            }
        })

        self.assertIn("contents", docs_response)
        self.assertEqual(docs_response["contents"][0]["mimeType"], "text/markdown")
        self.assertIn("API Documentation", docs_response["contents"][0]["text"])

        # Test system status
        status_response = await self.server.handle_request({
            "method": "resources/read",
            "params": {
                "uri": "content-tamer://status/system"
            }
        })

        self.assertIn("contents", status_response)
        status_data = json.loads(status_response["contents"][0]["text"])
        self.assertIn("supported_providers", status_data)

class TestInterfaceRouting(unittest.TestCase):
    """Test interface routing and context detection."""

    def setUp(self):
        """Set up test environment."""
        self.detector = ContextDetector()
        self.router = InterfaceRouter()

    def test_context_detection_human(self):
        """Test human interface context detection."""
        with patch('sys.stdout.isatty', return_value=True):
            with patch('sys.argv', ['content-tamer-ai']):
                interface_type = self.detector.detect_interface_type()
                self.assertEqual(interface_type, InterfaceType.HUMAN)

    def test_context_detection_programmatic(self):
        """Test programmatic interface context detection."""
        with patch('sys.stdout.isatty', return_value=False):
            interface_type = self.detector.detect_interface_type()
            self.assertEqual(interface_type, InterfaceType.PROGRAMMATIC)

    def test_context_detection_mcp(self):
        """Test MCP interface context detection."""
        with patch.dict(os.environ, {'MCP_SERVER_MODE': '1'}):
            interface_type = self.detector.detect_interface_type()
            self.assertEqual(interface_type, InterfaceType.PROTOCOL)

    def test_forced_interface_type(self):
        """Test forcing specific interface type."""
        interface_type = self.detector.detect_interface_type("protocol")
        self.assertEqual(interface_type, InterfaceType.PROTOCOL)

    def test_interface_router_creation(self):
        """Test interface router creates correct interfaces."""
        # Human interface
        human_interface = self.router.get_interface(InterfaceType.HUMAN)
        self.assertIsInstance(human_interface, InteractiveCLI)

        # Programmatic interface
        api_interface = self.router.get_interface(InterfaceType.PROGRAMMATIC)
        self.assertIsInstance(api_interface, ContentTamerAPI)

        # Protocol interface
        protocol_interface = self.router.get_interface(InterfaceType.PROTOCOL)
        self.assertIsInstance(protocol_interface, MCPServer)

    def test_interface_caching(self):
        """Test interface instance caching."""
        interface1 = self.router.get_interface(InterfaceType.HUMAN)
        interface2 = self.router.get_interface(InterfaceType.HUMAN)
        self.assertIs(interface1, interface2)

    def test_routing_info(self):
        """Test routing information generation."""
        info = self.router.get_routing_info()

        self.assertIn("detected_type", info)
        self.assertIn("context", info)
        self.assertIn("routing_reasons", info)
        self.assertIsInstance(info["routing_reasons"], list)

    def test_persona_detection(self):
        """Test persona detection logic."""
        # Test different context scenarios
        with patch('sys.stdout.isatty', return_value=True):
            with patch('sys.argv', ['content-tamer-ai']):
                persona = detect_persona()
                self.assertIn(persona, ['developer', 'analyst'])

        with patch.dict(os.environ, {'CI': 'true'}):
            with patch('sys.stdout.isatty', return_value=False):
                persona = detect_persona()
                self.assertEqual(persona, 'automation')

    def test_persona_router_configuration(self):
        """Test persona-based configuration."""
        dev_config = PersonaRouter.get_persona_config("developer")
        self.assertEqual(dev_config["interface"], "human")
        self.assertTrue(dev_config["verbose"])

        auto_config = PersonaRouter.get_persona_config("automation")
        self.assertEqual(auto_config["interface"], "programmatic")
        self.assertFalse(auto_config["verbose"])

    def test_convenience_functions(self):
        """Test convenience routing functions."""
        # Test get_interface
        interface = get_interface("human")
        self.assertIsInstance(interface, InteractiveCLI)

        # Test auto_route
        auto_interface = auto_route()
        self.assertIsNotNone(auto_interface)

        # Test routing info
        info = get_routing_info()
        self.assertIn("detected_type", info)

class TestInterfaceIntegration(unittest.TestCase):
    """Test integration between different interface components."""

    def test_unified_display_manager_integration(self):
        """Test UnifiedDisplayManager integration with interfaces."""
        cli = InteractiveCLI()

        # Test that display manager is properly initialized
        self.assertIsNotNone(cli.display_manager)
        self.assertIs(cli.display_manager.console, cli._console)

    def test_shared_emoji_handler_integration(self):
        """Test shared emoji handler integration."""
        console_manager = RichConsoleManager()

        # Test that emoji handler is initialized
        self.assertTrue(hasattr(console_manager, '_emoji_handler'))

        # Test emoji handler usage doesn't raise exceptions
        console_manager.show_status("Test with emoji", "success")
        console_manager.show_loading("Loading with emoji")

    def test_configuration_sharing(self):
        """Test configuration sharing between interfaces."""
        api = ContentTamerAPI()
        cli = InteractiveCLI()

        # Both should use same configuration manager type
        self.assertEqual(type(api.config_manager), type(cli.config_manager))

    def test_cross_interface_error_handling(self):
        """Test consistent error handling across interfaces."""
        # All interfaces should handle basic exceptions gracefully

        # Human interface
        cli = InteractiveCLI()
        try:
            cli.handle_error(Exception("Test error"), {})
        except Exception as e:
            self.fail("Human interface error handling failed: {e}")

        # Programmatic interface
        api = ContentTamerAPI()
        try:
            result = api.process_documents({"invalid": "config"})
            self.assertFalse(result.success)
        except Exception as e:
            self.fail("Programmatic interface error handling failed: {e}")

if __name__ == '__main__':
    # Run tests with proper test discovery
    unittest.main(verbosity=2)
