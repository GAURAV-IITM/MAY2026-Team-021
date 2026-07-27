"""Physical floor, seat, and shift management schemas."""
from __future__ import annotations

import uuid
from datetime import datetime, time

from pydantic import Field, model_validator

from app.models.enums import SeatOperationalStatus, SeatType
from app.schemas.common import APIModel


class FloorCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=32)
    level_number: int | None = None
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class FloorUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=32)
    level_number: int | None = None
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class FloorResponse(APIModel):
    id: uuid.UUID
    name: str
    code: str
    level_number: int | None
    sort_order: int
    is_active: bool
    seat_count: int
    created_at: datetime
    updated_at: datetime


class SeatCreate(APIModel):
    seat_number: str = Field(min_length=1, max_length=64)
    floor_id: uuid.UUID
    seat_type: SeatType = SeatType.STANDARD
    status: SeatOperationalStatus = SeatOperationalStatus.AVAILABLE
    status_note: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=4000)


class SeatUpdate(APIModel):
    seat_number: str | None = Field(default=None, min_length=1, max_length=64)
    floor_id: uuid.UUID | None = None
    seat_type: SeatType | None = None
    status: SeatOperationalStatus | None = None
    status_note: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=4000)


class SeatStatusUpdate(APIModel):
    status: SeatOperationalStatus
    reason: str | None = Field(default=None, max_length=2000)


class BulkSeatStatusUpdate(SeatStatusUpdate):
    seat_ids: list[uuid.UUID] = Field(min_length=1, max_length=500)


class BulkSeatDeleteRequest(APIModel):
    seat_ids: list[uuid.UUID] = Field(min_length=1, max_length=500)


class ShiftAvailabilityResponse(APIModel):
    shift_id: uuid.UUID
    shift_name: str
    status: str
    is_partial_block: bool = False


class SeatResponse(APIModel):
    id: uuid.UUID
    seat_number: str
    floor_id: uuid.UUID
    floor_name: str
    floor: int | None
    seat_type: SeatType
    physical_status: SeatOperationalStatus
    status: SeatOperationalStatus
    status_note: str | None
    current_occupancy: str
    is_occupied: bool
    occupied_shift_count: int
    notes: str | None
    is_active: bool
    active_shifts: list[str] = Field(default_factory=list)
    shift_availability: list[ShiftAvailabilityResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BulkSeatResult(APIModel):
    seats: list[SeatResponse] = Field(default_factory=list)
    deleted_seat_ids: list[uuid.UUID] = Field(default_factory=list)


class SeatListResponse(APIModel):
    seats: list[SeatResponse]
    shifts: list["ShiftResponse"]


class ShiftCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    start_time: time
    end_time: time
    is_enabled: bool = True

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time == self.end_time:
            raise ValueError("Shift start and end time must be different.")
        return self


class ShiftUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_time: time | None = None
    end_time: time | None = None
    is_enabled: bool | None = None


class ShiftStatusUpdate(APIModel):
    is_enabled: bool


class ShiftSelectionValidation(APIModel):
    shift_ids: list[uuid.UUID] = Field(min_length=1, max_length=24)


class ShiftConflict(APIModel):
    first_shift_id: uuid.UUID
    first_shift_name: str
    second_shift_id: uuid.UUID
    second_shift_name: str


class ShiftSelectionResult(APIModel):
    valid: bool
    conflicts: list[ShiftConflict] = Field(default_factory=list)


class ShiftResponse(APIModel):
    id: uuid.UUID
    name: str
    start_time: str
    end_time: str
    crosses_midnight: bool
    is_default: bool
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
