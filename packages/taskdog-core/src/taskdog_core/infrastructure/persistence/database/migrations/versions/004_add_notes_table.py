"""Add notes table for database-based note storage.

Revision ID: 004_add_notes_table
Revises: 003_make_priority_nullable
Create Date: 2026-01-29

This migration adds a notes table to store task notes in the database
instead of the filesystem. This eliminates N filesystem stat() calls
per task list request, improving performance.

Notes are automatically deleted when their parent task is deleted via
ON DELETE CASCADE foreign key constraint.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_notes_table"
down_revision: str | None = "003_make_priority_nullable"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the notes table.

    Schema:
    - task_id: Primary key, foreign key to tasks.id with CASCADE delete
    - content: Note content (TEXT, not null)
    - created_at: Timestamp when note was created
    - updated_at: Timestamp when note was last updated
    """
    # Check if table already exists (for databases created with create_all)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "notes" in inspector.get_table_names():
        return

    op.create_table(
        "notes",
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # Create index on task_id for efficient lookups
    op.create_index("idx_notes_task_id", "notes", ["task_id"])


def downgrade() -> None:
    """Drop the notes table.

    WARNING: This will permanently delete all notes stored in the database.
    Make sure to export notes to files before downgrading if you want to
    preserve them.
    """
    op.drop_index("idx_notes_task_id", table_name="notes")
    op.drop_table("notes")
