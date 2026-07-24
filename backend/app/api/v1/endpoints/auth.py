from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.deps import DatabaseSession, get_current_user
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.identity import User
from app.schemas.auth import (
    AuthResponse,
    BrowserAuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterLibraryRequest,
    UpdateProfileRequest,
    UserResponse,
)
from app.services import auth as auth_service


router = APIRouter()
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


@router.post("/register-library", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_library(payload: RegisterLibraryRequest, request: Request, db: DatabaseSession) -> AuthResponse:
    ip_address, user_agent = _request_metadata(request)
    return auth_service.register_library(db, payload, ip_address=ip_address, user_agent=user_agent)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, db: DatabaseSession) -> AuthResponse:
    ip_address, user_agent = _request_metadata(request)
    return auth_service.login(db, payload.email, payload.password, ip_address=ip_address, user_agent=user_agent)


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, request: Request, db: DatabaseSession) -> AuthResponse:
    ip_address, user_agent = _request_metadata(request)
    return auth_service.refresh(db, payload.refresh_token, ip_address=ip_address, user_agent=user_agent)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: DatabaseSession) -> MessageResponse:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        payload = decode_access_token(authorization[7:], verify_expiry=False)
        if payload and payload.get("sid"):
            auth_service.logout(db, payload["sid"])
    response.status_code = status.HTTP_200_OK
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserResponse)
def me(db: DatabaseSession, current_user: User = Depends(get_current_user)) -> UserResponse:
    return auth_service.user_response(db, current_user)


@router.post(
    "/session/register-library",
    response_model=BrowserAuthResponse,
    status_code=status.HTTP_201_CREATED,
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


@router.post("/session/login", response_model=BrowserAuthResponse)
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


@router.post("/session/refresh", response_model=BrowserAuthResponse)
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


@router.post("/session/logout", response_model=MessageResponse)
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


@router.patch("/profile", response_model=UserResponse)
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


@router.post("/change-password", response_model=MessageResponse)
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
