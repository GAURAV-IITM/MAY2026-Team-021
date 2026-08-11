"""Super Admin platform-library API contracts."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

from app.core.exceptions import BusinessRuleError
from app.models.enums import InvitationStatus, LibraryStatus, MembershipStatus
from app.schemas.common import APIModel, PaginationMeta


EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


class PlatformOwnerStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class PlatformOwnerStatusAction(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class PlatformSettingValueType(StrEnum):
    TEXT = "text"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    ENUM = "enum"


class PlatformTimezone(StrEnum):
    ASIA_KOLKATA = "Asia/Kolkata"
    UTC = "UTC"
    ASIA_DUBAI = "Asia/Dubai"


class PlatformSettingDefinition(APIModel):
    key: str
    display_name: str
    type: PlatformSettingValueType
    editable: bool
    default_value: str | bool | int
    description: str
    runtime_effect: str
    minimum: int | None = None
    maximum: int | None = None
    options: list[str] = Field(default_factory=list)


class PlatformSettingsValues(APIModel):
    platform_name: str
    allow_library_registrations: bool
    session_timeout_minutes: int = Field(ge=15, le=1440)
    default_timezone: PlatformTimezone


class PlatformSettingsResponse(APIModel):
    settings: PlatformSettingsValues
    definitions: list[PlatformSettingDefinition]
    version: int = Field(ge=0)
    updated_at: datetime | None = None


class PlatformSettingsSuccessResponse(APIModel):
    message: str
    data: PlatformSettingsResponse


class PlatformSettingsUpdate(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="allow",
        json_schema_extra={"additionalProperties": False},
    )

    version: StrictInt = Field(ge=0)
    allow_library_registrations: StrictBool | None = None
    session_timeout_minutes: StrictInt | None = Field(default=None, ge=15, le=1440)
    default_timezone: PlatformTimezone | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_setting_keys_and_types(cls, value: object) -> object:
        if not isinstance(value, dict):
            raise BusinessRuleError(
                "Platform settings must be submitted as an object.",
                code="PLATFORM_SETTING_INVALID_VALUE",
            )

        aliases = {
            "version",
            "platformName",
            "platform_name",
            "allowLibraryRegistrations",
            "allow_library_registrations",
            "sessionTimeoutMinutes",
            "session_timeout_minutes",
            "defaultTimezone",
            "default_timezone",
        }
        unknown = sorted(str(key) for key in value if key not in aliases)
        if unknown:
            raise BusinessRuleError(
                "One or more platform setting keys are not allowed.",
                code="PLATFORM_SETTING_UNKNOWN",
                details={"keys": unknown},
            )
        if "platformName" in value or "platform_name" in value:
            raise BusinessRuleError(
                "Platform name is managed by deployment configuration and is read-only.",
                code="PLATFORM_SETTING_READ_ONLY",
                details={"key": "platformName"},
            )

        def supplied(*keys: str) -> tuple[bool, object | None]:
            for key in keys:
                if key in value:
                    return True, value[key]
            return False, None

        checks = (
            ("version", ("version",), int),
            (
                "allowLibraryRegistrations",
                ("allowLibraryRegistrations", "allow_library_registrations"),
                bool,
            ),
            (
                "sessionTimeoutMinutes",
                ("sessionTimeoutMinutes", "session_timeout_minutes"),
                int,
            ),
            (
                "defaultTimezone",
                ("defaultTimezone", "default_timezone"),
                str,
            ),
        )
        for api_key, keys, expected_type in checks:
            is_supplied, setting_value = supplied(*keys)
            if is_supplied and type(setting_value) is not expected_type:
                raise BusinessRuleError(
                    f"{api_key} has an invalid value type.",
                    code="PLATFORM_SETTING_INVALID_VALUE",
                    details={"key": api_key},
                )
            if (
                api_key == "sessionTimeoutMinutes"
                and is_supplied
                and not 15 <= setting_value <= 1440
            ):
                raise BusinessRuleError(
                    "sessionTimeoutMinutes must be between 15 and 1440.",
                    code="PLATFORM_SETTING_INVALID_VALUE",
                    details={"key": api_key, "minimum": 15, "maximum": 1440},
                )
            if (
                api_key == "defaultTimezone"
                and is_supplied
                and setting_value not in {item.value for item in PlatformTimezone}
            ):
                raise BusinessRuleError(
                    "defaultTimezone is not an approved timezone.",
                    code="PLATFORM_SETTING_INVALID_VALUE",
                    details={"key": api_key},
                )
        return value


class PlatformDashboardMetrics(APIModel):
    total_libraries: int = Field(ge=0)
    active_libraries: int = Field(ge=0)
    pending_libraries: int = Field(ge=0)
    suspended_libraries: int = Field(ge=0)
    total_owners: int = Field(ge=0)
    active_owners: int = Field(ge=0)
    suspended_owners: int = Field(ge=0)
    invited_owners: int = Field(ge=0)
    total_students: int = Field(ge=0)
    total_seats: int = Field(ge=0)
    average_occupancy: int = Field(ge=0, le=100)


class PlatformDashboardRange(APIModel):
    start_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    end_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    timezone: str = "UTC"


class PlatformDashboardStatusCount(APIModel):
    status: LibraryStatus
    count: int = Field(ge=0)


class PlatformDashboardTrendPoint(APIModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    libraries: int = Field(ge=0)
    owners: int = Field(ge=0)
    students: int = Field(ge=0)


class PlatformDashboardTopLibrary(APIModel):
    id: uuid.UUID
    code: str
    name: str
    city: str | None = None
    state: str | None = None
    student_count: int = Field(ge=0)
    seat_count: int = Field(ge=0)
    occupied_seat_count: int = Field(ge=0)
    occupancy_rate: int = Field(ge=0, le=100)


class PlatformDashboardActivityActor(APIModel):
    id: uuid.UUID
    name: str


class PlatformDashboardActivity(APIModel):
    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: str | None = None
    description: str
    category: str
    actor: PlatformDashboardActivityActor | None = None
    created_at: datetime


class PlatformDashboardResponse(APIModel):
    totals: PlatformDashboardMetrics
    library_status: list[PlatformDashboardStatusCount]
    trend: list[PlatformDashboardTrendPoint]
    top_libraries: list[PlatformDashboardTopLibrary]
    recent_activity: list[PlatformDashboardActivity]
    range: PlatformDashboardRange
    last_updated: datetime


class PlatformDashboardSuccessResponse(APIModel):
    message: str
    data: PlatformDashboardResponse


class PlatformOwnerSummary(APIModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None = None


class PlatformOwnerLibrarySummary(APIModel):
    id: uuid.UUID
    code: str
    name: str
    status: LibraryStatus


class PlatformOwnerAssignmentHistory(APIModel):
    library_id: uuid.UUID
    library_name: str
    membership_status: MembershipStatus
    joined_at: datetime
    left_at: datetime | None = None


class PlatformOwnerResponse(APIModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    invitation_id: uuid.UUID | None = None
    name: str
    email: str
    phone: str | None = None
    status: PlatformOwnerStatus
    invitation_status: InvitationStatus | None = None
    invitation_expires_at: datetime | None = None
    assignments: list[PlatformOwnerLibrarySummary] = Field(default_factory=list)
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PlatformOwnerDetailResponse(PlatformOwnerResponse):
    assignment_history: list[PlatformOwnerAssignmentHistory] = Field(
        default_factory=list
    )


class PlatformOwnerListSummary(APIModel):
    total: int = Field(ge=0)
    active: int = Field(ge=0)
    invited: int = Field(ge=0)
    suspended: int = Field(ge=0)


class PlatformOwnerListResponse(APIModel):
    message: str
    data: list[PlatformOwnerResponse]
    meta: PaginationMeta
    summary: PlatformOwnerListSummary


class PlatformOwnerSuccessResponse(APIModel):
    message: str
    data: PlatformOwnerResponse


class PlatformOwnerDetailSuccessResponse(APIModel):
    message: str
    data: PlatformOwnerDetailResponse


class PlatformOwnerInvite(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )

    name: str = Field(min_length=2, max_length=160)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=320)
    phone: str | None = Field(default=None, max_length=32)
    library_id: uuid.UUID

    @field_validator("name", "email", "phone", mode="before")
    @classmethod
    def trim_invite_fields(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip()


class PlatformOwnerInvitationResponse(APIModel):
    owner: PlatformOwnerResponse
    created_invitation: bool
    invitation_setup_url: str | None = None


class PlatformOwnerInvitationSuccessResponse(APIModel):
    message: str
    data: PlatformOwnerInvitationResponse


class PlatformOwnerUpdate(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )

    name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    expected_updated_at: datetime | None = None

    @field_validator("name", "phone", mode="before")
    @classmethod
    def trim_update_fields(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class PlatformOwnerAssignmentUpdate(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )

    library_id: uuid.UUID
    expected_updated_at: datetime | None = None


class PlatformOwnerStatusUpdate(APIModel):
    model_config = ConfigDict(
        alias_generator=APIModel.model_config["alias_generator"],
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )

    status: PlatformOwnerStatusAction
    reason: str | None = Field(default=None, max_length=500)
    expected_updated_at: datetime | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def trim_owner_status_reason(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip() or None


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
