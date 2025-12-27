"""Remove deprecated actual_daily_hours column.

Revision ID: 002_remove_actual_daily_hours
Revises: 001_initial
Create Date: 2025-12-27

This migration removes the actual_daily_hours column which was deprecated
and is no longer used by the application. The column was originally used
for tracking daily work hours but this functionality has been removed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_remove_actual_daily_hours"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove the deprecated actual_daily_hours column from tasks table.

    Uses batch mode for SQLite compatibility since SQLite doesn't support
    DROP COLUMN directly. Checks if column exists first to handle databases
    created with newer model that never had this column.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("tasks")}

    if "actual_daily_hours" in columns:
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.drop_column("actual_daily_hours")


def downgrade() -> None:
    """Restore actual_daily_hours column for rollback."""
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "actual_daily_hours", sa.Text(), nullable=False, server_default="{}"
            )
        )
