"""Tests for TaskService."""

import unittest
from unittest.mock import MagicMock

from application.queries.task_query_service import TaskQueryService
from domain.repositories.notes_repository import NotesRepository
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from presentation.tui.context import TUIContext
from presentation.tui.services.task_service import TaskService
from shared.config_manager import ConfigManager


class TestTaskService(unittest.TestCase):
    """Test cases for TaskService."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = MagicMock(spec=TaskRepository)
        self.time_tracker = MagicMock(spec=TimeTracker)
        self.query_service = MagicMock(spec=TaskQueryService)
        self.notes_repository = MagicMock(spec=NotesRepository)
        self.config = ConfigManager._default_config()

        # Create TUIContext
        self.context = TUIContext(
            repository=self.repository,
            time_tracker=self.time_tracker,
            query_service=self.query_service,
            config=self.config,
            notes_repository=self.notes_repository,
        )

        # Initialize TaskService with context
        self.service = TaskService(self.context)


if __name__ == "__main__":
    unittest.main()
