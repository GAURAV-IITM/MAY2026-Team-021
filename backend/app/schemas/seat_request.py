"""Owner seat-change request review contracts."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.models.enums import AllocationStatus, SeatRequestStatus
from app.schemas.common import APIModel, PaginationMeta


class SeatRequestStudentSummary(APIModel):
    id: uuid.UUID
    enrollment_number: str
    name: str


class SeatRequestSeatSummary(APIModel):
    id: uuid.UUID
    seat_number: str


class SeatRequestFloorSummary(APIModel):
    id: uuid.UUID
    name: str
    level_number: int | None = None


class SeatRequestShiftSummary(APIModel):
    id: uuid.UUID
    name: str
    start_time: str
    end_time: str


class SeatRequestAllocationSummary(APIModel):
    id: uuid.UUID
    seat_id: uuid.UUID
    seat_number: str
    floor_id: uuid.UUID | None
    floor_name: str | None
    shift_id: uuid.UUID
    shift_name: str
    start_date: date
    end_date: date
    status: AllocationStatus


class SeatRequestReviewerSummary(APIModel):
    id: uuid.UUID
    name: str


class SeatChangeRequestResponse(APIModel):
    id: uuid.UUID
    request_number: str
    status: SeatRequestStatus
    student: SeatRequestStudentSummary
    current_allocation: SeatRequestAllocationSummary | None
    preferred_seat: SeatRequestSeatSummary | None
    preferred_floor: SeatRequestFloorSummary | None
    preferred_shift: SeatRequestShiftSummary
    reason: str
    submitted_at: datetime
    reviewed_by: SeatRequestReviewerSummary | None
    reviewed_at: datetime | None
    review_note: str | None
    resulting_allocation_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class SeatRequestSummary(APIModel):
    total: int = Field(ge=0)
    pending: int = Field(ge=0)
    approved: int = Field(ge=0)
    rejected: int = Field(ge=0)
    cancelled: int = Field(ge=0)


class SeatRequestListResponse(APIModel):
    message: str
    data: list[SeatChangeRequestResponse]
    meta: PaginationMeta
    summary: SeatRequestSummary


class SeatRequestReview(APIModel):
    decision: Literal["approved", "rejected"]
    review_note: str | None = Field(default=None, max_length=2000)

    @field_validator("review_note", mode="before")
    @classmethod
    def trim_note(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip() or None

    @model_validator(mode="after")
    def require_rejection_note(self):
        if self.decision == "rejected" and (
            self.review_note is None or len(self.review_note) < 5
        ):
            raise ValueError(
                "A rejection note of at least 5 characters is required."
            )
        return self
