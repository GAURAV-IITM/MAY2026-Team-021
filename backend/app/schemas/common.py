"""Shared API response, pagination, and error contracts."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


DataT = TypeVar("DataT")


def to_camel(value: str) -> str:
    first, *remaining = value.split("_")
    return first + "".join(part.capitalize() for part in remaining)


class APIModel(BaseModel):
    """Base model for contracts that accept field names and aliases."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class MessageResponse(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"message": "Operation completed successfully."}]
        }
    )

    message: str


class PaginationMeta(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page": 1,
                    "pageSize": 20,
                    "totalItems": 42,
                    "totalPages": 3,
                }
            ]
        }
    )

    page: int = Field(ge=1)
    page_size: int = Field(alias="pageSize", ge=1, le=100)
    total_items: int = Field(alias="totalItems", ge=0)
    total_pages: int = Field(alias="totalPages", ge=0)


class SuccessResponse(APIModel, Generic[DataT]):
    message: str
    data: DataT
    meta: dict[str, Any] | None = None


class PaginatedResponse(APIModel, Generic[DataT]):
    message: str
    data: list[DataT]
    meta: PaginationMeta


class ErrorDetail(APIModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": {
                        "code": "RESOURCE_CONFLICT",
                        "message": "The request conflicts with existing data.",
                        "details": {},
                    },
                    "requestId": "frontend-request-123",
                }
            ]
        }
    )

    error: ErrorDetail
    request_id: str = Field(alias="requestId")


class PaginationParams(APIModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page": 1,
                    "pageSize": 20,
                    "search": "A-01",
                    "sortBy": "createdAt",
                    "sortOrder": "desc",
                }
            ]
        }
    )

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, alias="pageSize", ge=1, le=100)
    search: str | None = Field(default=None, max_length=200)
    sort_by: str = Field(default="createdAt", alias="sortBy", max_length=80)
    sort_order: str = Field(
        default="desc",
        alias="sortOrder",
        pattern="^(asc|desc)$",
    )


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ErrorResponse,
        "description": "The request is malformed or cannot be processed.",
    },
    401: {
        "model": ErrorResponse,
        "description": "Authentication is required or the session is invalid.",
    },
    403: {
        "model": ErrorResponse,
        "description": "The authenticated user does not have permission.",
    },
    404: {
        "model": ErrorResponse,
        "description": "The requested resource was not found in the current scope.",
    },
    409: {
        "model": ErrorResponse,
        "description": "The request conflicts with existing data.",
    },
    422: {
        "model": ErrorResponse,
        "description": "Request validation or a business rule failed.",
    },
    500: {
        "model": ErrorResponse,
        "description": "An unexpected server error occurred.",
    },
}


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    unknown_statuses = [
        status_code
        for status_code in status_codes
        if status_code not in COMMON_ERROR_RESPONSES
    ]
    if unknown_statuses:
        raise ValueError(
            f"No shared error response for status codes: {unknown_statuses}"
        )
    return {
        status_code: deepcopy(COMMON_ERROR_RESPONSES[status_code])
        for status_code in status_codes
    }
