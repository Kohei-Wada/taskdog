"""Gantt query contracts through the shipped client and production server."""

from datetime import date, datetime, time, timedelta

import pytest
from taskdog_client.taskdog_api_client import TaskdogApiClient

from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


def test_gantt_filter_and_chart_ranges_are_independent(
    client: TaskdogApiClient,
) -> None:
    start = date.today() + timedelta(days=1)
    client.create_task(name="Before", deadline=datetime.combine(start, time()))
    selected = client.create_task(
        name="Selected",
        deadline=datetime.combine(start + timedelta(days=10), time()),
        tags=["gantt"],
    )
    client.create_task(
        name="After", deadline=datetime.combine(start + timedelta(days=20), time())
    )

    emitted_params: set[str] = set()
    client.client.event_hooks["request"].append(
        lambda request: emitted_params.update(request.url.params.keys())
    )
    result = client.get_gantt_data(
        include_archived=True,
        status="PENDING",
        tags=["gantt"],
        filter_start_date=start + timedelta(days=5),
        filter_end_date=start + timedelta(days=15),
        sort_by="priority",
        reverse=True,
        start_date=start,
        end_date=start + timedelta(days=30),
    )

    assert [task.id for task in result.tasks] == [selected.id]
    assert result.gantt_data is not None
    assert result.gantt_data.date_range.start_date == start
    assert result.gantt_data.date_range.end_date == start + timedelta(days=30)

    request_params = client.client.get("/openapi.json").json()["paths"][
        "/api/v1/gantt"
    ]["get"]["parameters"]
    declared = {param["name"] for param in request_params if param["in"] == "query"}
    assert emitted_params <= declared


def test_gantt_date_filters_select_tasks_over_http(client: TaskdogApiClient) -> None:
    start = date.today() + timedelta(days=1)
    client.create_task(name="Before", deadline=datetime.combine(start, time()))
    selected = client.create_task(
        name="Selected", deadline=datetime.combine(start + timedelta(days=10), time())
    )
    client.create_task(
        name="After", deadline=datetime.combine(start + timedelta(days=20), time())
    )

    result = client.get_gantt_data(
        filter_start_date=start + timedelta(days=5),
        filter_end_date=start + timedelta(days=15),
    )

    assert [task.id for task in result.tasks] == [selected.id]


def test_gantt_invalid_filter_date_uses_client_validation_error(
    client: TaskdogApiClient,
) -> None:
    with pytest.raises(TaskValidationError, match="Invalid date format"):
        client._base._request_json(
            "get", "/api/v1/gantt", params={"filter_start_date": "invalid-date"}
        )
