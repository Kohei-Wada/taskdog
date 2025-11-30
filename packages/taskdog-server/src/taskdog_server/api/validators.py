"""Shared validators for Pydantic request models."""


def validate_tags(tags: list[str]) -> list[str]:
    """Validate tags are non-empty and unique.

    Args:
        tags: List of tag strings

    Returns:
        Validated list of tags

    Raises:
        ValueError: If any tag is empty or tags are not unique
    """
    if any(not tag.strip() for tag in tags):
        raise ValueError("Tags must be non-empty")
    if len(tags) != len(set(tags)):
        raise ValueError("Tags must be unique")
    return tags
