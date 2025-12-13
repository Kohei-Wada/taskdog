"""Configuration management for taskdog.

Loads configuration from TOML file and environment variables with fallback to default values.
Priority: Environment variables > TOML file > Default values
"""

from dataclasses import dataclass, field
from pathlib import Path

from taskdog_core.shared.config_loader import ConfigLoader
from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_ALGORITHM,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_END_HOUR,
    DEFAULT_MAX_HOURS_PER_DAY,
    DEFAULT_PRIORITY,
    DEFAULT_START_HOUR,
)
from taskdog_core.shared.xdg_utils import XDGDirectories


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
        backend: Storage backend to use (currently only "sqlite" is supported)
        database_url: SQLite database URL
                      If None, defaults to XDG data directory
    """

    backend: str = "sqlite"
    database_url: str | None = None


@dataclass(frozen=True)
class ApiConfig:
    """API server configuration.

    Note: host and port are configured via CLI arguments, not here.
    This config only contains settings that affect server behavior.

    Attributes:
        cors_origins: List of allowed CORS origins for API requests (for future Web UI)
    """

    cors_origins: list[str] = field(default_factory=lambda: DEFAULT_CORS_ORIGINS.copy())


@dataclass(frozen=True)
class Config:
    """Taskdog configuration.

    Attributes:
        optimization: Optimization-related settings
        task: Task-related settings
        time: Time-related settings
        region: Region-related settings (holidays, etc.)
        storage: Storage backend settings
        api: API server settings
    """

    optimization: OptimizationConfig
    task: TaskConfig
    time: TimeConfig
    region: RegionConfig = field(default_factory=RegionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    api: ApiConfig = field(default_factory=ApiConfig)


class ConfigManager:
    """Manages taskdog configuration loading.

    Configuration priority (highest to lowest):
    1. Environment variables (TASKDOG_*)
    2. TOML configuration file
    3. Default values
    """

    @classmethod
    def load(cls, config_path: Path | None = None) -> Config:
        """Load configuration from environment variables and TOML file.

        Args:
            config_path: Path to config file (default: XDG config path)

        Returns:
            Config object with loaded or default values
        """
        if config_path is None:
            config_path = XDGDirectories.get_config_file()

        # Load TOML file data (or empty dict if not available)
        toml_data = ConfigLoader.load_toml(config_path)

        # Parse sections with fallback to defaults, then apply env overrides
        optimization_data = toml_data.get("optimization", {})
        task_data = toml_data.get("task", {})
        time_data = toml_data.get("time", {})
        region_data = toml_data.get("region", {})
        storage_data = toml_data.get("storage", {})
        api_data = toml_data.get("api", {})

        return Config(
            optimization=OptimizationConfig(
                max_hours_per_day=ConfigLoader.get_env(
                    "OPTIMIZATION_MAX_HOURS_PER_DAY",
                    optimization_data.get(
                        "max_hours_per_day", DEFAULT_MAX_HOURS_PER_DAY
                    ),
                    float,
                ),
                default_algorithm=ConfigLoader.get_env(
                    "OPTIMIZATION_DEFAULT_ALGORITHM",
                    optimization_data.get("default_algorithm", DEFAULT_ALGORITHM),
                    str,
                ),
            ),
            task=TaskConfig(
                default_priority=ConfigLoader.get_env(
                    "TASK_DEFAULT_PRIORITY",
                    task_data.get("default_priority", DEFAULT_PRIORITY),
                    int,
                ),
            ),
            time=TimeConfig(
                default_start_hour=ConfigLoader.get_env(
                    "TIME_DEFAULT_START_HOUR",
                    time_data.get("default_start_hour", DEFAULT_START_HOUR),
                    int,
                ),
                default_end_hour=ConfigLoader.get_env(
                    "TIME_DEFAULT_END_HOUR",
                    time_data.get("default_end_hour", DEFAULT_END_HOUR),
                    int,
                ),
            ),
            region=RegionConfig(
                country=ConfigLoader.get_env(
                    "REGION_COUNTRY",
                    region_data.get("country"),
                    str,
                ),
            ),
            storage=StorageConfig(
                backend=ConfigLoader.get_env(
                    "STORAGE_BACKEND",
                    storage_data.get("backend", "sqlite"),
                    str,
                ),
                database_url=ConfigLoader.get_env(
                    "STORAGE_DATABASE_URL",
                    storage_data.get("database_url"),
                    str,
                ),
            ),
            api=ApiConfig(
                cors_origins=ConfigLoader.get_env_list(
                    "API_CORS_ORIGINS",
                    api_data.get("cors_origins", DEFAULT_CORS_ORIGINS),
                ),
            ),
        )
