"""Authentication API contracts."""
from __future__ import annotations

import uuid

from pydantic import ConfigDict, Field

from app.schemas.common import APIModel, MessageResponse


USER_RESPONSE_EXAMPLE = {
    "id": "f2618f84-afc1-4b94-9339-d4113a9c9134",
    "name": "Library Owner",
    "email": "owner@example.com",
    "phone": "9876543210",
    "role": "admin",
    "libraryId": "24b9ce74-59bb-44a3-b67c-d92b121e01c9",
    "libraryName": "Central Study Library",
}


class LoginRequest(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "owner@example.com",
                    "password": "SecurePass123",
                    "rememberMe": True,
                }
            ]
        }
    )

    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=8, max_length=128)
    remember_me: bool = False


class RegisterLibraryRequest(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "libraryName": "Central Study Library",
                    "ownerName": "Library Owner",
                    "email": "owner@example.com",
                    "password": "SecurePass123",
                    "phone": "9876543210",
                    "address": "1 Reading Lane",
                    "seatCount": 25,
                }
            ]
        }
    )

    library_name: str = Field(min_length=2, max_length=180)
    owner_name: str = Field(min_length=2, max_length=160)
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=255)
    seat_count: int = Field(default=1, ge=1, le=1000)


class RefreshRequest(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "refreshToken": (
                        "refresh-token-value-at-least-32-characters"
                    )
                }
            ]
        }
    )

    refresh_token: str = Field(min_length=32)


class UserResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [USER_RESPONSE_EXAMPLE]
        },
    )
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    role: str
    library_id: uuid.UUID | None = None
    library_name: str | None = None


class AuthResponse(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "accessToken": "header.payload.signature",
                    "refreshToken": "refresh-token-value-at-least-32-characters",
                    "tokenType": "bearer",
                    "expiresIn": 1800,
                    "user": USER_RESPONSE_EXAMPLE,
                }
            ]
        }
    )

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class BrowserAuthResponse(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "accessToken": "header.payload.signature",
                    "tokenType": "bearer",
                    "expiresIn": 1800,
                    "user": USER_RESPONSE_EXAMPLE,
                }
            ]
        }
    )

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UpdateProfileRequest(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Updated Owner",
                    "email": "updated.owner@example.com",
                    "phone": "9876543210",
                }
            ]
        }
    )

    name: str = Field(min_length=2, max_length=160)
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone: str | None = Field(default=None, max_length=32)


class ChangePasswordRequest(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "currentPassword": "SecurePass123",
                    "newPassword": "NewSecurePass456",
                }
            ]
        }
    )

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
