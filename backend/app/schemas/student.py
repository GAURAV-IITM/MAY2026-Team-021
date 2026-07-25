"""Student management and student account invitation schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import Field, model_validator

from app.models.enums import InvitationStatus, StudentStatus
from app.schemas.common import APIModel


class StudentCreate(APIModel):
    enrollment_number: str | None = Field(default=None, min_length=1, max_length=64)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone: str = Field(min_length=7, max_length=32)
    address: str | None = Field(default=None, max_length=2000)
    guardian_name: str | None = Field(default=None, max_length=160)
    guardian_phone: str | None = Field(default=None, max_length=32)
    date_of_birth: date | None = None
    preferred_language: str = Field(default="en", min_length=2, max_length=16)
    joining_date: date = Field(default_factory=date.today)
    fee_amount: float = Field(ge=0)
    status: StudentStatus = StudentStatus.ACTIVE
    notes: str | None = Field(default=None, max_length=4000)
    send_invitation: bool = True


class StudentUpdate(APIModel):
    enrollment_number: str | None = Field(default=None, min_length=1, max_length=64)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(
        default=None,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
    )
    phone: str | None = Field(default=None, min_length=7, max_length=32)
    address: str | None = Field(default=None, max_length=2000)
    guardian_name: str | None = Field(default=None, max_length=160)
    guardian_phone: str | None = Field(default=None, max_length=32)
    date_of_birth: date | None = None
    preferred_language: str | None = Field(default=None, min_length=2, max_length=16)
    joining_date: date | None = None
    fee_amount: float | None = Field(default=None, ge=0)
    status: StudentStatus | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        required_when_present = {
            "enrollment_number",
            "first_name",
            "last_name",
            "email",
            "phone",
            "preferred_language",
            "joining_date",
            "fee_amount",
            "status",
        }
        null_fields = sorted(
            field
            for field in required_when_present
            if field in self.model_fields_set and getattr(self, field) is None
        )
        if null_fields:
            raise ValueError(
                f"These fields cannot be null: {', '.join(null_fields)}."
            )
        return self


class StudentStatusUpdate(APIModel):
    status: StudentStatus


class StudentResponse(APIModel):
    id: uuid.UUID
    enrollment_number: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str | None
    guardian_name: str | None
    guardian_phone: str | None
    date_of_birth: date | None
    preferred_language: str
    joining_date: date
    left_on: date | None
    fee_amount: float
    status: StudentStatus
    notes: str | None
    portal_access_status: str
    invitation_status: InvitationStatus | None = None
    invitation_expires_at: datetime | None = None
    invitation_setup_url: str | None = None
    seat_number: str | None = None
    active_shifts: list[str] = Field(default_factory=list)
    fee_status: str | None = None
    fee_due_date: date | None = None
    created_at: datetime
    updated_at: datetime


class StudentInvitationResponse(APIModel):
    student_id: uuid.UUID
    email: str
    status: InvitationStatus
    expires_at: datetime
    setup_url: str
    delivery_method: str = "manual"
