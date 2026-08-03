"""Tenant-scoped seat availability and allocation persistence queries."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import AllocationStatus
from app.models.seat import Floor, Seat, SeatAllocation, Shift
from app.models.student import Student
from app.schemas.common import PaginationParams


SORT_COLUMNS = {
    "allocatedAt": SeatAllocation.allocated_at,
    "startDate": SeatAllocation.start_date,
    "endDate": SeatAllocation.end_date,
    "status": SeatAllocation.status,
    "seatNumber": SeatAllocation.seat_number_snapshot,
    "shiftName": SeatAllocation.shift_name,
}


def _allocation_load_options():
    return (
        selectinload(SeatAllocation.student),
        selectinload(SeatAllocation.seat).selectinload(Seat.floor),
        selectinload(SeatAllocation.allocated_by),
        selectinload(SeatAllocation.closed_by),
    )


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


def lock_active_shifts_by_ids(
    db: Session,
    library_id: uuid.UUID,
    shift_ids: list[uuid.UUID],
) -> list[Shift]:
    if not shift_ids:
        return []
    return list(
        db.scalars(
            select(Shift)
            .where(
                Shift.library_id == library_id,
                Shift.id.in_(shift_ids),
                Shift.is_active.is_(True),
                Shift.deleted_at.is_(None),
            )
            .order_by(Shift.id.asc())
            .with_for_update()
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


def get_allocation(
    db: Session,
    library_id: uuid.UUID,
    allocation_id: uuid.UUID,
) -> SeatAllocation | None:
    return db.scalar(
        select(SeatAllocation)
        .options(*_allocation_load_options())
        .where(
            SeatAllocation.id == allocation_id,
            SeatAllocation.library_id == library_id,
        )
    )


def lock_allocation(
    db: Session,
    library_id: uuid.UUID,
    allocation_id: uuid.UUID,
) -> SeatAllocation | None:
    return db.scalar(
        select(SeatAllocation)
        .options(*_allocation_load_options())
        .where(
            SeatAllocation.id == allocation_id,
            SeatAllocation.library_id == library_id,
        )
        .with_for_update()
    )


def list_allocations(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    student_id: uuid.UUID | None = None,
    seat_id: uuid.UUID | None = None,
    shift_id: uuid.UUID | None = None,
    status: AllocationStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[SeatAllocation], int]:
    conditions = [SeatAllocation.library_id == library_id]
    if student_id is not None:
        conditions.append(SeatAllocation.student_id == student_id)
    if seat_id is not None:
        conditions.append(SeatAllocation.seat_id == seat_id)
    if shift_id is not None:
        conditions.append(SeatAllocation.shift_id == shift_id)
    if status is not None:
        conditions.append(SeatAllocation.status == status)
    if start_date is not None:
        conditions.append(SeatAllocation.end_date >= start_date)
    if end_date is not None:
        conditions.append(SeatAllocation.start_date <= end_date)
    if pagination.search:
        search = f"%{pagination.search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Student.first_name).like(search),
                func.lower(Student.last_name).like(search),
                func.lower(Student.enrollment_number).like(search),
                func.lower(SeatAllocation.shift_name).like(search),
                func.lower(
                    func.coalesce(
                        SeatAllocation.seat_number_snapshot,
                        Seat.seat_number,
                    )
                ).like(search),
            )
        )

    joined = (
        select(SeatAllocation)
        .join(Student, Student.id == SeatAllocation.student_id)
        .join(Seat, Seat.id == SeatAllocation.seat_id)
        .where(*conditions)
    )
    total = db.scalar(
        select(func.count(SeatAllocation.id))
        .join(Student, Student.id == SeatAllocation.student_id)
        .join(Seat, Seat.id == SeatAllocation.seat_id)
        .where(*conditions)
    ) or 0
    sort_column = SORT_COLUMNS.get(
        pagination.sort_by,
        SeatAllocation.allocated_at,
    )
    ordering = (
        sort_column.asc()
        if pagination.sort_order == "asc"
        else sort_column.desc()
    )
    allocations = list(
        db.scalars(
            joined
            .options(*_allocation_load_options())
            .order_by(ordering, SeatAllocation.id.asc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
    )
    return allocations, total


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
            .options(*_allocation_load_options())
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
