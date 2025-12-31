"""Server-specific configuration management.

Handles server.toml for authentication and other server-specific settings.
"""

from dataclasses import dataclass, field
from pathlib import Path

from taskdog_core.shared.config_loader import ConfigLoader
from taskdog_core.shared.xdg_utils import XDGDirectories

SERVER_CONFIG_FILENAME = "server.toml"

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]


@dataclass(frozen=True)
class CorsConfig:
    """CORS (Cross-Origin Resource Sharing) configuration.

    Attributes:
        origins: List of allowed CORS origins for API requests (for future Web UI)
    """

    origins: tuple[str, ...] = tuple(DEFAULT_CORS_ORIGINS)


@dataclass(frozen=True)
class ApiKeyEntry:
    """API key entry with associated name.

    Attributes:
        name: Human-readable name for the API key (e.g., "claude-code", "webhook-github")
        key: The actual API key value
    """

    name: str
    key: str


@dataclass(frozen=True)
class AuthConfig:
    """Authentication configuration.

    Attributes:
        enabled: Whether authentication is enabled. Default is True.
                 When disabled, all requests are allowed without API key.
        api_keys: Tuple of API key entries. When enabled=True and empty,
                  all requests are rejected.
    """

    enabled: bool = True
    api_keys: tuple[ApiKeyEntry, ...] = ()


@dataclass(frozen=True)
class ServerConfig:
    """Server-specific configuration.

    Attributes:
        auth: Authentication configuration
        cors: CORS configuration
    """

    auth: AuthConfig = field(default_factory=AuthConfig)
    cors: CorsConfig = field(default_factory=CorsConfig)


class ServerConfigManager:
    """Manages server-specific configuration from server.toml.

    Configuration file location follows XDG spec:
    - $XDG_CONFIG_HOME/taskdog/server.toml
    - Falls back to ~/.config/taskdog/server.toml

    Example server.toml:
        [auth]
        enabled = true  # optional, default true

        [[auth.api_keys]]
        name = "claude-code"
        key = "sk-xxxxxxxxxxxxxxxx"

        [[auth.api_keys]]
        name = "webhook-github"
        key = "sk-yyyyyyyyyyyyyyyy"

    Environment variables:
        TASKDOG_AUTH_ENABLED: Override auth.enabled (true/false)
    """

    @classmethod
    def load(cls, config_path: Path | None = None) -> ServerConfig:
        """Load server configuration from file.

        Args:
            config_path: Optional path to config file. If None, uses XDG default.

        Returns:
            ServerConfig: Loaded configuration with defaults applied
        """
        if config_path is None:
            config_path = XDGDirectories.get_config_home() / SERVER_CONFIG_FILENAME

        data = ConfigLoader.load_toml(config_path)
        auth_data = data.get("auth", {})

        # Parse enabled flag with environment variable override
        enabled_from_file = auth_data.get("enabled", True)
        enabled = ConfigLoader.get_env(
            "AUTH_ENABLED",
            enabled_from_file,
            bool,
        )

        # Parse API keys
        api_keys_data = auth_data.get("api_keys", [])
        api_keys = tuple(
            ApiKeyEntry(name=entry["name"], key=entry["key"])
            for entry in api_keys_data
            if isinstance(entry, dict) and "name" in entry and "key" in entry
        )

        # Parse CORS configuration
        cors_data = data.get("cors", {})
        cors_origins_from_file = cors_data.get("origins", DEFAULT_CORS_ORIGINS)
        cors_origins = ConfigLoader.get_env_list(
            "CORS_ORIGINS",
            cors_origins_from_file,
        )

        return ServerConfig(
            auth=AuthConfig(enabled=enabled, api_keys=api_keys),
            cors=CorsConfig(origins=tuple(cors_origins)),
        )
