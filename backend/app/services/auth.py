"""Authentication use cases and session lifecycle."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.security import create_access_token, hash_password, hash_token, new_refresh_token, verify_password
from app.models.enums import LibraryStatus, MembershipStatus, RoleName
from app.models.identity import Role, User, UserRole, UserSession
from app.models.library import Library, LibraryMembership
from app.schemas.auth import AuthResponse, RegisterLibraryRequest, UserResponse


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or session.")


def _role_label(role: RoleName) -> str:
    return {RoleName.LIBRARY_OWNER: "admin", RoleName.SUPER_ADMIN: "superadmin"}.get(role, role.value)


def _is_expired(value: datetime) -> bool:
    """Compare SQLite's naive datetimes safely with UTC timestamps."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= datetime.now(timezone.utc)


def _active_membership(db: Session, user_id: uuid.UUID) -> LibraryMembership | None:
    return db.scalar(select(LibraryMembership).where(LibraryMembership.user_id == user_id, LibraryMembership.status == MembershipStatus.ACTIVE))


def user_response(db: Session, user: User) -> UserResponse:
    roles = [link.role.name for link in user.role_links]
    membership = _active_membership(db, user.id)
    role = membership.role if membership else (roles[0] if roles else RoleName.STUDENT)
    library = membership.library if membership else None
    return UserResponse(id=user.id, name=user.full_name, email=user.email, phone=user.phone,
                        role=_role_label(role), library_id=membership.library_id if membership else None,
                        library_name=library.name if library else None)


def _auth_response(db: Session, user: User, session: UserSession, refresh_token: str) -> AuthResponse:
    roles = [link.role.name.value for link in user.role_links]
    return AuthResponse(access_token=create_access_token(subject=str(user.id), session_id=str(session.id), roles=roles),
                        refresh_token=refresh_token, expires_in=settings.access_token_expire_minutes * 60,
                        user=user_response(db, user))


def _create_session(db: Session, user: User, *, ip_address: str | None, user_agent: str | None) -> AuthResponse:
    refresh_token = new_refresh_token()
    session = UserSession(user_id=user.id, refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        ip_address=ip_address, user_agent=user_agent)
    db.add(session)
    db.flush()
    return _auth_response(db, user, session, refresh_token)


def register_library(db: Session, payload: RegisterLibraryRequest, *, ip_address: str | None, user_agent: str | None) -> AuthResponse:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email address.")
    code_base = re.sub(r"[^A-Z0-9]", "", payload.library_name.upper())[:12] or "LIB"
    library = Library(code=f"{code_base}-{uuid.uuid4().hex[:8].upper()}", name=payload.library_name,
        contact_email=email, contact_phone=payload.phone, address_line=payload.address, status=LibraryStatus.ACTIVE)
    user = User(email=email, password_hash=hash_password(payload.password), full_name=payload.owner_name, phone=payload.phone)
    owner_role = db.scalar(select(Role).where(Role.name == RoleName.LIBRARY_OWNER))
    if owner_role is None:
        owner_role = Role(name=RoleName.LIBRARY_OWNER, description="Library owner")
        db.add(owner_role)
        db.flush()
    user.role_links.append(UserRole(role=owner_role))
    db.add_all([user, library])
    db.flush()
    library.primary_owner_user_id = user.id
    db.add(LibraryMembership(library_id=library.id, user_id=user.id, role=RoleName.LIBRARY_OWNER,
        status=MembershipStatus.ACTIVE, joined_at=datetime.now(timezone.utc)))
    response = _create_session(db, user, ip_address=ip_address, user_agent=user_agent)
    db.commit()
    return response


def login(db: Session, email: str, password: str, *, ip_address: str | None, user_agent: str | None) -> AuthResponse:
    user = db.scalar(select(User).options(selectinload(User.role_links).selectinload(UserRole.role)).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise _unauthorized()
    user.last_login_at = datetime.now(timezone.utc)
    response = _create_session(db, user, ip_address=ip_address, user_agent=user_agent)
    db.commit()
    return response


def refresh(db: Session, refresh_token: str, *, ip_address: str | None, user_agent: str | None) -> AuthResponse:
    session = db.scalar(select(UserSession).options(selectinload(UserSession.user).selectinload(User.role_links).selectinload(UserRole.role)).where(UserSession.refresh_token_hash == hash_token(refresh_token)))
    if session is None or session.revoked_at is not None or _is_expired(session.expires_at) or not session.user.is_active:
        raise _unauthorized()
    session.revoked_at = datetime.now(timezone.utc)
    response = _create_session(db, session.user, ip_address=ip_address, user_agent=user_agent)
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
