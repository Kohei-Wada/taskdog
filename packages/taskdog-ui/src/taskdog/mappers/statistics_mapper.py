"""Mapper for converting StatisticsOutput DTO to StatisticsViewModel.

This mapper extracts necessary fields from TaskSummaryDto and creates
presentation-ready view models.
"""

from taskdog.view_models.statistics_view_model import (
    EstimationAccuracyStatisticsViewModel,
    StatisticsViewModel,
    TaskSummaryViewModel,
    TimeStatisticsViewModel,
)
from taskdog_core.application.dto.statistics_output import (
    EstimationAccuracyStatistics,
    StatisticsOutput,
    TimeStatistics,
)
from taskdog_core.application.dto.task_dto import TaskSummaryDto


class StatisticsMapper:
    """Mapper for converting StatisticsOutput to StatisticsViewModel.

    This class is responsible for:
    1. Extracting necessary fields from TaskSummaryDto
    2. Converting DTO data to presentation-ready ViewModels
    """

    @staticmethod
    def from_statistics_result(
        statistics_result: StatisticsOutput,
    ) -> StatisticsViewModel:
        """Convert StatisticsOutput DTO to StatisticsViewModel.

        Args:
            statistics_result: Application layer DTO with Task entities

        Returns:
            StatisticsViewModel with TaskSummaryViewModel (no Task entities)
        """
        # Convert TimeStatistics if present
        time_stats_vm = None
        if statistics_result.time_stats:
            time_stats_vm = StatisticsMapper._map_time_statistics(
                statistics_result.time_stats
            )

        # Convert EstimationAccuracyStatistics if present
        estimation_stats_vm = None
        if statistics_result.estimation_stats:
            estimation_stats_vm = StatisticsMapper._map_estimation_statistics(
                statistics_result.estimation_stats
            )

        # Other statistics don't contain Task entities, so use them directly
        return StatisticsViewModel(
            task_stats=statistics_result.task_stats,
            time_stats=time_stats_vm,
            estimation_stats=estimation_stats_vm,
            deadline_stats=statistics_result.deadline_stats,
            priority_stats=statistics_result.priority_stats,
            trend_stats=statistics_result.trend_stats,
        )

    @staticmethod
    def _map_time_statistics(time_stats: TimeStatistics) -> TimeStatisticsViewModel:
        """Convert TimeStatistics to TimeStatisticsViewModel.

        Args:
            time_stats: Time statistics DTO with Task entities

        Returns:
            TimeStatisticsViewModel with TaskSummaryViewModel
        """
        longest_task_vm = None
        if time_stats.longest_task:
            longest_task_vm = StatisticsMapper._map_task_to_summary(
                time_stats.longest_task
            )

        shortest_task_vm = None
        if time_stats.shortest_task:
            shortest_task_vm = StatisticsMapper._map_task_to_summary(
                time_stats.shortest_task
            )

        return TimeStatisticsViewModel(
            total_work_hours=time_stats.total_work_hours,
            average_work_hours=time_stats.average_work_hours,
            median_work_hours=time_stats.median_work_hours,
            longest_task=longest_task_vm,
            shortest_task=shortest_task_vm,
            tasks_with_time_tracking=time_stats.tasks_with_time_tracking,
        )

    @staticmethod
    def _map_estimation_statistics(
        estimation_stats: EstimationAccuracyStatistics,
    ) -> EstimationAccuracyStatisticsViewModel:
        """Convert EstimationAccuracyStatistics to EstimationAccuracyStatisticsViewModel.

        Args:
            estimation_stats: Estimation statistics DTO with Task entities

        Returns:
            EstimationAccuracyStatisticsViewModel with TaskSummaryViewModel
        """
        best_estimated_tasks_vm = [
            StatisticsMapper._map_task_to_summary(task)
            for task in estimation_stats.best_estimated_tasks
        ]

        worst_estimated_tasks_vm = [
            StatisticsMapper._map_task_to_summary(task)
            for task in estimation_stats.worst_estimated_tasks
        ]

        return EstimationAccuracyStatisticsViewModel(
            total_tasks_with_estimation=estimation_stats.total_tasks_with_estimation,
            accuracy_rate=estimation_stats.accuracy_rate,
            over_estimated_count=estimation_stats.over_estimated_count,
            under_estimated_count=estimation_stats.under_estimated_count,
            exact_count=estimation_stats.exact_count,
            best_estimated_tasks=best_estimated_tasks_vm,
            worst_estimated_tasks=worst_estimated_tasks_vm,
        )

    @staticmethod
    def _map_task_to_summary(task: TaskSummaryDto) -> TaskSummaryViewModel:
        """Convert a TaskSummaryDto to TaskSummaryViewModel.

        Args:
            task: TaskSummaryDto from application layer

        Returns:
            TaskSummaryViewModel with basic task information
        """
        # TaskSummaryDto only has id and name, so we set optional fields to None
        return TaskSummaryViewModel(
            id=task.id,
            name=task.name,
            estimated_duration=None,
            actual_duration_hours=None,
        )
