"""Library settings contracts."""
from __future__ import annotations

import uuid
from datetime import datetime, time

from pydantic import Field, model_validator

from app.schemas.common import APIModel


class LibrarySettingsUpdate(APIModel):
    library_name: str = Field(min_length=2, max_length=180)
    contact_email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    contact_phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    timezone: str = Field(min_length=1, max_length=64)
    opening_time: time
    closing_time: time
    weekly_off: str = Field(default="none", max_length=16)
    default_monthly_fee: float = Field(ge=0)
    fee_due_day: int = Field(ge=1, le=28)
    payment_grace_days: int = Field(ge=0, le=30)
    receipt_prefix: str = Field(pattern=r"^[A-Za-z0-9]{2,10}$")
    allow_seat_change_requests: bool
    require_seat_request_reason: bool
    whatsapp_reminders_enabled: bool
    notify_pending_payments: bool
    notify_seat_requests: bool
    notify_maintenance_seats: bool
    email_announcement_copy: bool

    @model_validator(mode="after")
    def validate_operating_hours(self):
        if self.closing_time <= self.opening_time:
            raise ValueError("Closing time must be later than opening time.")
        return self


class LibrarySettingsResponse(LibrarySettingsUpdate):
    library_id: uuid.UUID
    updated_at: datetime
