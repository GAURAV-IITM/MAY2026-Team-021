"""Platform-scoped persistence for Super Admin library management."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.enums import LibraryStatus, MembershipStatus, RoleName
from app.models.identity import Role, User, UserRole
from app.models.library import Library, LibraryMembership
from app.models.seat import Seat
from app.models.student import Student
from app.schemas.common import PaginationParams
from app.schemas.platform import PlatformLibrarySummary


SORT_COLUMNS = {
    "createdAt": Library.created_at,
    "updatedAt": Library.updated_at,
    "name": Library.name,
    "code": Library.code,
    "status": Library.status,
    "city": Library.city,
    "state": Library.state,
    "lastActivityAt": Library.last_activity_at,
}


@dataclass(frozen=True, slots=True)
class LibraryRecord:
    library: Library
    student_count: int
    seat_count: int
    membership_count: int


def _list_conditions(
    pagination: PaginationParams,
    *,
    status: LibraryStatus | None,
    owner_id: uuid.UUID | None,
    state: str | None,
) -> list[object]:
    conditions: list[object] = [Library.deleted_at.is_(None)]
    if pagination.search:
        pattern = f"%{pagination.search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Library.name).like(pattern),
                func.lower(Library.code).like(pattern),
                func.lower(Library.contact_email).like(pattern),
                func.lower(func.coalesce(Library.contact_phone, "")).like(pattern),
                func.lower(func.coalesce(Library.city, "")).like(pattern),
                func.lower(func.coalesce(Library.state, "")).like(pattern),
                func.lower(func.coalesce(Library.address_line, "")).like(pattern),
            )
        )
    if status is not None:
        conditions.append(Library.status == status)
    if owner_id is not None:
        conditions.append(Library.primary_owner_user_id == owner_id)
    if state:
        conditions.append(func.lower(Library.state) == state.strip().lower())
    return conditions


def list_libraries(
    db: Session,
    pagination: PaginationParams,
    *,
    status: LibraryStatus | None = None,
    owner_id: uuid.UUID | None = None,
    state: str | None = None,
) -> tuple[list[LibraryRecord], int, PlatformLibrarySummary]:
    conditions = _list_conditions(
        pagination,
        status=status,
        owner_id=owner_id,
        state=state,
    )
    total = db.scalar(select(func.count(Library.id)).where(*conditions)) or 0

    student_count = (
        select(func.count(Student.id))
        .where(
            Student.library_id == Library.id,
            Student.deleted_at.is_(None),
        )
        .correlate(Library)
        .scalar_subquery()
    )
    seat_count = (
        select(func.count(Seat.id))
        .where(
            Seat.library_id == Library.id,
            Seat.deleted_at.is_(None),
        )
        .correlate(Library)
        .scalar_subquery()
    )
    membership_count = (
        select(func.count(LibraryMembership.id))
        .where(
            LibraryMembership.library_id == Library.id,
            LibraryMembership.status == MembershipStatus.ACTIVE,
        )
        .correlate(Library)
        .scalar_subquery()
    )
    sort_column = SORT_COLUMNS.get(pagination.sort_by, Library.created_at)
    ordering = sort_column.asc() if pagination.sort_order == "asc" else sort_column.desc()
    rows = db.execute(
        select(Library, student_count, seat_count, membership_count)
        .options(joinedload(Library.primary_owner))
        .where(*conditions)
        .order_by(ordering, Library.id.asc())
        .offset((pagination.page - 1) * pagination.page_size)
        .limit(pagination.page_size)
    ).all()

    summary_values = db.execute(
        select(
            func.count(Library.id),
            func.sum(case((Library.status == LibraryStatus.ACTIVE, 1), else_=0)),
            func.sum(case((Library.status == LibraryStatus.PENDING, 1), else_=0)),
            func.sum(case((Library.status == LibraryStatus.SUSPENDED, 1), else_=0)),
        ).where(Library.deleted_at.is_(None))
    ).one()
    summary = PlatformLibrarySummary(
        total=summary_values[0] or 0,
        active=summary_values[1] or 0,
        pending=summary_values[2] or 0,
        suspended=summary_values[3] or 0,
    )
    return (
        [
            LibraryRecord(
                library=row[0],
                student_count=row[1] or 0,
                seat_count=row[2] or 0,
                membership_count=row[3] or 0,
            )
            for row in rows
        ],
        total,
        summary,
    )


def get_library(
    db: Session,
    library_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> Library | None:
    query = select(Library).where(
        Library.id == library_id,
        Library.deleted_at.is_(None),
    )
    if for_update:
        query = query.with_for_update(of=Library)
    else:
        query = query.options(joinedload(Library.primary_owner))
    return db.scalar(query)


def get_library_counts(db: Session, library_id: uuid.UUID) -> tuple[int, int, int]:
    return (
        db.scalar(
            select(func.count(Student.id)).where(
                Student.library_id == library_id,
                Student.deleted_at.is_(None),
            )
        )
        or 0,
        db.scalar(
            select(func.count(Seat.id)).where(
                Seat.library_id == library_id,
                Seat.deleted_at.is_(None),
            )
        )
        or 0,
        db.scalar(
            select(func.count(LibraryMembership.id)).where(
                LibraryMembership.library_id == library_id,
                LibraryMembership.status == MembershipStatus.ACTIVE,
            )
        )
        or 0,
    )


def library_identity_exists(
    db: Session,
    *,
    name: str,
    code: str | None = None,
    exclude_library_id: uuid.UUID | None = None,
) -> bool:
    identity = [func.lower(Library.name) == name.strip().lower()]
    if code is not None:
        identity.append(func.lower(Library.code) == code.strip().lower())
    conditions: list[object] = [
        Library.deleted_at.is_(None),
        or_(*identity),
    ]
    if exclude_library_id is not None:
        conditions.append(Library.id != exclude_library_id)
    return db.scalar(select(Library.id).where(*conditions).limit(1)) is not None


def add_library(db: Session, library: Library) -> Library:
    db.add(library)
    db.flush()
    return library


def get_owner_user(
    db: Session,
    owner_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> User | None:
    query = (
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .options(selectinload(User.role_links).selectinload(UserRole.role))
        .where(
            User.id == owner_id,
            User.deleted_at.is_(None),
            Role.name == RoleName.LIBRARY_OWNER,
        )
    )
    if for_update:
        query = query.with_for_update(of=User)
    return db.scalar(query)


def get_active_owner_membership(
    db: Session,
    owner_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> LibraryMembership | None:
    query = select(LibraryMembership).where(
        LibraryMembership.user_id == owner_id,
        LibraryMembership.role == RoleName.LIBRARY_OWNER,
        LibraryMembership.status == MembershipStatus.ACTIVE,
    )
    if for_update:
        query = query.with_for_update(of=LibraryMembership)
    return db.scalar(query)


def get_membership(
    db: Session,
    library_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> LibraryMembership | None:
    query = select(LibraryMembership).where(
        LibraryMembership.library_id == library_id,
        LibraryMembership.user_id == user_id,
    )
    if for_update:
        query = query.with_for_update(of=LibraryMembership)
    return db.scalar(query)


def list_eligible_owners(db: Session) -> list[User]:
    active_owner_membership = (
        select(LibraryMembership.id)
        .where(
            LibraryMembership.user_id == User.id,
            LibraryMembership.role == RoleName.LIBRARY_OWNER,
            LibraryMembership.status == MembershipStatus.ACTIVE,
        )
        .exists()
    )
    return list(
        db.scalars(
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                Role.name == RoleName.LIBRARY_OWNER,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
                ~active_owner_membership,
            )
            .order_by(User.full_name.asc(), User.id.asc())
        )
    )
