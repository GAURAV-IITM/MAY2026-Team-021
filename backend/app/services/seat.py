"""Physical floor, seat, and shift management use cases."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, time, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, ResourceNotFoundError
from app.models.enums import AllocationStatus, SeatOperationalStatus
from app.models.seat import Floor, Seat, SeatStatusEvent, Shift
from app.repositories import seat as repository
from app.schemas.seat import (
    BulkSeatResult,
    FloorCreate,
    FloorResponse,
    FloorUpdate,
    SeatCreate,
    SeatResponse,
    SeatStatusUpdate,
    SeatUpdate,
    ShiftAvailabilityResponse,
    ShiftConflict,
    ShiftCreate,
    ShiftResponse,
    ShiftSelectionResult,
    ShiftUpdate,
)


def _floor_response(db: Session, floor: Floor) -> FloorResponse:
    return FloorResponse(
        id=floor.id,
        name=floor.name,
        code=floor.code,
        level_number=floor.level_number,
        sort_order=floor.sort_order,
        is_active=floor.is_active,
        seat_count=repository.floor_seat_count(db, floor.library_id, floor.id),
        created_at=floor.created_at,
        updated_at=floor.updated_at,
    )


def list_floors(db: Session, library_id: uuid.UUID) -> list[FloorResponse]:
    return [
        _floor_response(db, floor)
        for floor in repository.list_floors(db, library_id)
    ]


def _ensure_floor_code(
    db: Session,
    library_id: uuid.UUID,
    code: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> None:
    if repository.find_floor_code(
        db,
        library_id,
        code,
        exclude_id=exclude_id,
    ):
        raise ConflictError(
            "A floor with this code already exists.",
            code="FLOOR_CODE_EXISTS",
        )


def create_floor(
    db: Session,
    library_id: uuid.UUID,
    payload: FloorCreate,
) -> FloorResponse:
    code = payload.code.strip().upper()
    _ensure_floor_code(db, library_id, code)
    floor = Floor(
        library_id=library_id,
        name=payload.name.strip(),
        code=code,
        level_number=payload.level_number,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(floor)
    try:
        db.commit()
        db.refresh(floor)
        return _floor_response(db, floor)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The floor conflicts with an existing record.",
            code="FLOOR_CONFLICT",
        ) from exc


def update_floor(
    db: Session,
    library_id: uuid.UUID,
    floor_id: uuid.UUID,
    payload: FloorUpdate,
) -> FloorResponse:
    floor = repository.get_floor(db, library_id, floor_id)
    if floor is None:
        raise ResourceNotFoundError("Floor not found.", code="FLOOR_NOT_FOUND")
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if "code" in changes:
        changes["code"] = changes["code"].strip().upper()
        _ensure_floor_code(
            db,
            library_id,
            changes["code"],
            exclude_id=floor.id,
        )
    if "name" in changes:
        changes["name"] = changes["name"].strip()
    for field, value in changes.items():
        setattr(floor, field, value)
    db.commit()
    db.refresh(floor)
    return _floor_response(db, floor)


def delete_floor(
    db: Session,
    library_id: uuid.UUID,
    floor_id: uuid.UUID,
) -> None:
    floor = repository.get_floor(db, library_id, floor_id)
    if floor is None:
        raise ResourceNotFoundError("Floor not found.", code="FLOOR_NOT_FOUND")
    if repository.floor_seat_count(db, library_id, floor_id):
        raise ConflictError(
            "Move or delete the seats on this floor before deleting it.",
            code="FLOOR_HAS_SEATS",
        )
    floor.deleted_at = datetime.now(timezone.utc)
    floor.is_active = False
    db.commit()


def _shift_response(shift: Shift) -> ShiftResponse:
    return ShiftResponse(
        id=shift.id,
        name=shift.name,
        start_time=shift.start_time.strftime("%H:%M"),
        end_time=shift.end_time.strftime("%H:%M"),
        crosses_midnight=shift.crosses_midnight,
        is_default=shift.is_default,
        is_enabled=shift.is_active,
        created_at=shift.created_at,
        updated_at=shift.updated_at,
    )


def list_shifts(
    db: Session,
    library_id: uuid.UUID,
    *,
    include_inactive: bool = True,
) -> list[ShiftResponse]:
    return [
        _shift_response(shift)
        for shift in repository.list_shifts(
            db,
            library_id,
            include_inactive=include_inactive,
        )
    ]


def _allocation_map(db: Session, library_id: uuid.UUID, seats: list[Seat]):
    allocations = repository.active_allocations_for_seats(
        db,
        library_id,
        [seat.id for seat in seats],
    )
    by_seat = defaultdict(list)
    for allocation in allocations:
        by_seat[allocation.seat_id].append(allocation)
    return by_seat


def _seat_response(
    seat: Seat,
    shifts: list[Shift],
    allocations: list,
) -> SeatResponse:
    today = date.today()
    current_allocations = [
        allocation
        for allocation in allocations
        if allocation.status == AllocationStatus.ACTIVE
        and allocation.start_date <= today <= allocation.end_date
    ]
    shift_availability = []
    for shift in shifts:
        status = "available"
        if seat.operational_status != SeatOperationalStatus.AVAILABLE:
            status = seat.operational_status.value
        else:
            shift_allocations = [
                allocation
                for allocation in allocations
                if allocation.shift_id == shift.id
            ]
            if any(
                allocation.start_date <= today <= allocation.end_date
                for allocation in shift_allocations
            ):
                status = "occupied"
            elif any(allocation.start_date > today for allocation in shift_allocations):
                status = "reserved"
        shift_availability.append(
            ShiftAvailabilityResponse(
                shift_id=shift.id,
                shift_name=shift.name,
                status=status,
            )
        )
    occupied_shift_ids = {
        allocation.shift_id for allocation in current_allocations
    }
    return SeatResponse(
        id=seat.id,
        seat_number=seat.seat_number,
        floor_id=seat.floor_id,
        floor_name=seat.floor.name,
        floor=seat.floor.level_number,
        seat_type=seat.seat_type,
        physical_status=seat.operational_status,
        status=seat.operational_status,
        status_note=seat.status_note,
        current_occupancy="Occupied" if current_allocations else "Available",
        is_occupied=bool(current_allocations),
        occupied_shift_count=len(occupied_shift_ids),
        notes=seat.notes,
        is_active=seat.is_active,
        active_shifts=[str(shift.id) for shift in shifts],
        shift_availability=shift_availability,
        created_at=seat.created_at,
        updated_at=seat.updated_at,
    )


def list_seats(
    db: Session,
    library_id: uuid.UUID,
    *,
    search: str | None = None,
    floor_id: uuid.UUID | None = None,
    status: SeatOperationalStatus | None = None,
) -> tuple[list[SeatResponse], list[ShiftResponse]]:
    seats = repository.list_seats(
        db,
        library_id,
        search=search,
        floor_id=floor_id,
        status=status,
    )
    shifts = repository.list_shifts(db, library_id, include_inactive=False)
    allocations = _allocation_map(db, library_id, seats)
    return (
        [
            _seat_response(seat, shifts, allocations[seat.id])
            for seat in seats
        ],
        [_shift_response(shift) for shift in shifts],
    )


def get_seat(
    db: Session,
    library_id: uuid.UUID,
    seat_id: uuid.UUID,
) -> SeatResponse:
    seat = repository.get_seat(db, library_id, seat_id)
    if seat is None:
        raise ResourceNotFoundError("Seat not found.", code="SEAT_NOT_FOUND")
    shifts = repository.list_shifts(db, library_id, include_inactive=False)
    allocations = repository.active_allocations_for_seats(
        db,
        library_id,
        [seat.id],
    )
    return _seat_response(seat, shifts, allocations)


def _ensure_seat_number(
    db: Session,
    library_id: uuid.UUID,
    seat_number: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> None:
    if repository.find_seat_number(
        db,
        library_id,
        seat_number,
        exclude_id=exclude_id,
    ):
        raise ConflictError(
            "A seat with this number already exists.",
            code="SEAT_NUMBER_EXISTS",
        )


def _require_floor(
    db: Session,
    library_id: uuid.UUID,
    floor_id: uuid.UUID,
) -> Floor:
    floor = repository.get_floor(db, library_id, floor_id)
    if floor is None:
        raise ResourceNotFoundError("Floor not found.", code="FLOOR_NOT_FOUND")
    if not floor.is_active:
        raise BusinessRuleError(
            "Seats can only be assigned to an active floor.",
            code="FLOOR_INACTIVE",
        )
    return floor


def create_seat(
    db: Session,
    library_id: uuid.UUID,
    payload: SeatCreate,
    changed_by_user_id: uuid.UUID,
) -> SeatResponse:
    number = payload.seat_number.strip().upper()
    _ensure_seat_number(db, library_id, number)
    floor = _require_floor(db, library_id, payload.floor_id)
    seat = Seat(
        library_id=library_id,
        floor_id=floor.id,
        seat_number=number,
        seat_type=payload.seat_type,
        operational_status=payload.status,
        status_note=payload.status_note,
        notes=payload.notes,
    )
    db.add(seat)
    try:
        db.flush()
        db.add(
            SeatStatusEvent(
                library_id=library_id,
                seat_id=seat.id,
                from_status=None,
                to_status=payload.status,
                reason=payload.status_note or "Seat created.",
                changed_by_user_id=changed_by_user_id,
            )
        )
        db.commit()
        return get_seat(db, library_id, seat.id)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The seat conflicts with an existing record.",
            code="SEAT_CONFLICT",
        ) from exc


def _validate_can_make_unavailable(
    db: Session,
    library_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
    status: SeatOperationalStatus,
) -> None:
    if (
        status != SeatOperationalStatus.AVAILABLE
        and repository.has_active_allocations(
            db,
            library_id,
            seat_ids=seat_ids,
        )
    ):
        raise ConflictError(
            "Seats with current or future active allocations cannot be made unavailable.",
            code="SEAT_HAS_ACTIVE_ALLOCATIONS",
        )


def _change_seat_status(
    db: Session,
    seat: Seat,
    status: SeatOperationalStatus,
    *,
    reason: str | None,
    changed_by_user_id: uuid.UUID,
) -> None:
    previous = seat.operational_status
    if previous == status and seat.status_note == reason:
        return
    seat.operational_status = status
    seat.status_note = reason
    db.add(
        SeatStatusEvent(
            library_id=seat.library_id,
            seat_id=seat.id,
            from_status=previous,
            to_status=status,
            reason=reason,
            changed_by_user_id=changed_by_user_id,
        )
    )


def update_seat(
    db: Session,
    library_id: uuid.UUID,
    seat_id: uuid.UUID,
    payload: SeatUpdate,
    changed_by_user_id: uuid.UUID,
) -> SeatResponse:
    seat = repository.get_seat(db, library_id, seat_id)
    if seat is None:
        raise ResourceNotFoundError("Seat not found.", code="SEAT_NOT_FOUND")
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if "seat_number" in changes:
        changes["seat_number"] = changes["seat_number"].strip().upper()
        _ensure_seat_number(
            db,
            library_id,
            changes["seat_number"],
            exclude_id=seat.id,
        )
    if "floor_id" in changes:
        _require_floor(db, library_id, changes["floor_id"])
    if "status" in changes:
        _validate_can_make_unavailable(
            db,
            library_id,
            [seat.id],
            changes["status"],
        )
        _change_seat_status(
            db,
            seat,
            changes.pop("status"),
            reason=changes.get("status_note"),
            changed_by_user_id=changed_by_user_id,
        )
    for field, value in changes.items():
        setattr(seat, field, value)
    db.commit()
    return get_seat(db, library_id, seat.id)


def change_seat_status(
    db: Session,
    library_id: uuid.UUID,
    seat_id: uuid.UUID,
    payload: SeatStatusUpdate,
    changed_by_user_id: uuid.UUID,
) -> SeatResponse:
    seat = repository.get_seat(db, library_id, seat_id)
    if seat is None:
        raise ResourceNotFoundError("Seat not found.", code="SEAT_NOT_FOUND")
    _validate_can_make_unavailable(db, library_id, [seat.id], payload.status)
    _change_seat_status(
        db,
        seat,
        payload.status,
        reason=payload.reason,
        changed_by_user_id=changed_by_user_id,
    )
    db.commit()
    return get_seat(db, library_id, seat.id)


def bulk_change_status(
    db: Session,
    library_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
    payload: SeatStatusUpdate,
    changed_by_user_id: uuid.UUID,
) -> BulkSeatResult:
    unique_ids = list(dict.fromkeys(seat_ids))
    seats = [repository.get_seat(db, library_id, seat_id) for seat_id in unique_ids]
    if any(seat is None for seat in seats):
        raise ResourceNotFoundError(
            "One or more selected seats were not found.",
            code="SEAT_NOT_FOUND",
        )
    _validate_can_make_unavailable(db, library_id, unique_ids, payload.status)
    for seat in seats:
        _change_seat_status(
            db,
            seat,
            payload.status,
            reason=payload.reason,
            changed_by_user_id=changed_by_user_id,
        )
    db.commit()
    return BulkSeatResult(
        seats=[get_seat(db, library_id, seat.id) for seat in seats],
    )


def _validate_can_delete_seats(
    db: Session,
    library_id: uuid.UUID,
    seats: list[Seat],
) -> None:
    if repository.has_active_allocations(
        db,
        library_id,
        seat_ids=[seat.id for seat in seats],
    ):
        raise ConflictError(
            "Seats with current or future active allocations cannot be deleted.",
            code="SEAT_HAS_ACTIVE_ALLOCATIONS",
        )


def delete_seats(
    db: Session,
    library_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
) -> list[uuid.UUID]:
    unique_ids = list(dict.fromkeys(seat_ids))
    seats = [repository.get_seat(db, library_id, seat_id) for seat_id in unique_ids]
    if any(seat is None for seat in seats):
        raise ResourceNotFoundError(
            "One or more selected seats were not found.",
            code="SEAT_NOT_FOUND",
        )
    _validate_can_delete_seats(db, library_id, seats)
    now = datetime.now(timezone.utc)
    for seat in seats:
        seat.deleted_at = now
        seat.is_active = False
    db.commit()
    return unique_ids


def _minute(value: time) -> int:
    return value.hour * 60 + value.minute


def _segments(start: time, end: time) -> list[tuple[int, int]]:
    start_minute, end_minute = _minute(start), _minute(end)
    if end_minute > start_minute:
        return [(start_minute, end_minute)]
    return [(start_minute, 24 * 60), (0, end_minute)]


def shifts_overlap(first: Shift, second: Shift) -> bool:
    return any(
        first_start < second_end and second_start < first_end
        for first_start, first_end in _segments(first.start_time, first.end_time)
        for second_start, second_end in _segments(second.start_time, second.end_time)
    )


def _ensure_shift_name(
    db: Session,
    library_id: uuid.UUID,
    name: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> None:
    if repository.find_shift_name(
        db,
        library_id,
        name,
        exclude_id=exclude_id,
    ):
        raise ConflictError(
            "A shift with this name already exists.",
            code="SHIFT_NAME_EXISTS",
        )


def create_shift(
    db: Session,
    library_id: uuid.UUID,
    payload: ShiftCreate,
) -> ShiftResponse:
    name = payload.name.strip()
    _ensure_shift_name(db, library_id, name)
    shift = Shift(
        library_id=library_id,
        name=name,
        start_time=payload.start_time,
        end_time=payload.end_time,
        crosses_midnight=payload.end_time <= payload.start_time,
        is_active=payload.is_enabled,
    )
    db.add(shift)
    try:
        db.commit()
        db.refresh(shift)
        return _shift_response(shift)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The shift conflicts with an existing record.",
            code="SHIFT_CONFLICT",
        ) from exc


def update_shift(
    db: Session,
    library_id: uuid.UUID,
    shift_id: uuid.UUID,
    payload: ShiftUpdate,
) -> ShiftResponse:
    shift = repository.get_shift(db, library_id, shift_id)
    if shift is None:
        raise ResourceNotFoundError("Shift not found.", code="SHIFT_NOT_FOUND")
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if "name" in changes:
        changes["name"] = changes["name"].strip()
        _ensure_shift_name(
            db,
            library_id,
            changes["name"],
            exclude_id=shift.id,
        )
    if "is_enabled" in changes:
        changes["is_active"] = changes.pop("is_enabled")
    start = changes.get("start_time", shift.start_time)
    end = changes.get("end_time", shift.end_time)
    if start == end:
        raise BusinessRuleError(
            "Shift start and end time must be different.",
            code="SHIFT_TIMING_INVALID",
        )
    changes["crosses_midnight"] = end <= start
    for field, value in changes.items():
        setattr(shift, field, value)
    db.commit()
    db.refresh(shift)
    return _shift_response(shift)


def delete_shift(
    db: Session,
    library_id: uuid.UUID,
    shift_id: uuid.UUID,
) -> None:
    shift = repository.get_shift(db, library_id, shift_id)
    if shift is None:
        raise ResourceNotFoundError("Shift not found.", code="SHIFT_NOT_FOUND")
    if shift.is_default:
        raise ConflictError(
            "Default shifts can be disabled but cannot be deleted.",
            code="DEFAULT_SHIFT_DELETE_NOT_ALLOWED",
        )
    if repository.has_active_allocations(db, library_id, shift_id=shift.id):
        raise ConflictError(
            "A shift with active allocations cannot be deleted.",
            code="SHIFT_HAS_ACTIVE_ALLOCATIONS",
        )
    shift.deleted_at = datetime.now(timezone.utc)
    shift.is_active = False
    db.commit()


def validate_shift_selection(
    db: Session,
    library_id: uuid.UUID,
    shift_ids: list[uuid.UUID],
) -> ShiftSelectionResult:
    unique_ids = list(dict.fromkeys(shift_ids))
    shifts = [
        repository.get_shift(db, library_id, shift_id)
        for shift_id in unique_ids
    ]
    if any(shift is None or not shift.is_active for shift in shifts):
        raise BusinessRuleError(
            "Every selected shift must exist and be active in this library.",
            code="SHIFT_SELECTION_INVALID",
        )
    conflicts = []
    for index, first in enumerate(shifts):
        for second in shifts[index + 1 :]:
            if shifts_overlap(first, second):
                conflicts.append(
                    ShiftConflict(
                        first_shift_id=first.id,
                        first_shift_name=first.name,
                        second_shift_id=second.id,
                        second_shift_name=second.name,
                    )
                )
    return ShiftSelectionResult(valid=not conflicts, conflicts=conflicts)
