"""Analyzer for deadline reschedule statistics from audit log events."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from taskdog_core.application.dto.statistics_output import (
    ChronicSlipperTask,
    LeadTimeBreakdown,
    RescheduleStatistics,
)
from taskdog_core.domain.entities.audit_log import AuditLog

CHRONIC_SLIPPER_THRESHOLD = 3

_LEAD_TIME_CATEGORIES = ("same_day", "1_2_days", "3_7_days", "8_plus_days")


@dataclass
class _TaskHistory:
    """Accumulated deadline history for one task."""

    name: str = ""
    reschedule_count: int = 0
    slip_days: float = 0.0
    deadlines: list[datetime] = field(default_factory=list)
    initial_set_at: datetime | None = None
    initial_deadline: datetime | None = None


def _parse_deadline(value: object) -> datetime | None:
    """Parse an audit-log deadline value (ISO string) into a datetime."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _lead_time_category(lead_days: int) -> str:
    if lead_days <= 0:
        return "same_day"
    if lead_days <= 2:
        return "1_2_days"
    if lead_days <= 7:
        return "3_7_days"
    return "8_plus_days"


class RescheduleAnalyzer:
    """Calculates deadline reschedule statistics from audit log events.

    Expects events where the deadline changed (any combination of set,
    change, or removal). A *reschedule* is a value-to-value change; the
    initial setting (null to value) and removal (value to null) are
    tracked but not counted as reschedules.
    """

    def calculate(self, events: list[AuditLog]) -> RescheduleStatistics:
        """Calculate reschedule statistics from deadline-change events.

        Args:
            events: Audit log entries whose deadline value changed

        Returns:
            RescheduleStatistics derived from the events
        """
        histories: dict[int, _TaskHistory] = {}
        total_reschedules = 0
        moved_earlier = 0
        weekly_trend: Counter[str] = Counter()

        for event in sorted(events, key=lambda e: e.timestamp):
            if event.resource_id is None:
                continue
            old = _parse_deadline((event.old_values or {}).get("deadline"))
            new = _parse_deadline((event.new_values or {}).get("deadline"))
            if old is None and new is None:
                continue

            history = histories.setdefault(event.resource_id, _TaskHistory())
            if event.resource_name:
                history.name = event.resource_name
            history.deadlines.extend(d for d in (old, new) if d is not None)

            if old is None and new is not None:
                if history.initial_set_at is None:
                    history.initial_set_at = event.timestamp
                    history.initial_deadline = new
            elif old is not None and new is not None and old != new:
                history.reschedule_count += 1
                history.slip_days += (new - old).total_seconds() / 86400
                total_reschedules += 1
                if new < old:
                    moved_earlier += 1
                iso = event.timestamp.isocalendar()
                weekly_trend[f"{iso.year}-W{iso.week:02d}"] += 1

        tasks_with_deadline = len(histories)
        rescheduled_tasks = [h for h in histories.values() if h.reschedule_count > 0]

        return RescheduleStatistics(
            tasks_with_deadline=tasks_with_deadline,
            rescheduled_task_count=len(rescheduled_tasks),
            total_reschedule_events=total_reschedules,
            reschedule_rate=(
                len(rescheduled_tasks) / tasks_with_deadline
                if tasks_with_deadline
                else 0.0
            ),
            moved_earlier_count=moved_earlier,
            lead_time_breakdown=self._build_lead_time_breakdown(histories),
            chronic_slippers=self._build_chronic_slippers(histories),
            weekly_reschedule_trend=dict(weekly_trend),
        )

    def _build_lead_time_breakdown(
        self, histories: dict[int, _TaskHistory]
    ) -> list[LeadTimeBreakdown]:
        """Group tasks by planning lead time and compute reschedule rates.

        Only tasks whose initial deadline-setting event was observed are
        included; for the rest the lead time is unknown.
        """
        totals: Counter[str] = Counter()
        rescheduled: Counter[str] = Counter()

        for history in histories.values():
            if history.initial_set_at is None or history.initial_deadline is None:
                continue
            lead_days = (
                history.initial_deadline.date() - history.initial_set_at.date()
            ).days
            category = _lead_time_category(lead_days)
            totals[category] += 1
            if history.reschedule_count > 0:
                rescheduled[category] += 1

        return [
            LeadTimeBreakdown(
                category=category,
                task_count=totals[category],
                rescheduled_count=rescheduled[category],
                reschedule_rate=(
                    rescheduled[category] / totals[category]
                    if totals[category]
                    else 0.0
                ),
            )
            for category in _LEAD_TIME_CATEGORIES
        ]

    def _build_chronic_slippers(
        self, histories: dict[int, _TaskHistory]
    ) -> list[ChronicSlipperTask]:
        """Collect tasks rescheduled at least CHRONIC_SLIPPER_THRESHOLD times."""
        slippers = [
            ChronicSlipperTask(
                task_id=task_id,
                task_name=history.name,
                reschedule_count=history.reschedule_count,
                total_slip_days=round(history.slip_days, 1),
                first_deadline=history.deadlines[0].isoformat(),
                latest_deadline=history.deadlines[-1].isoformat(),
            )
            for task_id, history in histories.items()
            if history.reschedule_count >= CHRONIC_SLIPPER_THRESHOLD
        ]
        return sorted(slippers, key=lambda s: s.reschedule_count, reverse=True)
