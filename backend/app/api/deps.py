import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token, is_expired
from app.db.session import get_db
from app.models.enums import RoleName
from app.models.identity import User, UserRole, UserSession
from app.models.library import Library, LibraryMembership
from app.schemas.common import PaginationParams
from app.services import auth as auth_service


DatabaseSession = Annotated[Session, Depends(get_db)]


def get_pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=200)] = None,
    sort_by: Annotated[str, Query(alias="sortBy", max_length=80)] = "createdAt",
    sort_order: Annotated[
        str,
        Query(alias="sortOrder", pattern="^(asc|desc)$"),
    ] = "desc",
) -> PaginationParams:
    return PaginationParams(
        page=page,
        pageSize=page_size,
        search=search,
        sortBy=sort_by,
        sortOrder=sort_order,
    )


Pagination = Annotated[PaginationParams, Depends(get_pagination_params)]

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="Short-lived JWT access token returned by an authentication endpoint.",
)


def get_current_user(
    db: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Authentication is required.")
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise AuthenticationError(
            "Invalid or expired access token.",
            code="INVALID_ACCESS_TOKEN",
        )
    try:
        user_id, session_id = uuid.UUID(payload["sub"]), uuid.UUID(payload["sid"])
    except (KeyError, ValueError):
        raise AuthenticationError(
            "Invalid access token.",
            code="INVALID_ACCESS_TOKEN",
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
        raise AuthenticationError(
            "Session is no longer active.",
            code="SESSION_INACTIVE",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_membership(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> LibraryMembership:
    membership = auth_service.get_active_membership(db, current_user.id)
    if membership is None:
        raise PermissionDeniedError(
            "An active library membership is required.",
            code="ACTIVE_LIBRARY_MEMBERSHIP_REQUIRED",
        )
    return membership


CurrentMembership = Annotated[
    LibraryMembership,
    Depends(get_current_membership),
]


def get_current_library(
    membership: CurrentMembership,
) -> Library:
    return membership.library


CurrentLibrary = Annotated[Library, Depends(get_current_library)]


def get_current_library_id(
    membership: CurrentMembership,
) -> uuid.UUID:
    return membership.library_id


CurrentLibraryId = Annotated[uuid.UUID, Depends(get_current_library_id)]


@dataclass(frozen=True, slots=True)
class TenantContext:
    user: User
    membership: LibraryMembership
    library: Library

    @property
    def library_id(self) -> uuid.UUID:
        return self.membership.library_id

    @property
    def role(self) -> RoleName:
        return self.membership.role


def get_tenant_context(
    current_user: CurrentUser,
    membership: CurrentMembership,
) -> TenantContext:
    return TenantContext(
        user=current_user,
        membership=membership,
        library=membership.library,
    )


CurrentTenant = Annotated[TenantContext, Depends(get_tenant_context)]


def require_roles(*roles: RoleName) -> Callable[..., User]:
    allowed_roles = frozenset(roles)
    if not allowed_roles:
        raise ValueError("At least one role is required.")

    def dependency(
        db: DatabaseSession,
        current_user: CurrentUser,
    ) -> User:
        current_roles = {link.role.name for link in current_user.role_links}
        if (
            RoleName.SUPER_ADMIN in allowed_roles
            and RoleName.SUPER_ADMIN in current_roles
        ):
            return current_user

        membership = auth_service.get_active_membership(db, current_user.id)
        if (
            membership is not None
            and membership.role in allowed_roles
            and membership.role in current_roles
        ):
            return current_user

        raise PermissionDeniedError(
            "Insufficient permissions.",
            details={
                "requiredRoles": sorted(role.value for role in allowed_roles),
            },
        )

    return dependency


require_library_owner = require_roles(RoleName.LIBRARY_OWNER)
require_library_staff = require_roles(
    RoleName.LIBRARY_OWNER,
    RoleName.STAFF,
)
require_library_member = require_roles(
    RoleName.LIBRARY_OWNER,
    RoleName.STAFF,
    RoleName.STUDENT,
)
require_super_admin = require_roles(RoleName.SUPER_ADMIN)
