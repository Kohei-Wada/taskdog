"""Initial schema - captures existing database structure.

Revision ID: 001_initial
Revises:
Create Date: 2025-12-26

This migration captures the current database schema for tasks, tags, task_tags,
and audit_logs tables. For existing databases, this migration will be stamped
(not executed) to bring them under version control.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial schema if tables don't exist.

    Uses conditional creation to handle both fresh databases and existing
    databases being brought under version control.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create tasks table
    if "tasks" not in existing_tables:
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(500), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(50), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("planned_start", sa.DateTime(), nullable=True),
            sa.Column("planned_end", sa.DateTime(), nullable=True),
            sa.Column("deadline", sa.DateTime(), nullable=True),
            sa.Column("actual_start", sa.DateTime(), nullable=True),
            sa.Column("actual_end", sa.DateTime(), nullable=True),
            sa.Column("actual_duration", sa.Float(), nullable=True),
            sa.Column("estimated_duration", sa.Float(), nullable=True),
            sa.Column("is_fixed", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column(
                "daily_allocations", sa.Text(), nullable=False, server_default="{}"
            ),
            sa.Column(
                "actual_daily_hours", sa.Text(), nullable=False, server_default="{}"
            ),
            sa.Column("depends_on", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_status", "tasks", ["status"])
        op.create_index("idx_is_archived", "tasks", ["is_archived"])
        op.create_index("idx_deadline", "tasks", ["deadline"])
        op.create_index("idx_planned_start", "tasks", ["planned_start"])
        op.create_index("idx_priority", "tasks", ["priority"])

    # Create tags table
    if "tags" not in existing_tables:
        op.create_table(
            "tags",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        op.create_index("idx_tag_name", "tags", ["name"])

    # Create task_tags junction table
    if "task_tags" not in existing_tables:
        op.create_table(
            "task_tags",
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("tag_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("task_id", "tag_id"),
        )
        op.create_index("idx_task_tags_task_id", "task_tags", ["task_id"])
        op.create_index("idx_task_tags_tag_id", "task_tags", ["tag_id"])

    # Create audit_logs table
    if "audit_logs" not in existing_tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("client_name", sa.String(100), nullable=True),
            sa.Column("operation", sa.String(50), nullable=False),
            sa.Column("resource_type", sa.String(50), nullable=False),
            sa.Column("resource_id", sa.Integer(), nullable=True),
            sa.Column("resource_name", sa.String(500), nullable=True),
            sa.Column("old_values", sa.Text(), nullable=True),
            sa.Column("new_values", sa.Text(), nullable=True),
            sa.Column("success", sa.Boolean(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        # Single-column indexes
        op.create_index("idx_audit_timestamp", "audit_logs", ["timestamp"])
        op.create_index("idx_audit_client_name", "audit_logs", ["client_name"])
        op.create_index("idx_audit_operation", "audit_logs", ["operation"])
        op.create_index("idx_audit_resource_id", "audit_logs", ["resource_id"])
        op.create_index("idx_audit_success", "audit_logs", ["success"])
        # Composite indexes
        op.create_index(
            "idx_audit_client_timestamp", "audit_logs", ["client_name", "timestamp"]
        )
        op.create_index(
            "idx_audit_operation_timestamp", "audit_logs", ["operation", "timestamp"]
        )
        op.create_index(
            "idx_audit_resource", "audit_logs", ["resource_type", "resource_id"]
        )


def downgrade() -> None:
    """Drop all tables (destructive - use with caution)."""
    op.drop_table("task_tags")
    op.drop_table("tags")
    op.drop_table("audit_logs")
    op.drop_table("tasks")
