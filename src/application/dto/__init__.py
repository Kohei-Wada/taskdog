"""Data Transfer Objects."""

from application.dto.statistics_result import (
    CalculateStatisticsRequest,
    DeadlineComplianceStatistics,
    EstimationAccuracyStatistics,
    PriorityDistributionStatistics,
    StatisticsResult,
    TaskStatistics,
    TimeStatistics,
    TrendStatistics,
)
from application.dto.task_detail_result import GetTaskDetailResult

__all__ = [
    "CalculateStatisticsRequest",
    "DeadlineComplianceStatistics",
    "EstimationAccuracyStatistics",
    "GetTaskDetailResult",
    "PriorityDistributionStatistics",
    "StatisticsResult",
    "TaskStatistics",
    "TimeStatistics",
    "TrendStatistics",
]
