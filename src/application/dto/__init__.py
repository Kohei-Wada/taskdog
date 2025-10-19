"""Data Transfer Objects."""

from application.dto.statistics_result import (
    CalculateStatisticsInput,
    DeadlineComplianceStatistics,
    EstimationAccuracyStatistics,
    PriorityDistributionStatistics,
    StatisticsResult,
    TaskStatistics,
    TimeStatistics,
    TrendStatistics,
)
from application.dto.task_detail_dto import TaskDetailDTO

__all__ = [
    "CalculateStatisticsInput",
    "DeadlineComplianceStatistics",
    "EstimationAccuracyStatistics",
    "PriorityDistributionStatistics",
    "StatisticsResult",
    "TaskDetailDTO",
    "TaskStatistics",
    "TimeStatistics",
    "TrendStatistics",
]
