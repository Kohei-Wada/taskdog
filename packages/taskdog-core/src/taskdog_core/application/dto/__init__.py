"""Data Transfer Objects."""

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.query_inputs import (
    GetGanttDataInput,
    ListTasksInput,
    TimeRange,
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
    "CalculateStatisticsInput",
    "DeadlineComplianceStatistics",
    "EstimationAccuracyStatistics",
    "GanttDateRange",
    "GanttOutput",
    "GetGanttDataInput",
    "ListTasksInput",
    "PriorityDistributionStatistics",
    "SingleTaskInput",
    "StatisticsOutput",
    "TaskDetailOutput",
    "TaskStatistics",
    "TimeRange",
    "TimeStatistics",
    "TrendStatistics",
]
