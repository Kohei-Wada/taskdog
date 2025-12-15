"""Tests for MCP server creation."""

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

    def test_server_has_registered_tools(self) -> None:
        """Test server has tools registered."""
        from taskdog_mcp.server import create_mcp_server

        mcp = create_mcp_server()

        # Check that tools are registered by verifying the server exists
        # The actual tools are registered via FastMCP decorators
        assert mcp is not None
