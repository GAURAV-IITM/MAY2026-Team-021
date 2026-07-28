"""Owner announcement-management API contracts."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import (
    AnnouncementAudience,
    AnnouncementCategory,
    AnnouncementPriority,
    AnnouncementStatus,
)
from app.schemas.common import APIModel, PaginationMeta


class AnnouncementActorSummary(APIModel):
    id: uuid.UUID
    name: str


class AnnouncementCreate(APIModel):
    model_config = {
        **APIModel.model_config,
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Library Closed on Sunday",
                    "body": (
                        "The library will remain closed this Sunday for "
                        "maintenance."
                    ),
                    "category": "general",
                    "priority": "normal",
                    "audience": "all_students",
                    "status": "draft",
                    "scheduledAt": None,
                    "expiresAt": None,
                }
            ]
        },
    }

    title: str = Field(min_length=5, max_length=120)
    body: str = Field(min_length=10, max_length=1000)
    category: AnnouncementCategory = AnnouncementCategory.GENERAL
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL
    audience: AnnouncementAudience = AnnouncementAudience.ALL_STUDENTS
    status: AnnouncementStatus = AnnouncementStatus.DRAFT
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None

    @field_validator("title", "body", mode="before")
    @classmethod
    def trim_content(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AnnouncementUpdate(APIModel):
    title: str | None = Field(default=None, min_length=5, max_length=120)
    body: str | None = Field(default=None, min_length=10, max_length=1000)
    category: AnnouncementCategory | None = None
    priority: AnnouncementPriority | None = None
    audience: AnnouncementAudience | None = None
    status: AnnouncementStatus | None = None
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None
    expected_updated_at: datetime | None = None

    @field_validator("title", "body", mode="before")
    @classmethod
    def trim_content(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AnnouncementArchiveRequest(APIModel):
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def trim_reason(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip() or None


class AnnouncementResponse(APIModel):
    id: uuid.UUID
    title: str
    body: str
    category: AnnouncementCategory
    priority: AnnouncementPriority
    audience: AnnouncementAudience
    status: AnnouncementStatus
    scheduled_at: datetime | None
    published_at: datetime | None
    expires_at: datetime | None
    archived_at: datetime | None
    is_expired: bool
    created_at: datetime
    updated_at: datetime
    created_by: AnnouncementActorSummary | None


class AnnouncementSummary(APIModel):
    total: int = Field(ge=0)
    drafts: int = Field(ge=0)
    scheduled: int = Field(ge=0)
    published: int = Field(ge=0)
    archived: int = Field(ge=0)
    expired: int = Field(ge=0)
    important: int = Field(ge=0)


class AnnouncementListResponse(APIModel):
    message: str
    data: list[AnnouncementResponse]
    meta: PaginationMeta
    summary: AnnouncementSummary
