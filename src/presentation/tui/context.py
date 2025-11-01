"""TUI context for dependency injection."""

from dataclasses import dataclass

from application.queries.task_query_service import TaskQueryService
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.file_notes_repository import FileNotesRepository
from shared.config_manager import Config


@dataclass
class TUIContext:
    """Context object holding TUI dependencies.

    This dataclass provides a clean way to pass dependencies to TUI commands
    without coupling them to the entire app instance.

    Attributes:
        repository: Task repository for data access
        time_tracker: Time tracker service for recording timestamps
        query_service: Query service for read-only operations
        config: Application configuration
        notes_repository: Notes repository for notes file operations
    """

    repository: TaskRepository
    time_tracker: TimeTracker
    query_service: TaskQueryService
    config: Config
    notes_repository: FileNotesRepository
