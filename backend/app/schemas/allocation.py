"""Seat availability and allocation contracts."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.models.enums import AllocationStatus, SeatOperationalStatus, SeatType
from app.schemas.common import APIModel


class StudentSeatAllocationCreate(APIModel):
    seat_id: uuid.UUID
    shift_ids: list[uuid.UUID] = Field(min_length=1, max_length=24)
    start_date: date
    end_date: date
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("shift_ids")
    @classmethod
    def reject_duplicate_shifts(
        cls,
        shift_ids: list[uuid.UUID],
    ) -> list[uuid.UUID]:
        if len(set(shift_ids)) != len(shift_ids):
            raise ValueError("Each selected shift must be unique.")
        return shift_ids

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("Allocation end date cannot be earlier than start date.")
        return self


class SeatAllocationCreate(StudentSeatAllocationCreate):
    student_id: uuid.UUID


class StudentSeatAllocationChange(APIModel):
    action: Literal["replace", "remove"]
    allocation: StudentSeatAllocationCreate | None = None
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_action_payload(self):
        if self.action == "replace" and self.allocation is None:
            raise ValueError("A replacement allocation is required.")
        if self.action == "remove" and self.allocation is not None:
            raise ValueError("A remove action cannot include an allocation.")
        return self


class SeatAvailabilityBlockerResponse(APIModel):
    allocation_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    shift_id: uuid.UUID
    shift_name: str
    shift_start_time: str
    shift_end_time: str
    start_date: date
    end_date: date


class SeatAvailabilitySeatResponse(APIModel):
    seat_id: uuid.UUID
    seat_number: str
    floor_id: uuid.UUID
    floor_name: str
    floor: int | None
    seat_type: SeatType
    physical_status: SeatOperationalStatus
    status: Literal[
        "available",
        "allotted",
        "reserved",
        "blocked",
        "maintenance",
        "physically_blocked",
    ]
    is_available: bool
    status_note: str | None = None
    blockers: list[SeatAvailabilityBlockerResponse] = Field(default_factory=list)


class SeatAvailabilitySummaryResponse(APIModel):
    available: int = 0
    allotted: int = 0
    reserved: int = 0
    blocked: int = 0
    maintenance: int = 0
    physically_blocked: int = 0


class SeatAvailabilityResponse(APIModel):
    shift_ids: list[uuid.UUID]
    start_date: date
    end_date: date
    total_seats: int
    available_seat_count: int
    summary: SeatAvailabilitySummaryResponse
    seats: list[SeatAvailabilitySeatResponse]


class StudentSeatAssignmentResponse(APIModel):
    seat_id: uuid.UUID
    seat_number: str
    floor_id: uuid.UUID
    floor_name: str
    shift_ids: list[uuid.UUID]
    shift_names: list[str]
    start_date: date
    end_date: date
    status: AllocationStatus
    close_reason: str | None = None
    previous_allocation_id: uuid.UUID | None = None
    transfer_group_id: uuid.UUID | None = None


class AllocationStudentSummary(APIModel):
    id: uuid.UUID
    enrollment_number: str
    name: str
    status: str


class AllocationSeatSummary(APIModel):
    id: uuid.UUID
    seat_number: str
    floor_id: uuid.UUID
    floor_name: str


class AllocationShiftSummary(APIModel):
    id: uuid.UUID
    name: str
    start_time: str
    end_time: str
    crosses_midnight: bool


class AllocationActorSummary(APIModel):
    id: uuid.UUID
    name: str


class SeatAllocationResponse(APIModel):
    id: uuid.UUID
    library_id: uuid.UUID
    student: AllocationStudentSummary
    seat: AllocationSeatSummary
    shift: AllocationShiftSummary
    start_date: date
    end_date: date
    status: AllocationStatus
    notes: str | None
    close_reason: str | None
    allocated_at: datetime
    closed_at: datetime | None
    allocated_by: AllocationActorSummary | None = None
    closed_by: AllocationActorSummary | None = None
    previous_allocation_id: uuid.UUID | None = None
    transfer_group_id: uuid.UUID | None = None


class SeatAllocationCreateResponse(APIModel):
    allocation_count: int
    allocations: list[SeatAllocationResponse]


class SeatAllocationStatusUpdate(APIModel):
    status: Literal[AllocationStatus.COMPLETED, AllocationStatus.CANCELLED]
    effective_end_date: date | None = None
    close_reason: str = Field(min_length=1, max_length=2000)
