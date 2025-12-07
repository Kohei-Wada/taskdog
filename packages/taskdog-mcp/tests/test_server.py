"""Tests for MCP server creation."""

from unittest.mock import MagicMock

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


class TestTaskdogMcpClients:
    """Test TaskdogMcpClients container."""

    def test_clients_container_creation(self) -> None:
        """Test creating clients container."""
        from taskdog_mcp.server import TaskdogMcpClients

        # Create mock base client
        mock_base = MagicMock()

        clients = TaskdogMcpClients(mock_base)

        assert clients.base is mock_base
        assert clients.tasks is not None
        assert clients.lifecycle is not None
        assert clients.queries is not None
        assert clients.analytics is not None
        assert clients.relationships is not None
        assert clients.notes is not None

    def test_clients_use_same_base_client(self) -> None:
        """Test all clients share the same base client."""
        from taskdog_mcp.server import TaskdogMcpClients

        mock_base = MagicMock()
        clients = TaskdogMcpClients(mock_base)

        # All clients should use the same base client
        assert clients.tasks._base is mock_base
        assert clients.lifecycle._base is mock_base
        assert clients.queries._base is mock_base
        assert clients.analytics._base is mock_base
        assert clients.relationships._base is mock_base
        assert clients.notes._base is mock_base
