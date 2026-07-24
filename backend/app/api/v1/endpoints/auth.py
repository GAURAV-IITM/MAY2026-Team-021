from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import DatabaseSession, get_current_user
from app.core.security import decode_access_token
from app.models.identity import User
from app.schemas.auth import AuthResponse, LoginRequest, MessageResponse, RefreshRequest, RegisterLibraryRequest, UserResponse
from app.services import auth as auth_service


router = APIRouter()


def _request_metadata(request: Request) -> tuple[str | None, str | None]:
    return (request.client.host if request.client else None, request.headers.get("user-agent"))


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
