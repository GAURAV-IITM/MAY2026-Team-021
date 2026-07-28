"""Read-optimized, tenant-scoped dashboard and report source queries."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.audit import AuditLog
from app.models.enums import (
    AllocationStatus,
    FeeStatus,
    SeatRequestStatus,
)
from app.models.payment import FeeRecord, PaymentTransaction
from app.models.seat import Floor, Seat, SeatAllocation, SeatChangeRequest, Shift
from app.models.student import Student


def list_students(db: Session, library_id: uuid.UUID) -> list[Student]:
    return list(
        db.scalars(
            select(Student)
            .where(
                Student.library_id == library_id,
                Student.deleted_at.is_(None),
            )
            .order_by(
                Student.joined_on.asc(),
                Student.id.asc(),
            )
        )
    )


def list_floors(db: Session, library_id: uuid.UUID) -> list[Floor]:
    return list(
        db.scalars(
            select(Floor)
            .where(
                Floor.library_id == library_id,
                Floor.deleted_at.is_(None),
            )
            .order_by(
                Floor.sort_order.asc(),
                Floor.level_number.asc().nullslast(),
                Floor.id.asc(),
            )
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


def list_shifts(db: Session, library_id: uuid.UUID) -> list[Shift]:
    return list(
        db.scalars(
            select(Shift)
            .where(
                Shift.library_id == library_id,
                Shift.deleted_at.is_(None),
            )
            .order_by(
                Shift.is_active.desc(),
                Shift.start_time.asc(),
                Shift.name.asc(),
                Shift.id.asc(),
            )
        )
    )


def list_historical_shift_ids(
    db: Session,
    library_id: uuid.UUID,
) -> set[uuid.UUID]:
    return set(
        db.scalars(
            select(SeatAllocation.shift_id)
            .where(SeatAllocation.library_id == library_id)
            .distinct()
        )
    )


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


def list_seats(
    db: Session,
    library_id: uuid.UUID,
    *,
    floor_id: uuid.UUID | None = None,
) -> list[Seat]:
    conditions = [
        Seat.library_id == library_id,
        Seat.deleted_at.is_(None),
        Seat.is_active.is_(True),
    ]
    if floor_id is not None:
        conditions.append(Seat.floor_id == floor_id)
    return list(
        db.scalars(
            select(Seat)
            .options(selectinload(Seat.floor))
            .where(*conditions)
            .order_by(Seat.floor_id.asc(), Seat.seat_number.asc())
        )
    )


def list_allocations_on_date(
    db: Session,
    library_id: uuid.UUID,
    report_date: date,
    *,
    seat_ids: set[uuid.UUID] | None = None,
) -> list[SeatAllocation]:
    conditions = [
        SeatAllocation.library_id == library_id,
        SeatAllocation.status == AllocationStatus.ACTIVE,
        SeatAllocation.start_date <= report_date,
        SeatAllocation.end_date >= report_date,
    ]
    if seat_ids is not None:
        if not seat_ids:
            return []
        conditions.append(SeatAllocation.seat_id.in_(seat_ids))
    return list(
        db.scalars(
            select(SeatAllocation)
            .options(
                selectinload(SeatAllocation.seat).selectinload(Seat.floor),
                selectinload(SeatAllocation.student),
            )
            .where(*conditions)
            .order_by(
                SeatAllocation.seat_id.asc(),
                SeatAllocation.shift_start_time.asc(),
                SeatAllocation.id.asc(),
            )
        )
    )


def list_fee_records(
    db: Session,
    library_id: uuid.UUID,
    start_month: date,
    end_month: date,
    *,
    student_ids: set[uuid.UUID] | None = None,
) -> list[FeeRecord]:
    conditions = [
        FeeRecord.library_id == library_id,
        FeeRecord.billing_month >= start_month,
        FeeRecord.billing_month <= end_month,
        FeeRecord.status.not_in(
            [FeeStatus.WAIVED, FeeStatus.CANCELLED]
        ),
    ]
    if student_ids is not None:
        if not student_ids:
            return []
        conditions.append(FeeRecord.student_id.in_(student_ids))
    return list(
        db.scalars(
            select(FeeRecord)
            .options(
                selectinload(FeeRecord.student),
                selectinload(FeeRecord.transactions).selectinload(
                    PaymentTransaction.recorded_by
                ),
            )
            .where(*conditions)
            .order_by(
                FeeRecord.billing_month.asc(),
                FeeRecord.due_date.asc(),
                FeeRecord.id.asc(),
            )
        ).unique()
    )


def list_all_fee_months(
    db: Session,
    library_id: uuid.UUID,
) -> list[date]:
    return list(
        db.scalars(
            select(FeeRecord.billing_month)
            .where(FeeRecord.library_id == library_id)
            .distinct()
            .order_by(FeeRecord.billing_month.asc())
        )
    )


def list_payment_dates(
    db: Session,
    library_id: uuid.UUID,
) -> list:
    return list(
        db.scalars(
            select(PaymentTransaction.paid_at)
            .where(PaymentTransaction.library_id == library_id)
            .order_by(PaymentTransaction.paid_at.asc())
        )
    )


def list_pending_requests(
    db: Session,
    library_id: uuid.UUID,
) -> list[SeatChangeRequest]:
    return list(
        db.scalars(
            select(SeatChangeRequest)
            .where(
                SeatChangeRequest.library_id == library_id,
                SeatChangeRequest.status == SeatRequestStatus.PENDING,
            )
            .order_by(
                SeatChangeRequest.submitted_at.asc(),
                SeatChangeRequest.id.asc(),
            )
        )
    )


def list_recent_audits(
    db: Session,
    library_id: uuid.UUID,
    *,
    limit: int = 6,
) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog)
            .options(selectinload(AuditLog.actor))
            .where(AuditLog.library_id == library_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
        )
    )
