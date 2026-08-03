"""Authentication use cases and session lifecycle."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    is_expired,
    new_refresh_token,
    verify_password,
)
from app.models.enums import (
    InvitationStatus,
    LibraryStatus,
    MembershipStatus,
    RoleName,
    StudentStatus,
)
from app.models.identity import AccountInvitation, Role, User, UserRole, UserSession
from app.models.library import Library, LibraryMembership, LibrarySettings
from app.models.seat import Floor, Seat, Shift
from app.models.student import Student
from app.schemas.auth import (
    AcceptInvitationResponse,
    AuthResponse,
    RegisterLibraryRequest,
    UserResponse,
    ValidateInvitationResponse,
)


DEFAULT_SHIFTS = (
    ("Morning", time(6, 0), time(12, 0)),
    ("Afternoon", time(12, 0), time(18, 0)),
    ("Evening", time(18, 0), time(23, 59)),
)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials or session.",
    )


def _role_label(role: RoleName) -> str:
    return {
        RoleName.LIBRARY_OWNER: "admin",
        RoleName.SUPER_ADMIN: "superadmin",
    }.get(role, role.value)


def get_active_membership(
    db: Session,
    user_id: uuid.UUID,
) -> LibraryMembership | None:
    return db.scalar(
        select(LibraryMembership)
        .join(Library, Library.id == LibraryMembership.library_id)
        .options(selectinload(LibraryMembership.library))
        .where(
            LibraryMembership.user_id == user_id,
            LibraryMembership.status == MembershipStatus.ACTIVE,
            Library.status == LibraryStatus.ACTIVE,
            Library.deleted_at.is_(None),
        )
        .order_by(LibraryMembership.joined_at.asc())
    )


def user_can_authenticate(db: Session, user: User | None) -> bool:
    if (
        user is None
        or not user.is_active
        or user.deleted_at is not None
    ):
        return False

    roles = {link.role.name for link in user.role_links}
    if RoleName.SUPER_ADMIN in roles:
        return True
    if not roles:
        return False
    return get_active_membership(db, user.id) is not None


def user_response(db: Session, user: User) -> UserResponse:
    roles = [link.role.name for link in user.role_links]
    membership = get_active_membership(db, user.id)
    role = membership.role if membership else (roles[0] if roles else RoleName.STUDENT)
    library = membership.library if membership else None
    return UserResponse(
        id=user.id,
        name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=_role_label(role),
        library_id=membership.library_id if membership else None,
        library_name=library.name if library else None,
    )


def _auth_response(
    db: Session,
    user: User,
    session: UserSession,
    refresh_token: str,
) -> AuthResponse:
    roles = [link.role.name.value for link in user.role_links]
    return AuthResponse(
        access_token=create_access_token(
            subject=str(user.id),
            session_id=str(session.id),
            roles=roles,
        ),
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_response(db, user),
    )


def _create_session(
    db: Session,
    user: User,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResponse:
    refresh_token = new_refresh_token()
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.flush()
    return _auth_response(db, user, session, refresh_token)


def _initialize_library_resources(
    db: Session,
    library: Library,
    seat_count: int,
) -> None:
    floor = Floor(
        library=library,
        name="Floor 1",
        code="F1",
        level_number=1,
        sort_order=1,
    )
    shifts = [
        Shift(
            library=library,
            name=name,
            start_time=start_time,
            end_time=end_time,
            crosses_midnight=False,
            is_default=True,
            is_active=True,
        )
        for name, start_time, end_time in DEFAULT_SHIFTS
    ]
    seats = [
        Seat(
            library=library,
            floor=floor,
            seat_number=f"A-{sequence:02d}",
            notes="Created during library registration.",
        )
        for sequence in range(1, seat_count + 1)
    ]
    db.add(LibrarySettings(library=library))
    db.add(floor)
    db.add_all(shifts)
    db.add_all(seats)


def register_library(
    db: Session,
    payload: RegisterLibraryRequest,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResponse:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email address.",
        )

    try:
        code_base = (
            re.sub(r"[^A-Z0-9]", "", payload.library_name.upper())[:12] or "LIB"
        )
        library = Library(
            code=f"{code_base}-{uuid.uuid4().hex[:8].upper()}",
            name=payload.library_name,
            contact_email=email,
            contact_phone=payload.phone,
            address_line=payload.address,
            status=LibraryStatus.ACTIVE,
        )
        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            full_name=payload.owner_name,
            phone=payload.phone,
        )
        owner_role = db.scalar(
            select(Role).where(Role.name == RoleName.LIBRARY_OWNER)
        )
        if owner_role is None:
            owner_role = Role(
                name=RoleName.LIBRARY_OWNER,
                description="Library owner",
            )
            db.add(owner_role)
            db.flush()
        user.role_links.append(UserRole(role=owner_role))
        db.add_all([user, library])
        db.flush()
        library.primary_owner_user_id = user.id
        db.add(
            LibraryMembership(
                library_id=library.id,
                user_id=user.id,
                role=RoleName.LIBRARY_OWNER,
                status=MembershipStatus.ACTIVE,
                joined_at=datetime.now(timezone.utc),
            )
        )
        _initialize_library_resources(db, library, payload.seat_count)
        response = _create_session(
            db,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
        return response
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The library or owner account conflicts with an existing record.",
        ) from exc
    except Exception:
        db.rollback()
        raise


def login(
    db: Session,
    email: str,
    password: str,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResponse:
    user = db.scalar(
        select(User)
        .options(selectinload(User.role_links).selectinload(UserRole.role))
        .where(
            User.email == email.lower(),
            User.deleted_at.is_(None),
        )
    )
    if (
        not user_can_authenticate(db, user)
        or not verify_password(password, user.password_hash)
    ):
        raise _unauthorized()
    user.last_login_at = datetime.now(timezone.utc)
    response = _create_session(
        db,
        user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return response


def refresh(
    db: Session,
    refresh_token: str,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResponse:
    session = db.scalar(
        select(UserSession)
        .options(
            selectinload(UserSession.user)
            .selectinload(User.role_links)
            .selectinload(UserRole.role)
        )
        .where(UserSession.refresh_token_hash == hash_token(refresh_token))
        .with_for_update()
    )
    if (
        session is None
        or session.revoked_at is not None
        or is_expired(session.expires_at)
        or not user_can_authenticate(db, session.user)
    ):
        raise _unauthorized()
    session.revoked_at = datetime.now(timezone.utc)
    db.flush()
    response = _create_session(
        db,
        session.user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return response


def logout(db: Session, session_id: str) -> None:
    try:
        session = db.get(UserSession, uuid.UUID(session_id))
    except ValueError:
        return
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()


def logout_refresh_token(db: Session, refresh_token: str) -> None:
    session = db.scalar(
        select(UserSession).where(
            UserSession.refresh_token_hash == hash_token(refresh_token)
        )
    )
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()


def update_profile(
    db: Session,
    user: User,
    *,
    name: str,
    email: str,
    phone: str | None,
) -> UserResponse:
    normalized_email = email.strip().lower()
    existing_user_id = db.scalar(
        select(User.id).where(
            User.email == normalized_email,
            User.id != user.id,
            User.deleted_at.is_(None),
        )
    )
    if existing_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account already uses this email address.",
        )

    user.full_name = name.strip()
    user.email = normalized_email
    user.phone = phone
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account already uses this email address.",
        ) from exc

    return user_response(db, user)


def change_password(
    db: Session,
    user: User,
    *,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The current password is incorrect.",
        )
    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The new password must be different from the current password.",
        )

    user.password_hash = hash_password(new_password)
    db.commit()


def _invitation_record(
    db: Session,
    token: str,
    *,
    for_update: bool = False,
) -> AccountInvitation:
    query = select(AccountInvitation).where(
            AccountInvitation.token_hash == hash_token(token),
            AccountInvitation.status == InvitationStatus.PENDING,
        )
    if for_update:
        query = query.with_for_update(of=AccountInvitation)
    invitation = db.scalar(query)
    if invitation is None or is_expired(invitation.expires_at):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This invitation is invalid or has expired.",
        )
    return invitation


def validate_account_invitation(
    db: Session,
    token: str,
) -> ValidateInvitationResponse:
    invitation = _invitation_record(db, token)
    library = db.get(Library, invitation.library_id)
    eligible_statuses = (
        {LibraryStatus.ACTIVE}
        if invitation.role == RoleName.STUDENT
        else {LibraryStatus.PENDING, LibraryStatus.ACTIVE}
    )
    if (
        library is None
        or library.deleted_at is not None
        or library.status not in eligible_statuses
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This invitation can no longer be used.",
        )

    if invitation.role == RoleName.LIBRARY_OWNER:
        if (
            library.primary_owner_user_id is not None
            or db.scalar(
                select(User.id).where(
                    User.email == invitation.email,
                    User.deleted_at.is_(None),
                )
            )
            is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="This invitation can no longer be used.",
            )
        return ValidateInvitationResponse(
            valid=True,
            email=invitation.email,
            library_name=library.name,
            name=invitation.invitee_name or invitation.email.split("@", 1)[0],
            role=RoleName.LIBRARY_OWNER,
            expires_at=invitation.expires_at,
        )
    if invitation.role != RoleName.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This invitation role is not supported.",
        )
    student = db.scalar(
        select(Student).where(
            Student.library_id == invitation.library_id,
            Student.email == invitation.email,
            Student.deleted_at.is_(None),
        )
    )
    if (
        student is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This invitation can no longer be used.",
        )
    return ValidateInvitationResponse(
        valid=True,
        email=student.email,
        library_name=library.name,
        name=f"{student.first_name} {student.last_name}".strip(),
        role=RoleName.STUDENT,
        expires_at=invitation.expires_at,
    )


def accept_account_invitation(
    db: Session,
    token: str,
    password: str,
) -> AcceptInvitationResponse:
    invitation = _invitation_record(db, token)
    library = db.scalar(
        select(Library)
        .where(Library.id == invitation.library_id)
        .with_for_update(of=Library)
    )
    invitation = _invitation_record(db, token, for_update=True)
    eligible_statuses = (
        {LibraryStatus.ACTIVE}
        if invitation.role == RoleName.STUDENT
        else {LibraryStatus.PENDING, LibraryStatus.ACTIVE}
    )
    if (
        library is None
        or library.deleted_at is not None
        or library.status not in eligible_statuses
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This invitation cannot be used while the library is unavailable.",
        )
    if invitation.role == RoleName.LIBRARY_OWNER:
        return _accept_owner_invitation(db, invitation, library, password)
    if invitation.role != RoleName.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This invitation role is not supported.",
        )
    student = db.scalar(
        select(Student).where(
            Student.library_id == invitation.library_id,
            Student.email == invitation.email,
            Student.deleted_at.is_(None),
        )
    )
    if student is None or student.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This invitation can no longer be used.",
        )
    if student.status != StudentStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only active students can activate portal access.",
        )
    if db.scalar(select(User.id).where(User.email == student.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email address.",
        )

    try:
        student_role = db.scalar(select(Role).where(Role.name == RoleName.STUDENT))
        if student_role is None:
            student_role = Role(
                name=RoleName.STUDENT,
                description="Student portal user",
            )
            db.add(student_role)
            db.flush()
        user = User(
            email=student.email,
            password_hash=hash_password(password),
            full_name=f"{student.first_name} {student.last_name}".strip(),
            phone=student.phone,
            email_verified_at=datetime.now(timezone.utc),
        )
        user.role_links.append(UserRole(role=student_role))
        db.add(user)
        db.flush()
        db.add(
            LibraryMembership(
                library_id=student.library_id,
                user_id=user.id,
                role=RoleName.STUDENT,
                status=MembershipStatus.ACTIVE,
                joined_at=datetime.now(timezone.utc),
            )
        )
        student.user_id = user.id
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(timezone.utc)
        invitation.accepted_user_id = user.id
        db.commit()
        return AcceptInvitationResponse(
            message="Student portal password created successfully.",
            email=student.email,
            role=RoleName.STUDENT,
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The student account conflicts with an existing account.",
        ) from exc


def _accept_owner_invitation(
    db: Session,
    invitation: AccountInvitation,
    library: Library,
    password: str,
) -> AcceptInvitationResponse:
    if library.primary_owner_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This library already has an assigned owner.",
        )
    if db.scalar(select(User.id).where(User.email == invitation.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email address.",
        )
    try:
        owner_role = db.scalar(
            select(Role).where(Role.name == RoleName.LIBRARY_OWNER)
        )
        if owner_role is None:
            owner_role = Role(
                name=RoleName.LIBRARY_OWNER,
                description="Library owner",
            )
            db.add(owner_role)
            db.flush()
        now = datetime.now(timezone.utc)
        user = User(
            email=invitation.email,
            password_hash=hash_password(password),
            full_name=(
                invitation.invitee_name or invitation.email.split("@", 1)[0]
            ),
            phone=invitation.invitee_phone,
            email_verified_at=now,
        )
        user.role_links.append(
            UserRole(role=owner_role, assigned_by_user_id=invitation.invited_by_user_id)
        )
        db.add(user)
        db.flush()
        db.add(
            LibraryMembership(
                library_id=library.id,
                user_id=user.id,
                role=RoleName.LIBRARY_OWNER,
                status=MembershipStatus.ACTIVE,
                joined_at=now,
            )
        )
        library.primary_owner_user_id = user.id
        library.last_activity_at = now
        library.updated_at = now
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = now
        invitation.accepted_user_id = user.id
        db.commit()
        return AcceptInvitationResponse(
            message="Library owner password created successfully.",
            email=user.email,
            role=RoleName.LIBRARY_OWNER,
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The owner account conflicts with current platform data.",
        ) from exc


# Backward-compatible service names for existing student-management callers.
validate_student_invitation = validate_account_invitation
accept_student_invitation = accept_account_invitation
