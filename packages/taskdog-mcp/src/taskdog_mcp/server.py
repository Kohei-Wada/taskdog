"""MCP server for Taskdog.

This module creates and configures the MCP server with all task management tools.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from taskdog_client import TaskdogApiClient

from taskdog_core.domain.exceptions.task_exceptions import TaskError
from taskdog_mcp.config.mcp_config_manager import McpConfig, load_mcp_config

logger = logging.getLogger(__name__)


class TaskdogMCPServer(MCPServer):
    """MCPServer that reports expected tool failures to the client.

    mcp 2.x hides the message of any exception other than ToolError, so
    TaskError and ValueError are converted to keep their message visible.
    """

    def add_tool(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        @functools.wraps(fn)
        def wrapper(*fn_args: Any, **fn_kwargs: Any) -> Any:
            try:
                return fn(*fn_args, **fn_kwargs)
            except (TaskError, ValueError) as e:
                raise ToolError(str(e)) from e

        super().add_tool(wrapper, *args, **kwargs)


def create_mcp_server(config: McpConfig | None = None) -> MCPServer:
    """Create and configure the MCP server.

    Args:
        config: MCP configuration. If None, loads from mcp.toml.

    Returns:
        Configured MCPServer instance
    """
    if config is None:
        config = load_mcp_config()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.server.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create API client
    client = TaskdogApiClient(config.api.base_url, api_key=config.api.api_key)

    # Create MCP server
    mcp = TaskdogMCPServer(config.server.name)

    # Register all tools
    from taskdog_mcp.tools import (
        task_audit,
        task_crud,
        task_decomposition,
        task_lifecycle,
        task_optimization,
        task_query,
        task_tags,
    )

    task_crud.register_tools(mcp, client)
    task_lifecycle.register_tools(mcp, client)
    task_query.register_tools(mcp, client)
    task_decomposition.register_tools(mcp, client)
    task_tags.register_tools(mcp, client)
    task_audit.register_tools(mcp, client)
    task_optimization.register_tools(mcp, client)

    logger.info(
        f"MCP server '{config.server.name}' initialized, "
        f"connecting to {config.api.base_url}"
    )

    return mcp
