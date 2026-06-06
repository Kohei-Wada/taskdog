"""Output DTO for restore operations."""

from pydantic import BaseModel


class RestoreResultDTO(BaseModel):
    """Result of staging a restore.

    Restore is applied on the next server startup, so the response only reports
    that the upload was accepted and a restart is required.

    Attributes:
        status: Restore lifecycle status (e.g. "pending").
        message: Human-readable instruction (e.g. "restart required").
    """

    status: str
    message: str
