"""Tenant-scoped seat availability and allocation persistence queries."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import AllocationStatus
from app.models.seat import Floor, Seat, SeatAllocation, Shift
from app.models.student import Student


def list_active_shifts_by_ids(
    db: Session,
    library_id: uuid.UUID,
    shift_ids: list[uuid.UUID],
) -> list[Shift]:
    if not shift_ids:
        return []
    return list(
        db.scalars(
            select(Shift).where(
                Shift.library_id == library_id,
                Shift.id.in_(shift_ids),
                Shift.is_active.is_(True),
                Shift.deleted_at.is_(None),
            )
        )
    )


def lock_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Student | None:
    return db.scalar(
        select(Student)
        .where(
            Student.id == student_id,
            Student.library_id == library_id,
            Student.deleted_at.is_(None),
        )
        .with_for_update()
    )


def get_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Student | None:
    return db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.library_id == library_id,
            Student.deleted_at.is_(None),
        )
    )


def lock_seat(
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
        .with_for_update()
    )


def allocations_for_seats_in_range(
    db: Session,
    library_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
    start_date: date,
    end_date: date,
    exclude_student_id: uuid.UUID | None = None,
) -> list[SeatAllocation]:
    if not seat_ids:
        return []
    statement = (
        select(SeatAllocation)
        .options(selectinload(SeatAllocation.student))
        .where(
            SeatAllocation.library_id == library_id,
            SeatAllocation.seat_id.in_(seat_ids),
            SeatAllocation.status == AllocationStatus.ACTIVE,
            SeatAllocation.start_date <= end_date,
            SeatAllocation.end_date >= start_date,
        )
        .order_by(
            SeatAllocation.start_date.asc(),
            SeatAllocation.allocated_at.asc(),
        )
    )
    if exclude_student_id is not None:
        statement = statement.where(
            SeatAllocation.student_id != exclude_student_id
        )
    return list(db.scalars(statement))


def lock_seat_conflicts(
    db: Session,
    library_id: uuid.UUID,
    seat_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> list[SeatAllocation]:
    return list(
        db.scalars(
            select(SeatAllocation)
            .options(selectinload(SeatAllocation.student))
            .where(
                SeatAllocation.library_id == library_id,
                SeatAllocation.seat_id == seat_id,
                SeatAllocation.status == AllocationStatus.ACTIVE,
                SeatAllocation.start_date <= end_date,
                SeatAllocation.end_date >= start_date,
            )
            .order_by(SeatAllocation.start_date.asc())
            .with_for_update()
        )
    )


def lock_student_conflicts(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> list[SeatAllocation]:
    return list(
        db.scalars(
            select(SeatAllocation)
            .options(selectinload(SeatAllocation.seat))
            .where(
                SeatAllocation.library_id == library_id,
                SeatAllocation.student_id == student_id,
                SeatAllocation.status == AllocationStatus.ACTIVE,
                SeatAllocation.start_date <= end_date,
                SeatAllocation.end_date >= start_date,
            )
            .order_by(SeatAllocation.start_date.asc())
            .with_for_update()
        )
    )


def lock_active_student_allocations(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> list[SeatAllocation]:
    return list(
        db.scalars(
            select(SeatAllocation)
            .where(
                SeatAllocation.library_id == library_id,
                SeatAllocation.student_id == student_id,
                SeatAllocation.status == AllocationStatus.ACTIVE,
            )
            .order_by(
                SeatAllocation.start_date.asc(),
                SeatAllocation.allocated_at.asc(),
            )
            .with_for_update()
        )
    )


def allocations_for_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> list[SeatAllocation]:
    return list(
        db.scalars(
            select(SeatAllocation)
            .options(
                selectinload(SeatAllocation.seat).selectinload(Seat.floor),
            )
            .where(
                SeatAllocation.library_id == library_id,
                SeatAllocation.student_id == student_id,
            )
            .order_by(
                SeatAllocation.start_date.desc(),
                SeatAllocation.seat_id.asc(),
                SeatAllocation.shift_start_time.asc(),
            )
        )
    )
