"""MCP-specific configuration management.

This module provides configuration loading for the MCP server.
"""

from dataclasses import dataclass, field

from taskdog_core.shared.config_loader import ConfigLoader
from taskdog_core.shared.xdg_utils import XDGDirectories

MCP_CONFIG_FILENAME = "mcp.toml"


@dataclass(frozen=True)
class McpApiConfig:
    """API connection configuration for MCP server.

    Attributes:
        host: API server hostname
        port: API server port
        api_key: API key for authentication
    """

    host: str = "127.0.0.1"
    port: int = 8000
    api_key: str | None = None


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
        TASKDOG_API_HOST: API server hostname
        TASKDOG_API_PORT: API server port
        TASKDOG_API_KEY: API key for authentication
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
            host=ConfigLoader.get_env(
                "API_HOST",
                api_data.get("host", "127.0.0.1"),
                str,
            ),
            port=ConfigLoader.get_env(
                "API_PORT",
                api_data.get("port", 8000),
                int,
                log_errors=False,
            ),
            api_key=ConfigLoader.get_env(
                "API_KEY",
                api_data.get("api_key"),
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
