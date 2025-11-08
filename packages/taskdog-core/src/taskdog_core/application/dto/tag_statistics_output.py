"""Output DTO for tag statistics queries.

This DTO provides a presentation-agnostic representation of tag usage statistics,
containing tag counts and metadata for display or API responses.
"""

from dataclasses import dataclass


@dataclass
class TagStatisticsOutput:
    """Output DTO for tag statistics.

    Contains tag usage statistics across all tasks.
    Used by tags command (list mode) and future API endpoints.

    Attributes:
        tag_counts: Dictionary mapping tag names to task counts
        total_tags: Total number of unique tags
        total_tagged_tasks: Total number of tasks with at least one tag
    """

    tag_counts: dict[str, int]
    total_tags: int
    total_tagged_tasks: int
