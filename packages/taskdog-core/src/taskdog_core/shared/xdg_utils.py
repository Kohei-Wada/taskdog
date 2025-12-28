"""XDG Base Directory utilities for taskdog.

Implements the XDG Base Directory Specification:
https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

On Windows, uses platformdirs for cross-platform compatibility:
- Data: %LOCALAPPDATA%/taskdog
- Config: %LOCALAPPDATA%/taskdog
"""

import os
import sys
from pathlib import Path

from taskdog_core.shared.constants.file_management import (
    CONFIG_FILE_NAME,
    NOTE_FILE_EXTENSION,
    NOTES_DIR_NAME,
)

# Import platformdirs for Windows support
if sys.platform == "win32":
    import platformdirs


class XDGDirectories:
    """XDG Base Directory helper for taskdog.

    On Linux/macOS: Uses XDG Base Directory Specification.
    On Windows: Uses platformdirs for standard Windows paths.
    """

    APP_NAME = "taskdog"

    @classmethod
    def get_data_home(cls, create: bool = True) -> Path:
        """Get data directory for taskdog.

        Returns:
            Linux/macOS: $XDG_DATA_HOME/taskdog (default: ~/.local/share/taskdog)
            Windows: %LOCALAPPDATA%/taskdog

        Args:
            create: Create directory if it doesn't exist (default: True)
        """
        # XDG environment variable takes precedence on all platforms
        xdg_data = os.getenv("XDG_DATA_HOME")
        if xdg_data:
            data_dir = Path(xdg_data) / cls.APP_NAME
        elif sys.platform == "win32":
            # Windows: use platformdirs for %LOCALAPPDATA%
            data_dir = Path(platformdirs.user_data_dir(cls.APP_NAME, roaming=False))
        else:
            # Linux/macOS: use XDG default
            base_dir = os.path.expanduser("~/.local/share")
            data_dir = Path(base_dir) / cls.APP_NAME

        if create:
            data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir

    @classmethod
    def get_config_home(cls, create: bool = True) -> Path:
        """Get config directory for taskdog.

        Returns:
            Linux/macOS: $XDG_CONFIG_HOME/taskdog (default: ~/.config/taskdog)
            Windows: %LOCALAPPDATA%/taskdog

        Args:
            create: Create directory if it doesn't exist (default: True)
        """
        # XDG environment variable takes precedence on all platforms
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / cls.APP_NAME
        elif sys.platform == "win32":
            # Windows: use platformdirs for %LOCALAPPDATA%
            config_dir = Path(platformdirs.user_config_dir(cls.APP_NAME, roaming=False))
        else:
            # Linux/macOS: use XDG default
            base_dir = os.path.expanduser("~/.config")
            config_dir = Path(base_dir) / cls.APP_NAME

        if create:
            config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir

    @classmethod
    def get_notes_dir(cls) -> Path:
        """Get path to notes directory.

        Returns:
            Path to notes directory in data directory
        """
        notes_dir = cls.get_data_home() / NOTES_DIR_NAME
        notes_dir.mkdir(parents=True, exist_ok=True)
        return notes_dir

    @classmethod
    def get_note_file(cls, task_id: int | None) -> Path:
        """Get path to a specific task's note file.

        Args:
            task_id: Task ID

        Returns:
            Path to note markdown file
        """
        return cls.get_notes_dir() / f"{task_id}{NOTE_FILE_EXTENSION}"

    @classmethod
    def get_config_file(cls) -> Path:
        """Get path to config.toml file.

        Returns:
            Path to config.toml in config directory
        """
        return cls.get_config_home() / CONFIG_FILE_NAME
