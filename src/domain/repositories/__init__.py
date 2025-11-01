"""Domain layer repository interfaces."""

from domain.repositories.notes_repository import NotesRepository
from domain.repositories.task_repository import TaskRepository

__all__ = ["NotesRepository", "TaskRepository"]
