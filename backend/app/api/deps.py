import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import decode_access_token, is_expired
from app.db.session import get_db
from app.models.enums import RoleName
from app.models.identity import User, UserRole, UserSession
from app.services import auth as auth_service


DatabaseSession = Annotated[Session, Depends(get_db)]

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )
    try:
        user_id, session_id = uuid.UUID(payload["sub"]), uuid.UUID(payload["sid"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        ) from None
    session = db.get(UserSession, session_id)
    user = db.scalar(
        select(User)
        .options(selectinload(User.role_links).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    if (
        session is None
        or session.user_id != user_id
        or session.revoked_at is not None
        or is_expired(session.expires_at)
        or not auth_service.user_can_authenticate(db, user)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is no longer active.",
        )
    return user


def require_roles(*roles: RoleName) -> Callable[..., User]:
    def dependency(
        db: DatabaseSession,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        current_roles = {link.role.name for link in current_user.role_links}
        if (
            RoleName.SUPER_ADMIN in roles
            and RoleName.SUPER_ADMIN in current_roles
        ):
            return current_user

        membership = auth_service.get_active_membership(db, current_user.id)
        if (
            membership is not None
            and membership.role in roles
            and membership.role in current_roles
        ):
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )

    return dependency
