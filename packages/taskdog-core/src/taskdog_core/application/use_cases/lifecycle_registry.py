"""Registry mapping lifecycle operation names to their status-change use cases."""

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.use_cases.cancel_task import CancelTaskUseCase
from taskdog_core.application.use_cases.complete_task import CompleteTaskUseCase
from taskdog_core.application.use_cases.pause_task import PauseTaskUseCase
from taskdog_core.application.use_cases.reopen_task import ReopenTaskUseCase
from taskdog_core.application.use_cases.start_task import StartTaskUseCase
from taskdog_core.application.use_cases.status_change_use_case import (
    StatusChangeUseCase,
)

LIFECYCLE_USE_CASES: dict[str, type[StatusChangeUseCase[SingleTaskInput]]] = {
    "start": StartTaskUseCase,
    "complete": CompleteTaskUseCase,
    "pause": PauseTaskUseCase,
    "cancel": CancelTaskUseCase,
    "reopen": ReopenTaskUseCase,
}
