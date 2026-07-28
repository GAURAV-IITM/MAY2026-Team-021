"""Owner seat-change request list and review use cases."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.models.enums import SeatRequestStatus
from app.models.seat import SeatAllocation, SeatChangeRequest
from app.repositories import seat_request as repository
from app.schemas.common import PaginationParams
from app.schemas.seat_request import (
    SeatChangeRequestResponse,
    SeatRequestAllocationSummary,
    SeatRequestFloorSummary,
    SeatRequestReview,
    SeatRequestReviewerSummary,
    SeatRequestSeatSummary,
    SeatRequestShiftSummary,
    SeatRequestStudentSummary,
    SeatRequestSummary,
)
from app.services.audit import AuditContext, write_audit_log


@dataclass(frozen=True, slots=True)
class SeatRequestListResult:
    requests: list[SeatChangeRequestResponse]
    total: int
    summary: SeatRequestSummary


def _allocation_summary(
    allocation: SeatAllocation | None,
) -> SeatRequestAllocationSummary | None:
    if allocation is None:
        return None
    return SeatRequestAllocationSummary(
        id=allocation.id,
        seat_id=allocation.seat_id,
        seat_number=(
            allocation.seat_number_snapshot or allocation.seat.seat_number
        ),
        floor_id=allocation.floor_id_snapshot,
        floor_name=(
            allocation.floor_name_snapshot or allocation.seat.floor.name
        ),
        shift_id=allocation.shift_id,
        shift_name=allocation.shift_name,
        start_date=allocation.start_date,
        end_date=allocation.end_date,
        status=allocation.status,
    )


def _response(request: SeatChangeRequest) -> SeatChangeRequestResponse:
    student = request.student
    shift = request.preferred_shift
    reviewer = request.reviewed_by
    return SeatChangeRequestResponse(
        id=request.id,
        request_number=request.request_number,
        status=request.status,
        student=SeatRequestStudentSummary(
            id=student.id,
            enrollment_number=student.enrollment_number,
            name=f"{student.first_name} {student.last_name}".strip(),
        ),
        current_allocation=_allocation_summary(request.current_allocation),
        preferred_seat=(
            SeatRequestSeatSummary(
                id=request.preferred_seat.id,
                seat_number=request.preferred_seat.seat_number,
            )
            if request.preferred_seat
            else None
        ),
        preferred_floor=(
            SeatRequestFloorSummary(
                id=request.preferred_floor.id,
                name=request.preferred_floor.name,
                level_number=request.preferred_floor.level_number,
            )
            if request.preferred_floor
            else None
        ),
        preferred_shift=SeatRequestShiftSummary(
            id=shift.id,
            name=shift.name,
            start_time=shift.start_time.strftime("%H:%M"),
            end_time=shift.end_time.strftime("%H:%M"),
        ),
        reason=request.reason,
        submitted_at=request.submitted_at,
        reviewed_by=(
            SeatRequestReviewerSummary(
                id=reviewer.id,
                name=reviewer.full_name,
            )
            if reviewer
            else None
        ),
        reviewed_at=request.resolved_at,
        review_note=request.admin_note,
        resulting_allocation_id=request.resulting_allocation_id,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def list_requests(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    **filters: object,
) -> SeatRequestListResult:
    records, total, summary = repository.list_requests(
        db,
        library_id,
        pagination,
        **filters,
    )
    return SeatRequestListResult(
        requests=[_response(record) for record in records],
        total=total,
        summary=summary,
    )


def _ensure_pending_for_review(
    request: SeatChangeRequest,
    payload: SeatRequestReview,
) -> None:
    if request.status == SeatRequestStatus.PENDING:
        return
    raise ConflictError(
        "This seat-change request has already been reviewed.",
        code="SEAT_REQUEST_ALREADY_REVIEWED",
        details={
            "requestId": str(request.id),
            "currentStatus": request.status.value,
            "requestedDecision": payload.decision,
            "reviewedAt": (
                request.resolved_at.isoformat()
                if request.resolved_at
                else None
            ),
        },
    )


def review_request(
    db: Session,
    library_id: uuid.UUID,
    request_id: uuid.UUID,
    payload: SeatRequestReview,
    reviewer_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> SeatChangeRequestResponse:
    try:
        request = repository.get_request(
            db,
            library_id,
            request_id,
            for_update=True,
        )
        if request is None:
            raise ResourceNotFoundError(
                "Seat-change request not found.",
                code="SEAT_REQUEST_NOT_FOUND",
            )
        _ensure_pending_for_review(request, payload)

        now = datetime.now(timezone.utc)
        request.status = SeatRequestStatus(payload.decision)
        request.admin_note = payload.review_note
        request.resolved_at = now
        request.reviewed_by_user_id = reviewer_user_id
        request.updated_at = now
        db.flush()
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=reviewer_user_id,
            action=f"seat_change_request.{payload.decision}",
            entity_type="seat_change_request",
            entity_id=str(request.id),
            old_values={"status": SeatRequestStatus.PENDING.value},
            new_values={
                "status": payload.decision,
                "reviewedAt": now.isoformat(),
                "reviewNoteProvided": bool(payload.review_note),
                "resultingAllocationId": (
                    str(request.resulting_allocation_id)
                    if request.resulting_allocation_id
                    else None
                ),
            },
            context={"studentId": str(request.student_id)},
            request_context=audit_context,
        )
        db.commit()
        db.expire(request, ["reviewed_by"])
        saved = repository.get_request(db, library_id, request.id)
        assert saved is not None
        return _response(saved)
    except Exception:
        db.rollback()
        raise
