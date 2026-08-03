"""add library suspension metadata

Revision ID: e82f4c7a19d1
Revises: c31f7a2d9e44
Create Date: 2026-08-03
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e82f4c7a19d1"
down_revision: str | Sequence[str] | None = "c31f7a2d9e44"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.add_column(
            sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("suspended_by_user_id", sa.Uuid(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("suspension_reason", sa.Text(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_libraries_suspended_by_user_id_users",
            "users",
            ["suspended_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.drop_constraint(
            "fk_libraries_suspended_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("suspension_reason")
        batch_op.drop_column("suspended_by_user_id")
        batch_op.drop_column("suspended_at")
