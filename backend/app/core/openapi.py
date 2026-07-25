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
        application.openapi_schema = deepcopy(schema)
        return application.openapi_schema

    application.openapi = custom_openapi
