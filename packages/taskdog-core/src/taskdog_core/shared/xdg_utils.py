"""XDG Base Directory utilities for taskdog.

Implements the XDG Base Directory Specification:
https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
"""

import os
from pathlib import Path

from taskdog_core.shared.constants.file_management import (
    CONFIG_FILE_NAME,
    NOTE_FILE_EXTENSION,
    NOTES_DIR_NAME,
)


class XDGDirectories:
    """XDG Base Directory helper for taskdog."""

    APP_NAME = "taskdog"

    @classmethod
    def get_data_home(cls, create: bool = True) -> Path:
        """Get XDG_DATA_HOME directory for taskdog.

        Returns:
            Path to $XDG_DATA_HOME/taskdog (default: ~/.local/share/taskdog)

        Args:
            create: Create directory if it doesn't exist (default: True)
        """
        base_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        data_dir = Path(base_dir) / cls.APP_NAME

        if create:
            data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir

    @classmethod
    def get_config_home(cls, create: bool = True) -> Path:
        """Get XDG_CONFIG_HOME directory for taskdog.

        Returns:
            Path to $XDG_CONFIG_HOME/taskdog (default: ~/.config/taskdog)

        Args:
            create: Create directory if it doesn't exist (default: True)
        """
        base_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
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
