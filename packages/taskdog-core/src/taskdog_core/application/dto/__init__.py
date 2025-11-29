"""Data Transfer Objects."""

from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.query_inputs import (
    GetGanttDataInput,
    ListTasksInput,
    TimeRange,
)
from taskdog_core.application.dto.single_task_inputs import (
    ArchiveTaskInput,
    CancelTaskInput,
    CompleteTaskInput,
    PauseTaskInput,
    RemoveTaskInput,
    ReopenTaskInput,
    RestoreTaskInput,
    StartTaskInput,
)
from taskdog_core.application.dto.statistics_output import (
    CalculateStatisticsInput,
    DeadlineComplianceStatistics,
    EstimationAccuracyStatistics,
    PriorityDistributionStatistics,
    StatisticsOutput,
    TaskStatistics,
    TimeStatistics,
    TrendStatistics,
)
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput

__all__ = [
    "ArchiveTaskInput",
    "CalculateStatisticsInput",
    "CancelTaskInput",
    "CompleteTaskInput",
    "DeadlineComplianceStatistics",
    "EstimationAccuracyStatistics",
    "GanttDateRange",
    "GanttOutput",
    "GetGanttDataInput",
    "ListTasksInput",
    "PauseTaskInput",
    "PriorityDistributionStatistics",
    "RemoveTaskInput",
    "ReopenTaskInput",
    "RestoreTaskInput",
    "StartTaskInput",
    "StatisticsOutput",
    "TaskDetailOutput",
    "TaskStatistics",
    "TimeRange",
    "TimeStatistics",
    "TrendStatistics",
]
