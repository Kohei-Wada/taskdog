"""Tests for GanttPresenter."""

from datetime import date, datetime

from taskdog.presenters.gantt_presenter import GanttPresenter
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.task_dto import GanttTaskDto
from taskdog_core.domain.entities.task import TaskStatus


class TestGanttPresenter:
    """Test cases for GanttPresenter."""

    def setup_method(self):
        self.presenter = GanttPresenter()

    def _make_task(
        self,
        task_id: int = 1,
        name: str = "Test task",
        status: TaskStatus = TaskStatus.PENDING,
        is_finished: bool = False,
        estimated_duration: float | None = 8.0,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        actual_start: datetime | None = None,
        actual_end: datetime | None = None,
        deadline: datetime | None = None,
    ) -> GanttTaskDto:
        return GanttTaskDto(
            id=task_id,
            name=name,
            status=status,
            is_finished=is_finished,
            estimated_duration=estimated_duration,
            planned_start=planned_start,
            planned_end=planned_end,
            actual_start=actual_start,
            actual_end=actual_end,
            deadline=deadline,
        )

    def _make_gantt_output(
        self, tasks: list[GanttTaskDto] | None = None
    ) -> GanttOutput:
        return GanttOutput(
            tasks=tasks or [],
            date_range=GanttDateRange(
                start_date=date(2026, 1, 1), end_date=date(2026, 1, 7)
            ),
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
            total_estimated_duration=0.0,
        )

    def test_present_empty(self):
        result = self.presenter.present(self._make_gantt_output())

        assert isinstance(result, GanttViewModel)
        assert result.tasks == []
        assert result.start_date == date(2026, 1, 1)
        assert result.end_date == date(2026, 1, 7)

    def test_present_task_name_not_finished(self):
        task = self._make_task(name="My task", is_finished=False)
        result = self.presenter.present(self._make_gantt_output([task]))

        assert result.tasks[0].name == "My task"

    def test_present_task_name_finished_is_plain_text(self):
        task = self._make_task(
            name="Done task",
            status=TaskStatus.COMPLETED,
            is_finished=True,
        )
        result = self.presenter.present(self._make_gantt_output([task]))

        assert result.tasks[0].name == "Done task"
        assert result.tasks[0].is_finished is True

    def test_present_task_name_with_square_brackets(self):
        task = self._make_task(name="[tracker] My task", is_finished=False)
        result = self.presenter.present(self._make_gantt_output([task]))

        assert result.tasks[0].name == "[tracker] My task"

    def test_present_estimated_duration_formatted(self):
        task = self._make_task(estimated_duration=4.5)
        result = self.presenter.present(self._make_gantt_output([task]))

        assert result.tasks[0].formatted_estimated_duration == "4.5"

    def test_present_estimated_duration_none(self):
        task = self._make_task(estimated_duration=None)
        result = self.presenter.present(self._make_gantt_output([task]))

        assert result.tasks[0].formatted_estimated_duration == "-"

    def test_present_dates_converted_to_date(self):
        task = self._make_task(
            planned_start=datetime(2026, 1, 2, 9, 0),
            planned_end=datetime(2026, 1, 5, 18, 0),
            actual_start=datetime(2026, 1, 3, 10, 0),
            actual_end=datetime(2026, 1, 4, 17, 0),
            deadline=datetime(2026, 1, 6, 23, 59),
        )
        result = self.presenter.present(self._make_gantt_output([task]))

        row = result.tasks[0]
        assert row.planned_start == date(2026, 1, 2)
        assert row.planned_end == date(2026, 1, 5)
        assert row.actual_start == date(2026, 1, 3)
        assert row.actual_end == date(2026, 1, 4)
        assert row.deadline == date(2026, 1, 6)

    def test_present_dates_none(self):
        task = self._make_task()
        result = self.presenter.present(self._make_gantt_output([task]))

        row = result.tasks[0]
        assert row.planned_start is None
        assert row.planned_end is None
        assert row.actual_start is None
        assert row.actual_end is None
        assert row.deadline is None

    def test_present_preserves_metadata(self):
        output = GanttOutput(
            tasks=[self._make_task()],
            date_range=GanttDateRange(
                start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
            ),
            task_daily_hours={1: {date(2026, 3, 1): 4.0}},
            daily_workload={date(2026, 3, 1): 4.0},
            holidays={date(2026, 3, 20)},
            total_estimated_duration=8.0,
        )
        result = self.presenter.present(output)

        assert result.task_daily_hours == {1: {date(2026, 3, 1): 4.0}}
        assert result.daily_workload == {date(2026, 3, 1): 4.0}
        assert result.holidays == {date(2026, 3, 20)}
        assert result.total_estimated_duration == 8.0

    def test_present_multiple_tasks(self):
        tasks = [
            self._make_task(task_id=1, name="Task A"),
            self._make_task(
                task_id=2, name="Task B", is_finished=True, status=TaskStatus.COMPLETED
            ),
        ]
        result = self.presenter.present(self._make_gantt_output(tasks))

        assert len(result.tasks) == 2
        assert result.tasks[0].id == 1
        assert result.tasks[1].id == 2
