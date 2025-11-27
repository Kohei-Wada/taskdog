"""Configuration management for taskdog.

Loads configuration from TOML file and environment variables with fallback to default values.
Priority: Environment variables > TOML file > Default values
"""

import logging
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_ALGORITHM,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_END_HOUR,
    DEFAULT_MAX_HOURS_PER_DAY,
    DEFAULT_PRIORITY,
    DEFAULT_START_HOUR,
)
from taskdog_core.shared.xdg_utils import XDGDirectories

logger = logging.getLogger(__name__)


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

    # Environment variable prefix
    ENV_PREFIX = "TASKDOG_"

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
        toml_data = cls._load_toml(config_path)

        # Parse sections with fallback to defaults, then apply env overrides
        optimization_data = toml_data.get("optimization", {})
        task_data = toml_data.get("task", {})
        time_data = toml_data.get("time", {})
        region_data = toml_data.get("region", {})
        storage_data = toml_data.get("storage", {})
        api_data = toml_data.get("api", {})

        return Config(
            optimization=OptimizationConfig(
                max_hours_per_day=cls._get_env_or(
                    "OPTIMIZATION_MAX_HOURS_PER_DAY",
                    optimization_data.get(
                        "max_hours_per_day", DEFAULT_MAX_HOURS_PER_DAY
                    ),
                    float,
                ),
                default_algorithm=cls._get_env_or(
                    "OPTIMIZATION_DEFAULT_ALGORITHM",
                    optimization_data.get("default_algorithm", DEFAULT_ALGORITHM),
                    str,
                ),
            ),
            task=TaskConfig(
                default_priority=cls._get_env_or(
                    "TASK_DEFAULT_PRIORITY",
                    task_data.get("default_priority", DEFAULT_PRIORITY),
                    int,
                ),
            ),
            time=TimeConfig(
                default_start_hour=cls._get_env_or(
                    "TIME_DEFAULT_START_HOUR",
                    time_data.get("default_start_hour", DEFAULT_START_HOUR),
                    int,
                ),
                default_end_hour=cls._get_env_or(
                    "TIME_DEFAULT_END_HOUR",
                    time_data.get("default_end_hour", DEFAULT_END_HOUR),
                    int,
                ),
            ),
            region=RegionConfig(
                country=cls._get_env_or(
                    "REGION_COUNTRY",
                    region_data.get("country"),
                    str,
                ),
            ),
            storage=StorageConfig(
                backend=cls._get_env_or(
                    "STORAGE_BACKEND",
                    storage_data.get("backend", "sqlite"),
                    str,
                ),
                database_url=cls._get_env_or(
                    "STORAGE_DATABASE_URL",
                    storage_data.get("database_url"),
                    str,
                ),
            ),
            api=ApiConfig(
                cors_origins=cls._get_env_list_or(
                    "API_CORS_ORIGINS",
                    api_data.get("cors_origins", DEFAULT_CORS_ORIGINS),
                ),
            ),
        )

    @classmethod
    def _load_toml(cls, config_path: Path) -> dict[str, Any]:
        """Load TOML configuration file.

        Args:
            config_path: Path to the TOML configuration file

        Returns:
            Parsed TOML data as dictionary, or empty dict if file doesn't exist or is invalid
        """
        if not config_path.exists():
            return {}

        try:
            with config_path.open("rb") as f:
                return tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return {}

    @classmethod
    def _get_env_or(
        cls,
        key: str,
        default: Any,
        type_: type[int] | type[float] | type[str] | type[bool],
    ) -> Any:
        """Get value from environment variable with type conversion.

        Args:
            key: Environment variable key (without TASKDOG_ prefix)
            default: Default value if environment variable is not set
            type_: Type to convert the value to

        Returns:
            Environment variable value converted to type_, or default if not set.
            If conversion fails, logs a warning and returns the default value.
        """
        env_key = f"{cls.ENV_PREFIX}{key}"
        value = os.environ.get(env_key)

        if value is None:
            return default

        try:
            if type_ is bool:
                return value.lower() in ("true", "1", "yes")
            if type_ is int:
                return int(value)
            if type_ is float:
                return float(value)
            return value
        except ValueError:
            logger.warning(
                "Invalid value for environment variable %s: '%s'. "
                "Expected %s, using default: %s",
                env_key,
                value,
                type_.__name__,
                default,
            )
            return default

    @classmethod
    def _get_env_list_or(cls, key: str, default: list[str]) -> list[str]:
        """Get list value from environment variable.

        Args:
            key: Environment variable key (without TASKDOG_ prefix)
            default: Default value if environment variable is not set

        Returns:
            List parsed from comma-separated environment variable, or default
        """
        env_key = f"{cls.ENV_PREFIX}{key}"
        value = os.environ.get(env_key)

        if value is None:
            return default

        # Parse comma-separated list, stripping whitespace
        return [item.strip() for item in value.split(",") if item.strip()]

    @classmethod
    def _default_config(cls) -> Config:
        """Create default configuration.

        Returns:
            Config with all default values
        """
        return Config(
            optimization=OptimizationConfig(),
            task=TaskConfig(),
            time=TimeConfig(),
            region=RegionConfig(),
            storage=StorageConfig(),
            api=ApiConfig(),
        )
