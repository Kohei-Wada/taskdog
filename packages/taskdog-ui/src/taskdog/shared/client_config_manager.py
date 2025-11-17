"""Client configuration management for taskdog CLI/TUI.

This module provides configuration management specifically for the client components (CLI/TUI),
separating client concerns (optimization defaults, API connection, UI settings) from server concerns.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_ALGORITHM,
    DEFAULT_MAX_HOURS_PER_DAY,
)
from taskdog_core.shared.xdg_utils import XDGDirectories


@dataclass(frozen=True)
class OptimizationConfig:
    """Optimization-related configuration for client.

    Attributes:
        max_hours_per_day: Maximum work hours per day for schedule optimization
        default_algorithm: Default optimization algorithm to use
    """

    max_hours_per_day: float = DEFAULT_MAX_HOURS_PER_DAY
    default_algorithm: str = DEFAULT_ALGORITHM


@dataclass(frozen=True)
class ApiConfig:
    """API connection configuration for client.

    Attributes:
        url: Full API URL (e.g., "http://localhost:8000")
             If provided, this takes precedence over host+port
        host: API server host (fallback if url is not provided)
        port: API server port (fallback if url is not provided)
    """

    url: str | None = None
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass(frozen=True)
class ClientConfig:
    """Client configuration.

    This contains all configuration needed by the taskdog CLI/TUI components.

    Attributes:
        optimization: Optimization-related settings (defaults for CLI/TUI)
        api: API connection settings (server URL)
    """

    optimization: OptimizationConfig
    api: ApiConfig


class ClientConfigManager:
    """Manages client configuration loading from client.toml file."""

    @classmethod
    def load(cls, config_path: Path | None = None) -> ClientConfig:
        """Load client configuration from TOML file.

        Args:
            config_path: Path to client.toml file. If None, uses default XDG location.

        Returns:
            ClientConfig with loaded or default values
        """
        if config_path is None:
            config_path = XDGDirectories.get_client_config_file()

        if not config_path.exists():
            return cls._default_config()

        try:
            with config_path.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return cls._default_config()

        optimization_data = data.get("optimization", {})
        api_data = data.get("api", {})

        return ClientConfig(
            optimization=OptimizationConfig(
                max_hours_per_day=optimization_data.get(
                    "max_hours_per_day", DEFAULT_MAX_HOURS_PER_DAY
                ),
                default_algorithm=optimization_data.get(
                    "default_algorithm", DEFAULT_ALGORITHM
                ),
            ),
            api=ApiConfig(
                url=api_data.get("url"),
                host=api_data.get("host", "127.0.0.1"),
                port=api_data.get("port", 8000),
            ),
        )

    @classmethod
    def _default_config(cls) -> ClientConfig:
        """Create default client configuration.

        Returns:
            ClientConfig with all default values
        """
        return ClientConfig(
            optimization=OptimizationConfig(),
            api=ApiConfig(),
        )
