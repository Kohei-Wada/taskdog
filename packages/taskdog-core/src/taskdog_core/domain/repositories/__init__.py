"""Domain layer repository interfaces."""

from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository

__all__ = ["NotesRepository", "TaskRepository"]
