from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import Field

from app.models.enums import (
    AllocationStatus,
    AnnouncementCategory,
    AnnouncementPriority,
    FeeStatus,
    PaymentMethod,
    SeatRequestStatus,
    SeatType,
)
from app.schemas.common import APIModel

DataT = TypeVar("DataT")


# Seat allocations /me schemas
class StudentSeatSummary(APIModel):
    id: uuid.UUID
    seat_number: str
    floor: str | int
    seat_type: SeatType
    notes: str | None = None


class StudentAllocationItem(APIModel):
    id: uuid.UUID
    seat_id: uuid.UUID
    seat_number: str
    floor: str | int | None
    shift_id: uuid.UUID
    shift_name: str
    start_time: str
    end_time: str
    start_date: date
    end_date: date
    status: AllocationStatus
    allocated_at: datetime


class StudentSeatAllocationsResponse(APIModel):
    seat: StudentSeatSummary | None = None
    allocations: list[StudentAllocationItem] = Field(default_factory=list)


# Fees /me schemas
class StudentTransactionItem(APIModel):
    id: uuid.UUID
    amount: Decimal
    method: PaymentMethod
    paid_at: datetime


class StudentFeeItem(APIModel):
    id: uuid.UUID
    billing_month: str  # YYYY-MM
    due_date: date
    total_amount: Decimal
    paid_amount: Decimal
    remaining_balance: Decimal
    status: FeeStatus
    transactions: list[StudentTransactionItem] = Field(default_factory=list)


class StudentFeeSummary(APIModel):
    current_payment: StudentFeeItem | None = None
    payments: list[StudentFeeItem] = Field(default_factory=list)
    total_paid: Decimal
    total_outstanding: Decimal
    paid_count: int
    unpaid_count: int
    next_due_date: date | None = None


class StudentFeesResponse(APIModel):
    fee_summary: StudentFeeSummary


# Seat change requests schemas
class StudentSeatRequestListItem(APIModel):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    student_email: str
    library_id: uuid.UUID
    library_name: str
    current_seat_number: str | None = None
    preferred_seat_number: str | None = None
    preferred_floor: str | int | None = None
    preferred_shift_id: uuid.UUID
    preferred_shift_name: str
    reason: str
    status: SeatRequestStatus
    admin_note: str | None = None
    submitted_at: datetime
    resolved_at: datetime | None = None
    reviewed_by: dict[str, Any] | None = None


class StudentSeatRequestsResponse(APIModel):
    requests: list[StudentSeatRequestListItem] = Field(default_factory=list)
    shifts: list[dict[str, Any]] = Field(default_factory=list)


class StudentSeatRequestCreate(APIModel):
    preferred_seat_id: uuid.UUID | None = None
    preferred_floor_id: uuid.UUID | None = None
    preferred_shift_id: uuid.UUID
    reason: str = Field(min_length=15)


class StudentSeatRequestCancel(APIModel):
    reason: str | None = Field(default=None)


# Announcements /feed schemas
class StudentAnnouncementItem(APIModel):
    id: uuid.UUID
    title: str
    body: str
    category: AnnouncementCategory
    priority: AnnouncementPriority
    published_at: datetime
    expires_at: datetime | None = None
    is_read: bool = False


class StudentAnnouncementsResponse(APIModel):
    announcements: list[StudentAnnouncementItem] = Field(default_factory=list)
