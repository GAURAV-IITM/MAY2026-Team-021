"""phase 2 core library data

Revision ID: 83c42dc2a7e1
Revises: d42b878aa019
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "83c42dc2a7e1"
down_revision: Union[str, Sequence[str], None] = "d42b878aa019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("account_invitations") as batch_op:
        batch_op.drop_constraint(
            "uq_invitation_library_email_status",
            type_="unique",
        )
        batch_op.create_index(
            "uq_pending_invitation_library_email",
            ["library_id", "email"],
            unique=True,
            sqlite_where=sa.text("status = 'pending'"),
            postgresql_where=sa.text("status = 'pending'"),
        )


def downgrade() -> None:
    with op.batch_alter_table("account_invitations") as batch_op:
        batch_op.drop_index("uq_pending_invitation_library_email")
        batch_op.create_unique_constraint(
            "uq_invitation_library_email_status",
            ["library_id", "email", "status"],
        )
