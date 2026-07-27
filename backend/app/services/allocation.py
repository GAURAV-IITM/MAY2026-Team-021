"""Seat availability calculations and allocation business rules."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, ResourceNotFoundError
from app.models.enums import AllocationStatus, SeatOperationalStatus, StudentStatus
from app.models.seat import Seat, SeatAllocation, Shift
from app.models.student import Student
from app.repositories import allocation as repository
from app.repositories import seat as seat_repository
from app.schemas.allocation import (
    AllocationActorSummary,
    AllocationSeatSummary,
    AllocationShiftSummary,
    AllocationStudentSummary,
    SeatAllocationCreate,
    SeatAllocationCreateResponse,
    SeatAllocationResponse,
    SeatAllocationStatusUpdate,
    SeatAvailabilityBlockerResponse,
    SeatAvailabilityResponse,
    SeatAvailabilitySeatResponse,
    SeatAvailabilitySummaryResponse,
    StudentSeatAllocationChange,
    StudentSeatAllocationCreate,
    StudentSeatAssignmentResponse,
)
from app.schemas.common import PaginationParams
from app.services import audit as audit_service


def _minute(value: time) -> int:
    return value.hour * 60 + value.minute


def _segments(start: time, end: time) -> list[tuple[int, int]]:
    start_minute = _minute(start)
    end_minute = _minute(end)
    if end_minute > start_minute:
        return [(start_minute, end_minute)]
    return [(start_minute, 24 * 60), (0, end_minute)]


def time_ranges_overlap(
    first_start: time,
    first_end: time,
    second_start: time,
    second_end: time,
) -> bool:
    return any(
        first_segment_start < second_segment_end
        and second_segment_start < first_segment_end
        for first_segment_start, first_segment_end in _segments(
            first_start,
            first_end,
        )
        for second_segment_start, second_segment_end in _segments(
            second_start,
            second_end,
        )
    )


def _require_active_shifts(
    db: Session,
    library_id: uuid.UUID,
    shift_ids: list[uuid.UUID],
    *,
    lock: bool = False,
) -> list[Shift]:
    if not shift_ids:
        raise BusinessRuleError(
            "Select at least one shift.",
            code="ALLOCATION_SHIFT_REQUIRED",
        )
    shifts = (
        repository.lock_active_shifts_by_ids(db, library_id, shift_ids)
        if lock
        else repository.list_active_shifts_by_ids(db, library_id, shift_ids)
    )
    shifts_by_id = {shift.id: shift for shift in shifts}
    if len(shifts_by_id) != len(shift_ids):
        raise BusinessRuleError(
            "Every selected shift must be active and belong to this library.",
            code="ALLOCATION_SHIFT_INVALID",
        )
    ordered_shifts = [shifts_by_id[shift_id] for shift_id in shift_ids]
    for index, first in enumerate(ordered_shifts):
        for second in ordered_shifts[index + 1 :]:
            if time_ranges_overlap(
                first.start_time,
                first.end_time,
                second.start_time,
                second.end_time,
            ):
                raise BusinessRuleError(
                    f"{first.name} overlaps with {second.name}. "
                    "Select non-overlapping shifts.",
                    code="ALLOCATION_SHIFTS_OVERLAP",
                    details={
                        "firstShiftId": str(first.id),
                        "firstShiftName": first.name,
                        "secondShiftId": str(second.id),
                        "secondShiftName": second.name,
                    },
                )
    return ordered_shifts


def _ensure_valid_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise BusinessRuleError(
            "Allocation end date cannot be earlier than start date.",
            code="ALLOCATION_DATE_RANGE_INVALID",
        )


def date_ranges_overlap(
    first_start: date,
    first_end: date,
    second_start: date,
    second_end: date,
) -> bool:
    return first_start <= second_end and first_end >= second_start


def _allocation_overlaps_shifts(
    allocation: SeatAllocation,
    shifts: list[Shift],
) -> bool:
    return any(
        time_ranges_overlap(
            allocation.shift_start_time,
            allocation.shift_end_time,
            shift.start_time,
            shift.end_time,
        )
        for shift in shifts
    )


def _blocker_response(
    allocation: SeatAllocation,
) -> SeatAvailabilityBlockerResponse:
    student_name = " ".join(
        (
            allocation.student.first_name,
            allocation.student.last_name,
        )
    ).strip()
    return SeatAvailabilityBlockerResponse(
        allocation_id=allocation.id,
        student_id=allocation.student_id,
        student_name=student_name,
        shift_id=allocation.shift_id,
        shift_name=allocation.shift_name,
        shift_start_time=allocation.shift_start_time.strftime("%H:%M"),
        shift_end_time=allocation.shift_end_time.strftime("%H:%M"),
        start_date=allocation.start_date,
        end_date=allocation.end_date,
    )


def get_seat_availability(
    db: Session,
    library_id: uuid.UUID,
    *,
    shift_ids: list[uuid.UUID],
    start_date: date,
    end_date: date,
    floor_id: uuid.UUID | None = None,
    exclude_student_id: uuid.UUID | None = None,
) -> SeatAvailabilityResponse:
    _ensure_valid_range(start_date, end_date)
    shifts = _require_active_shifts(db, library_id, list(dict.fromkeys(shift_ids)))
    if (
        exclude_student_id is not None
        and repository.get_student(db, library_id, exclude_student_id) is None
    ):
        raise ResourceNotFoundError(
            "Student not found.",
            code="STUDENT_NOT_FOUND",
        )
    if floor_id is not None:
        floor = seat_repository.get_floor(db, library_id, floor_id)
        if floor is None:
            raise ResourceNotFoundError("Floor not found.", code="FLOOR_NOT_FOUND")
        if not floor.is_active:
            raise BusinessRuleError(
                "Seat availability can only be checked on an active floor.",
                code="FLOOR_INACTIVE",
            )
    seats = seat_repository.list_seats(db, library_id, floor_id=floor_id)
    allocations = repository.allocations_for_seats_in_range(
        db,
        library_id,
        [seat.id for seat in seats],
        start_date,
        end_date,
        exclude_student_id=exclude_student_id,
    )
    allocations_by_seat: dict[uuid.UUID, list[SeatAllocation]] = defaultdict(list)
    for allocation in allocations:
        allocations_by_seat[allocation.seat_id].append(allocation)

    selected_shift_ids = {shift.id for shift in shifts}
    seat_results = []
    for seat in seats:
        blockers = [
            allocation
            for allocation in allocations_by_seat[seat.id]
            if _allocation_overlaps_shifts(allocation, shifts)
        ]
        if seat.operational_status == SeatOperationalStatus.MAINTENANCE:
            availability_status = "maintenance"
        elif (
            not seat.is_active
            or not seat.floor.is_active
            or seat.operational_status == SeatOperationalStatus.BLOCKED
        ):
            availability_status = "physically_blocked"
        elif blockers:
            exact_shift_blockers = [
                allocation
                for allocation in blockers
                if allocation.shift_id in selected_shift_ids
            ]
            if exact_shift_blockers:
                availability_status = (
                    "reserved"
                    if all(
                        allocation.start_date > date.today()
                        for allocation in exact_shift_blockers
                    )
                    else "allotted"
                )
            else:
                availability_status = "blocked"
        else:
            availability_status = "available"
        seat_results.append(
            SeatAvailabilitySeatResponse(
                seat_id=seat.id,
                seat_number=seat.seat_number,
                floor_id=seat.floor_id,
                floor_name=seat.floor.name,
                floor=seat.floor.level_number,
                seat_type=seat.seat_type,
                physical_status=seat.operational_status,
                status=availability_status,
                is_available=availability_status == "available",
                status_note=seat.status_note,
                blockers=[_blocker_response(allocation) for allocation in blockers],
            )
        )
    summary_counts = {
        status: sum(seat.status == status for seat in seat_results)
        for status in (
            "available",
            "allotted",
            "reserved",
            "blocked",
            "maintenance",
            "physically_blocked",
        )
    }
    return SeatAvailabilityResponse(
        shift_ids=[shift.id for shift in shifts],
        start_date=start_date,
        end_date=end_date,
        total_seats=len(seat_results),
        available_seat_count=sum(seat.is_available for seat in seat_results),
        summary=SeatAvailabilitySummaryResponse(**summary_counts),
        seats=seat_results,
    )


def _seat_conflict_error(
    seat: Seat,
    allocation: SeatAllocation,
) -> ConflictError:
    student_name = " ".join(
        (
            allocation.student.first_name,
            allocation.student.last_name,
        )
    ).strip()
    return ConflictError(
        f"Seat {seat.seat_number} is already allocated to {student_name} "
        f"from {allocation.start_date.isoformat()} to "
        f"{allocation.end_date.isoformat()} during {allocation.shift_name}.",
        code="SEAT_ALLOCATION_CONFLICT",
        details={
            "allocationId": str(allocation.id),
            "seatId": str(seat.id),
            "seatNumber": seat.seat_number,
            "studentId": str(allocation.student_id),
            "studentName": student_name,
            "shiftId": str(allocation.shift_id),
            "shiftName": allocation.shift_name,
            "shiftStartTime": allocation.shift_start_time.strftime("%H:%M"),
            "shiftEndTime": allocation.shift_end_time.strftime("%H:%M"),
            "startDate": allocation.start_date.isoformat(),
            "endDate": allocation.end_date.isoformat(),
        },
    )


def create_student_allocations(
    db: Session,
    library_id: uuid.UUID,
    student: Student,
    payload: StudentSeatAllocationCreate,
    allocated_by_user_id: uuid.UUID,
    *,
    previous_allocation_id: uuid.UUID | None = None,
    transfer_group_id: uuid.UUID | None = None,
    audit_context: audit_service.AuditContext | None = None,
) -> list[SeatAllocation]:
    _ensure_valid_range(payload.start_date, payload.end_date)
    if payload.end_date < date.today():
        raise BusinessRuleError(
            "A new active seat allocation cannot end in the past.",
            code="ALLOCATION_END_DATE_IN_PAST",
        )

    seat = repository.lock_seat(db, library_id, payload.seat_id)
    if seat is None:
        raise ResourceNotFoundError("Seat not found.", code="SEAT_NOT_FOUND")
    locked_student = repository.lock_student(db, library_id, student.id)
    if locked_student is None:
        raise ResourceNotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    if locked_student.status != StudentStatus.ACTIVE:
        raise BusinessRuleError(
            "Only active students can be assigned a seat.",
            code="STUDENT_NOT_ACTIVE",
        )
    if payload.start_date < locked_student.joined_on:
        raise BusinessRuleError(
            "Seat allocation cannot start before the student's joining date.",
            code="ALLOCATION_BEFORE_JOINING_DATE",
        )
    if not seat.is_active or not seat.floor.is_active:
        raise BusinessRuleError(
            "The selected seat and floor must be active.",
            code="SEAT_INACTIVE",
        )
    if seat.operational_status != SeatOperationalStatus.AVAILABLE:
        raise BusinessRuleError(
            f"Seat {seat.seat_number} is currently "
            f"{seat.operational_status.value}.",
            code="SEAT_NOT_OPERATIONALLY_AVAILABLE",
            details={
                "seatId": str(seat.id),
                "seatNumber": seat.seat_number,
                "status": seat.operational_status.value,
            },
        )

    shifts = _require_active_shifts(
        db,
        library_id,
        payload.shift_ids,
        lock=True,
    )
    seat_conflicts = repository.lock_seat_conflicts(
        db,
        library_id,
        seat.id,
        payload.start_date,
        payload.end_date,
    )
    for allocation in seat_conflicts:
        if _allocation_overlaps_shifts(allocation, shifts):
            raise _seat_conflict_error(seat, allocation)

    student_conflicts = repository.lock_student_conflicts(
        db,
        library_id,
        student.id,
        payload.start_date,
        payload.end_date,
    )
    for allocation in student_conflicts:
        if _allocation_overlaps_shifts(allocation, shifts):
            raise ConflictError(
                "The student already has a seat during an overlapping period "
                f"and shift ({allocation.shift_name}, "
                f"{allocation.start_date.isoformat()} to "
                f"{allocation.end_date.isoformat()}).",
                code="STUDENT_ALLOCATION_CONFLICT",
                details={
                    "allocationId": str(allocation.id),
                    "seatId": str(allocation.seat_id),
                    "shiftId": str(allocation.shift_id),
                    "shiftName": allocation.shift_name,
                    "startDate": allocation.start_date.isoformat(),
                    "endDate": allocation.end_date.isoformat(),
                },
            )

    allocation_group_id = transfer_group_id or uuid.uuid4()
    allocations = [
        SeatAllocation(
            library_id=library_id,
            student_id=student.id,
            seat_id=seat.id,
            shift_id=shift.id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=AllocationStatus.ACTIVE,
            shift_name=shift.name,
            shift_start_time=shift.start_time,
            shift_end_time=shift.end_time,
            shift_crosses_midnight=shift.crosses_midnight,
            seat_number_snapshot=seat.seat_number,
            floor_id_snapshot=seat.floor_id,
            floor_name_snapshot=seat.floor.name,
            notes=payload.notes.strip() if payload.notes else None,
            allocated_by_user_id=allocated_by_user_id,
            previous_allocation_id=previous_allocation_id,
            transfer_group_id=allocation_group_id,
        )
        for shift in shifts
    ]
    db.add_all(allocations)
    db.flush()
    audit_service.write_audit_log(
        db,
        library_id=library_id,
        actor_user_id=allocated_by_user_id,
        action="seat_allocation.created",
        entity_type="seat_allocation_group",
        entity_id=str(allocation_group_id),
        new_values={
            "allocationIds": [str(allocation.id) for allocation in allocations],
            "studentId": str(locked_student.id),
            "seatId": str(seat.id),
            "shiftIds": [str(shift.id) for shift in shifts],
            "startDate": payload.start_date.isoformat(),
            "endDate": payload.end_date.isoformat(),
        },
        context={"notes": payload.notes},
        request_context=audit_context,
    )
    return allocations


def close_student_allocations(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
    closed_by_user_id: uuid.UUID,
    *,
    effective_date: date | None = None,
    reason: str | None = None,
    audit_context: audit_service.AuditContext | None = None,
) -> list[SeatAllocation]:
    transition_date = effective_date or date.today()
    allocations = repository.lock_active_student_allocations(
        db,
        library_id,
        student_id,
    )
    changed = []
    for allocation in allocations:
        if allocation.end_date < transition_date:
            continue

        old_values = {
            "status": allocation.status.value,
            "endDate": allocation.end_date.isoformat(),
            "closeReason": allocation.close_reason,
        }
        if allocation.start_date >= transition_date:
            allocation.status = AllocationStatus.CANCELLED
            allocation.closed_at = datetime.now(timezone.utc)
        else:
            allocation.end_date = transition_date - timedelta(days=1)
            if allocation.end_date < date.today():
                allocation.status = AllocationStatus.COMPLETED
                allocation.closed_at = datetime.now(timezone.utc)

        allocation.close_reason = (
            reason.strip()
            if reason and reason.strip()
            else "Seat allocation changed by an administrator."
        )
        allocation.closed_by_user_id = closed_by_user_id
        changed.append(allocation)
        audit_service.write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=closed_by_user_id,
            action=(
                f"seat_allocation.{allocation.status.value}"
                if allocation.status != AllocationStatus.ACTIVE
                else "seat_allocation.scheduled_close"
            ),
            entity_type="seat_allocation",
            entity_id=str(allocation.id),
            old_values=old_values,
            new_values={
                "status": allocation.status.value,
                "endDate": allocation.end_date.isoformat(),
                "closeReason": allocation.close_reason,
            },
            request_context=audit_context,
        )
    db.flush()
    return changed


def apply_student_allocation_change(
    db: Session,
    library_id: uuid.UUID,
    student: Student,
    change: StudentSeatAllocationChange,
    changed_by_user_id: uuid.UUID,
    audit_context: audit_service.AuditContext | None = None,
) -> list[SeatAllocation]:
    reason = change.reason or (
        "Seat allocation removed during student update."
        if change.action == "remove"
        else "Seat or shift allocation changed during student update."
    )
    if change.action == "remove":
        close_student_allocations(
            db,
            library_id,
            student.id,
            changed_by_user_id,
            reason=reason,
            audit_context=audit_context,
        )
        return []

    replacement = change.allocation
    if replacement is None:
        raise BusinessRuleError(
            "A replacement allocation is required.",
            code="ALLOCATION_REPLACEMENT_REQUIRED",
        )
    previous_allocations = close_student_allocations(
        db,
        library_id,
        student.id,
        changed_by_user_id,
        effective_date=replacement.start_date,
        reason=reason,
        audit_context=audit_context,
    )
    transfer_group_id = uuid.uuid4()
    return create_student_allocations(
        db,
        library_id,
        student,
        replacement,
        changed_by_user_id,
        previous_allocation_id=(
            previous_allocations[0].id
            if previous_allocations
            else None
        ),
        transfer_group_id=transfer_group_id,
        audit_context=audit_context,
    )


def _actor_summary(actor) -> AllocationActorSummary | None:
    if actor is None:
        return None
    return AllocationActorSummary(id=actor.id, name=actor.full_name)


def allocation_response(
    allocation: SeatAllocation,
) -> SeatAllocationResponse:
    student_name = " ".join(
        (allocation.student.first_name, allocation.student.last_name)
    ).strip()
    return SeatAllocationResponse(
        id=allocation.id,
        library_id=allocation.library_id,
        student=AllocationStudentSummary(
            id=allocation.student_id,
            enrollment_number=allocation.student.enrollment_number,
            name=student_name,
            status=allocation.student.status.value,
        ),
        seat=AllocationSeatSummary(
            id=allocation.seat_id,
            seat_number=(
                allocation.seat_number_snapshot
                or allocation.seat.seat_number
            ),
            floor_id=(
                allocation.floor_id_snapshot
                or allocation.seat.floor_id
            ),
            floor_name=(
                allocation.floor_name_snapshot
                or allocation.seat.floor.name
            ),
        ),
        shift=AllocationShiftSummary(
            id=allocation.shift_id,
            name=allocation.shift_name,
            start_time=allocation.shift_start_time.strftime("%H:%M"),
            end_time=allocation.shift_end_time.strftime("%H:%M"),
            crosses_midnight=allocation.shift_crosses_midnight,
        ),
        start_date=allocation.start_date,
        end_date=allocation.end_date,
        status=allocation.status,
        notes=allocation.notes,
        close_reason=allocation.close_reason,
        allocated_at=allocation.allocated_at,
        closed_at=allocation.closed_at,
        allocated_by=_actor_summary(allocation.allocated_by),
        closed_by=_actor_summary(allocation.closed_by),
        previous_allocation_id=allocation.previous_allocation_id,
        transfer_group_id=allocation.transfer_group_id,
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
) -> tuple[list[SeatAllocationResponse], int]:
    if start_date is not None and end_date is not None:
        _ensure_valid_range(start_date, end_date)
    allocations, total = repository.list_allocations(
        db,
        library_id,
        pagination,
        student_id=student_id,
        seat_id=seat_id,
        shift_id=shift_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    return [allocation_response(item) for item in allocations], total


def create_allocations(
    db: Session,
    library_id: uuid.UUID,
    payload: SeatAllocationCreate,
    allocated_by_user_id: uuid.UUID,
    *,
    audit_context: audit_service.AuditContext | None = None,
) -> SeatAllocationCreateResponse:
    student = repository.get_student(db, library_id, payload.student_id)
    if student is None:
        raise ResourceNotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    allocation_payload = StudentSeatAllocationCreate(
        seat_id=payload.seat_id,
        shift_ids=payload.shift_ids,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    try:
        allocations = create_student_allocations(
            db,
            library_id,
            student,
            allocation_payload,
            allocated_by_user_id,
            audit_context=audit_context,
        )
        db.commit()
        return SeatAllocationCreateResponse(
            allocation_count=len(allocations),
            allocations=[allocation_response(item) for item in allocations],
        )
    except Exception:
        db.rollback()
        raise


def close_allocation(
    db: Session,
    library_id: uuid.UUID,
    allocation_id: uuid.UUID,
    payload: SeatAllocationStatusUpdate,
    closed_by_user_id: uuid.UUID,
    *,
    audit_context: audit_service.AuditContext | None = None,
) -> SeatAllocationResponse:
    allocation = repository.lock_allocation(db, library_id, allocation_id)
    if allocation is None:
        raise ResourceNotFoundError(
            "Seat allocation not found.",
            code="SEAT_ALLOCATION_NOT_FOUND",
        )
    if allocation.status != AllocationStatus.ACTIVE:
        raise ConflictError(
            "Only an active allocation can be completed or cancelled.",
            code="ALLOCATION_ALREADY_CLOSED",
            details={
                "allocationId": str(allocation.id),
                "currentStatus": allocation.status.value,
            },
        )

    effective_end_date = payload.effective_end_date or date.today()
    if effective_end_date > allocation.end_date:
        raise BusinessRuleError(
            "Effective end date cannot be after the allocation end date.",
            code="ALLOCATION_EFFECTIVE_END_INVALID",
        )
    if (
        payload.status == AllocationStatus.COMPLETED
        and (
            effective_end_date < allocation.start_date
            or effective_end_date > date.today()
        )
    ):
        raise BusinessRuleError(
            "A completed allocation must end between its start date and today.",
            code="ALLOCATION_EFFECTIVE_END_INVALID",
        )

    old_values = {
        "status": allocation.status.value,
        "endDate": allocation.end_date.isoformat(),
        "closeReason": allocation.close_reason,
    }
    if effective_end_date >= allocation.start_date:
        allocation.end_date = effective_end_date
    allocation.status = payload.status
    allocation.close_reason = payload.close_reason.strip()
    allocation.closed_by_user_id = closed_by_user_id
    allocation.closed_at = datetime.now(timezone.utc)
    audit_service.write_audit_log(
        db,
        library_id=library_id,
        actor_user_id=closed_by_user_id,
        action=f"seat_allocation.{payload.status.value}",
        entity_type="seat_allocation",
        entity_id=str(allocation.id),
        old_values=old_values,
        new_values={
            "status": allocation.status.value,
            "endDate": allocation.end_date.isoformat(),
            "closeReason": allocation.close_reason,
        },
        request_context=audit_context,
    )
    try:
        db.commit()
        db.refresh(allocation)
        return allocation_response(allocation)
    except Exception:
        db.rollback()
        raise


def student_seat_assignments(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> list[StudentSeatAssignmentResponse]:
    allocations = repository.allocations_for_student(
        db,
        library_id,
        student_id,
    )
    grouped: dict[
        tuple[uuid.UUID, date, date, AllocationStatus],
        list[SeatAllocation],
    ] = defaultdict(list)
    for allocation in allocations:
        grouped[
            (
                allocation.seat_id,
                allocation.start_date,
                allocation.end_date,
                allocation.status,
            )
        ].append(allocation)

    assignments = []
    for group in grouped.values():
        first = group[0]
        assignments.append(
            StudentSeatAssignmentResponse(
                seat_id=first.seat_id,
                seat_number=first.seat.seat_number,
                floor_id=first.seat.floor_id,
                floor_name=first.seat.floor.name,
                shift_ids=[allocation.shift_id for allocation in group],
                shift_names=[allocation.shift_name for allocation in group],
                start_date=first.start_date,
                end_date=first.end_date,
                status=first.status,
                close_reason=first.close_reason,
                previous_allocation_id=first.previous_allocation_id,
                transfer_group_id=first.transfer_group_id,
            )
        )
    return assignments
