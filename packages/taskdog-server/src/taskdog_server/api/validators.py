"""Shared validators for Pydantic request models."""

from taskdog_core.shared.constants import MAX_TAG_LENGTH, MAX_TAGS_PER_TASK


def validate_tags(tags: list[str]) -> list[str]:
    """Validate tags are non-empty, unique, and within limits.

    Args:
        tags: List of tag strings

    Returns:
        Validated list of tags

    Raises:
        ValueError: If validation fails
    """
    if not tags:
        return tags
    if len(tags) > MAX_TAGS_PER_TASK:
        raise ValueError(f"Cannot have more than {MAX_TAGS_PER_TASK} tags per task")
    for tag in tags:
        if not tag.strip():
            raise ValueError("Tags must be non-empty")
        if len(tag) > MAX_TAG_LENGTH:
            raise ValueError(f"Tag cannot exceed {MAX_TAG_LENGTH} characters")
    if len(tags) != len(set(tags)):
        raise ValueError("Tags must be unique")
    return tags
