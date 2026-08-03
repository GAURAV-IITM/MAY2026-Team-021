"""Add owner invitation metadata and concurrency constraints.

Revision ID: a15c9e7d2b41
Revises: e82f4c7a19d1
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a15c9e7d2b41"
down_revision: str | None = "e82f4c7a19d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("account_invitations") as batch_op:
        batch_op.add_column(
            sa.Column("invitee_name", sa.String(length=160), nullable=True)
        )
        batch_op.add_column(
            sa.Column("invitee_phone", sa.String(length=32), nullable=True)
        )
        batch_op.add_column(
            sa.Column("accepted_user_id", sa.Uuid(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_account_invitations_accepted_user_id_users",
            "users",
            ["accepted_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_account_invitations_accepted_user_id",
            ["accepted_user_id"],
        )
    op.create_index(
        "uq_pending_owner_invitation_email",
        "account_invitations",
        ["email"],
        unique=True,
        sqlite_where=sa.text(
            "status = 'pending' AND role = 'library_owner'"
        ),
        postgresql_where=sa.text(
            "status = 'pending' AND role = 'library_owner'"
        ),
    )
    op.create_index(
        "uq_pending_owner_invitation_library",
        "account_invitations",
        ["library_id"],
        unique=True,
        sqlite_where=sa.text(
            "status = 'pending' AND role = 'library_owner'"
        ),
        postgresql_where=sa.text(
            "status = 'pending' AND role = 'library_owner'"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_pending_owner_invitation_library",
        table_name="account_invitations",
    )
    op.drop_index(
        "uq_pending_owner_invitation_email",
        table_name="account_invitations",
    )
    with op.batch_alter_table("account_invitations") as batch_op:
        batch_op.drop_index("ix_account_invitations_accepted_user_id")
        batch_op.drop_constraint(
            "fk_account_invitations_accepted_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("accepted_user_id")
        batch_op.drop_column("invitee_phone")
        batch_op.drop_column("invitee_name")
