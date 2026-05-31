"""Platform directory utilities for taskdog.

Uses XDG Base Directory defaults on Unix-like systems and AppData defaults on
Windows, while keeping XDG environment variables as explicit overrides.
"""

import os
import platform
from pathlib import Path

from taskdog_core.shared.constants.file_management import CONFIG_FILE_NAME


class XDGDirectories:
    """Platform-specific directory helper for taskdog.

    XDG environment variables are honored first for compatibility. Native
    Windows defaults use AppData locations when XDG variables are not set.
    """

    APP_NAME = "taskdog"

    @classmethod
    def _default_data_base(cls) -> Path:
        """Get platform default base directory for application data."""
        if platform.system() == "Windows":
            local_app_data = os.getenv("LOCALAPPDATA")
            if local_app_data:
                return Path(local_app_data)
            return Path.home() / "AppData" / "Local"
        return Path.home() / ".local" / "share"

    @classmethod
    def _default_config_base(cls) -> Path:
        """Get platform default base directory for configuration files."""
        if platform.system() == "Windows":
            app_data = os.getenv("APPDATA")
            if app_data:
                return Path(app_data)
            return Path.home() / "AppData" / "Roaming"
        return Path.home() / ".config"

    @classmethod
    def get_data_home(cls, create: bool = True) -> Path:
        """Get application data directory for taskdog.

        Returns:
            Path to $XDG_DATA_HOME/taskdog, or the platform default.

        Args:
            create: Create directory if it doesn't exist (default: True)
        """
        base_dir = Path(os.getenv("XDG_DATA_HOME") or cls._default_data_base())
        data_dir = Path(base_dir) / cls.APP_NAME

        if create:
            data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir

    @classmethod
    def get_config_home(cls, create: bool = True) -> Path:
        """Get configuration directory for taskdog.

        Returns:
            Path to $XDG_CONFIG_HOME/taskdog, or the platform default.

        Args:
            create: Create directory if it doesn't exist (default: True)
        """
        base_dir = Path(os.getenv("XDG_CONFIG_HOME") or cls._default_config_base())
        config_dir = Path(base_dir) / cls.APP_NAME

        if create:
            config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir

    @classmethod
    def get_config_file(cls) -> Path:
        """Get path to config.toml file.

        Returns:
            Path to config.toml in config directory
        """
        return cls.get_config_home() / CONFIG_FILE_NAME
