"""Generic configuration loading utilities.

Provides common functionality for loading TOML files and
reading environment variables with type conversion.
"""

import logging
import os
import tomllib
from pathlib import Path
from typing import Any, TypeVar, overload

logger = logging.getLogger(__name__)

T = TypeVar("T", int, float, str, bool)


class ConfigLoader:
    """Generic configuration loading utilities.

    Provides common functionality for loading TOML files and
    reading environment variables with type conversion.

    This class is used by ConfigManager (core) and cli_config (ui)
    to avoid code duplication.
    """

    @staticmethod
    def load_toml(path: Path) -> dict[str, Any]:
        """Load TOML file, returning empty dict if not found or invalid.

        Args:
            path: Path to the TOML configuration file

        Returns:
            Parsed TOML data as dictionary, or empty dict if file
            doesn't exist or is invalid
        """
        if not path.exists():
            return {}
        try:
            with path.open("rb") as f:
                return tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return {}

    @overload
    @staticmethod
    def get_env(
        key: str,
        default: T,
        type_: type[T],
        prefix: str = ...,
        log_errors: bool = ...,
    ) -> T: ...

    @overload
    @staticmethod
    def get_env(
        key: str,
        default: None,
        type_: type[T],
        prefix: str = ...,
        log_errors: bool = ...,
    ) -> T | None: ...

    @staticmethod
    def get_env(
        key: str,
        default: T | None,
        type_: type[T],
        prefix: str = "TASKDOG_",
        log_errors: bool = True,
    ) -> T | None:
        """Get environment variable with type conversion.

        Args:
            key: Environment variable key (without prefix)
            default: Default value if not set or conversion fails
            type_: Target type (int, float, str, bool)
            prefix: Environment variable prefix (default: "TASKDOG_")
            log_errors: Whether to log conversion errors (default: True)

        Returns:
            Converted value or default if not set or conversion fails.
            If default is non-None, return type is guaranteed to be T.
            If default is None, return type is T | None.
        """
        env_key = f"{prefix}{key}"
        value = os.environ.get(env_key)

        if value is None or value.strip() == "":
            return default

        try:
            if type_ is bool:
                return value.lower() in ("true", "1", "yes")  # type: ignore[return-value]
            if type_ is int:
                return int(value)  # type: ignore[return-value]
            if type_ is float:
                return float(value)  # type: ignore[return-value]
            return value  # type: ignore[return-value]
        except ValueError:
            if log_errors:
                logger.warning(
                    "Invalid value for environment variable %s: '%s'. "
                    "Expected %s, using default: %s",
                    env_key,
                    value,
                    type_.__name__,
                    default,
                )
            return default

    @staticmethod
    def get_env_list(
        key: str,
        default: list[str],
        prefix: str = "TASKDOG_",
    ) -> list[str]:
        """Get comma-separated list from environment variable.

        Args:
            key: Environment variable key (without prefix)
            default: Default value if environment variable is not set
            prefix: Environment variable prefix (default: "TASKDOG_")

        Returns:
            List parsed from comma-separated environment variable,
            or default if not set
        """
        env_key = f"{prefix}{key}"
        value = os.environ.get(env_key)

        if value is None or value.strip() == "":
            return default

        return [item.strip() for item in value.split(",") if item.strip()]
