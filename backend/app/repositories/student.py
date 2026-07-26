"""Tenant-scoped student persistence operations."""
from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import InvitationStatus, StudentStatus
from app.models.identity import AccountInvitation
from app.models.student import Student
from app.schemas.common import PaginationParams


SORT_COLUMNS = {
    "createdAt": Student.created_at,
    "updatedAt": Student.updated_at,
    "firstName": Student.first_name,
    "joiningDate": Student.joined_on,
    "status": Student.status,
}


def list_students(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    status: StudentStatus | None = None,
) -> tuple[list[Student], int]:
    conditions = [
        Student.library_id == library_id,
        Student.deleted_at.is_(None),
    ]
    if status is not None:
        conditions.append(Student.status == status)
    if pagination.search:
        search = f"%{pagination.search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Student.first_name).like(search),
                func.lower(Student.last_name).like(search),
                func.lower(Student.email).like(search),
                func.lower(Student.enrollment_number).like(search),
                func.lower(Student.phone).like(search),
            )
        )

    total = db.scalar(select(func.count(Student.id)).where(*conditions)) or 0
    sort_column = SORT_COLUMNS.get(pagination.sort_by, Student.created_at)
    ordering = (
        sort_column.asc()
        if pagination.sort_order == "asc"
        else sort_column.desc()
    )
    students = list(
        db.scalars(
            select(Student)
            .where(*conditions)
            .order_by(ordering, Student.id.asc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
    )
    return students, total


def get_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Student | None:
    return db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.library_id == library_id,
            Student.deleted_at.is_(None),
        )
    )


def find_by_email(
    db: Session,
    library_id: uuid.UUID,
    email: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> Student | None:
    query = select(Student).where(
        Student.library_id == library_id,
        func.lower(Student.email) == email.lower(),
        Student.deleted_at.is_(None),
    )
    if exclude_id:
        query = query.where(Student.id != exclude_id)
    return db.scalar(query)


def find_by_enrollment(
    db: Session,
    library_id: uuid.UUID,
    enrollment_number: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> Student | None:
    query = select(Student).where(
        Student.library_id == library_id,
        func.lower(Student.enrollment_number) == enrollment_number.lower(),
        Student.deleted_at.is_(None),
    )
    if exclude_id:
        query = query.where(Student.id != exclude_id)
    return db.scalar(query)


def generate_enrollment_number(db: Session, library_id: uuid.UUID) -> str:
    sequence = (
        db.scalar(
            select(func.count(Student.id)).where(Student.library_id == library_id)
        )
        or 0
    ) + 1
    while True:
        candidate = f"STU-{sequence:05d}"
        if find_by_enrollment(db, library_id, candidate) is None:
            return candidate
        sequence += 1


def latest_invitation(
    db: Session,
    library_id: uuid.UUID,
    email: str,
) -> AccountInvitation | None:
    return db.scalar(
        select(AccountInvitation)
        .where(
            AccountInvitation.library_id == library_id,
            func.lower(AccountInvitation.email) == email.lower(),
        )
        .order_by(AccountInvitation.created_at.desc())
    )


def pending_invitation(
    db: Session,
    library_id: uuid.UUID,
    email: str,
) -> AccountInvitation | None:
    return db.scalar(
        select(AccountInvitation).where(
            AccountInvitation.library_id == library_id,
            func.lower(AccountInvitation.email) == email.lower(),
            AccountInvitation.status == InvitationStatus.PENDING,
        )
    )
