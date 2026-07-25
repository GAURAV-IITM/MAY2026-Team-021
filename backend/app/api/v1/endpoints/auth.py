from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.deps import DatabaseSession, get_current_user
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.identity import User
from app.schemas.auth import (
    AcceptInvitationRequest,
    AcceptInvitationResponse,
    AuthResponse,
    BrowserAuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterLibraryRequest,
    UpdateProfileRequest,
    UserResponse,
    ValidateInvitationResponse,
)
from app.schemas.common import error_responses
from app.services import auth as auth_service


router = APIRouter(responses=error_responses(500))
REFRESH_COOKIE_NAME = "smart_library_refresh_token"
REMEMBER_COOKIE_NAME = "smart_library_remember_session"
AUTH_COOKIE_PATH = f"{settings.api_v1_prefix}/auth"
LOCAL_ENVIRONMENTS = {"development", "local", "test"}


def _request_metadata(request: Request) -> tuple[str | None, str | None]:
    return (request.client.host if request.client else None, request.headers.get("user-agent"))


def _browser_auth_response(result: AuthResponse) -> BrowserAuthResponse:
    return BrowserAuthResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
        user=result.user,
    )


def _set_refresh_cookie(
    response: Response,
    refresh_token: str,
    *,
    remember_me: bool,
) -> None:
    secure = settings.environment.lower() not in LOCAL_ENVIRONMENTS
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60 if remember_me else None
    cookie_options = {
        "httponly": True,
        "secure": secure,
        "samesite": "lax",
        "path": AUTH_COOKIE_PATH,
        "max_age": max_age,
    }
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        **cookie_options,
    )
    response.set_cookie(
        key=REMEMBER_COOKIE_NAME,
        value="1" if remember_me else "0",
        **cookie_options,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=AUTH_COOKIE_PATH,
        samesite="lax",
    )
    response.delete_cookie(
        REMEMBER_COOKIE_NAME,
        path=AUTH_COOKIE_PATH,
        samesite="lax",
    )


@router.post(
    "/register-library",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="registerLibraryWithTokens",
    summary="Register a library and owner",
    description=(
        "Creates the library, owner account, active membership, settings, "
        "default shifts, first floor, requested seats, and an API token session."
    ),
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["AUTH-REGISTER-LIBRARY"]},
)
def register_library(
    payload: RegisterLibraryRequest,
    request: Request,
    db: DatabaseSession,
) -> AuthResponse:
    ip_address, user_agent = _request_metadata(request)
    return auth_service.register_library(db, payload, ip_address=ip_address, user_agent=user_agent)


@router.post(
    "/login",
    response_model=AuthResponse,
    operation_id="loginWithTokens",
    summary="Log in and return API tokens",
    responses=error_responses(401, 422),
    openapi_extra={"x-user-stories": ["AUTH-LOGIN"]},
)
def login(payload: LoginRequest, request: Request, db: DatabaseSession) -> AuthResponse:
    ip_address, user_agent = _request_metadata(request)
    return auth_service.login(db, payload.email, payload.password, ip_address=ip_address, user_agent=user_agent)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    operation_id="refreshTokenSession",
    summary="Rotate an API refresh token",
    description="Rotates the supplied refresh token and revokes its previous session.",
    responses=error_responses(401, 422),
    openapi_extra={"x-user-stories": ["AUTH-REFRESH-SESSION"]},
)
def refresh(payload: RefreshRequest, request: Request, db: DatabaseSession) -> AuthResponse:
    ip_address, user_agent = _request_metadata(request)
    return auth_service.refresh(db, payload.refresh_token, ip_address=ip_address, user_agent=user_agent)


@router.post(
    "/logout",
    response_model=MessageResponse,
    operation_id="logoutTokenSession",
    summary="Log out an API token session",
    openapi_extra={
        "security": [{"BearerAuth": []}],
        "x-user-stories": ["AUTH-LOGOUT"],
    },
)
def logout(request: Request, response: Response, db: DatabaseSession) -> MessageResponse:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        payload = decode_access_token(authorization[7:], verify_expiry=False)
        if payload and payload.get("sid"):
            auth_service.logout(db, payload["sid"])
    response.status_code = status.HTTP_200_OK
    return MessageResponse(message="Logged out successfully.")


@router.get(
    "/me",
    response_model=UserResponse,
    operation_id="getAuthenticatedUser",
    summary="Get the authenticated user",
    responses=error_responses(401),
    openapi_extra={"x-user-stories": ["AUTH-CURRENT-USER"]},
)
def me(db: DatabaseSession, current_user: User = Depends(get_current_user)) -> UserResponse:
    return auth_service.user_response(db, current_user)


@router.post(
    "/session/register-library",
    response_model=BrowserAuthResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="registerLibraryBrowserSession",
    summary="Register a library using a browser session",
    description=(
        "Creates the library account and sets a rotating HttpOnly refresh cookie. "
        "The refresh token is never returned to browser JavaScript."
    ),
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["AUTH-REGISTER-LIBRARY"]},
)
def register_library_session(
    payload: RegisterLibraryRequest,
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> BrowserAuthResponse:
    ip_address, user_agent = _request_metadata(request)
    result = auth_service.register_library(
        db,
        payload,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    _set_refresh_cookie(response, result.refresh_token, remember_me=False)
    return _browser_auth_response(result)


@router.post(
    "/session/login",
    response_model=BrowserAuthResponse,
    operation_id="loginBrowserSession",
    summary="Log in using a browser session",
    description="Returns an access token and sets a rotating HttpOnly refresh cookie.",
    responses=error_responses(401, 422),
    openapi_extra={"x-user-stories": ["AUTH-LOGIN"]},
)
def login_session(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> BrowserAuthResponse:
    ip_address, user_agent = _request_metadata(request)
    result = auth_service.login(
        db,
        payload.email,
        payload.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    _set_refresh_cookie(
        response,
        result.refresh_token,
        remember_me=payload.remember_me,
    )
    return _browser_auth_response(result)


@router.post(
    "/session/refresh",
    response_model=BrowserAuthResponse,
    operation_id="refreshBrowserSession",
    summary="Refresh a browser session",
    description="Rotates the HttpOnly refresh cookie and returns a new access token.",
    responses=error_responses(401),
    openapi_extra={"x-user-stories": ["AUTH-REFRESH-SESSION"]},
)
def refresh_session(
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> BrowserAuthResponse:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or session.",
        )

    ip_address, user_agent = _request_metadata(request)
    result = auth_service.refresh(
        db,
        refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    remember_me = request.cookies.get(REMEMBER_COOKIE_NAME) == "1"
    _set_refresh_cookie(
        response,
        result.refresh_token,
        remember_me=remember_me,
    )
    return _browser_auth_response(result)


@router.post(
    "/session/logout",
    response_model=MessageResponse,
    operation_id="logoutBrowserSession",
    summary="Log out a browser session",
    description="Revokes available refresh and access-token sessions and clears cookies.",
    openapi_extra={"x-user-stories": ["AUTH-LOGOUT"]},
)
def logout_session(
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> MessageResponse:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        auth_service.logout_refresh_token(db, refresh_token)

    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        payload = decode_access_token(authorization[7:], verify_expiry=False)
        if payload and payload.get("sid"):
            auth_service.logout(db, payload["sid"])

    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully.")


@router.patch(
    "/profile",
    response_model=UserResponse,
    operation_id="updateAuthenticatedProfile",
    summary="Update the authenticated profile",
    responses=error_responses(401, 409, 422),
    openapi_extra={"x-user-stories": ["AUTH-UPDATE-PROFILE"]},
)
def update_profile(
    payload: UpdateProfileRequest,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return auth_service.update_profile(
        db,
        current_user,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    operation_id="changeAuthenticatedPassword",
    summary="Change the authenticated password",
    responses=error_responses(401, 422),
    openapi_extra={"x-user-stories": ["AUTH-CHANGE-PASSWORD"]},
)
def change_password(
    payload: ChangePasswordRequest,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    auth_service.change_password(
        db,
        current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return MessageResponse(message="Password changed successfully.")


@router.get(
    "/invitations/validate",
    response_model=ValidateInvitationResponse,
    operation_id="validateStudentInvitation",
    summary="Validate a student portal invitation",
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-INVITATION"]},
)
def validate_invitation(
    token: str,
    db: DatabaseSession,
) -> ValidateInvitationResponse:
    return auth_service.validate_student_invitation(db, token)


@router.post(
    "/invitations/accept",
    response_model=AcceptInvitationResponse,
    operation_id="acceptStudentInvitation",
    summary="Create a student password from an invitation",
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-ACTIVATION"]},
)
def accept_invitation(
    payload: AcceptInvitationRequest,
    db: DatabaseSession,
) -> AcceptInvitationResponse:
    return auth_service.accept_student_invitation(
        db,
        payload.token,
        payload.password,
    )
