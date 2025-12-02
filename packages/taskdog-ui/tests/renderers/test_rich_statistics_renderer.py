"""Tests for rich statistics renderer."""

from unittest.mock import MagicMock

import pytest

from taskdog.renderers.rich_statistics_renderer import RichStatisticsRenderer
from taskdog.view_models.statistics_view_model import (
    EstimationAccuracyStatisticsViewModel,
    StatisticsViewModel,
    TaskSummaryViewModel,
    TimeStatisticsViewModel,
)
from taskdog_core.application.dto.statistics_output import (
    DeadlineComplianceStatistics,
    PriorityDistributionStatistics,
    TaskStatistics,
    TrendStatistics,
)


class TestRichStatisticsRenderer:
    """Test cases for RichStatisticsRenderer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.renderer = RichStatisticsRenderer(self.console_writer)

    def _create_basic_view_model(self) -> StatisticsViewModel:
        """Create a basic StatisticsViewModel for tests."""
        return StatisticsViewModel(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=3,
                in_progress_count=2,
                completed_count=4,
                canceled_count=1,
                completion_rate=0.4,
            ),
            priority_stats=PriorityDistributionStatistics(
                high_priority_count=2,
                medium_priority_count=5,
                low_priority_count=3,
                high_priority_completion_rate=0.5,
                priority_completion_map={50: 3, 80: 1},
            ),
            time_stats=None,
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=None,
        )

    def test_render_all_sections(self):
        """Test rendering all sections with focus='all'."""
        # Setup
        view_model = self._create_basic_view_model()

        # Execute
        self.renderer.render(view_model, focus="all")

        # Verify - should call print multiple times for title, tables, etc.
        assert self.console_writer.print.called
        assert self.console_writer.empty_line.called

    def test_render_basic_focus(self):
        """Test rendering with focus='basic'."""
        # Setup
        view_model = self._create_basic_view_model()

        # Execute
        self.renderer.render(view_model, focus="basic")

        # Verify
        assert self.console_writer.print.called

    def test_render_priority_focus(self):
        """Test rendering with focus='priority'."""
        # Setup
        view_model = self._create_basic_view_model()

        # Execute
        self.renderer.render(view_model, focus="priority")

        # Verify
        assert self.console_writer.print.called

    def test_render_with_time_stats(self):
        """Test rendering with time statistics."""
        # Setup
        view_model = StatisticsViewModel(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=3,
                in_progress_count=2,
                completed_count=4,
                canceled_count=1,
                completion_rate=0.4,
            ),
            priority_stats=PriorityDistributionStatistics(
                high_priority_count=2,
                medium_priority_count=5,
                low_priority_count=3,
                high_priority_completion_rate=0.5,
                priority_completion_map={50: 3, 80: 1},
            ),
            time_stats=TimeStatisticsViewModel(
                total_work_hours=100.0,
                average_work_hours=10.0,
                median_work_hours=8.0,
                longest_task=TaskSummaryViewModel(
                    id=1,
                    name="Long Task",
                    estimated_duration=None,
                    actual_duration_hours=20.0,
                ),
                shortest_task=TaskSummaryViewModel(
                    id=2,
                    name="Short Task",
                    estimated_duration=None,
                    actual_duration_hours=1.0,
                ),
                tasks_with_time_tracking=10,
            ),
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=None,
        )

        # Execute
        self.renderer.render(view_model, focus="time")

        # Verify
        assert self.console_writer.print.called

    def test_render_with_time_stats_no_tasks(self):
        """Test rendering with time stats but no longest/shortest tasks."""
        # Setup
        view_model = StatisticsViewModel(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=3,
                in_progress_count=2,
                completed_count=4,
                canceled_count=1,
                completion_rate=0.4,
            ),
            priority_stats=PriorityDistributionStatistics(
                high_priority_count=2,
                medium_priority_count=5,
                low_priority_count=3,
                high_priority_completion_rate=0.5,
                priority_completion_map={50: 3, 80: 1},
            ),
            time_stats=TimeStatisticsViewModel(
                total_work_hours=50.0,
                average_work_hours=5.0,
                median_work_hours=4.0,
                longest_task=None,
                shortest_task=None,
                tasks_with_time_tracking=5,
            ),
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=None,
        )

        # Execute
        self.renderer.render(view_model, focus="time")

        # Verify
        assert self.console_writer.print.called

    def test_render_with_estimation_stats(self):
        """Test rendering with estimation statistics."""
        # Setup
        view_model = StatisticsViewModel(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=3,
                in_progress_count=2,
                completed_count=4,
                canceled_count=1,
                completion_rate=0.4,
            ),
            priority_stats=PriorityDistributionStatistics(
                high_priority_count=2,
                medium_priority_count=5,
                low_priority_count=3,
                high_priority_completion_rate=0.5,
                priority_completion_map={50: 3, 80: 1},
            ),
            time_stats=None,
            estimation_stats=EstimationAccuracyStatisticsViewModel(
                total_tasks_with_estimation=8,
                accuracy_rate=0.95,
                over_estimated_count=2,
                under_estimated_count=1,
                exact_count=5,
                best_estimated_tasks=[
                    TaskSummaryViewModel(
                        id=3,
                        name="Best Task",
                        estimated_duration=5.0,
                        actual_duration_hours=5.0,
                    )
                ],
                worst_estimated_tasks=[
                    TaskSummaryViewModel(
                        id=4,
                        name="Worst Task",
                        estimated_duration=2.0,
                        actual_duration_hours=10.0,
                    )
                ],
            ),
            deadline_stats=None,
            trend_stats=None,
        )

        # Execute
        self.renderer.render(view_model, focus="estimation")

        # Verify
        assert self.console_writer.print.called

    def test_render_with_deadline_stats(self):
        """Test rendering with deadline statistics."""
        # Setup
        view_model = StatisticsViewModel(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=3,
                in_progress_count=2,
                completed_count=4,
                canceled_count=1,
                completion_rate=0.4,
            ),
            priority_stats=PriorityDistributionStatistics(
                high_priority_count=2,
                medium_priority_count=5,
                low_priority_count=3,
                high_priority_completion_rate=0.5,
                priority_completion_map={50: 3, 80: 1},
            ),
            time_stats=None,
            estimation_stats=None,
            deadline_stats=DeadlineComplianceStatistics(
                total_tasks_with_deadline=5,
                met_deadline_count=4,
                missed_deadline_count=1,
                compliance_rate=0.8,
                average_delay_days=2.0,
            ),
            trend_stats=None,
        )

        # Execute
        self.renderer.render(view_model, focus="deadline")

        # Verify
        assert self.console_writer.print.called

    def test_render_with_trend_stats(self):
        """Test rendering with trend statistics."""
        # Setup
        view_model = StatisticsViewModel(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=3,
                in_progress_count=2,
                completed_count=4,
                canceled_count=1,
                completion_rate=0.4,
            ),
            priority_stats=PriorityDistributionStatistics(
                high_priority_count=2,
                medium_priority_count=5,
                low_priority_count=3,
                high_priority_completion_rate=0.5,
                priority_completion_map={50: 3, 80: 1},
            ),
            time_stats=None,
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=TrendStatistics(
                last_7_days_completed=3,
                last_30_days_completed=12,
                weekly_completion_trend={},
                monthly_completion_trend={"2025-01": 5, "2025-02": 7},
            ),
        )

        # Execute
        self.renderer.render(view_model, focus="trends")

        # Verify
        assert self.console_writer.print.called


class TestRateColors:
    """Test cases for rate color methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.renderer = RichStatisticsRenderer(self.console_writer)

    @pytest.mark.parametrize(
        "rate,expected_color",
        [
            (0.8, "green"),
            (1.0, "green"),
            (0.5, "yellow"),
            (0.79, "yellow"),
            (0.49, "red"),
            (0.0, "red"),
        ],
        ids=[
            "high_0.8",
            "high_1.0",
            "medium_0.5",
            "medium_0.79",
            "low_0.49",
            "low_0.0",
        ],
    )
    def test_get_rate_color(self, rate, expected_color):
        """Test color for different rate values."""
        assert self.renderer._get_rate_color(rate) == expected_color

    @pytest.mark.parametrize(
        "accuracy,expected_color",
        [
            (0.9, "green"),
            (1.0, "green"),
            (1.1, "green"),
            (0.7, "yellow"),
            (1.3, "yellow"),
            (0.5, "red"),
            (1.5, "red"),
        ],
        ids=[
            "good_0.9",
            "good_1.0",
            "good_1.1",
            "moderate_0.7",
            "moderate_1.3",
            "poor_0.5",
            "poor_1.5",
        ],
    )
    def test_get_estimation_accuracy_color(self, accuracy, expected_color):
        """Test color for different estimation accuracy values."""
        assert self.renderer._get_estimation_accuracy_color(accuracy) == expected_color
