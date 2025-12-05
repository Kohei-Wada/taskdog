"""SQLAlchemy ORM model for Audit Log entity.

This module defines the database schema for audit logs using SQLAlchemy 2.0 ORM.
Audit logs track all operations performed through the API for accountability
and review purposes.
"""

from datetime import datetime

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import (  # type: ignore[attr-defined]
    Mapped,
    mapped_column,
)

from .task_model import Base


class AuditLogModel(Base):
    """SQLAlchemy ORM model for Audit Log entity.

    Maps to the 'audit_logs' table in the database. Records all API operations
    for audit trail purposes, including who performed the action, what was changed,
    and whether it succeeded.

    This is particularly useful for tracking actions performed by AI agents
    or automated systems when the user is not actively monitoring.
    """

    __tablename__ = "audit_logs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # When the operation occurred
    timestamp: Mapped[datetime] = mapped_column(nullable=False)

    # Who performed the operation (from API key authentication)
    # None if authentication is disabled
    client_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # What operation was performed (e.g., "create_task", "complete_task")
    operation: Mapped[str] = mapped_column(String(50), nullable=False)

    # Resource type (e.g., "task", "schedule")
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Resource ID (task ID, etc.) - nullable for batch operations
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Resource name for easier identification in logs
    resource_name: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Values before the change (JSON format)
    # Example: {"status": "PENDING", "priority": 3}
    old_values: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Values after the change (JSON format)
    # Example: {"status": "COMPLETED"}
    new_values: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Whether the operation succeeded
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Error message if the operation failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Database indexes for common query patterns
    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_client_name", "client_name"),
        Index("idx_audit_operation", "operation"),
        Index("idx_audit_resource_id", "resource_id"),
        Index("idx_audit_success", "success"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<AuditLogModel(id={self.id}, operation='{self.operation}', "
            f"client='{self.client_name}', resource_id={self.resource_id})>"
        )
