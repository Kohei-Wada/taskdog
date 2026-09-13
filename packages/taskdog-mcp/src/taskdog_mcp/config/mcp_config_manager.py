"""MCP-specific configuration management.

This module provides configuration loading for the MCP server.
"""

from dataclasses import dataclass, field

from taskdog_core.shared.config_loader import ConfigLoader
from taskdog_core.shared.xdg_utils import XDGDirectories

MCP_CONFIG_FILENAME = "mcp.toml"
DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


@dataclass(frozen=True)
class McpApiConfig:
    """API connection configuration for MCP server.

    Attributes:
        api_key: API key for authentication
        base_url: Full API base URL (e.g. "https://tasks.example.com").
            Supports HTTPS endpoints and reverse proxies serving the API under
            a path prefix.
    """

    api_key: str | None = None
    base_url: str = DEFAULT_API_BASE_URL


@dataclass(frozen=True)
class McpServerConfig:
    """MCP server configuration.

    Attributes:
        name: Server name shown to MCP clients
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    name: str = "taskdog"
    log_level: str = "INFO"


@dataclass(frozen=True)
class McpConfig:
    """MCP configuration.

    Attributes:
        api: API connection settings
        server: MCP server settings
    """

    api: McpApiConfig = field(default_factory=McpApiConfig)
    server: McpServerConfig = field(default_factory=McpServerConfig)


def load_mcp_config() -> McpConfig:
    """Load MCP configuration with priority: env vars > mcp.toml > defaults.

    Environment variables:
        TASKDOG_API_KEY: API key for authentication
        TASKDOG_API_BASE_URL: Full API base URL
        TASKDOG_MCP_NAME: MCP server name
        TASKDOG_MCP_LOG_LEVEL: Logging level

    Returns:
        McpConfig with merged settings

    Note:
        If mcp.toml doesn't exist, uses defaults.
        Environment variables override file settings.
    """
    # Load from mcp.toml (returns empty dict if not exists or invalid)
    config_path = XDGDirectories.get_config_home() / MCP_CONFIG_FILENAME
    data = ConfigLoader.load_toml(config_path)

    # Parse sections
    api_data = data.get("api", {})
    server_data = data.get("server", {})

    # Build config with env var overrides
    return McpConfig(
        api=McpApiConfig(
            api_key=ConfigLoader.get_env(
                "API_KEY",
                api_data.get("api_key"),
                str,
            ),
            base_url=ConfigLoader.get_env(
                "API_BASE_URL",
                api_data.get("base_url", DEFAULT_API_BASE_URL),
                str,
            ),
        ),
        server=McpServerConfig(
            name=ConfigLoader.get_env(
                "MCP_NAME",
                server_data.get("name", "taskdog"),
                str,
            ),
            log_level=ConfigLoader.get_env(
                "MCP_LOG_LEVEL",
                server_data.get("log_level", "INFO"),
                str,
            ),
        ),
    )
