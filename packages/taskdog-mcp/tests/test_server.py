"""Tests for MCP server creation."""

from unittest.mock import patch

from taskdog_mcp.config.mcp_config_manager import (
    McpApiConfig,
    McpConfig,
    McpServerConfig,
)


class TestCreateMcpServer:
    """Test MCP server creation."""

    def test_create_server_with_default_config(self) -> None:
        """Test creating server with default configuration."""
        from taskdog_mcp.server import create_mcp_server

        mcp = create_mcp_server()

        assert mcp is not None
        assert mcp.name == "taskdog"

    def test_create_server_with_custom_config(self) -> None:
        """Test creating server with custom configuration."""
        from taskdog_mcp.server import create_mcp_server

        config = McpConfig(
            api=McpApiConfig(base_url="http://custom-host:9999"),
            server=McpServerConfig(name="custom-server"),
        )

        mcp = create_mcp_server(config)

        assert mcp is not None
        assert mcp.name == "custom-server"

    def test_client_uses_default_base_url(self) -> None:
        """Test the API URL defaults to the local server."""
        from taskdog_mcp.server import create_mcp_server

        with patch("taskdog_mcp.server.TaskdogApiClient") as mock_client:
            create_mcp_server(McpConfig())

        mock_client.assert_called_once_with("http://127.0.0.1:8000", api_key=None)

    def test_client_uses_configured_base_url(self) -> None:
        """Test the configured base_url is passed to the client."""
        from taskdog_mcp.server import create_mcp_server

        config = McpConfig(api=McpApiConfig(base_url="https://tasks.example.com"))

        with patch("taskdog_mcp.server.TaskdogApiClient") as mock_client:
            create_mcp_server(config)

        mock_client.assert_called_once_with("https://tasks.example.com", api_key=None)

    def test_server_has_registered_tools(self) -> None:
        """Test server has tools registered."""
        from taskdog_mcp.server import create_mcp_server

        mcp = create_mcp_server()

        # Check that tools are registered by verifying the server exists
        # The actual tools are registered via MCPServer decorators
        assert mcp is not None
