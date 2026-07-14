"""Tests for RescheduleAnalyzer."""

from datetime import datetime

from taskdog_core.application.services.reschedule_analyzer import RescheduleAnalyzer
from taskdog_core.domain.entities.audit_log import AuditLog


def _event(
    task_id: int,
    old_deadline: str | None,
    new_deadline: str | None,
    timestamp: datetime,
    name: str = "task",
) -> AuditLog:
    return AuditLog(
        timestamp=timestamp,
        operation="update_task",
        resource_type="task",
        success=True,
        resource_id=task_id,
        resource_name=name,
        old_values={"deadline": old_deadline},
        new_values={"deadline": new_deadline},
    )


class TestRescheduleAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = RescheduleAnalyzer()

    def test_empty_events(self) -> None:
        stats = self.analyzer.calculate([])

        assert stats.tasks_with_deadline == 0
        assert stats.rescheduled_task_count == 0
        assert stats.total_reschedule_events == 0
        assert stats.reschedule_rate == 0.0
        assert stats.moved_earlier_count == 0
        assert stats.chronic_slippers == []
        assert stats.weekly_reschedule_trend == {}

    def test_initial_setting_is_not_a_reschedule(self) -> None:
        events = [
            _event(1, None, "2026-07-20T18:00:00", datetime(2026, 7, 14, 10, 0)),
        ]

        stats = self.analyzer.calculate(events)

        assert stats.tasks_with_deadline == 1
        assert stats.total_reschedule_events == 0
        assert stats.rescheduled_task_count == 0
        assert stats.reschedule_rate == 0.0

    def test_deadline_removal_is_not_a_reschedule(self) -> None:
        events = [
            _event(1, "2026-07-20T18:00:00", None, datetime(2026, 7, 14, 10, 0)),
        ]

        stats = self.analyzer.calculate(events)

        assert stats.tasks_with_deadline == 1
        assert stats.total_reschedule_events == 0

    def test_value_to_value_change_counts_as_reschedule(self) -> None:
        events = [
            _event(1, None, "2026-07-20T18:00:00", datetime(2026, 7, 14, 10, 0)),
            _event(
                1,
                "2026-07-20T18:00:00",
                "2026-07-25T18:00:00",
                datetime(2026, 7, 15, 10, 0),
            ),
        ]

        stats = self.analyzer.calculate(events)

        assert stats.tasks_with_deadline == 1
        assert stats.total_reschedule_events == 1
        assert stats.rescheduled_task_count == 1
        assert stats.reschedule_rate == 1.0
        assert stats.moved_earlier_count == 0

    def test_moved_earlier_counted(self) -> None:
        events = [
            _event(
                1,
                "2026-07-25T18:00:00",
                "2026-07-20T18:00:00",
                datetime(2026, 7, 15, 10, 0),
            ),
        ]

        stats = self.analyzer.calculate(events)

        assert stats.total_reschedule_events == 1
        assert stats.moved_earlier_count == 1

    def test_reschedule_rate_over_multiple_tasks(self) -> None:
        events = [
            _event(1, None, "2026-07-20T18:00:00", datetime(2026, 7, 10, 10, 0)),
            _event(2, None, "2026-07-21T18:00:00", datetime(2026, 7, 10, 11, 0)),
            _event(
                2,
                "2026-07-21T18:00:00",
                "2026-07-22T18:00:00",
                datetime(2026, 7, 11, 10, 0),
            ),
        ]

        stats = self.analyzer.calculate(events)

        assert stats.tasks_with_deadline == 2
        assert stats.rescheduled_task_count == 1
        assert stats.reschedule_rate == 0.5

    def test_chronic_slipper_needs_three_reschedules(self) -> None:
        deadlines = [
            "2026-07-20T18:00:00",
            "2026-07-22T18:00:00",
            "2026-07-24T18:00:00",
            "2026-07-26T18:00:00",
        ]
        events = [
            _event(
                1,
                deadlines[i],
                deadlines[i + 1],
                datetime(2026, 7, 10 + i, 10, 0),
                name="slipper",
            )
            for i in range(3)
        ]
        # A task with only two reschedules is not chronic
        events += [
            _event(
                2,
                "2026-07-20T18:00:00",
                "2026-07-21T18:00:00",
                datetime(2026, 7, 10, 10, 0),
            ),
            _event(
                2,
                "2026-07-21T18:00:00",
                "2026-07-22T18:00:00",
                datetime(2026, 7, 11, 10, 0),
            ),
        ]

        stats = self.analyzer.calculate(events)

        assert len(stats.chronic_slippers) == 1
        slipper = stats.chronic_slippers[0]
        assert slipper.task_id == 1
        assert slipper.task_name == "slipper"
        assert slipper.reschedule_count == 3
        assert slipper.total_slip_days == 6.0
        assert slipper.first_deadline == "2026-07-20T18:00:00"
        assert slipper.latest_deadline == "2026-07-26T18:00:00"

    def test_chronic_slippers_sorted_by_reschedule_count(self) -> None:
        def slip(task_id: int, count: int) -> list[AuditLog]:
            return [
                _event(
                    task_id,
                    f"2026-07-{10 + i:02d}T18:00:00",
                    f"2026-07-{11 + i:02d}T18:00:00",
                    datetime(2026, 7, 1 + i, 10, 0),
                )
                for i in range(count)
            ]

        stats = self.analyzer.calculate(slip(1, 3) + slip(2, 5))

        assert [s.task_id for s in stats.chronic_slippers] == [2, 1]

    def test_weekly_reschedule_trend_uses_iso_weeks(self) -> None:
        events = [
            _event(
                1,
                "2026-07-20T18:00:00",
                "2026-07-21T18:00:00",
                datetime(2026, 7, 14, 10, 0),  # 2026-W29
            ),
            _event(
                1,
                "2026-07-21T18:00:00",
                "2026-07-22T18:00:00",
                datetime(2026, 7, 15, 10, 0),  # 2026-W29
            ),
            _event(
                2,
                "2026-07-28T18:00:00",
                "2026-07-29T18:00:00",
                datetime(2026, 7, 21, 10, 0),  # 2026-W30
            ),
        ]

        stats = self.analyzer.calculate(events)

        assert stats.weekly_reschedule_trend == {"2026-W29": 2, "2026-W30": 1}

    def test_lead_time_breakdown_buckets(self) -> None:
        events = [
            # same_day: deadline on the day it was set
            _event(1, None, "2026-07-14T18:00:00", datetime(2026, 7, 14, 9, 0)),
            # 1_2_days ahead, later rescheduled
            _event(2, None, "2026-07-16T18:00:00", datetime(2026, 7, 14, 9, 0)),
            _event(
                2,
                "2026-07-16T18:00:00",
                "2026-07-18T18:00:00",
                datetime(2026, 7, 15, 9, 0),
            ),
            # 3_7_days ahead
            _event(3, None, "2026-07-19T18:00:00", datetime(2026, 7, 14, 9, 0)),
            # 8_plus_days ahead
            _event(4, None, "2026-07-31T18:00:00", datetime(2026, 7, 14, 9, 0)),
        ]

        stats = self.analyzer.calculate(events)

        by_category = {b.category: b for b in stats.lead_time_breakdown}
        assert by_category["same_day"].task_count == 1
        assert by_category["same_day"].rescheduled_count == 0
        assert by_category["1_2_days"].task_count == 1
        assert by_category["1_2_days"].rescheduled_count == 1
        assert by_category["1_2_days"].reschedule_rate == 1.0
        assert by_category["3_7_days"].task_count == 1
        assert by_category["8_plus_days"].task_count == 1

    def test_lead_time_skips_tasks_without_initial_setting(self) -> None:
        # Only a reschedule event exists; the initial setting is unknown
        events = [
            _event(
                1,
                "2026-07-20T18:00:00",
                "2026-07-21T18:00:00",
                datetime(2026, 7, 14, 10, 0),
            ),
        ]

        stats = self.analyzer.calculate(events)

        assert all(b.task_count == 0 for b in stats.lead_time_breakdown)

    def test_events_without_resource_id_are_ignored(self) -> None:
        event = AuditLog(
            timestamp=datetime(2026, 7, 14, 10, 0),
            operation="update_task",
            resource_type="task",
            success=True,
            resource_id=None,
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": "2026-07-21T18:00:00"},
        )

        stats = self.analyzer.calculate([event])

        assert stats.tasks_with_deadline == 0
        assert stats.total_reschedule_events == 0
