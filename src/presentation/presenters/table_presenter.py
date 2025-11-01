"""Presenter for converting TaskListOutput to TaskRowViewModels.

This presenter extracts necessary fields from TaskRowDto within TaskListOutput
and creates presentation-ready view models for table/list display.
"""

from application.dto.task_dto import TaskRowDto
from application.dto.task_list_output import TaskListOutput
from domain.entities.task import TaskStatus as DomainTaskStatus
from domain.repositories.notes_repository import NotesRepository
from presentation.enums.task_status import TaskStatus as PresentationTaskStatus
from presentation.view_models.task_view_model import TaskRowViewModel


class TablePresenter:
    """Presenter for converting TaskListOutput DTO to TaskRowViewModels.

    This class is responsible for:
    1. Extracting necessary fields from TaskRowDto within DTOs
    2. Checking for associated notes
    3. Converting DTO data to presentation-ready ViewModels
    """

    def __init__(self, notes_repository: NotesRepository):
        """Initialize the presenter.

        Args:
            notes_repository: Repository for checking note existence
        """
        self.notes_repository = notes_repository

    @staticmethod
    def convert_status(domain_status: DomainTaskStatus) -> PresentationTaskStatus:
        """Convert domain TaskStatus to presentation TaskStatus.

        This maintains separation between domain and presentation layers while
        ensuring the status values are properly converted.

        Args:
            domain_status: Domain layer TaskStatus

        Returns:
            Presentation layer TaskStatus
        """
        # Direct mapping by enum value
        return PresentationTaskStatus(domain_status.value)

    def present(self, output: TaskListOutput) -> list[TaskRowViewModel]:
        """Convert TaskListOutput DTO to list of TaskRowViewModels.

        Args:
            output: TaskListOutput DTO from QueryController

        Returns:
            List of TaskRowViewModels ready for rendering
        """
        return [self._task_to_view_model(task) for task in output.tasks]

    def _task_to_view_model(self, task: TaskRowDto) -> TaskRowViewModel:
        """Convert a TaskRowDto to TaskRowViewModel.

        Args:
            task: TaskRowDto from application layer

        Returns:
            TaskRowViewModel with presentation-ready data
        """
        # Check if task has notes
        has_notes = self.notes_repository.has_notes(task.id)

        return TaskRowViewModel(
            id=task.id,
            name=task.name,
            status=self.convert_status(task.status),
            priority=task.priority,
            is_fixed=task.is_fixed,
            estimated_duration=task.estimated_duration,
            actual_duration_hours=task.actual_duration_hours,
            deadline=task.deadline,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            depends_on=task.depends_on.copy() if task.depends_on else [],
            tags=task.tags.copy() if task.tags else [],
            is_finished=task.is_finished,
            has_notes=has_notes,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
