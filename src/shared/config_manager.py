"""Configuration management for taskdog.

Loads configuration from TOML file with fallback to default values.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from shared.xdg_utils import XDGDirectories


@dataclass(frozen=True)
class OptimizationConfig:
    """Optimization-related configuration.

    Attributes:
        max_hours_per_day: Maximum work hours per day for schedule optimization
        default_algorithm: Default optimization algorithm to use
    """

    max_hours_per_day: float = 6.0
    default_algorithm: str = "greedy"


@dataclass(frozen=True)
class TaskConfig:
    """Task-related configuration.

    Attributes:
        default_priority: Default priority for new tasks
    """

    default_priority: int = 5


@dataclass(frozen=True)
class DisplayConfig:
    """Display-related configuration.

    Attributes:
        datetime_format: Format string for datetime display
    """

    datetime_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class Config:
    """Taskdog configuration.

    Attributes:
        optimization: Optimization-related settings
        task: Task-related settings
        display: Display-related settings
    """

    optimization: OptimizationConfig
    task: TaskConfig
    display: DisplayConfig


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

        return Config(
            optimization=OptimizationConfig(
                max_hours_per_day=optimization_data.get("max_hours_per_day", 6.0),
                default_algorithm=optimization_data.get("default_algorithm", "greedy"),
            ),
            task=TaskConfig(
                default_priority=task_data.get("default_priority", 5),
            ),
            display=DisplayConfig(
                datetime_format=display_data.get("datetime_format", "%Y-%m-%d %H:%M:%S"),
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
        )
