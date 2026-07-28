"""add announcement archive timestamp

Revision ID: c31f7a2d9e44
Revises: b7d9a16c44ef
Create Date: 2026-07-28
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c31f7a2d9e44"
down_revision: str | Sequence[str] | None = "b7d9a16c44ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("announcements") as batch_op:
        batch_op.add_column(
            sa.Column(
                "archived_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("announcements") as batch_op:
        batch_op.drop_column("archived_at")
