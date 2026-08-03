"""OpenAPI customization shared by Swagger UI and the checked-in YAML."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.request_context import REQUEST_ID_HEADER
from app.schemas.common import (
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    SuccessResponse,
)


REFRESH_COOKIE_NAME = "smart_library_refresh_token"


OPERATION_DESCRIPTIONS = {
    "loginWithTokens": (
        "Authenticates an active user and membership, then issues a short-lived "
        "access token and rotating refresh token."
    ),
    "logoutTokenSession": (
        "Revokes the session identified by the supplied access token so that "
        "the token can no longer access protected APIs."
    ),
    "getAuthenticatedUser": (
        "Returns the currently authenticated user after validating the JWT, "
        "backing session, account, library, and membership state."
    ),
    "updateAuthenticatedProfile": (
        "Updates the current user's name, email, and phone while enforcing "
        "account-level uniqueness rules."
    ),
    "changeAuthenticatedPassword": (
        "Verifies the current password, stores a new scrypt password hash, and "
        "revokes the user's other active sessions."
    ),
    "validateStudentInvitation": (
        "Validates a one-time, unexpired student account invitation without "
        "activating the account."
    ),
    "acceptStudentInvitation": (
        "Consumes a valid student invitation, creates the portal login and "
        "membership, and stores the student's chosen password securely."
    ),
    "listStudents": (
        "Returns a paginated, searchable list of non-deleted students from the "
        "authenticated staff member's current library."
    ),
    "createStudent": (
        "Creates a tenant-scoped student and may atomically create an invitation "
        "and validated seat allocations supplied during registration."
    ),
    "getStudent": (
        "Returns one non-deleted student from the current library, including "
        "the profile and current allocation information."
    ),
    "updateStudent": (
        "Updates a student profile and, when requested, replaces or removes "
        "current allocations while retaining allocation history."
    ),
    "deleteStudent": (
        "Soft-deletes a student in the current library after applying the "
        "student lifecycle and historical-record rules."
    ),
    "changeStudentStatus": (
        "Changes a student's lifecycle status after checking tenant ownership "
        "and status-transition requirements."
    ),
    "inviteStudent": (
        "Revokes an earlier pending setup invitation and creates a new expiring "
        "student portal password-setup link."
    ),
    "listFloors": (
        "Returns active, non-deleted physical floors belonging to the current "
        "library in configured display order."
    ),
    "createFloor": (
        "Creates a physical floor with a library-unique code in the authenticated "
        "staff member's current library."
    ),
    "updateFloor": (
        "Updates a current-library floor while preserving tenant isolation and "
        "floor-code uniqueness."
    ),
    "deleteFloor": (
        "Soft-deletes an empty floor; floors that still contain seats are "
        "rejected to preserve physical-seat references."
    ),
    "listSeats": (
        "Returns physical seats and shift metadata for the current library, with "
        "optional search, floor, and physical-status filters."
    ),
    "createSeat": (
        "Creates a physical seat on a valid current-library floor and enforces "
        "library-wide seat-number uniqueness."
    ),
    "bulkChangeSeatStatus": (
        "Atomically changes selected physical seats to Available, Maintenance, "
        "or Blocked after checking allocation restrictions."
    ),
    "bulkDeleteSeats": (
        "Soft-deletes selected current-library seats in one transaction when no "
        "active or future allocation prevents deletion."
    ),
    "getSeat": (
        "Returns one non-deleted physical seat from the current library without "
        "exposing another tenant's record."
    ),
    "updateSeat": (
        "Updates a physical seat number, floor, type, status, or notes while "
        "enforcing tenant and allocation rules."
    ),
    "deleteSeat": (
        "Soft-deletes one physical seat when it has no active or future allocation "
        "that must remain available to history."
    ),
    "changeSeatStatus": (
        "Changes one seat's physical operational status and records the reason "
        "and administrative status history."
    ),
    "listShifts": (
        "Returns current-library shift definitions and optionally includes "
        "inactive shifts required for administration or history."
    ),
    "createShift": (
        "Creates a same-day or overnight shift with a library-unique name and a "
        "validated non-zero time interval."
    ),
    "validateShiftSelection": (
        "Checks whether selected current-library shifts can be assigned together "
        "using boundary-safe and overnight-aware overlap rules."
    ),
    "updateShift": (
        "Updates a current-library shift's name, timing, or active state while "
        "preserving historical allocation snapshots."
    ),
    "deleteShift": (
        "Soft-deletes a non-default shift when domain history rules allow it; "
        "default shifts remain available for administration."
    ),
    "changeShiftStatus": (
        "Activates or deactivates a current-library shift without deleting "
        "historical allocations linked to it."
    ),
    "getSeatAllocationAvailability": (
        "Calculates tenant-scoped Available, Allotted, Reserved, Maintenance, "
        "physical-block, and overlapping-shift statuses for the requested dates."
    ),
    "listSeatAllocations": (
        "Returns paginated allocation history for the current library with "
        "student, seat, shift, status, date, search, and sorting filters."
    ),
    "createSeatAllocation": (
        "Atomically creates allocations for mutually non-overlapping shifts after "
        "validating student, seat, date, tenant, and conflict rules."
    ),
    "closeSeatAllocation": (
        "Completes or cancels an active allocation, records the actor and reason, "
        "and preserves the closed record for audit and history."
    ),
    "getLibrarySettings": (
        "Returns the current library's profile, operating hours, fee defaults, "
        "receipt rules, and notification preferences."
    ),
    "updateLibrarySettings": (
        "Updates validated settings for the authenticated staff member's current "
        "library without accepting a client-supplied tenant identifier."
    ),
    "getApiRoot": (
        "Returns a small discovery response confirming that the Smart Library API "
        "application is reachable."
    ),
    "getHealth": (
        "Returns the process health status for deployment checks and development "
        "diagnostics."
    ),
}


def _complete_operation_descriptions(schema: dict[str, Any]) -> None:
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or operation.get("description"):
                continue
            description = OPERATION_DESCRIPTIONS.get(operation.get("operationId"))
            if description:
                operation["description"] = description


def _add_shared_schemas(schema: dict[str, Any]) -> None:
    component_schemas = (
        schema.setdefault("components", {})
        .setdefault("schemas", {})
    )
    shared_models = {
        "PaginationMeta": PaginationMeta,
        "PaginationParams": PaginationParams,
        "SuccessResponse": SuccessResponse[dict[str, Any]],
        "PaginatedResponse": PaginatedResponse[dict[str, Any]],
    }

    for component_name, model in shared_models.items():
        model_schema = model.model_json_schema(
            by_alias=True,
            ref_template="#/components/schemas/{model}",
        )
        definitions = model_schema.pop("$defs", {})
        for definition_name, definition in definitions.items():
            component_schemas.setdefault(definition_name, definition)
        model_schema["title"] = component_name
        component_schemas.setdefault(component_name, model_schema)


def _add_request_id_headers(schema: dict[str, Any]) -> None:
    components = schema.setdefault("components", {})
    headers = components.setdefault("headers", {})
    headers["XRequestId"] = {
        "description": "Correlation identifier for the request.",
        "schema": {
            "type": "string",
            "example": "req-7d566b29-8d93-4b09-8a22-b6ce8fba25c1",
        },
    }

    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            for response in operation.get("responses", {}).values():
                if not isinstance(response, dict):
                    continue
                response.setdefault("headers", {})[REQUEST_ID_HEADER] = {
                    "$ref": "#/components/headers/XRequestId"
                }


def _add_browser_cookie_security(schema: dict[str, Any]) -> None:
    security_schemes = (
        schema.setdefault("components", {})
        .setdefault("securitySchemes", {})
    )
    security_schemes["RefreshCookie"] = {
        "type": "apiKey",
        "in": "cookie",
        "name": REFRESH_COOKIE_NAME,
        "description": (
            "Rotating HttpOnly refresh cookie set by browser-session "
            "authentication endpoints."
        ),
    }

    paths = schema.get("paths", {})
    refresh_operation = paths.get(
        f"{settings.api_v1_prefix}/auth/session/refresh",
        {},
    ).get("post")
    if refresh_operation:
        refresh_operation["security"] = [{"RefreshCookie": []}]

    logout_operation = paths.get(
        f"{settings.api_v1_prefix}/auth/session/logout",
        {},
    ).get("post")
    if logout_operation:
        logout_operation["security"] = [
            {"RefreshCookie": []},
            {"BearerAuth": []},
        ]


def configure_openapi(application: FastAPI) -> None:
    def custom_openapi() -> dict[str, Any]:
        if application.openapi_schema:
            return application.openapi_schema

        schema = get_openapi(
            title=application.title,
            version=application.version,
            description=(
                "Contract for the Smart Library App. Library-owned resources "
                "are tenant-scoped from the authenticated membership."
            ),
            routes=application.routes,
            openapi_version="3.1.0",
            tags=application.openapi_tags,
        )
        schema["info"]["contact"] = {
            "name": "MAY2026-Team-021",
        }
        schema["servers"] = [
            {
                "url": "/",
                "description": "Current host",
            }
        ]
        schema["x-api-conventions"] = {
            "dates": "YYYY-MM-DD",
            "dateTimes": "ISO 8601 with timezone",
            "identifiers": "UUID strings",
            "errors": "Structured ErrorResponse with requestId",
        }
        _add_shared_schemas(schema)
        _add_browser_cookie_security(schema)
        _add_request_id_headers(schema)
        _complete_operation_descriptions(schema)
        application.openapi_schema = deepcopy(schema)
        return application.openapi_schema

    application.openapi = custom_openapi
