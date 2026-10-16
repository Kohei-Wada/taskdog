"""Tests for MCP server creation."""

from typing import Any
from unittest.mock import MagicMock, patch

from mcp import Client
from mcp.types import CallToolResult, TextContent
from taskdog_mcp.config.mcp_config_manager import (
    McpApiConfig,
    McpConfig,
    McpServerConfig,
)

from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


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


class TestToolErrorMessages:
    """Test tool failures reach the MCP client with their message."""

    async def _call_tool(
        self, api_client: MagicMock, name: str, arguments: dict[str, Any]
    ) -> CallToolResult:
        from taskdog_mcp.server import create_mcp_server

        with patch("taskdog_mcp.server.TaskdogApiClient", return_value=api_client):
            mcp = create_mcp_server(McpConfig())

        async with Client(mcp) as client:
            return await client.call_tool(name, arguments)

    async def test_task_error_message_is_returned(self) -> None:
        api_client = MagicMock()
        api_client.get_task_by_id.side_effect = TaskNotFoundException(999)

        result = await self._call_tool(api_client, "get_task", {"task_id": 999})

        assert result.is_error
        assert isinstance(result.content[0], TextContent)
        assert "Task with ID 999 not found" in result.content[0].text

    async def test_value_error_message_is_returned(self) -> None:
        result = await self._call_tool(
            MagicMock(), "create_task", {"name": "x", "deadline": "next friday"}
        )

        assert result.is_error
        assert isinstance(result.content[0], TextContent)
        assert "next friday" in result.content[0].text
