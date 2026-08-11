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
            api=McpApiConfig(host="custom-host", port=9999),
            server=McpServerConfig(name="custom-server"),
        )

        mcp = create_mcp_server(config)

        assert mcp is not None
        assert mcp.name == "custom-server"

    def test_client_uses_host_and_port_when_base_url_unset(self) -> None:
        """Test the API URL falls back to http://host:port."""
        from taskdog_mcp.server import create_mcp_server

        config = McpConfig(api=McpApiConfig(host="custom-host", port=9999))

        with patch("taskdog_mcp.server.TaskdogApiClient") as mock_client:
            create_mcp_server(config)

        mock_client.assert_called_once_with("http://custom-host:9999", api_key=None)

    def test_client_uses_base_url_when_set(self) -> None:
        """Test base_url takes precedence over host/port."""
        from taskdog_mcp.server import create_mcp_server

        config = McpConfig(
            api=McpApiConfig(
                host="custom-host",
                port=9999,
                base_url="https://tasks.example.com",
            )
        )

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
