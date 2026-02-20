"""DTO for deleting a tag."""

from dataclasses import dataclass


@dataclass
class DeleteTagInput:
    """Request data for deleting a tag.

    Attributes:
        tag_name: Name of the tag to delete
    """

    tag_name: str
