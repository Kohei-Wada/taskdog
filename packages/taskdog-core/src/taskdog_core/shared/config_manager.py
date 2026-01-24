"""Configuration management for taskdog.

Loads configuration from TOML file and environment variables with fallback to default values.
Priority: Environment variables > TOML file > Default values
"""

from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Any

from taskdog_core.shared.config_loader import ConfigLoader
from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_END_TIME,
    DEFAULT_START_TIME,
)
from taskdog_core.shared.xdg_utils import XDGDirectories


def _is_valid_hour(hour: int) -> bool:
    """Check if hour is in valid range (0-23)."""
    return 0 <= hour <= 23


def _is_valid_minute(minute: int) -> bool:
    """Check if minute is in valid range (0-59)."""
    return 0 <= minute <= 59


def parse_time_value(value: int | str | None, default: time) -> time:
    """Parse time value with backward compatibility.

    Accepts:
    - int: 9 -> time(9, 0)
    - str: "09:30" -> time(9, 30)
    - str: "9" -> time(9, 0)
    - None: returns default

    Invalid values (out of range hours/minutes) return the default.

    Args:
        value: Time value in various formats
        default: Default time to use if value is None or invalid

    Returns:
        Parsed time object

    Examples:
        >>> parse_time_value(9, time(9, 0))
        datetime.time(9, 0)
        >>> parse_time_value("09:30", time(9, 0))
        datetime.time(9, 30)
        >>> parse_time_value("9", time(9, 0))
        datetime.time(9, 0)
        >>> parse_time_value(25, time(9, 0))  # Invalid hour
        datetime.time(9, 0)
    """
    if value is None:
        return default

    if isinstance(value, int):
        # Backward compatibility: integer hours (e.g., 9 -> 09:00)
        if not _is_valid_hour(value):
            return default
        return time(value, 0)

    if isinstance(value, str):
        value = value.strip()
        if ":" in value:
            # Format: "HH:MM" or "H:MM"
            parts = value.split(":")
            try:
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                if not _is_valid_hour(hour) or not _is_valid_minute(minute):
                    return default
                return time(hour, minute)
            except (ValueError, IndexError):
                return default
        else:
            # Single integer as string (e.g., "9")
            try:
                hour = int(value)
                if not _is_valid_hour(hour):
                    return default
                return time(hour, 0)
            except ValueError:
                return default

    return default


@dataclass(frozen=True)
class TimeConfig:
    """Time-related configuration.

    Attributes:
        default_start_time: Default time for task start times (business day start)
        default_end_time: Default time for task end times and deadlines (business day end)
    """

    default_start_time: time = DEFAULT_START_TIME
    default_end_time: time = DEFAULT_END_TIME


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
class Config:
    """Taskdog configuration.

    Attributes:
        time: Time-related settings
        region: Region-related settings (holidays, etc.)
        storage: Storage backend settings
    """

    time: TimeConfig
    region: RegionConfig = field(default_factory=RegionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)


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
        time_data = toml_data.get("time", {})
        region_data = toml_data.get("region", {})
        storage_data = toml_data.get("storage", {})

        # Parse time values with backward compatibility
        # Priority: env var > TOML > default
        # Supports: int (9), str ("09:30"), str ("9")
        start_time_raw: Any = ConfigLoader.get_env(
            "TIME_DEFAULT_START_TIME",
            time_data.get("default_start_time", time_data.get("default_start_hour")),
            str,
        )
        end_time_raw: Any = ConfigLoader.get_env(
            "TIME_DEFAULT_END_TIME",
            time_data.get("default_end_time", time_data.get("default_end_hour")),
            str,
        )

        return Config(
            time=TimeConfig(
                default_start_time=parse_time_value(start_time_raw, DEFAULT_START_TIME),
                default_end_time=parse_time_value(end_time_raw, DEFAULT_END_TIME),
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
        )
