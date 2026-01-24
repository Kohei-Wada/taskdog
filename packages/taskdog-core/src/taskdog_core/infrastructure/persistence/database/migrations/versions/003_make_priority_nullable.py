"""Make priority column nullable.

Revision ID: 003_make_priority_nullable
Revises: 002_remove_actual_daily_hours
Create Date: 2026-01-24

This migration makes the priority column nullable to support tasks
without an explicit priority value. Existing tasks retain their
current priority values.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_make_priority_nullable"
down_revision: str | None = "002_remove_actual_daily_hours"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make the priority column nullable.

    Uses batch mode for SQLite compatibility since SQLite doesn't support
    ALTER COLUMN directly.
    """
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "priority",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    """Restore priority column to NOT NULL.

    Note: This will fail if there are any NULL priority values in the database.
    To safely downgrade, first update all NULL priorities to a default value:
        UPDATE tasks SET priority = 5 WHERE priority IS NULL;
    """
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "priority",
            existing_type=sa.Integer(),
            nullable=False,
        )
