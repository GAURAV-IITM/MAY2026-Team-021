"""Tenant-scoped floor, seat, shift, and occupancy queries."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import AllocationStatus, SeatOperationalStatus
from app.models.seat import Floor, Seat, SeatAllocation, Shift


def list_floors(
    db: Session,
    library_id: uuid.UUID,
    *,
    include_inactive: bool = True,
) -> list[Floor]:
    query = select(Floor).where(
        Floor.library_id == library_id,
        Floor.deleted_at.is_(None),
    )
    if not include_inactive:
        query = query.where(Floor.is_active.is_(True))
    return list(
        db.scalars(
            query.order_by(Floor.sort_order.asc(), Floor.level_number.asc(), Floor.name.asc())
        )
    )


def get_floor(
    db: Session,
    library_id: uuid.UUID,
    floor_id: uuid.UUID,
) -> Floor | None:
    return db.scalar(
        select(Floor).where(
            Floor.id == floor_id,
            Floor.library_id == library_id,
            Floor.deleted_at.is_(None),
        )
    )


def find_floor_code(
    db: Session,
    library_id: uuid.UUID,
    code: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> Floor | None:
    query = select(Floor).where(
        Floor.library_id == library_id,
        func.lower(Floor.code) == code.lower(),
        Floor.deleted_at.is_(None),
    )
    if exclude_id:
        query = query.where(Floor.id != exclude_id)
    return db.scalar(query)


def floor_seat_count(
    db: Session,
    library_id: uuid.UUID,
    floor_id: uuid.UUID,
) -> int:
    return db.scalar(
        select(func.count(Seat.id)).where(
            Seat.library_id == library_id,
            Seat.floor_id == floor_id,
            Seat.deleted_at.is_(None),
        )
    ) or 0


def list_seats(
    db: Session,
    library_id: uuid.UUID,
    *,
    search: str | None = None,
    floor_id: uuid.UUID | None = None,
    status: SeatOperationalStatus | None = None,
) -> list[Seat]:
    query = (
        select(Seat)
        .join(Floor, Floor.id == Seat.floor_id)
        .options(selectinload(Seat.floor))
        .where(
            Seat.library_id == library_id,
            Seat.deleted_at.is_(None),
        )
    )
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Seat.seat_number).like(pattern),
                func.lower(Seat.notes).like(pattern),
                func.lower(Floor.name).like(pattern),
                func.lower(Floor.code).like(pattern),
            )
        )
    if floor_id:
        query = query.where(Seat.floor_id == floor_id)
    if status:
        query = query.where(Seat.operational_status == status)
    return list(
        db.scalars(
            query.order_by(Floor.sort_order.asc(), Seat.seat_number.asc())
        )
    )


def get_seat(
    db: Session,
    library_id: uuid.UUID,
    seat_id: uuid.UUID,
) -> Seat | None:
    return db.scalar(
        select(Seat)
        .options(selectinload(Seat.floor))
        .where(
            Seat.id == seat_id,
            Seat.library_id == library_id,
            Seat.deleted_at.is_(None),
        )
    )


def find_seat_number(
    db: Session,
    library_id: uuid.UUID,
    seat_number: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> Seat | None:
    query = select(Seat).where(
        Seat.library_id == library_id,
        func.lower(Seat.seat_number) == seat_number.lower(),
        Seat.deleted_at.is_(None),
    )
    if exclude_id:
        query = query.where(Seat.id != exclude_id)
    return db.scalar(query)


def active_allocations_for_seats(
    db: Session,
    library_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
) -> list[SeatAllocation]:
    if not seat_ids:
        return []
    return list(
        db.scalars(
            select(SeatAllocation).where(
                SeatAllocation.library_id == library_id,
                SeatAllocation.seat_id.in_(seat_ids),
                SeatAllocation.status == AllocationStatus.ACTIVE,
                SeatAllocation.end_date >= date.today(),
            )
        )
    )


def has_active_allocations(
    db: Session,
    library_id: uuid.UUID,
    *,
    seat_ids: list[uuid.UUID] | None = None,
    shift_id: uuid.UUID | None = None,
) -> bool:
    query = select(SeatAllocation.id).where(
        SeatAllocation.library_id == library_id,
        SeatAllocation.status == AllocationStatus.ACTIVE,
        SeatAllocation.end_date >= date.today(),
    )
    if seat_ids is not None:
        query = query.where(SeatAllocation.seat_id.in_(seat_ids))
    if shift_id is not None:
        query = query.where(SeatAllocation.shift_id == shift_id)
    return db.scalar(query.limit(1)) is not None


def list_shifts(
    db: Session,
    library_id: uuid.UUID,
    *,
    include_inactive: bool = True,
) -> list[Shift]:
    query = select(Shift).where(
        Shift.library_id == library_id,
        Shift.deleted_at.is_(None),
    )
    if not include_inactive:
        query = query.where(Shift.is_active.is_(True))
    return list(db.scalars(query.order_by(Shift.start_time.asc(), Shift.name.asc())))


def get_shift(
    db: Session,
    library_id: uuid.UUID,
    shift_id: uuid.UUID,
) -> Shift | None:
    return db.scalar(
        select(Shift).where(
            Shift.id == shift_id,
            Shift.library_id == library_id,
            Shift.deleted_at.is_(None),
        )
    )


def find_shift_name(
    db: Session,
    library_id: uuid.UUID,
    name: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> Shift | None:
    query = select(Shift).where(
        Shift.library_id == library_id,
        func.lower(Shift.name) == name.lower(),
        Shift.deleted_at.is_(None),
    )
    if exclude_id:
        query = query.where(Shift.id != exclude_id)
    return db.scalar(query)
