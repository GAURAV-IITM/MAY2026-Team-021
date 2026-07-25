"""Student management, status, and account invitation use cases."""
from __future__ import annotations

import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.core.security import hash_token
from app.models.enums import InvitationStatus, MembershipStatus, RoleName, StudentStatus
from app.models.identity import AccountInvitation, User
from app.models.library import LibraryMembership
from app.models.student import Student
from app.repositories import student as repository
from app.schemas.common import PaginationParams
from app.schemas.student import (
    StudentCreate,
    StudentInvitationResponse,
    StudentResponse,
    StudentUpdate,
)


def _clean(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _setup_url(token: str) -> str:
    return f"{settings.frontend_base_url}/accept-invitation?token={quote(token)}"


def _student_response(
    db: Session,
    student: Student,
    *,
    setup_url: str | None = None,
) -> StudentResponse:
    invitation = repository.latest_invitation(db, student.library_id, student.email)
    return StudentResponse(
        id=student.id,
        enrollment_number=student.enrollment_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        phone=student.phone,
        address=student.address,
        guardian_name=student.guardian_name,
        guardian_phone=student.guardian_phone,
        date_of_birth=student.date_of_birth,
        preferred_language=student.preferred_language,
        joining_date=student.joined_on,
        left_on=student.left_on,
        fee_amount=float(student.monthly_fee),
        status=student.status,
        notes=student.notes,
        portal_access_status="active" if student.user_id else "not_activated",
        invitation_status=invitation.status if invitation else None,
        invitation_expires_at=invitation.expires_at if invitation else None,
        invitation_setup_url=setup_url,
        created_at=student.created_at,
        updated_at=student.updated_at,
    )


def list_students(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    status: StudentStatus | None = None,
) -> tuple[list[StudentResponse], int]:
    students, total = repository.list_students(
        db,
        library_id,
        pagination,
        status=status,
    )
    return [_student_response(db, student) for student in students], total


def get_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> StudentResponse:
    student = repository.get_student(db, library_id, student_id)
    if student is None:
        raise ResourceNotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    return _student_response(db, student)


def _ensure_unique(
    db: Session,
    library_id: uuid.UUID,
    *,
    email: str,
    enrollment_number: str,
    exclude_id: uuid.UUID | None = None,
) -> None:
    if repository.find_by_email(
        db,
        library_id,
        email,
        exclude_id=exclude_id,
    ):
        raise ConflictError(
            "A student with this email already exists in the library.",
            code="STUDENT_EMAIL_EXISTS",
        )
    if repository.find_by_enrollment(
        db,
        library_id,
        enrollment_number,
        exclude_id=exclude_id,
    ):
        raise ConflictError(
            "A student with this enrollment number already exists.",
            code="STUDENT_ENROLLMENT_EXISTS",
        )


def _create_invitation(
    db: Session,
    student: Student,
    invited_by_user_id: uuid.UUID,
) -> StudentInvitationResponse:
    if student.user_id:
        raise ConflictError(
            "This student already has portal access.",
            code="STUDENT_PORTAL_ALREADY_ACTIVE",
        )
    existing_user = db.scalar(
        select(User).where(
            User.email == student.email,
            User.deleted_at.is_(None),
        )
    )
    if existing_user:
        raise ConflictError(
            "An account already exists for this email address.",
            code="ACCOUNT_EMAIL_EXISTS",
        )

    pending = repository.pending_invitation(db, student.library_id, student.email)
    if pending:
        pending.status = InvitationStatus.REVOKED
        db.flush()

    raw_token = secrets.token_urlsafe(48)
    invitation = AccountInvitation(
        library_id=student.library_id,
        email=student.email,
        role=RoleName.STUDENT,
        token_hash=hash_token(raw_token),
        status=InvitationStatus.PENDING,
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.account_invitation_expire_hours),
        invited_by_user_id=invited_by_user_id,
    )
    db.add(invitation)
    db.flush()
    return StudentInvitationResponse(
        student_id=student.id,
        email=student.email,
        status=invitation.status,
        expires_at=invitation.expires_at,
        setup_url=_setup_url(raw_token),
    )


def create_student(
    db: Session,
    library_id: uuid.UUID,
    invited_by_user_id: uuid.UUID,
    payload: StudentCreate,
) -> StudentResponse:
    email = payload.email.strip().lower()
    enrollment = (
        _clean(payload.enrollment_number)
        or repository.generate_enrollment_number(db, library_id)
    )
    _ensure_unique(
        db,
        library_id,
        email=email,
        enrollment_number=enrollment,
    )
    student = Student(
        library_id=library_id,
        enrollment_number=enrollment,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        phone=payload.phone.strip(),
        address=_clean(payload.address),
        guardian_name=_clean(payload.guardian_name),
        guardian_phone=_clean(payload.guardian_phone),
        date_of_birth=payload.date_of_birth,
        preferred_language=payload.preferred_language.strip().lower(),
        joined_on=payload.joining_date,
        monthly_fee=Decimal(str(payload.fee_amount)),
        status=payload.status,
        notes=_clean(payload.notes),
    )
    db.add(student)
    try:
        db.flush()
        invitation = (
            _create_invitation(db, student, invited_by_user_id)
            if payload.send_invitation
            else None
        )
        db.commit()
        db.refresh(student)
        return _student_response(
            db,
            student,
            setup_url=invitation.setup_url if invitation else None,
        )
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The student conflicts with an existing record.",
            code="STUDENT_CONFLICT",
        ) from exc
    except Exception:
        db.rollback()
        raise


def update_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
    payload: StudentUpdate,
) -> StudentResponse:
    student = repository.get_student(db, library_id, student_id)
    if student is None:
        raise ResourceNotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    changes = payload.model_dump(exclude_unset=True)
    previous_email = student.email
    email = str(changes.get("email", student.email)).strip().lower()
    enrollment = str(
        changes.get("enrollment_number", student.enrollment_number)
    ).strip()
    _ensure_unique(
        db,
        library_id,
        email=email,
        enrollment_number=enrollment,
        exclude_id=student.id,
    )
    linked_user = db.get(User, student.user_id) if student.user_id else None
    if linked_user and email != previous_email:
        email_owner = db.scalar(
            select(User.id).where(
                User.email == email,
                User.id != linked_user.id,
                User.deleted_at.is_(None),
            )
        )
        if email_owner:
            raise ConflictError(
                "Another account already uses this email address.",
                code="ACCOUNT_EMAIL_EXISTS",
            )
        linked_user.email = email
    if email != previous_email:
        pending = repository.pending_invitation(
            db,
            library_id,
            previous_email,
        )
        if pending:
            pending.status = InvitationStatus.REVOKED

    mapping = {
        "enrollment_number": "enrollment_number",
        "first_name": "first_name",
        "last_name": "last_name",
        "email": "email",
        "phone": "phone",
        "address": "address",
        "guardian_name": "guardian_name",
        "guardian_phone": "guardian_phone",
        "date_of_birth": "date_of_birth",
        "preferred_language": "preferred_language",
        "joining_date": "joined_on",
        "status": "status",
        "notes": "notes",
    }
    for field, attribute in mapping.items():
        if field in changes:
            value = changes[field]
            if isinstance(value, str):
                value = value.strip()
            setattr(student, attribute, value)
    if "fee_amount" in changes:
        student.monthly_fee = Decimal(str(changes["fee_amount"]))
    if linked_user:
        linked_user.full_name = f"{student.first_name} {student.last_name}".strip()
        linked_user.phone = student.phone
    _apply_status_side_effects(db, student, student.status)
    try:
        db.commit()
        db.refresh(student)
        return _student_response(db, student)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The student conflicts with an existing record.",
            code="STUDENT_CONFLICT",
        ) from exc


def _apply_status_side_effects(
    db: Session,
    student: Student,
    new_status: StudentStatus,
) -> None:
    student.status = new_status
    student.left_on = date.today() if new_status == StudentStatus.LEFT else None
    if student.user_id is None:
        return
    user = db.get(User, student.user_id)
    membership = db.scalar(
        select(LibraryMembership).where(
            LibraryMembership.library_id == student.library_id,
            LibraryMembership.user_id == student.user_id,
        )
    )
    is_active = new_status == StudentStatus.ACTIVE
    if user:
        user.is_active = is_active
    if membership:
        membership.status = (
            MembershipStatus.ACTIVE
            if is_active
            else (
                MembershipStatus.LEFT
                if new_status == StudentStatus.LEFT
                else MembershipStatus.SUSPENDED
            )
        )


def change_status(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
    status: StudentStatus,
) -> StudentResponse:
    student = repository.get_student(db, library_id, student_id)
    if student is None:
        raise ResourceNotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    _apply_status_side_effects(db, student, status)
    db.commit()
    db.refresh(student)
    return _student_response(db, student)


def delete_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
) -> None:
    student = repository.get_student(db, library_id, student_id)
    if student is None:
        raise ResourceNotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    _apply_status_side_effects(db, student, StudentStatus.LEFT)
    student.deleted_at = datetime.now(timezone.utc)
    pending = repository.pending_invitation(db, library_id, student.email)
    if pending:
        pending.status = InvitationStatus.REVOKED
    db.commit()


def invite_student(
    db: Session,
    library_id: uuid.UUID,
    student_id: uuid.UUID,
    invited_by_user_id: uuid.UUID,
) -> StudentInvitationResponse:
    student = repository.get_student(db, library_id, student_id)
    if student is None:
        raise ResourceNotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    invitation = _create_invitation(db, student, invited_by_user_id)
    db.commit()
    return invitation
