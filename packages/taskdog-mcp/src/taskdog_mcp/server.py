"""MCP server for Taskdog.

This module creates and configures the FastMCP server with all task management tools.
"""

import logging

from mcp.server.fastmcp import FastMCP
from taskdog_client import TaskdogApiClient

from taskdog_mcp.config.mcp_config_manager import McpConfig, load_mcp_config

logger = logging.getLogger(__name__)


def create_mcp_server(config: McpConfig | None = None) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        config: MCP configuration. If None, loads from mcp.toml.

    Returns:
        Configured FastMCP server instance
    """
    if config is None:
        config = load_mcp_config()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.server.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create API client
    base_url = f"http://{config.api.host}:{config.api.port}"
    client = TaskdogApiClient(base_url, api_key=config.api.api_key)

    # Create MCP server
    mcp = FastMCP(config.server.name)

    # Register all tools
    from taskdog_mcp.tools import (
        task_audit,
        task_crud,
        task_decomposition,
        task_lifecycle,
        task_query,
        task_tags,
    )

    task_crud.register_tools(mcp, client)
    task_lifecycle.register_tools(mcp, client)
    task_query.register_tools(mcp, client)
    task_decomposition.register_tools(mcp, client)
    task_tags.register_tools(mcp, client)
    task_audit.register_tools(mcp, client)

    logger.info(
        f"MCP server '{config.server.name}' initialized, connecting to {base_url}"
    )

    return mcp
