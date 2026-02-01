"""Add normalized daily_allocations table.

Revision ID: 005_add_daily_allocations_table
Revises: 004_add_notes_table
Create Date: 2026-02-01

This migration adds a normalized daily_allocations table to replace the
JSON TEXT column in the tasks table. Benefits include:
- SQL-native aggregation (SUM, GROUP BY for workload calculations)
- Efficient date range queries
- Atomic updates per date
- Database-level constraints

The JSON column in tasks table is preserved during the migration phase
(dual-write) and will be removed in a future migration.

Allocations are automatically deleted when their parent task is deleted via
ON DELETE CASCADE foreign key constraint.
"""

import json
from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_daily_allocations_table"
down_revision: str | None = "004_add_notes_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the daily_allocations table.

    Schema:
    - id: Primary key (auto-increment)
    - task_id: Foreign key to tasks.id with CASCADE delete
    - date: Date of the allocation
    - hours: Hours allocated (must be > 0)
    - created_at: Timestamp when allocation was created

    Constraints:
    - UNIQUE (task_id, date): One allocation per task per date
    - CHECK (hours > 0): Hours must be positive
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_exists = "daily_allocations" in inspector.get_table_names()

    # Create table if it doesn't exist
    if not table_exists:
        op.create_table(
            "daily_allocations",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "task_id",
                sa.Integer(),
                sa.ForeignKey("tasks.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("hours", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            # Constraints
            sa.UniqueConstraint(
                "task_id", "date", name="uq_daily_allocations_task_date"
            ),
            sa.CheckConstraint("hours > 0", name="ck_daily_allocations_hours_positive"),
        )

        # Create indexes for efficient queries
        op.create_index(
            "idx_daily_allocations_task_id", "daily_allocations", ["task_id"]
        )
        op.create_index("idx_daily_allocations_date", "daily_allocations", ["date"])

    # Migrate existing JSON data to normalized table
    # This handles databases that skipped the dual-write period
    # Always run this to ensure all JSON data is migrated (INSERT OR IGNORE handles duplicates)
    columns = {col["name"] for col in inspector.get_columns("tasks")}
    if "daily_allocations" in columns:
        result = conn.execute(
            sa.text(
                "SELECT id, daily_allocations FROM tasks "
                "WHERE daily_allocations IS NOT NULL AND daily_allocations != '{}'"
            )
        )
        for row in result:
            task_id = row[0]
            json_data = json.loads(row[1])
            for date_str, hours in json_data.items():
                if hours > 0:
                    conn.execute(
                        sa.text(
                            "INSERT OR IGNORE INTO daily_allocations "
                            "(task_id, date, hours, created_at) "
                            "VALUES (:task_id, :date, :hours, :created_at)"
                        ),
                        {
                            "task_id": task_id,
                            "date": date_str,
                            "hours": hours,
                            "created_at": datetime.now(),
                        },
                    )


def downgrade() -> None:
    """Drop the daily_allocations table.

    WARNING: This will permanently delete all normalized allocation data.
    The JSON column in tasks table should still contain the data if
    dual-write was properly maintained.
    """
    op.drop_index("idx_daily_allocations_date", table_name="daily_allocations")
    op.drop_index("idx_daily_allocations_task_id", table_name="daily_allocations")
    op.drop_table("daily_allocations")
