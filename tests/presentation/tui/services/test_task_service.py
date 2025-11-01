"""Tests for TaskService."""

import unittest
from unittest.mock import MagicMock

from domain.repositories.notes_repository import NotesRepository
from domain.repositories.task_repository import TaskRepository
from presentation.controllers.query_controller import QueryController
from presentation.controllers.task_controller import TaskController
from presentation.tui.context import TUIContext
from presentation.tui.services.task_service import TaskService
from shared.config_manager import ConfigManager


class TestTaskService(unittest.TestCase):
    """Test cases for TaskService."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = MagicMock(spec=TaskRepository)
        self.notes_repository = MagicMock(spec=NotesRepository)
        self.config = ConfigManager._default_config()
        self.task_controller = MagicMock(spec=TaskController)
        self.query_controller = MagicMock(spec=QueryController)

        # Create TUIContext with new structure
        self.context = TUIContext(
            config=self.config,
            notes_repository=self.notes_repository,
            task_controller=self.task_controller,
            query_controller=self.query_controller,
        )

        # Initialize TaskService with context and repository
        self.service = TaskService(self.context, self.repository)


if __name__ == "__main__":
    unittest.main()
