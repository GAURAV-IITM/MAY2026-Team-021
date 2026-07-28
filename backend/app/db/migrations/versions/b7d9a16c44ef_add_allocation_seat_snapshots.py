"""Add allocation seat and floor snapshots.

Revision ID: b7d9a16c44ef
Revises: 83c42dc2a7e1
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b7d9a16c44ef"
down_revision: str | Sequence[str] | None = "83c42dc2a7e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "seat_allocations",
        sa.Column("seat_number_snapshot", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "seat_allocations",
        sa.Column("floor_id_snapshot", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "seat_allocations",
        sa.Column("floor_name_snapshot", sa.String(length=100), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE seat_allocations
            SET seat_number_snapshot = (
                SELECT seats.seat_number
                FROM seats
                WHERE seats.id = seat_allocations.seat_id
            ),
            floor_id_snapshot = (
                SELECT seats.floor_id
                FROM seats
                WHERE seats.id = seat_allocations.seat_id
            ),
            floor_name_snapshot = (
                SELECT floors.name
                FROM seats
                JOIN floors ON floors.id = seats.floor_id
                WHERE seats.id = seat_allocations.seat_id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("seat_allocations", "floor_name_snapshot")
    op.drop_column("seat_allocations", "floor_id_snapshot")
    op.drop_column("seat_allocations", "seat_number_snapshot")
