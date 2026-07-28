"""Tenant-safe owner announcement lifecycle use cases."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ResourceNotFoundError,
)
from app.models.announcement import Announcement
from app.models.enums import AnnouncementStatus
from app.repositories import announcement as repository
from app.schemas.announcement import (
    AnnouncementActorSummary,
    AnnouncementArchiveRequest,
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementSummary,
    AnnouncementUpdate,
)
from app.schemas.common import PaginationParams
from app.services.audit import AuditContext, write_audit_log


EDITABLE_STATUSES = {
    AnnouncementStatus.DRAFT,
    AnnouncementStatus.SCHEDULED,
}
ARCHIVABLE_STATUSES = {
    AnnouncementStatus.SCHEDULED,
    AnnouncementStatus.PUBLISHED,
    AnnouncementStatus.EXPIRED,
}
DELETABLE_STATUSES = {
    AnnouncementStatus.DRAFT,
    AnnouncementStatus.ARCHIVED,
}


@dataclass(frozen=True, slots=True)
class AnnouncementListResult:
    announcements: list[AnnouncementResponse]
    total: int
    summary: AnnouncementSummary


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _timestamp_equal(left: datetime, right: datetime) -> bool:
    normalized_left = _utc(left)
    normalized_right = _utc(right)
    assert normalized_left is not None and normalized_right is not None
    return abs((normalized_left - normalized_right).total_seconds()) < 0.001


def _is_expired(announcement: Announcement, now: datetime) -> bool:
    expires_at = _utc(announcement.expires_at)
    return (
        announcement.status == AnnouncementStatus.EXPIRED
        or (
            announcement.status == AnnouncementStatus.PUBLISHED
            and expires_at is not None
            and expires_at <= now
        )
    )


def _response(
    announcement: Announcement,
    *,
    now: datetime | None = None,
) -> AnnouncementResponse:
    actor = announcement.author
    is_expired = _is_expired(announcement, now or _now())
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        body=announcement.body,
        category=announcement.category,
        priority=announcement.priority,
        audience=announcement.audience,
        status=(
            AnnouncementStatus.EXPIRED
            if is_expired
            else announcement.status
        ),
        scheduled_at=announcement.scheduled_for,
        published_at=announcement.published_at,
        expires_at=announcement.expires_at,
        archived_at=announcement.archived_at,
        is_expired=is_expired,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
        created_by=(
            AnnouncementActorSummary(id=actor.id, name=actor.full_name)
            if actor
            else None
        ),
    )


def _not_found() -> ResourceNotFoundError:
    return ResourceNotFoundError(
        "Announcement not found.",
        code="ANNOUNCEMENT_NOT_FOUND",
    )


def _invalid_transition(
    announcement: Announcement,
    requested_status: AnnouncementStatus,
) -> ConflictError:
    return ConflictError(
        (
            f"An announcement in {announcement.status.value} status cannot "
            f"transition to {requested_status.value}."
        ),
        code="ANNOUNCEMENT_INVALID_STATE_TRANSITION",
        details={
            "announcementId": str(announcement.id),
            "currentStatus": announcement.status.value,
            "requestedStatus": requested_status.value,
        },
    )


def _validate_dates(
    status: AnnouncementStatus,
    scheduled_at: datetime | None,
    expires_at: datetime | None,
    *,
    now: datetime,
) -> None:
    scheduled_at = _utc(scheduled_at)
    expires_at = _utc(expires_at)
    if status == AnnouncementStatus.DRAFT and scheduled_at is not None:
        raise BusinessRuleError(
            "A draft announcement cannot have a scheduled publish date.",
            code="ANNOUNCEMENT_DRAFT_SCHEDULE_INVALID",
        )
    if status == AnnouncementStatus.SCHEDULED:
        if scheduled_at is None:
            raise BusinessRuleError(
                "A scheduled announcement requires a publish date.",
                code="ANNOUNCEMENT_SCHEDULE_REQUIRED",
            )
        if scheduled_at <= now:
            raise BusinessRuleError(
                "The scheduled publish date must be in the future.",
                code="ANNOUNCEMENT_SCHEDULE_NOT_FUTURE",
            )
    if expires_at is not None:
        if expires_at <= now:
            raise BusinessRuleError(
                "The expiry date must be in the future.",
                code="ANNOUNCEMENT_EXPIRY_NOT_FUTURE",
            )
        if scheduled_at is not None and expires_at <= scheduled_at:
            raise BusinessRuleError(
                "The expiry date must be after the scheduled publish date.",
                code="ANNOUNCEMENT_EXPIRY_BEFORE_PUBLISH",
            )


def list_announcements(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    **filters: object,
) -> AnnouncementListResult:
    now = _now()
    records, total, summary = repository.list_announcements(
        db,
        library_id,
        pagination,
        now=now,
        **filters,
    )
    return AnnouncementListResult(
        announcements=[_response(record, now=now) for record in records],
        total=total,
        summary=summary,
    )


def create_announcement(
    db: Session,
    library_id: uuid.UUID,
    payload: AnnouncementCreate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> AnnouncementResponse:
    if payload.status not in EDITABLE_STATUSES:
        raise BusinessRuleError(
            "Announcements can only be created as draft or scheduled.",
            code="ANNOUNCEMENT_CREATE_STATUS_INVALID",
        )
    now = _now()
    _validate_dates(
        payload.status,
        payload.scheduled_at,
        payload.expires_at,
        now=now,
    )
    try:
        announcement = repository.add_announcement(
            db,
            Announcement(
                library_id=library_id,
                title=payload.title,
                body=payload.body,
                category=payload.category.value,
                priority=payload.priority,
                audience=payload.audience,
                status=payload.status,
                scheduled_for=_utc(payload.scheduled_at),
                expires_at=_utc(payload.expires_at),
                author_user_id=actor_user_id,
            ),
        )
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="announcement.created",
            entity_type="announcement",
            entity_id=str(announcement.id),
            new_values={
                "status": announcement.status.value,
                "title": announcement.title,
            },
            request_context=audit_context,
        )
        db.commit()
        saved = repository.get_announcement(
            db,
            library_id,
            announcement.id,
        )
        assert saved is not None
        return _response(saved)
    except Exception:
        db.rollback()
        raise


def update_announcement(
    db: Session,
    library_id: uuid.UUID,
    announcement_id: uuid.UUID,
    payload: AnnouncementUpdate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> AnnouncementResponse:
    try:
        announcement = repository.get_announcement(
            db,
            library_id,
            announcement_id,
            for_update=True,
        )
        if announcement is None:
            raise _not_found()
        if announcement.status not in EDITABLE_STATUSES:
            raise _invalid_transition(announcement, announcement.status)
        if (
            payload.expected_updated_at is not None
            and not _timestamp_equal(
                announcement.updated_at,
                payload.expected_updated_at,
            )
        ):
            raise ConflictError(
                "This announcement changed after it was opened. Refresh and try again.",
                code="ANNOUNCEMENT_STATE_CHANGED",
                details={
                    "announcementId": str(announcement.id),
                    "currentStatus": announcement.status.value,
                },
            )

        fields = payload.model_fields_set - {"expected_updated_at"}
        required_fields = {
            "title",
            "body",
            "category",
            "priority",
            "audience",
            "status",
        }
        null_fields = sorted(
            field
            for field in fields & required_fields
            if getattr(payload, field) is None
        )
        if null_fields:
            raise BusinessRuleError(
                "Editable announcement fields cannot be null.",
                code="ANNOUNCEMENT_FIELD_REQUIRED",
                details={"fields": null_fields},
            )
        target_status = (
            payload.status if "status" in fields else announcement.status
        )
        if target_status not in EDITABLE_STATUSES:
            raise _invalid_transition(announcement, target_status)

        scheduled_at = (
            payload.scheduled_at
            if "scheduled_at" in fields
            else announcement.scheduled_for
        )
        if target_status == AnnouncementStatus.DRAFT:
            scheduled_at = None
        expires_at = (
            payload.expires_at
            if "expires_at" in fields
            else announcement.expires_at
        )
        _validate_dates(
            target_status,
            scheduled_at,
            expires_at,
            now=_now(),
        )

        changed_fields: list[str] = []
        field_mapping = {
            "title": "title",
            "body": "body",
            "category": "category",
            "priority": "priority",
            "audience": "audience",
        }
        for payload_field, model_field in field_mapping.items():
            if payload_field not in fields:
                continue
            value = getattr(payload, payload_field)
            if payload_field == "category" and value is not None:
                value = value.value
            if getattr(announcement, model_field) != value:
                setattr(announcement, model_field, value)
                changed_fields.append(payload_field)

        if announcement.status != target_status:
            announcement.status = target_status
            changed_fields.append("status")
        normalized_schedule = _utc(scheduled_at)
        if announcement.scheduled_for != normalized_schedule:
            announcement.scheduled_for = normalized_schedule
            changed_fields.append("scheduledAt")
        normalized_expiry = _utc(expires_at)
        if announcement.expires_at != normalized_expiry:
            announcement.expires_at = normalized_expiry
            changed_fields.append("expiresAt")

        announcement.updated_at = _now()
        db.flush()
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="announcement.updated",
            entity_type="announcement",
            entity_id=str(announcement.id),
            new_values={"changedFields": sorted(set(changed_fields))},
            request_context=audit_context,
        )
        db.commit()
        saved = repository.get_announcement(db, library_id, announcement.id)
        assert saved is not None
        return _response(saved)
    except Exception:
        db.rollback()
        raise


def publish_announcement(
    db: Session,
    library_id: uuid.UUID,
    announcement_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> AnnouncementResponse:
    try:
        announcement = repository.get_announcement(
            db,
            library_id,
            announcement_id,
            for_update=True,
        )
        if announcement is None:
            raise _not_found()
        if announcement.status not in EDITABLE_STATUSES:
            raise _invalid_transition(
                announcement,
                AnnouncementStatus.PUBLISHED,
            )
        now = _now()
        expires_at = _utc(announcement.expires_at)
        if expires_at is not None and expires_at <= now:
            raise BusinessRuleError(
                "The expiry date must be in the future before publishing.",
                code="ANNOUNCEMENT_EXPIRY_NOT_FUTURE",
            )

        previous_status = announcement.status
        announcement.status = AnnouncementStatus.PUBLISHED
        announcement.published_at = now
        announcement.archived_at = None
        announcement.updated_at = now
        db.flush()
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="announcement.published",
            entity_type="announcement",
            entity_id=str(announcement.id),
            old_values={"status": previous_status.value},
            new_values={
                "status": AnnouncementStatus.PUBLISHED.value,
                "publishedAt": now.isoformat(),
            },
            request_context=audit_context,
        )
        db.commit()
        saved = repository.get_announcement(db, library_id, announcement.id)
        assert saved is not None
        return _response(saved)
    except Exception:
        db.rollback()
        raise


def archive_announcement(
    db: Session,
    library_id: uuid.UUID,
    announcement_id: uuid.UUID,
    payload: AnnouncementArchiveRequest,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> AnnouncementResponse:
    try:
        announcement = repository.get_announcement(
            db,
            library_id,
            announcement_id,
            for_update=True,
        )
        if announcement is None:
            raise _not_found()
        if announcement.status not in ARCHIVABLE_STATUSES:
            raise _invalid_transition(
                announcement,
                AnnouncementStatus.ARCHIVED,
            )

        previous_status = announcement.status
        now = _now()
        announcement.status = AnnouncementStatus.ARCHIVED
        announcement.archived_at = now
        announcement.updated_at = now
        db.flush()
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="announcement.archived",
            entity_type="announcement",
            entity_id=str(announcement.id),
            old_values={"status": previous_status.value},
            new_values={
                "status": AnnouncementStatus.ARCHIVED.value,
                "archivedAt": now.isoformat(),
            },
            context={"reason": payload.reason} if payload.reason else None,
            request_context=audit_context,
        )
        db.commit()
        saved = repository.get_announcement(db, library_id, announcement.id)
        assert saved is not None
        return _response(saved)
    except Exception:
        db.rollback()
        raise


def delete_announcement(
    db: Session,
    library_id: uuid.UUID,
    announcement_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> None:
    try:
        announcement = repository.get_announcement(
            db,
            library_id,
            announcement_id,
            for_update=True,
        )
        if announcement is None:
            raise _not_found()
        if announcement.status not in DELETABLE_STATUSES:
            raise _invalid_transition(
                announcement,
                AnnouncementStatus.ARCHIVED,
            )

        now = _now()
        announcement.deleted_at = now
        announcement.updated_at = now
        db.flush()
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="announcement.deleted",
            entity_type="announcement",
            entity_id=str(announcement.id),
            old_values={"status": announcement.status.value},
            new_values={"deletedAt": now.isoformat()},
            request_context=audit_context,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
