"""Remove daily_allocations JSON column from tasks table.

Revision ID: 006_remove_daily_allocations_json
Revises: 005_add_daily_allocations_table
Create Date: 2026-02-01

This migration removes the daily_allocations JSON column from the tasks table.
Daily allocations are now stored exclusively in the normalized daily_allocations
table, which provides:
- SQL-native aggregation (SUM, GROUP BY for workload calculations)
- Efficient date range queries
- Atomic updates per date
- Database-level constraints

Prerequisites:
- Migration 005 must have been run (creates the daily_allocations table)
- Dual-write should have been active, ensuring all data is in the normalized table
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_remove_daily_allocations_json"
down_revision: str | None = "005_add_daily_allocations_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove the daily_allocations JSON column from tasks table.

    SQLite requires batch mode for ALTER TABLE DROP COLUMN operations.
    """
    # Check if column exists before trying to drop it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("tasks")}

    if "daily_allocations" not in columns:
        # Column already removed (e.g., fresh database created with new schema)
        return

    # SQLite requires batch mode for column removal
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("daily_allocations")


def downgrade() -> None:
    """Re-add the daily_allocations JSON column.

    WARNING: This will create an empty column. To restore data, you would need to
    migrate from the daily_allocations table back to JSON format.
    """
    # SQLite requires batch mode for column addition
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "daily_allocations", sa.Text(), nullable=False, server_default="{}"
            )
        )
