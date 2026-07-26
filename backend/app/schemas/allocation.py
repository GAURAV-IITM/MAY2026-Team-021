"""Seat availability and allocation contracts."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.models.enums import AllocationStatus
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
    status: Literal["available", "allotted", "reserved", "blocked", "maintenance"]
    is_available: bool
    status_note: str | None = None
    blockers: list[SeatAvailabilityBlockerResponse] = Field(default_factory=list)


class SeatAvailabilityResponse(APIModel):
    shift_ids: list[uuid.UUID]
    start_date: date
    end_date: date
    total_seats: int
    available_seat_count: int
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
