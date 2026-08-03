"""Super Admin platform-library API contracts."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import ConfigDict, Field, field_validator

from app.models.enums import LibraryStatus
from app.schemas.common import APIModel, PaginationMeta


EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


class PlatformOwnerSummary(APIModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None = None


class PlatformLibraryBase(APIModel):
    name: str = Field(min_length=2, max_length=180)
    contact_email: str = Field(pattern=EMAIL_PATTERN, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=32)
    address_line: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=64)

    @field_validator(
        "name",
        "contact_email",
        "contact_phone",
        "address_line",
        "city",
        "state",
        "postal_code",
        "timezone",
        mode="before",
    )
    @classmethod
    def trim_strings(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip()


class PlatformLibraryCreate(PlatformLibraryBase):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Central Study Library",
                    "code": "CSL",
                    "contactEmail": "library@example.com",
                    "contactPhone": "+91 9999999999",
                    "addressLine": "1 Reading Lane",
                    "city": "Pune",
                    "state": "Maharashtra",
                    "postalCode": "411001",
                    "timezone": "Asia/Kolkata",
                    "ownerId": None,
                }
            ]
        },
    )

    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    owner_id: uuid.UUID | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value


class PlatformLibraryUpdate(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )

    name: str | None = Field(default=None, min_length=2, max_length=180)
    contact_email: str | None = Field(default=None, pattern=EMAIL_PATTERN, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=32)
    address_line: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    expected_updated_at: datetime | None = None

    @field_validator(
        "name",
        "contact_email",
        "contact_phone",
        "address_line",
        "city",
        "state",
        "postal_code",
        "timezone",
        mode="before",
    )
    @classmethod
    def trim_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class PlatformLibraryStatusUpdate(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )

    status: LibraryStatus
    reason: str | None = Field(default=None, max_length=500)
    expected_updated_at: datetime | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def trim_reason(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip() or None


class PlatformLibraryOwnerAssign(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )

    owner_id: uuid.UUID
    expected_updated_at: datetime | None = None


class PlatformLibraryResponse(APIModel):
    id: uuid.UUID
    code: str
    name: str
    contact_email: str
    contact_phone: str | None
    address_line: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    timezone: str
    status: LibraryStatus
    owner: PlatformOwnerSummary | None
    student_count: int = Field(ge=0)
    seat_count: int = Field(ge=0)
    membership_count: int = Field(ge=0)
    suspended_at: datetime | None
    suspension_reason: str | None
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime | None


class PlatformLibrarySummary(APIModel):
    total: int = Field(ge=0)
    active: int = Field(ge=0)
    pending: int = Field(ge=0)
    suspended: int = Field(ge=0)


class PlatformLibraryListResponse(APIModel):
    message: str
    data: list[PlatformLibraryResponse]
    meta: PaginationMeta
    summary: PlatformLibrarySummary


class PlatformLibrarySuccessResponse(APIModel):
    message: str
    data: PlatformLibraryResponse


class PlatformOwnerOptionListResponse(APIModel):
    message: str
    data: list[PlatformOwnerSummary]
