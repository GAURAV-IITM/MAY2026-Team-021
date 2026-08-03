"""Super Admin platform-library policies and transactional use cases."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, ResourceNotFoundError
from app.core.security import is_expired
from app.models.enums import (
    InvitationStatus,
    LibraryStatus,
    MembershipStatus,
    RoleName,
)
from app.models.identity import User
from app.models.library import Library, LibraryMembership, LibrarySettings
from app.repositories import platform as repository
from app.schemas.common import PaginationParams
from app.schemas.platform import (
    PlatformDashboardActivity,
    PlatformDashboardActivityActor,
    PlatformDashboardMetrics,
    PlatformDashboardRange,
    PlatformDashboardResponse,
    PlatformDashboardStatusCount,
    PlatformDashboardTopLibrary,
    PlatformDashboardTrendPoint,
    PlatformLibraryCreate,
    PlatformLibraryOwnerAssign,
    PlatformLibraryResponse,
    PlatformLibraryStatusUpdate,
    PlatformLibrarySummary,
    PlatformLibraryUpdate,
    PlatformOwnerAssignmentHistory,
    PlatformOwnerAssignmentUpdate,
    PlatformOwnerDetailResponse,
    PlatformOwnerInvitationResponse,
    PlatformOwnerInvite,
    PlatformOwnerLibrarySummary,
    PlatformOwnerListSummary,
    PlatformOwnerResponse,
    PlatformOwnerStatus,
    PlatformOwnerStatusAction,
    PlatformOwnerStatusUpdate,
    PlatformOwnerSummary,
    PlatformOwnerUpdate,
)
from app.services.audit import AuditContext, write_audit_log
from app.services.invitation import create_account_invitation


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
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MAX_DASHBOARD_MONTHS = 24
DEFAULT_DASHBOARD_MONTHS = 7

ACTIVITY_LABELS = {
    "platform.library.created": "Library created",
    "platform.library.edited": "Library profile updated",
    "platform.library.suspended": "Library suspended",
    "platform.library.activated": "Library activated",
    "platform.library.owner_assigned": "Library owner assigned",
    "platform.owner.invited": "Library owner invited",
    "platform.owner.invitation_reissued": "Owner invitation reissued",
    "platform.owner.assigned": "Library owner assigned",
    "platform.owner.reassigned": "Library owner reassigned",
    "platform.owner.edited": "Owner profile updated",
    "platform.owner.suspended": "Library owner suspended",
    "platform.owner.activated": "Library owner activated",
}


@dataclass(frozen=True, slots=True)
class PlatformLibraryListResult:
    libraries: list[PlatformLibraryResponse]
    total: int
    summary: PlatformLibrarySummary


@dataclass(frozen=True, slots=True)
class PlatformOwnerListResult:
    owners: list[PlatformOwnerResponse]
    total: int
    summary: PlatformOwnerListSummary


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _add_months(value: date, amount: int) -> date:
    month_index = value.year * 12 + value.month - 1 + amount
    return date(month_index // 12, month_index % 12 + 1, 1)


def _parse_dashboard_range(
    start_month: str | None,
    end_month: str | None,
    *,
    now: datetime,
) -> tuple[date, date]:
    if (start_month is None) != (end_month is None):
        raise BusinessRuleError(
            "Provide both startMonth and endMonth, or omit both.",
            code="PLATFORM_DASHBOARD_MONTH_RANGE_REQUIRED",
        )

    current_month = date(now.year, now.month, 1)
    if start_month is None:
        return _add_months(current_month, -(DEFAULT_DASHBOARD_MONTHS - 1)), current_month

    if not MONTH_PATTERN.fullmatch(start_month) or not MONTH_PATTERN.fullmatch(end_month or ""):
        raise BusinessRuleError(
            "Dashboard months must use YYYY-MM format.",
            code="PLATFORM_DASHBOARD_MONTH_INVALID",
        )

    start = date.fromisoformat(f"{start_month}-01")
    end = date.fromisoformat(f"{end_month}-01")
    if start > end:
        raise BusinessRuleError(
            "startMonth cannot be later than endMonth.",
            code="PLATFORM_DASHBOARD_MONTH_RANGE_INVALID",
        )
    if end > current_month:
        raise BusinessRuleError(
            "Dashboard trends cannot include future months.",
            code="PLATFORM_DASHBOARD_FUTURE_RANGE",
        )
    month_count = (end.year - start.year) * 12 + end.month - start.month + 1
    if month_count > MAX_DASHBOARD_MONTHS:
        raise BusinessRuleError(
            f"Dashboard trends are limited to {MAX_DASHBOARD_MONTHS} months.",
            code="PLATFORM_DASHBOARD_RANGE_TOO_LARGE",
        )
    return start, end


def _month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def _compose_trend(
    start: date,
    end: date,
    library_counts: dict[str, int],
    student_counts: dict[str, int],
    owner_counts: dict[str, int],
) -> list[PlatformDashboardTrendPoint]:
    library_total = sum(
        count for month, count in library_counts.items() if month < _month_key(start)
    )
    student_total = sum(
        count for month, count in student_counts.items() if month < _month_key(start)
    )
    owner_total = sum(
        count for month, count in owner_counts.items() if month < _month_key(start)
    )

    points: list[PlatformDashboardTrendPoint] = []
    month = start
    while month <= end:
        key = _month_key(month)
        library_total += library_counts.get(key, 0)
        student_total += student_counts.get(key, 0)
        owner_total += owner_counts.get(key, 0)
        points.append(
            PlatformDashboardTrendPoint(
                month=key,
                libraries=library_total,
                owners=owner_total,
                students=student_total,
            )
        )
        month = _add_months(month, 1)
    return points


def _activity_category(action: str, entity_type: str) -> str:
    if action.startswith("platform.library."):
        return "library"
    if action.startswith("platform.owner."):
        return "owner"
    return entity_type.strip().lower() or "platform"


def get_dashboard(
    db: Session,
    *,
    start_month: str | None = None,
    end_month: str | None = None,
) -> PlatformDashboardResponse:
    now = _now()
    today = now.date()
    range_start, range_end = _parse_dashboard_range(
        start_month,
        end_month,
        now=now,
    )
    end_exclusive_date = _add_months(range_end, 1)
    end_exclusive = datetime(
        end_exclusive_date.year,
        end_exclusive_date.month,
        1,
        tzinfo=timezone.utc,
    )

    metrics = repository.get_dashboard_metrics(db, today=today, now=now)
    active_seat_count = repository.get_active_library_seat_count(db)
    monthly_counts = repository.get_dashboard_monthly_counts(
        db,
        end_exclusive=end_exclusive,
        end_date_exclusive=end_exclusive_date,
    )
    top_records = repository.list_dashboard_top_libraries(db, today=today)
    activity_records = repository.list_recent_platform_activity(db)

    occupancy = (
        round(metrics.occupied_seats * 100 / active_seat_count)
        if active_seat_count
        else 0
    )
    totals = PlatformDashboardMetrics(
        total_libraries=metrics.total_libraries,
        active_libraries=metrics.active_libraries,
        pending_libraries=metrics.pending_libraries,
        suspended_libraries=metrics.suspended_libraries,
        total_owners=metrics.total_owners,
        active_owners=metrics.active_owners,
        suspended_owners=metrics.suspended_owners,
        invited_owners=metrics.invited_owners,
        total_students=metrics.total_students,
        total_seats=metrics.total_seats,
        average_occupancy=occupancy,
    )

    return PlatformDashboardResponse(
        totals=totals,
        library_status=[
            PlatformDashboardStatusCount(
                status=LibraryStatus.PENDING,
                count=metrics.pending_libraries,
            ),
            PlatformDashboardStatusCount(
                status=LibraryStatus.ACTIVE,
                count=metrics.active_libraries,
            ),
            PlatformDashboardStatusCount(
                status=LibraryStatus.SUSPENDED,
                count=metrics.suspended_libraries,
            ),
        ],
        trend=_compose_trend(
            range_start,
            range_end,
            monthly_counts[0],
            monthly_counts[1],
            monthly_counts[2],
        ),
        top_libraries=[
            PlatformDashboardTopLibrary(
                id=record.library.id,
                code=record.library.code,
                name=record.library.name,
                city=record.library.city,
                state=record.library.state,
                student_count=record.student_count,
                seat_count=record.seat_count,
                occupied_seat_count=record.occupied_seat_count,
                occupancy_rate=(
                    round(record.occupied_seat_count * 100 / record.seat_count)
                    if record.seat_count
                    else 0
                ),
            )
            for record in top_records
        ],
        recent_activity=[
            PlatformDashboardActivity(
                id=record.audit_log.id,
                action=record.audit_log.action,
                entity_type=record.audit_log.entity_type,
                entity_id=record.audit_log.entity_id,
                description=ACTIVITY_LABELS.get(
                    record.audit_log.action,
                    record.audit_log.action.rsplit(".", 1)[-1]
                    .replace("_", " ")
                    .capitalize(),
                ),
                category=_activity_category(
                    record.audit_log.action,
                    record.audit_log.entity_type,
                ),
                actor=(
                    PlatformDashboardActivityActor(
                        id=record.audit_log.actor_user_id,
                        name=record.actor_name,
                    )
                    if record.audit_log.actor_user_id is not None
                    and record.actor_name is not None
                    else None
                ),
                created_at=record.audit_log.created_at,
            )
            for record in activity_records
        ],
        range=PlatformDashboardRange(
            start_month=_month_key(range_start),
            end_month=_month_key(range_end),
            timezone="UTC",
        ),
        last_updated=now,
    )


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
    locked_owner: User | None = None,
) -> tuple[uuid.UUID | None, User]:
    owner = locked_owner or repository.get_owner_user(
        db,
        owner_id,
        for_update=True,
    )
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
        owner = repository.get_owner_user(
            db,
            payload.owner_id,
            for_update=True,
        )
        if owner is None or not owner.is_active:
            raise BusinessRuleError(
                "The selected user is not an eligible active library owner.",
                code="PLATFORM_LIBRARY_OWNER_INVALID",
                details={"ownerId": str(payload.owner_id)},
            )
        library = repository.get_library(db, library_id, for_update=True)
        if library is None:
            raise _not_found()
        _validate_state(library, payload.expected_updated_at)
        previous_owner_id, owner = _assign_owner(
            db,
            library,
            payload.owner_id,
            now=_now(),
            locked_owner=owner,
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


def _effective_invitation_status(invitation: object | None) -> InvitationStatus | None:
    if invitation is None:
        return None
    if (
        invitation.status == InvitationStatus.PENDING
        and is_expired(invitation.expires_at)
    ):
        return InvitationStatus.EXPIRED
    return invitation.status


def _current_owner_memberships(
    user: User,
    memberships: tuple[LibraryMembership, ...] | list[LibraryMembership],
) -> list[LibraryMembership]:
    return [
        membership
        for membership in memberships
        if membership.status
        in {MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED}
        and membership.library.primary_owner_user_id == user.id
    ]


def _owner_record_response(
    record: repository.OwnerRecord,
    libraries: dict[uuid.UUID, Library],
) -> PlatformOwnerResponse:
    invitation = record.invitation
    if record.user is None:
        assert invitation is not None
        library = libraries.get(invitation.library_id)
        assignments = (
            [
                PlatformOwnerLibrarySummary(
                    id=library.id,
                    code=library.code,
                    name=library.name,
                    status=library.status,
                )
            ]
            if library is not None
            else []
        )
        return PlatformOwnerResponse(
            id=invitation.id,
            invitation_id=invitation.id,
            name=invitation.invitee_name or invitation.email.split("@", 1)[0],
            email=invitation.email,
            phone=invitation.invitee_phone,
            status=PlatformOwnerStatus.INVITED,
            invitation_status=_effective_invitation_status(invitation),
            invitation_expires_at=invitation.expires_at,
            assignments=assignments,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at,
        )

    user = record.user
    current_memberships = _current_owner_memberships(user, record.memberships)
    return PlatformOwnerResponse(
        id=user.id,
        user_id=user.id,
        invitation_id=invitation.id if invitation else None,
        name=user.full_name,
        email=user.email,
        phone=user.phone,
        status=(
            PlatformOwnerStatus.ACTIVE
            if user.is_active
            else PlatformOwnerStatus.SUSPENDED
        ),
        invitation_status=_effective_invitation_status(invitation),
        invitation_expires_at=invitation.expires_at if invitation else None,
        assignments=[
            PlatformOwnerLibrarySummary(
                id=membership.library.id,
                code=membership.library.code,
                name=membership.library.name,
                status=membership.library.status,
            )
            for membership in current_memberships
        ],
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _owner_libraries(
    db: Session,
    records: list[repository.OwnerRecord],
) -> dict[uuid.UUID, Library]:
    library_ids = {
        record.invitation.library_id
        for record in records
        if record.invitation is not None
        and record.invitation.library_id is not None
    }
    library_ids.update(
        membership.library_id
        for record in records
        for membership in record.memberships
    )
    return repository.get_libraries_by_ids(db, library_ids)


def list_owners(
    db: Session,
    pagination: PaginationParams,
    *,
    status: PlatformOwnerStatus | None = None,
    library_id: uuid.UUID | None = None,
    invitation_status: InvitationStatus | None = None,
) -> PlatformOwnerListResult:
    records = repository.list_owner_records(db)
    libraries = _owner_libraries(db, records)
    all_owners = [
        _owner_record_response(record, libraries) for record in records
    ]
    summary = PlatformOwnerListSummary(
        total=len(all_owners),
        active=sum(owner.status == PlatformOwnerStatus.ACTIVE for owner in all_owners),
        invited=sum(owner.status == PlatformOwnerStatus.INVITED for owner in all_owners),
        suspended=sum(
            owner.status == PlatformOwnerStatus.SUSPENDED for owner in all_owners
        ),
    )

    search = (pagination.search or "").strip().lower()
    filtered = [
        owner
        for owner in all_owners
        if (status is None or owner.status == status)
        and (
            invitation_status is None
            or owner.invitation_status == invitation_status
        )
        and (
            library_id is None
            or any(item.id == library_id for item in owner.assignments)
        )
        and (
            not search
            or search
            in " ".join(
                [
                    owner.name,
                    owner.email,
                    owner.phone or "",
                    *(item.name for item in owner.assignments),
                ]
            ).lower()
        )
    ]

    def sort_value(owner: PlatformOwnerResponse) -> object:
        created_timestamp = _utc(owner.created_at).timestamp()
        updated_timestamp = _utc(owner.updated_at).timestamp()
        login_timestamp = (
            _utc(owner.last_login_at).timestamp()
            if owner.last_login_at is not None
            else float("-inf")
        )
        values = {
            "name": owner.name.lower(),
            "email": owner.email.lower(),
            "status": owner.status.value,
            "libraryName": (
                owner.assignments[0].name.lower() if owner.assignments else ""
            ),
            "updatedAt": updated_timestamp,
            "lastLoginAt": login_timestamp,
            "createdAt": created_timestamp,
        }
        return values.get(pagination.sort_by, created_timestamp)

    filtered.sort(
        key=lambda owner: (sort_value(owner), str(owner.id)),
        reverse=pagination.sort_order == "desc",
    )
    total = len(filtered)
    offset = (pagination.page - 1) * pagination.page_size
    return PlatformOwnerListResult(
        owners=filtered[offset : offset + pagination.page_size],
        total=total,
        summary=summary,
    )


def get_owner(db: Session, owner_id: uuid.UUID) -> PlatformOwnerDetailResponse:
    record = repository.get_owner_record(db, owner_id)
    if record is None:
        raise ResourceNotFoundError(
            "Library owner not found.",
            code="PLATFORM_OWNER_NOT_FOUND",
        )
    response = _owner_record_response(record, _owner_libraries(db, [record]))
    return PlatformOwnerDetailResponse(
        **response.model_dump(),
        assignment_history=[
            PlatformOwnerAssignmentHistory(
                library_id=membership.library_id,
                library_name=membership.library.name,
                membership_status=membership.status,
                joined_at=membership.joined_at or membership.created_at,
                left_at=membership.left_at,
            )
            for membership in record.memberships
        ],
    )


def _validate_owner_phone(phone: str | None) -> None:
    if not phone:
        return
    digits = "".join(character for character in phone if character.isdigit())
    if not PHONE_ALLOWED.fullmatch(phone) or not 7 <= len(digits) <= 15:
        raise BusinessRuleError(
            "Enter a valid owner phone number.",
            code="PLATFORM_OWNER_PHONE_INVALID",
        )


def _validate_owner_state(user: User, expected_updated_at: datetime | None) -> None:
    if expected_updated_at is not None and not _timestamp_equal(
        user.updated_at,
        expected_updated_at,
    ):
        raise ConflictError(
            "This owner changed after it was opened. Refresh and try again.",
            code="PLATFORM_OWNER_STATE_CHANGED",
            details={
                "ownerId": str(user.id),
                "updatedAt": user.updated_at.isoformat(),
            },
        )


def _owner_response_by_id(db: Session, owner_id: uuid.UUID) -> PlatformOwnerResponse:
    record = repository.get_owner_record(db, owner_id)
    if record is None:
        raise ResourceNotFoundError(
            "Library owner not found.",
            code="PLATFORM_OWNER_NOT_FOUND",
        )
    return _owner_record_response(record, _owner_libraries(db, [record]))


def _expire_pending_invitation(invitation: object | None) -> bool:
    if (
        invitation is not None
        and invitation.status == InvitationStatus.PENDING
        and is_expired(invitation.expires_at)
    ):
        invitation.status = InvitationStatus.EXPIRED
        return True
    return False


def _assign_owner_to_empty_library(
    db: Session,
    user: User,
    target_library_id: uuid.UUID,
    *,
    now: datetime,
) -> tuple[uuid.UUID | None, Library]:
    memberships = repository.owner_memberships(db, user.id, for_update=True)
    current = next(
        (
            membership
            for membership in memberships
            if membership.status == MembershipStatus.ACTIVE
        ),
        None,
    )
    source_library_id = current.library_id if current is not None else None
    libraries = repository.get_libraries_for_update(
        db,
        {target_library_id}
        | ({source_library_id} if source_library_id is not None else set()),
    )
    target = libraries.get(target_library_id)
    if target is None:
        raise ResourceNotFoundError(
            "Target library not found.",
            code="PLATFORM_LIBRARY_NOT_FOUND",
        )
    if target.status == LibraryStatus.SUSPENDED:
        raise BusinessRuleError(
            "A suspended library cannot receive an owner.",
            code="PLATFORM_OWNER_LIBRARY_INELIGIBLE",
        )
    if target.primary_owner_user_id not in {None, user.id}:
        raise ConflictError(
            "The target library already has an assigned owner.",
            code="PLATFORM_OWNER_ASSIGNMENT_CONFLICT",
            details={"libraryId": str(target.id)},
        )
    if source_library_id == target.id and target.primary_owner_user_id == user.id:
        raise ConflictError(
            "This owner is already assigned to the target library.",
            code="PLATFORM_OWNER_ASSIGNMENT_CONFLICT",
        )

    if current is not None:
        source = libraries.get(current.library_id)
        if source is not None and source.primary_owner_user_id == user.id:
            source.primary_owner_user_id = None
            source.last_activity_at = now
            source.updated_at = now
        current.status = MembershipStatus.LEFT
        current.left_at = now

    target_membership = next(
        (
            membership
            for membership in memberships
            if membership.library_id == target.id
        ),
        None,
    )
    if target_membership is None:
        target_membership = LibraryMembership(
            library_id=target.id,
            user_id=user.id,
            role=RoleName.LIBRARY_OWNER,
            status=MembershipStatus.ACTIVE,
            joined_at=now,
        )
        db.add(target_membership)
    else:
        target_membership.role = RoleName.LIBRARY_OWNER
        target_membership.status = MembershipStatus.ACTIVE
        target_membership.joined_at = now
        target_membership.left_at = None
    target.primary_owner_user_id = user.id
    target.last_activity_at = now
    target.updated_at = now
    user.updated_at = now
    db.flush()
    return source_library_id, target


def invite_owner(
    db: Session,
    payload: PlatformOwnerInvite,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformOwnerInvitationResponse:
    _validate_owner_phone(payload.phone)
    email = payload.email.strip().lower()
    try:
        existing_user = repository.get_user_by_email(db, email, for_update=True)
        target = repository.get_library(db, payload.library_id, for_update=True)
        if target is None:
            raise ResourceNotFoundError(
                "Target library not found.",
                code="PLATFORM_LIBRARY_NOT_FOUND",
            )
        if target.status == LibraryStatus.SUSPENDED:
            raise BusinessRuleError(
                "A suspended library cannot receive an owner invitation.",
                code="PLATFORM_OWNER_LIBRARY_INELIGIBLE",
            )
        if target.primary_owner_user_id is not None:
            raise ConflictError(
                "The target library already has an assigned owner.",
                code="PLATFORM_OWNER_ASSIGNMENT_CONFLICT",
            )

        pending_by_email = repository.pending_owner_invitation(
            db,
            email=email,
            for_update=True,
        )
        pending_by_library = repository.pending_owner_invitation(
            db,
            library_id=target.id,
            for_update=True,
        )
        expired_previous = False
        for pending in {
            invitation
            for invitation in (pending_by_email, pending_by_library)
            if invitation is not None
        }:
            expired_previous = _expire_pending_invitation(pending) or expired_previous
            if pending.status == InvitationStatus.PENDING:
                code = (
                    "PLATFORM_OWNER_INVITATION_EXISTS"
                    if pending.email.lower() == email
                    else "PLATFORM_OWNER_ASSIGNMENT_CONFLICT"
                )
                raise ConflictError(
                    "An active owner invitation already conflicts with this request.",
                    code=code,
                    details={"invitationId": str(pending.id)},
                )
        if expired_previous:
            db.flush()

        if existing_user is not None:
            owner = repository.get_owner_user(db, existing_user.id)
            if (
                owner is None
                or owner.deleted_at is not None
                or not owner.is_active
            ):
                raise ConflictError(
                    "This email belongs to an account that cannot be assigned as an owner.",
                    code="PLATFORM_OWNER_EMAIL_EXISTS",
                )
            existing_membership = repository.get_active_owner_membership(
                db,
                owner.id,
                for_update=True,
            )
            if existing_membership is not None:
                raise ConflictError(
                    "This owner already manages a library. Use the explicit reassignment action.",
                    code="PLATFORM_OWNER_ASSIGNMENT_CONFLICT",
                    details={
                        "ownerId": str(owner.id),
                        "assignedLibraryId": str(existing_membership.library_id),
                    },
                )
            source_library_id, assigned_library = _assign_owner_to_empty_library(
                db,
                owner,
                target.id,
                now=_now(),
            )
            write_audit_log(
                db,
                library_id=assigned_library.id,
                actor_user_id=actor_user_id,
                action="platform.owner.assigned",
                entity_type="user",
                entity_id=str(owner.id),
                old_values={
                    "libraryId": (
                        str(source_library_id) if source_library_id else None
                    )
                },
                new_values={"libraryId": str(assigned_library.id)},
                request_context=audit_context,
            )
            db.commit()
            db.expire_all()
            return PlatformOwnerInvitationResponse(
                owner=_owner_response_by_id(db, owner.id),
                created_invitation=False,
            )

        created = create_account_invitation(
            db,
            library_id=target.id,
            email=email,
            role=RoleName.LIBRARY_OWNER,
            invited_by_user_id=actor_user_id,
            invitee_name=payload.name,
            invitee_phone=payload.phone or None,
        )
        action = (
            "platform.owner.invitation_reissued"
            if expired_previous
            else "platform.owner.invited"
        )
        write_audit_log(
            db,
            library_id=target.id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type="account_invitation",
            entity_id=str(created.invitation.id),
            new_values={
                "email": email,
                "libraryId": str(target.id),
                "role": RoleName.LIBRARY_OWNER.value,
            },
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        record = repository.OwnerRecord(
            user=None,
            invitation=created.invitation,
            memberships=(),
        )
        return PlatformOwnerInvitationResponse(
            owner=_owner_record_response(record, {target.id: target}),
            created_invitation=True,
            invitation_setup_url=created.setup_url,
        )
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "An owner invitation already exists for this email or library.",
            code="PLATFORM_OWNER_INVITATION_EXISTS",
        ) from exc
    except Exception:
        db.rollback()
        raise


def update_owner(
    db: Session,
    owner_id: uuid.UUID,
    payload: PlatformOwnerUpdate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformOwnerResponse:
    try:
        user = repository.get_owner_user(db, owner_id, for_update=True)
        if user is None:
            raise ResourceNotFoundError(
                "Accepted library owner not found.",
                code="PLATFORM_OWNER_NOT_FOUND",
            )
        _validate_owner_state(user, payload.expected_updated_at)
        fields = payload.model_fields_set - {"expected_updated_at"}
        if not fields:
            raise BusinessRuleError(
                "Provide at least one editable owner field.",
                code="PLATFORM_OWNER_UPDATE_EMPTY",
            )
        if "name" in fields and payload.name is None:
            raise BusinessRuleError(
                "Owner name cannot be null.",
                code="PLATFORM_OWNER_NAME_REQUIRED",
            )
        _validate_owner_phone(payload.phone if "phone" in fields else user.phone)

        old_values: dict[str, object] = {}
        new_values: dict[str, object] = {}
        updates = {
            "full_name": payload.name,
            "phone": payload.phone or None,
        }
        requested = {
            "full_name": "name" in fields,
            "phone": "phone" in fields,
        }
        for field, value in updates.items():
            if requested[field] and getattr(user, field) != value:
                old_values[field] = getattr(user, field)
                new_values[field] = value
                setattr(user, field, value)
        if not new_values:
            raise ConflictError(
                "The submitted values do not change this owner.",
                code="PLATFORM_OWNER_STATE_CHANGED",
            )
        user.updated_at = _now()
        membership = repository.get_active_owner_membership(db, user.id)
        write_audit_log(
            db,
            library_id=membership.library_id if membership else None,
            actor_user_id=actor_user_id,
            action="platform.owner.edited",
            entity_type="user",
            entity_id=str(user.id),
            old_values=old_values,
            new_values=new_values,
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        return _owner_response_by_id(db, user.id)
    except Exception:
        db.rollback()
        raise


def assign_owner(
    db: Session,
    owner_id: uuid.UUID,
    payload: PlatformOwnerAssignmentUpdate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformOwnerResponse:
    try:
        user = repository.get_owner_user(db, owner_id, for_update=True)
        if user is None:
            raise ResourceNotFoundError(
                "Accepted library owner not found.",
                code="PLATFORM_OWNER_NOT_FOUND",
            )
        if not user.is_active:
            raise BusinessRuleError(
                "A suspended owner cannot be assigned.",
                code="PLATFORM_OWNER_ASSIGNMENT_CONFLICT",
            )
        _validate_owner_state(user, payload.expected_updated_at)
        source_library_id, target = _assign_owner_to_empty_library(
            db,
            user,
            payload.library_id,
            now=_now(),
        )
        write_audit_log(
            db,
            library_id=target.id,
            actor_user_id=actor_user_id,
            action=(
                "platform.owner.reassigned"
                if source_library_id is not None
                else "platform.owner.assigned"
            ),
            entity_type="user",
            entity_id=str(user.id),
            old_values={
                "libraryId": str(source_library_id) if source_library_id else None
            },
            new_values={"libraryId": str(target.id)},
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        return _owner_response_by_id(db, user.id)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The owner assignment conflicts with current membership data.",
            code="PLATFORM_OWNER_ASSIGNMENT_CONFLICT",
        ) from exc
    except Exception:
        db.rollback()
        raise


def change_owner_status(
    db: Session,
    owner_id: uuid.UUID,
    payload: PlatformOwnerStatusUpdate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformOwnerResponse:
    try:
        user = repository.get_owner_user(db, owner_id, for_update=True)
        if user is None:
            raise ResourceNotFoundError(
                "Accepted library owner not found.",
                code="PLATFORM_OWNER_NOT_FOUND",
            )
        _validate_owner_state(user, payload.expected_updated_at)
        current_status = (
            PlatformOwnerStatusAction.ACTIVE
            if user.is_active
            else PlatformOwnerStatusAction.SUSPENDED
        )
        if payload.status == current_status:
            raise ConflictError(
                f"This owner is already {current_status.value}.",
                code="PLATFORM_OWNER_INVALID_STATUS",
            )
        if (
            payload.status == PlatformOwnerStatusAction.SUSPENDED
            and not payload.reason
        ):
            raise BusinessRuleError(
                "A suspension reason is required.",
                code="PLATFORM_OWNER_SUSPENSION_REASON_REQUIRED",
            )

        now = _now()
        memberships = repository.owner_memberships(db, user.id, for_update=True)
        sessions_revoked = 0
        if payload.status == PlatformOwnerStatusAction.SUSPENDED:
            user.is_active = False
            for membership in memberships:
                if membership.status == MembershipStatus.ACTIVE:
                    membership.status = MembershipStatus.SUSPENDED
            sessions_revoked = repository.revoke_user_sessions(
                db,
                user.id,
                revoked_at=now,
            )
        else:
            user.is_active = True
            for membership in memberships:
                if membership.status == MembershipStatus.SUSPENDED:
                    membership.status = MembershipStatus.ACTIVE
        user.updated_at = now
        current_membership = next(
            (
                membership
                for membership in memberships
                if membership.status
                in {MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED}
            ),
            None,
        )
        write_audit_log(
            db,
            library_id=(
                current_membership.library_id if current_membership else None
            ),
            actor_user_id=actor_user_id,
            action=(
                "platform.owner.suspended"
                if payload.status == PlatformOwnerStatusAction.SUSPENDED
                else "platform.owner.activated"
            ),
            entity_type="user",
            entity_id=str(user.id),
            old_values={"status": current_status.value},
            new_values={"status": payload.status.value},
            context={
                "reason": payload.reason,
                "sessionsRevoked": sessions_revoked,
            },
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        return _owner_response_by_id(db, user.id)
    except Exception:
        db.rollback()
        raise
