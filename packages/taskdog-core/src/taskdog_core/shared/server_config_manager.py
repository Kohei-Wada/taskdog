"""Server configuration management for taskdog-server.

This module provides configuration management specifically for the server component,
separating server concerns (time, region, storage) from client concerns (optimization, UI).
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_END_HOUR,
    DEFAULT_PRIORITY,
    DEFAULT_START_HOUR,
)
from taskdog_core.shared.xdg_utils import XDGDirectories


@dataclass(frozen=True)
class TimeConfig:
    """Time-related configuration for server.

    Attributes:
        default_start_hour: Default hour for task start times (business day start)
        default_end_hour: Default hour for task end times and deadlines (business day end)
    """

    default_start_hour: int = DEFAULT_START_HOUR
    default_end_hour: int = DEFAULT_END_HOUR


@dataclass(frozen=True)
class RegionConfig:
    """Region-related configuration for server.

    Attributes:
        country: ISO 3166-1 alpha-2 country code (e.g., "JP", "US")
                 None means no holiday checking
    """

    country: str | None = None


@dataclass(frozen=True)
class StorageConfig:
    """Storage backend configuration for server.

    Attributes:
        backend: Storage backend to use (currently only "sqlite" is supported)
        database_url: SQLite database URL
                      If None, defaults to XDG data directory
    """

    backend: str = "sqlite"
    database_url: str | None = None


@dataclass(frozen=True)
class TaskConfig:
    """Task-related configuration.

    This is shared between server and client as both need default priority.

    Attributes:
        default_priority: Default priority for new tasks
    """

    default_priority: int = DEFAULT_PRIORITY


@dataclass(frozen=True)
class ServerConfig:
    """Server configuration.

    This contains all configuration needed by the taskdog-server component.

    Attributes:
        time: Time-related settings (business hours)
        region: Region-related settings (holidays)
        storage: Storage backend settings (database)
        task: Task-related settings (defaults)
    """

    time: TimeConfig
    region: RegionConfig
    storage: StorageConfig
    task: TaskConfig = field(default_factory=TaskConfig)


class ServerConfigManager:
    """Manages server configuration loading from server.toml file."""

    @classmethod
    def load(cls, config_path: Path | None = None) -> ServerConfig:
        """Load server configuration from TOML file.

        Args:
            config_path: Path to server.toml file. If None, uses default XDG location.

        Returns:
            ServerConfig with loaded or default values
        """
        if config_path is None:
            config_path = XDGDirectories.get_server_config_file()

        if not config_path.exists():
            return cls._default_config()

        try:
            with config_path.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return cls._default_config()

        time_data = data.get("time", {})
        region_data = data.get("region", {})
        storage_data = data.get("storage", {})
        task_data = data.get("task", {})

        return ServerConfig(
            time=TimeConfig(
                default_start_hour=time_data.get(
                    "default_start_hour", DEFAULT_START_HOUR
                ),
                default_end_hour=time_data.get("default_end_hour", DEFAULT_END_HOUR),
            ),
            region=RegionConfig(
                country=region_data.get("country"),
            ),
            storage=StorageConfig(
                backend=storage_data.get("backend", "sqlite"),
                database_url=storage_data.get("database_url"),
            ),
            task=TaskConfig(
                default_priority=task_data.get("default_priority", DEFAULT_PRIORITY),
            ),
        )

    @classmethod
    def _default_config(cls) -> ServerConfig:
        """Create default server configuration.

        Returns:
            ServerConfig with all default values
        """
        return ServerConfig(
            time=TimeConfig(),
            region=RegionConfig(),
            storage=StorageConfig(),
            task=TaskConfig(),
        )
