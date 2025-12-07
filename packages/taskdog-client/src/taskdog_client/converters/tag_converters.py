"""Tag statistics converters."""

from typing import Any

from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput


def convert_to_tag_statistics_output(data: dict[str, Any]) -> TagStatisticsOutput:
    """Convert API response to TagStatisticsOutput.

    Args:
        data: API response data with format:
            {tags: [{tag: str, count: int, completion_rate: float}], total_tags: int}

    Returns:
        TagStatisticsOutput with tag statistics
    """
    # Convert to DTO: {tag_counts: dict[str, int], total_tags: int, total_tagged_tasks: int}
    tag_counts = {item["tag"]: item["count"] for item in data["tags"]}

    return TagStatisticsOutput(
        tag_counts=tag_counts,
        total_tags=data["total_tags"],
        total_tagged_tasks=0,  # Not available from API response
    )
