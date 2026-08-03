"""Super Admin platform-library policies and transactional use cases."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, ResourceNotFoundError
from app.models.enums import LibraryStatus, MembershipStatus, RoleName
from app.models.library import Library, LibraryMembership, LibrarySettings
from app.repositories import platform as repository
from app.schemas.common import PaginationParams
from app.schemas.platform import (
    PlatformLibraryCreate,
    PlatformLibraryOwnerAssign,
    PlatformLibraryResponse,
    PlatformLibraryStatusUpdate,
    PlatformLibrarySummary,
    PlatformLibraryUpdate,
    PlatformOwnerSummary,
)
from app.services.audit import AuditContext, write_audit_log


PHONE_ALLOWED = re.compile(r"^[+()\-\s0-9]+$")
VALID_TRANSITIONS = {
    LibraryStatus.PENDING: {LibraryStatus.ACTIVE},
    LibraryStatus.ACTIVE: {LibraryStatus.SUSPENDED},
    LibraryStatus.SUSPENDED: {LibraryStatus.ACTIVE},
}
EDITABLE_FIELDS = {
    "name",
    "contact_email",
    "contact_phone",
    "address_line",
    "city",
    "state",
    "postal_code",
    "timezone",
}


@dataclass(frozen=True, slots=True)
class PlatformLibraryListResult:
    libraries: list[PlatformLibraryResponse]
    total: int
    summary: PlatformLibrarySummary


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


def _not_found() -> ResourceNotFoundError:
    return ResourceNotFoundError(
        "Library not found.",
        code="PLATFORM_LIBRARY_NOT_FOUND",
    )


def _validate_state(
    library: Library,
    expected_updated_at: datetime | None,
) -> None:
    if expected_updated_at is not None and not _timestamp_equal(
        library.updated_at,
        expected_updated_at,
    ):
        raise ConflictError(
            "This library changed after it was opened. Refresh and try again.",
            code="PLATFORM_LIBRARY_STATE_CHANGED",
            details={
                "libraryId": str(library.id),
                "currentStatus": library.status.value,
                "updatedAt": library.updated_at.isoformat(),
            },
        )


def _validate_profile(
    *,
    name: str,
    contact_email: str,
    contact_phone: str | None,
    timezone_name: str,
) -> None:
    if not name.strip():
        raise BusinessRuleError(
            "Library name is required.",
            code="PLATFORM_LIBRARY_NAME_REQUIRED",
        )
    if not contact_email.strip():
        raise BusinessRuleError(
            "Library contact email is required.",
            code="PLATFORM_LIBRARY_EMAIL_REQUIRED",
        )
    if contact_phone:
        digits = "".join(character for character in contact_phone if character.isdigit())
        if not PHONE_ALLOWED.fullmatch(contact_phone) or not 7 <= len(digits) <= 15:
            raise BusinessRuleError(
                "Enter a valid library phone number.",
                code="PLATFORM_LIBRARY_PHONE_INVALID",
            )
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise BusinessRuleError(
            "Select a valid IANA timezone.",
            code="PLATFORM_LIBRARY_TIMEZONE_INVALID",
            details={"timezone": timezone_name},
        ) from exc


def _owner_summary(user: object | None) -> PlatformOwnerSummary | None:
    if user is None:
        return None
    return PlatformOwnerSummary(
        id=user.id,
        name=user.full_name,
        email=user.email,
        phone=user.phone,
    )


def _response(
    library: Library,
    *,
    student_count: int,
    seat_count: int,
    membership_count: int,
) -> PlatformLibraryResponse:
    return PlatformLibraryResponse(
        id=library.id,
        code=library.code,
        name=library.name,
        contact_email=library.contact_email,
        contact_phone=library.contact_phone,
        address_line=library.address_line,
        city=library.city,
        state=library.state,
        postal_code=library.postal_code,
        timezone=library.timezone,
        status=library.status,
        owner=_owner_summary(library.primary_owner),
        student_count=student_count,
        seat_count=seat_count,
        membership_count=membership_count,
        suspended_at=library.suspended_at,
        suspension_reason=library.suspension_reason,
        created_at=library.created_at,
        updated_at=library.updated_at,
        last_activity_at=library.last_activity_at,
    )


def _detail_response(db: Session, library_id: uuid.UUID) -> PlatformLibraryResponse:
    library = repository.get_library(db, library_id)
    if library is None:
        raise _not_found()
    counts = repository.get_library_counts(db, library_id)
    return _response(
        library,
        student_count=counts[0],
        seat_count=counts[1],
        membership_count=counts[2],
    )


def list_libraries(
    db: Session,
    pagination: PaginationParams,
    *,
    status: LibraryStatus | None = None,
    owner_id: uuid.UUID | None = None,
    state: str | None = None,
) -> PlatformLibraryListResult:
    records, total, summary = repository.list_libraries(
        db,
        pagination,
        status=status,
        owner_id=owner_id,
        state=state,
    )
    return PlatformLibraryListResult(
        libraries=[
            _response(
                record.library,
                student_count=record.student_count,
                seat_count=record.seat_count,
                membership_count=record.membership_count,
            )
            for record in records
        ],
        total=total,
        summary=summary,
    )


def get_library(db: Session, library_id: uuid.UUID) -> PlatformLibraryResponse:
    return _detail_response(db, library_id)


def list_eligible_owners(db: Session) -> list[PlatformOwnerSummary]:
    return [
        PlatformOwnerSummary(
            id=owner.id,
            name=owner.full_name,
            email=owner.email,
            phone=owner.phone,
        )
        for owner in repository.list_eligible_owners(db)
    ]


def _assign_owner(
    db: Session,
    library: Library,
    owner_id: uuid.UUID,
    *,
    now: datetime,
) -> tuple[uuid.UUID | None, object]:
    owner = repository.get_owner_user(db, owner_id, for_update=True)
    if owner is None or not owner.is_active:
        raise BusinessRuleError(
            "The selected user is not an eligible active library owner.",
            code="PLATFORM_LIBRARY_OWNER_INVALID",
            details={"ownerId": str(owner_id)},
        )
    if library.primary_owner_user_id == owner_id:
        raise ConflictError(
            "This owner is already assigned to the library.",
            code="PLATFORM_LIBRARY_OWNER_ALREADY_ASSIGNED",
            details={"libraryId": str(library.id), "ownerId": str(owner_id)},
        )

    active_membership = repository.get_active_owner_membership(
        db,
        owner_id,
        for_update=True,
    )
    if active_membership is not None and active_membership.library_id != library.id:
        raise ConflictError(
            "This owner already manages another library.",
            code="PLATFORM_LIBRARY_OWNER_CONFLICT",
            details={
                "ownerId": str(owner_id),
                "assignedLibraryId": str(active_membership.library_id),
            },
        )

    previous_owner_id = library.primary_owner_user_id
    if previous_owner_id is not None:
        previous_membership = repository.get_membership(
            db,
            library.id,
            previous_owner_id,
            for_update=True,
        )
        if previous_membership is not None:
            previous_membership.status = MembershipStatus.LEFT
            previous_membership.left_at = now

    membership = repository.get_membership(
        db,
        library.id,
        owner_id,
        for_update=True,
    )
    if membership is None:
        membership = LibraryMembership(
            library_id=library.id,
            user_id=owner_id,
            role=RoleName.LIBRARY_OWNER,
            status=MembershipStatus.ACTIVE,
            joined_at=now,
        )
        db.add(membership)
    else:
        membership.role = RoleName.LIBRARY_OWNER
        membership.status = MembershipStatus.ACTIVE
        membership.joined_at = membership.joined_at or now
        membership.left_at = None

    library.primary_owner_user_id = owner_id
    library.last_activity_at = now
    library.updated_at = now
    db.flush()
    return previous_owner_id, owner


def create_library(
    db: Session,
    payload: PlatformLibraryCreate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformLibraryResponse:
    _validate_profile(
        name=payload.name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        timezone_name=payload.timezone,
    )
    if repository.library_identity_exists(db, name=payload.name, code=payload.code):
        raise ConflictError(
            "A library with this name or code already exists.",
            code="PLATFORM_LIBRARY_DUPLICATE",
        )

    try:
        now = _now()
        library = repository.add_library(
            db,
            Library(
                code=payload.code,
                name=payload.name,
                contact_email=payload.contact_email.lower(),
                contact_phone=payload.contact_phone or None,
                address_line=payload.address_line or None,
                city=payload.city or None,
                state=payload.state or None,
                postal_code=payload.postal_code or None,
                timezone=payload.timezone,
                status=LibraryStatus.PENDING,
                last_activity_at=now,
            ),
        )
        db.add(LibrarySettings(library_id=library.id))
        assigned_owner = None
        if payload.owner_id is not None:
            _previous_owner_id, assigned_owner = _assign_owner(
                db,
                library,
                payload.owner_id,
                now=now,
            )

        write_audit_log(
            db,
            library_id=library.id,
            actor_user_id=actor_user_id,
            action="platform.library.created",
            entity_type="library",
            entity_id=str(library.id),
            new_values={
                "code": library.code,
                "name": library.name,
                "status": library.status.value,
            },
            request_context=audit_context,
        )
        if assigned_owner is not None:
            write_audit_log(
                db,
                library_id=library.id,
                actor_user_id=actor_user_id,
                action="platform.library.owner_assigned",
                entity_type="library",
                entity_id=str(library.id),
                old_values={"ownerId": None},
                new_values={"ownerId": str(assigned_owner.id)},
                request_context=audit_context,
            )
        db.commit()
        db.expire_all()
        return _detail_response(db, library.id)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "A library with this name or code already exists.",
            code="PLATFORM_LIBRARY_DUPLICATE",
        ) from exc
    except Exception:
        db.rollback()
        raise


def update_library(
    db: Session,
    library_id: uuid.UUID,
    payload: PlatformLibraryUpdate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformLibraryResponse:
    try:
        library = repository.get_library(db, library_id, for_update=True)
        if library is None:
            raise _not_found()
        _validate_state(library, payload.expected_updated_at)
        fields = payload.model_fields_set - {"expected_updated_at"}
        if not fields:
            raise BusinessRuleError(
                "Provide at least one editable library field.",
                code="PLATFORM_LIBRARY_UPDATE_EMPTY",
            )
        null_required = sorted(
            field
            for field in fields & {"name", "contact_email", "timezone"}
            if getattr(payload, field) is None
        )
        if null_required:
            raise BusinessRuleError(
                "Required library fields cannot be null.",
                code="PLATFORM_LIBRARY_FIELD_REQUIRED",
                details={"fields": null_required},
            )

        next_values = {
            field: getattr(payload, field)
            if field in fields
            else getattr(library, field)
            for field in EDITABLE_FIELDS
        }
        _validate_profile(
            name=next_values["name"],
            contact_email=next_values["contact_email"],
            contact_phone=next_values["contact_phone"],
            timezone_name=next_values["timezone"],
        )
        if "name" in fields and repository.library_identity_exists(
            db,
            name=next_values["name"],
            exclude_library_id=library.id,
        ):
            raise ConflictError(
                "A library with this name already exists.",
                code="PLATFORM_LIBRARY_DUPLICATE",
            )

        old_values: dict[str, object] = {}
        new_values: dict[str, object] = {}
        for field in fields & EDITABLE_FIELDS:
            value = next_values[field]
            if field == "contact_email" and value is not None:
                value = value.lower()
            if isinstance(value, str) and not value:
                value = None
            old_value = getattr(library, field)
            if old_value != value:
                old_values[field] = old_value
                new_values[field] = value
                setattr(library, field, value)
        if not new_values:
            raise ConflictError(
                "The submitted values do not change this library.",
                code="PLATFORM_LIBRARY_STATE_CHANGED",
            )
        now = _now()
        library.last_activity_at = now
        library.updated_at = now
        db.flush()
        write_audit_log(
            db,
            library_id=library.id,
            actor_user_id=actor_user_id,
            action="platform.library.edited",
            entity_type="library",
            entity_id=str(library.id),
            old_values=old_values,
            new_values=new_values,
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        return _detail_response(db, library.id)
    except Exception:
        db.rollback()
        raise


def change_library_status(
    db: Session,
    library_id: uuid.UUID,
    payload: PlatformLibraryStatusUpdate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformLibraryResponse:
    try:
        library = repository.get_library(db, library_id, for_update=True)
        if library is None:
            raise _not_found()
        _validate_state(library, payload.expected_updated_at)
        if payload.status not in VALID_TRANSITIONS.get(library.status, set()):
            raise ConflictError(
                f"A {library.status.value} library cannot transition to {payload.status.value}.",
                code="PLATFORM_LIBRARY_INVALID_STATUS",
                details={
                    "libraryId": str(library.id),
                    "currentStatus": library.status.value,
                    "requestedStatus": payload.status.value,
                },
            )
        if payload.status == LibraryStatus.SUSPENDED and not payload.reason:
            raise BusinessRuleError(
                "A suspension reason is required.",
                code="PLATFORM_LIBRARY_SUSPENSION_REASON_REQUIRED",
            )

        now = _now()
        previous_status = library.status
        library.status = payload.status
        library.last_activity_at = now
        library.updated_at = now
        if payload.status == LibraryStatus.SUSPENDED:
            library.suspended_at = now
            library.suspended_by_user_id = actor_user_id
            library.suspension_reason = payload.reason
        else:
            library.suspended_at = None
            library.suspended_by_user_id = None
            library.suspension_reason = None
            if previous_status == LibraryStatus.PENDING:
                library.approved_at = now
                library.approved_by_user_id = actor_user_id
        db.flush()
        write_audit_log(
            db,
            library_id=library.id,
            actor_user_id=actor_user_id,
            action=(
                "platform.library.suspended"
                if payload.status == LibraryStatus.SUSPENDED
                else "platform.library.activated"
            ),
            entity_type="library",
            entity_id=str(library.id),
            old_values={"status": previous_status.value},
            new_values={"status": payload.status.value},
            context={"reason": payload.reason} if payload.reason else None,
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        return _detail_response(db, library.id)
    except Exception:
        db.rollback()
        raise


def assign_library_owner(
    db: Session,
    library_id: uuid.UUID,
    payload: PlatformLibraryOwnerAssign,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformLibraryResponse:
    try:
        library = repository.get_library(db, library_id, for_update=True)
        if library is None:
            raise _not_found()
        _validate_state(library, payload.expected_updated_at)
        previous_owner_id, owner = _assign_owner(
            db,
            library,
            payload.owner_id,
            now=_now(),
        )
        write_audit_log(
            db,
            library_id=library.id,
            actor_user_id=actor_user_id,
            action="platform.library.owner_assigned",
            entity_type="library",
            entity_id=str(library.id),
            old_values={
                "ownerId": str(previous_owner_id) if previous_owner_id else None,
            },
            new_values={"ownerId": str(owner.id)},
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        return _detail_response(db, library.id)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The owner assignment conflicts with current membership data.",
            code="PLATFORM_LIBRARY_OWNER_CONFLICT",
        ) from exc
    except Exception:
        db.rollback()
        raise
