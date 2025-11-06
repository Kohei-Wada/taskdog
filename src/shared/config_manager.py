"""Configuration management for taskdog.

Loads configuration from TOML file with fallback to default values.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from shared.constants.config_defaults import (
    DEFAULT_ALGORITHM,
    DEFAULT_DATETIME_FORMAT,
    DEFAULT_END_HOUR,
    DEFAULT_MAX_HOURS_PER_DAY,
    DEFAULT_PRIORITY,
    DEFAULT_START_HOUR,
)
from shared.xdg_utils import XDGDirectories


@dataclass(frozen=True)
class OptimizationConfig:
    """Optimization-related configuration.

    Attributes:
        max_hours_per_day: Maximum work hours per day for schedule optimization
        default_algorithm: Default optimization algorithm to use
    """

    max_hours_per_day: float = DEFAULT_MAX_HOURS_PER_DAY
    default_algorithm: str = DEFAULT_ALGORITHM


@dataclass(frozen=True)
class TaskConfig:
    """Task-related configuration.

    Attributes:
        default_priority: Default priority for new tasks
    """

    default_priority: int = DEFAULT_PRIORITY


@dataclass(frozen=True)
class DisplayConfig:
    """Display-related configuration.

    Attributes:
        datetime_format: Format string for datetime display
    """

    datetime_format: str = DEFAULT_DATETIME_FORMAT


@dataclass(frozen=True)
class TimeConfig:
    """Time-related configuration.

    Attributes:
        default_start_hour: Default hour for task start times (business day start)
        default_end_hour: Default hour for task end times and deadlines (business day end)
    """

    default_start_hour: int = DEFAULT_START_HOUR
    default_end_hour: int = DEFAULT_END_HOUR


@dataclass(frozen=True)
class RegionConfig:
    """Region-related configuration.

    Attributes:
        country: ISO 3166-1 alpha-2 country code (e.g., "JP", "US")
                 None means no holiday checking
    """

    country: str | None = None


@dataclass(frozen=True)
class StorageConfig:
    """Storage backend configuration.

    Attributes:
        backend: Storage backend to use ("json" or "sqlite")
        database_url: SQLite database URL (only used when backend="sqlite")
                      If None, defaults to XDG data directory
    """

    backend: str = "json"
    database_url: str | None = None


@dataclass(frozen=True)
class ApiConfig:
    """API server configuration.

    Attributes:
        enabled: Whether to use API mode (client-server communication)
        host: API server host
        port: API server port
        auto_start: Whether to automatically start server on CLI/TUI startup
    """

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    auto_start: bool = True


@dataclass(frozen=True)
class Config:
    """Taskdog configuration.

    Attributes:
        optimization: Optimization-related settings
        task: Task-related settings
        display: Display-related settings
        time: Time-related settings
        region: Region-related settings (holidays, etc.)
        storage: Storage backend settings
        api: API server settings
    """

    optimization: OptimizationConfig
    task: TaskConfig
    display: DisplayConfig
    time: TimeConfig
    region: RegionConfig = field(default_factory=RegionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    api: ApiConfig = field(default_factory=ApiConfig)


class ConfigManager:
    """Manages taskdog configuration loading."""

    @classmethod
    def load(cls, config_path: Path | None = None) -> Config:
        """Load configuration from TOML file with fallback to defaults.

        Args:
            config_path: Path to config file (default: XDG config path)

        Returns:
            Config object with loaded or default values
        """
        if config_path is None:
            config_path = XDGDirectories.get_config_file()

        # If config file doesn't exist, return defaults
        if not config_path.exists():
            return cls._default_config()

        # Load TOML file
        try:
            with config_path.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            # Fall back to defaults on read or parse error
            return cls._default_config()

        # Parse sections with fallback to defaults
        optimization_data = data.get("optimization", {})
        task_data = data.get("task", {})
        display_data = data.get("display", {})
        time_data = data.get("time", {})
        region_data = data.get("region", {})
        storage_data = data.get("storage", {})
        api_data = data.get("api", {})

        return Config(
            optimization=OptimizationConfig(
                max_hours_per_day=optimization_data.get(
                    "max_hours_per_day", DEFAULT_MAX_HOURS_PER_DAY
                ),
                default_algorithm=optimization_data.get("default_algorithm", DEFAULT_ALGORITHM),
            ),
            task=TaskConfig(
                default_priority=task_data.get("default_priority", DEFAULT_PRIORITY),
            ),
            display=DisplayConfig(
                datetime_format=display_data.get("datetime_format", DEFAULT_DATETIME_FORMAT),
            ),
            time=TimeConfig(
                default_start_hour=time_data.get("default_start_hour", DEFAULT_START_HOUR),
                default_end_hour=time_data.get("default_end_hour", DEFAULT_END_HOUR),
            ),
            region=RegionConfig(
                country=region_data.get("country"),
            ),
            storage=StorageConfig(
                backend=storage_data.get("backend", "json"),
                database_url=storage_data.get("database_url"),
            ),
            api=ApiConfig(
                enabled=api_data.get("enabled", False),
                host=api_data.get("host", "127.0.0.1"),
                port=api_data.get("port", 8000),
                auto_start=api_data.get("auto_start", True),
            ),
        )

    @classmethod
    def _default_config(cls) -> Config:
        """Create default configuration.

        Returns:
            Config with all default values
        """
        return Config(
            optimization=OptimizationConfig(),
            task=TaskConfig(),
            display=DisplayConfig(),
            time=TimeConfig(),
            region=RegionConfig(),
            storage=StorageConfig(),
            api=ApiConfig(),
        )
