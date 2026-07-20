"""Add optimistic-lock version column to tasks.

Revision ID: 007_add_task_version
Revises: 006_remove_daily_allocations_json
Create Date: 2026-07-20

Adds an integer ``version`` column (default 1) used for optimistic locking so
concurrent read-modify-write updates raise a conflict instead of silently
overwriting each other (see #961). Existing rows are backfilled to version 1
via the server default.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_add_task_version"
down_revision: str | None = "006_remove_daily_allocations_json"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the ``version`` column if it is not already present.

    Uses batch mode for SQLite compatibility and a server default of 1 so
    pre-existing rows are backfilled.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("tasks")}
    if "version" not in columns:
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "version",
                    sa.Integer(),
                    nullable=False,
                    server_default="1",
                )
            )


def downgrade() -> None:
    """Drop the ``version`` column."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("tasks")}
    if "version" in columns:
        with op.batch_alter_table("tasks") as batch_op:
            batch_op.drop_column("version")
