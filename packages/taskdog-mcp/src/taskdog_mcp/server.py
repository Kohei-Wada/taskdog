"""MCP server for Taskdog.

This module creates and configures the FastMCP server with all task management tools.
"""

import logging

from mcp.server.fastmcp import FastMCP
from taskdog_client import (
    AnalyticsClient,
    BaseApiClient,
    LifecycleClient,
    NotesClient,
    QueryClient,
    RelationshipClient,
    TaskClient,
)

from taskdog_mcp.config.mcp_config_manager import McpConfig, load_mcp_config

logger = logging.getLogger(__name__)


class TaskdogMcpClients:
    """Container for all API clients used by MCP tools."""

    def __init__(self, base_client: BaseApiClient) -> None:
        """Initialize all API clients.

        Args:
            base_client: Base HTTP client for API communication
        """
        self.base = base_client
        self.tasks = TaskClient(base_client)
        self.lifecycle = LifecycleClient(base_client)
        self.relationships = RelationshipClient(base_client)
        self._has_notes_cache: dict[int, bool] = {}
        self.queries = QueryClient(base_client, self._has_notes_cache)
        self.analytics = AnalyticsClient(base_client)
        self.notes = NotesClient(base_client)


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

    # Create base API client
    base_url = f"http://{config.api.host}:{config.api.port}"
    base_client = BaseApiClient(base_url, api_key=config.api.api_key)

    # Create clients container
    clients = TaskdogMcpClients(base_client)

    # Create MCP server
    mcp = FastMCP(config.server.name)

    # Register all tools
    from taskdog_mcp.tools import (
        task_crud,
        task_decomposition,
        task_lifecycle,
        task_query,
    )

    task_crud.register_tools(mcp, clients)
    task_lifecycle.register_tools(mcp, clients)
    task_query.register_tools(mcp, clients)
    task_decomposition.register_tools(mcp, clients)

    logger.info(
        f"MCP server '{config.server.name}' initialized, connecting to {base_url}"
    )

    return mcp
