"""Tenant-scoped owner seat-change request queries."""
from __future__ import annotations

import uuid

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.models.enums import SeatRequestStatus
from app.models.seat import Seat, SeatAllocation, SeatChangeRequest
from app.models.student import Student
from app.schemas.common import PaginationParams
from app.schemas.seat_request import SeatRequestSummary


SORT_COLUMNS = {
    "submittedAt": SeatChangeRequest.submitted_at,
    "reviewedAt": SeatChangeRequest.resolved_at,
    "updatedAt": SeatChangeRequest.updated_at,
    "status": SeatChangeRequest.status,
    "requestNumber": SeatChangeRequest.request_number,
    "studentName": Student.first_name,
}


def _load_options():
    return (
        selectinload(SeatChangeRequest.student),
        selectinload(SeatChangeRequest.current_allocation).selectinload(
            SeatAllocation.seat
        ).selectinload(Seat.floor),
        selectinload(SeatChangeRequest.preferred_seat),
        selectinload(SeatChangeRequest.preferred_floor),
        selectinload(SeatChangeRequest.preferred_shift),
        selectinload(SeatChangeRequest.reviewed_by),
    )


def list_requests(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    status: SeatRequestStatus | None = None,
    student_id: uuid.UUID | None = None,
    preferred_floor_id: uuid.UUID | None = None,
    preferred_shift_id: uuid.UUID | None = None,
) -> tuple[list[SeatChangeRequest], int, SeatRequestSummary]:
    preferred_seat = aliased(Seat)
    conditions: list[object] = [SeatChangeRequest.library_id == library_id]
    if status is not None:
        conditions.append(SeatChangeRequest.status == status)
    if student_id is not None:
        conditions.append(SeatChangeRequest.student_id == student_id)
    if preferred_floor_id is not None:
        conditions.append(
            SeatChangeRequest.preferred_floor_id == preferred_floor_id
        )
    if preferred_shift_id is not None:
        conditions.append(
            SeatChangeRequest.preferred_shift_id == preferred_shift_id
        )
    if pagination.search:
        search = f"%{pagination.search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Student.first_name).like(search),
                func.lower(Student.last_name).like(search),
                func.lower(
                    Student.first_name + " " + Student.last_name
                ).like(search),
                func.lower(Student.enrollment_number).like(search),
                func.lower(SeatChangeRequest.reason).like(search),
                func.lower(preferred_seat.seat_number).like(search),
            )
        )

    base = (
        select(SeatChangeRequest)
        .join(Student, Student.id == SeatChangeRequest.student_id)
        .outerjoin(
            preferred_seat,
            preferred_seat.id == SeatChangeRequest.preferred_seat_id,
        )
        .where(*conditions)
    )
    total = db.scalar(
        select(func.count())
        .select_from(base.with_only_columns(SeatChangeRequest.id).subquery())
    ) or 0
    sort_column = SORT_COLUMNS.get(
        pagination.sort_by,
        SeatChangeRequest.submitted_at,
    )
    ordering = (
        sort_column.asc()
        if pagination.sort_order == "asc"
        else sort_column.desc()
    )
    records = list(
        db.scalars(
            base.options(*_load_options())
            .order_by(ordering, SeatChangeRequest.id.asc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
    )
    counts = db.execute(
        select(
            func.count(SeatChangeRequest.id),
            *[
                func.sum(
                    case((SeatChangeRequest.status == item, 1), else_=0)
                )
                for item in (
                    SeatRequestStatus.PENDING,
                    SeatRequestStatus.APPROVED,
                    SeatRequestStatus.REJECTED,
                    SeatRequestStatus.CANCELLED,
                )
            ],
        ).where(SeatChangeRequest.library_id == library_id)
    ).one()
    return records, total, SeatRequestSummary(
        total=counts[0] or 0,
        pending=counts[1] or 0,
        approved=counts[2] or 0,
        rejected=counts[3] or 0,
        cancelled=counts[4] or 0,
    )


def get_request(
    db: Session,
    library_id: uuid.UUID,
    request_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> SeatChangeRequest | None:
    query = (
        select(SeatChangeRequest)
        .options(*_load_options())
        .where(
            SeatChangeRequest.id == request_id,
            SeatChangeRequest.library_id == library_id,
        )
    )
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)
