from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import selectinload

from app.api.deps import (
    get_current_library,
    get_current_library_id,
    get_current_membership,
    get_pagination_params,
    get_tenant_context,
    require_roles,
)
from app.core.exceptions import PermissionDeniedError
from app.models.enums import RoleName
from app.models.identity import Role, User, UserRole
from tests.api_helpers import register


def test_shared_pagination_uses_frozen_query_names() -> None:
    pagination = get_pagination_params(
        page=2,
        page_size=10,
        search="A-01",
        sort_by="seatNumber",
        sort_order="asc",
    )

    assert pagination.model_dump(by_alias=True) == {
        "page": 2,
        "pageSize": 10,
        "search": "A-01",
        "sortBy": "seatNumber",
        "sortOrder": "asc",
    }


def test_request_id_is_created_and_returned(api) -> None:
    client, _testing_session = api

    response = client.get("/health")

    assert response.status_code == 200
    assert uuid.UUID(response.headers["x-request-id"])


def test_valid_request_id_is_preserved_and_invalid_value_is_replaced(api) -> None:
    client, _testing_session = api

    preserved = client.get(
        "/health",
        headers={"X-Request-ID": "frontend-request-123"},
    )
    replaced = client.get(
        "/health",
        headers={"X-Request-ID": "invalid request id"},
    )

    assert preserved.headers["x-request-id"] == "frontend-request-123"
    assert replaced.headers["x-request-id"] != "invalid request id"
    assert uuid.UUID(replaced.headers["x-request-id"])


def test_validation_errors_use_the_shared_error_contract(api) -> None:
    client, _testing_session = api

    response = register(client, seatCount=0)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "The request contains invalid data."
    assert body["error"]["details"]["fields"]
    assert body["requestId"] == response.headers["x-request-id"]


def test_legacy_snake_case_requests_are_accepted_but_responses_are_camel_case(
    api,
) -> None:
    client, _testing_session = api

    response = client.post(
        "/api/v1/auth/register-library",
        json={
            "library_name": "Legacy Client Library",
            "owner_name": "Legacy Owner",
            "email": "legacy@example.com",
            "password": "SecurePass123",
            "seat_count": 5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["accessToken"]
    assert body["refreshToken"]
    assert body["user"]["libraryId"]
    assert "access_token" not in body
    assert "library_id" not in body["user"]


def test_http_errors_use_the_shared_error_contract(api) -> None:
    client, _testing_session = api

    response = client.get("/api/v1/not-a-real-route")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "Not Found",
            "details": {},
        },
        "requestId": response.headers["x-request-id"],
    }


def test_tenant_and_role_dependencies_use_active_membership(api) -> None:
    client, testing_session = api
    registered = register(client).json()

    with testing_session() as db:
        user = db.get(
            User,
            uuid.UUID(registered["user"]["id"]),
            options=[selectinload(User.role_links).selectinload(UserRole.role)],
        )
        assert user is not None

        membership = get_current_membership(db=db, current_user=user)
        library = get_current_library(membership=membership)
        tenant = get_tenant_context(
            current_user=user,
            membership=membership,
        )

        assert get_current_library_id(membership=membership) == library.id
        assert tenant.library_id == library.id
        assert tenant.role == RoleName.LIBRARY_OWNER
        assert require_roles(RoleName.LIBRARY_OWNER)(
            db=db,
            current_user=user,
        ) == user

        with pytest.raises(PermissionDeniedError) as denied:
            require_roles(RoleName.STUDENT)(
                db=db,
                current_user=user,
            )

        assert denied.value.status_code == 403
        assert denied.value.code == "PERMISSION_DENIED"


def test_super_admin_role_does_not_require_library_membership(api) -> None:
    _client, testing_session = api

    with testing_session() as db:
        super_admin_role = Role(
            name=RoleName.SUPER_ADMIN,
            description="Platform administrator",
        )
        super_admin = User(
            email="superadmin@example.com",
            password_hash="test-password-hash",
            full_name="Super Admin",
        )
        super_admin.role_links.append(UserRole(role=super_admin_role))
        db.add(super_admin)
        db.commit()

        assert require_roles(RoleName.SUPER_ADMIN)(
            db=db,
            current_user=super_admin,
        ) == super_admin

        with pytest.raises(PermissionDeniedError) as no_membership:
            get_current_membership(db=db, current_user=super_admin)

        assert no_membership.value.code == "ACTIVE_LIBRARY_MEMBERSHIP_REQUIRED"
