"""API coverage for Super Admin platform library management."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import func, select

from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.enums import LibraryStatus, MembershipStatus, RoleName
from app.models.identity import Role, User, UserRole
from app.models.library import Library, LibraryMembership, LibrarySettings
from app.models.seat import Floor, Seat
from app.schemas.platform import PlatformLibraryCreate
from app.services import platform as platform_service
from tests.api_helpers import bearer


PASSWORD = "SecurePass123"
BASE_PATH = "/api/v1/platform/libraries"


def _role(db, role_name: RoleName) -> Role:
    role = db.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name, description=f"{role_name.value} test role")
        db.add(role)
        db.flush()
    return role


def _create_user(
    testing_session,
    *,
    email: str,
    role_name: RoleName,
    library_id: uuid.UUID | None = None,
) -> uuid.UUID:
    with testing_session() as db:
        user = User(
            email=email,
            password_hash=hash_password(PASSWORD),
            full_name=email.split("@")[0].replace(".", " ").title(),
            phone="9876543210",
        )
        user.role_links.append(UserRole(role=_role(db, role_name)))
        db.add(user)
        db.flush()
        if library_id is not None:
            db.add(
                LibraryMembership(
                    library_id=library_id,
                    user_id=user.id,
                    role=role_name,
                    status=MembershipStatus.ACTIVE,
                    joined_at=datetime.now(timezone.utc),
                )
            )
        db.commit()
        return user.id


def _login(client, email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD, "rememberMe": False},
    )
    assert response.status_code == 200, response.json()
    return bearer(response.json()["accessToken"])


@pytest.fixture
def super_admin_headers(api) -> dict[str, str]:
    client, testing_session = api
    email = "platform.admin@example.com"
    _create_user(
        testing_session,
        email=email,
        role_name=RoleName.SUPER_ADMIN,
    )
    return _login(client, email)


def _library_payload(**overrides) -> dict[str, object]:
    suffix = uuid.uuid4().hex[:8].upper()
    payload: dict[str, object] = {
        "name": f"Platform Library {suffix}",
        "code": f"PL-{suffix}",
        "contactEmail": f"library-{suffix.lower()}@example.com",
        "contactPhone": "+91 9876543210",
        "addressLine": "1 Reading Lane",
        "city": "Pune",
        "state": "Maharashtra",
        "postalCode": "411001",
        "timezone": "Asia/Kolkata",
    }
    payload.update(overrides)
    return payload


def _create_library(client, headers, **overrides) -> dict[str, object]:
    response = client.post(
        BASE_PATH,
        json=_library_payload(**overrides),
        headers=headers,
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def test_platform_routes_require_super_admin(api, registered_owner, owner_headers) -> None:
    client, testing_session = api
    unauthenticated = client.get(BASE_PATH)
    assert unauthenticated.status_code == 401

    owner_denied = client.get(BASE_PATH, headers=owner_headers)
    assert owner_denied.status_code == 403

    library_id = uuid.UUID(registered_owner["user"]["libraryId"])
    for role_name in (RoleName.STAFF, RoleName.STUDENT):
        email = f"{role_name.value}@example.com"
        _create_user(
            testing_session,
            email=email,
            role_name=role_name,
            library_id=library_id,
        )
        denied = client.get(BASE_PATH, headers=_login(client, email))
        assert denied.status_code == 403


def test_list_search_filter_sort_paginate_and_get_details(
    api,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    alpha = _create_library(
        client,
        super_admin_headers,
        name="Alpha Reading Room",
        code="ALPHA",
        contactEmail="alpha@example.com",
        city="Jaipur",
        state="Rajasthan",
    )
    beta = _create_library(
        client,
        super_admin_headers,
        name="Beta Study Centre",
        code="BETA",
        contactEmail="beta@example.com",
        city="Pune",
    )
    activated = client.patch(
        f"{BASE_PATH}/{beta['id']}/status",
        json={"status": "active", "expectedUpdatedAt": beta["updatedAt"]},
        headers=super_admin_headers,
    )
    assert activated.status_code == 200

    searched = client.get(
        BASE_PATH,
        params={"search": "jaipur", "page": 1, "pageSize": 10},
        headers=super_admin_headers,
    )
    assert searched.status_code == 200
    assert [item["id"] for item in searched.json()["data"]] == [alpha["id"]]

    filtered = client.get(
        BASE_PATH,
        params={
            "status": "pending",
            "sortBy": "name",
            "sortOrder": "asc",
            "page": 1,
            "pageSize": 1,
        },
        headers=super_admin_headers,
    )
    body = filtered.json()
    assert filtered.status_code == 200
    assert body["meta"] == {
        "page": 1,
        "pageSize": 1,
        "totalItems": 1,
        "totalPages": 1,
    }
    assert body["summary"] == {"total": 2, "active": 1, "pending": 1, "suspended": 0}

    detail = client.get(f"{BASE_PATH}/{alpha['id']}", headers=super_admin_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["code"] == "ALPHA"
    assert "passwordHash" not in str(detail.json())


def test_create_library_adds_settings_audit_but_not_physical_inventory(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    created = _create_library(client, super_admin_headers, code="draft-lib")
    assert created["code"] == "DRAFT-LIB"
    assert created["status"] == "pending"
    assert created["seatCount"] == 0
    assert created["owner"] is None

    with testing_session() as db:
        library_id = uuid.UUID(created["id"])
        assert db.scalar(
            select(func.count(LibrarySettings.id)).where(
                LibrarySettings.library_id == library_id
            )
        ) == 1
        assert db.scalar(
            select(func.count(Floor.id)).where(Floor.library_id == library_id)
        ) == 0
        assert db.scalar(
            select(func.count(Seat.id)).where(Seat.library_id == library_id)
        ) == 0
        assert db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.library_id == library_id,
                AuditLog.action == "platform.library.created",
            )
        ) == 1


def test_create_rejects_duplicate_and_invalid_profile_data(
    api,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    original = _create_library(
        client,
        super_admin_headers,
        name="Unique Platform Library",
        code="UNIQUE-PLATFORM",
    )
    duplicate_name = client.post(
        BASE_PATH,
        json=_library_payload(name=" unique platform library ", code="OTHER-CODE"),
        headers=super_admin_headers,
    )
    assert duplicate_name.status_code == 409
    assert duplicate_name.json()["error"]["code"] == "PLATFORM_LIBRARY_DUPLICATE"

    duplicate_code = client.post(
        BASE_PATH,
        json=_library_payload(name="Another Name", code=original["code"]),
        headers=super_admin_headers,
    )
    assert duplicate_code.status_code == 409

    for overrides, expected_code in (
        ({"contactEmail": "invalid"}, "VALIDATION_ERROR"),
        ({"contactPhone": "abc"}, "PLATFORM_LIBRARY_PHONE_INVALID"),
        ({"timezone": "Mars/Olympus"}, "PLATFORM_LIBRARY_TIMEZONE_INVALID"),
    ):
        response = client.post(
            BASE_PATH,
            json=_library_payload(**overrides),
            headers=super_admin_headers,
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == expected_code


def test_edit_allows_profile_fields_and_rejects_immutable_or_stale_data(
    api,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    library = _create_library(client, super_admin_headers)
    updated = client.patch(
        f"{BASE_PATH}/{library['id']}",
        json={
            "name": "Updated Platform Library",
            "city": "Mumbai",
            "expectedUpdatedAt": library["updatedAt"],
        },
        headers=super_admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Updated Platform Library"
    assert updated.json()["data"]["code"] == library["code"]

    immutable = client.patch(
        f"{BASE_PATH}/{library['id']}",
        json={"code": "CHANGED"},
        headers=super_admin_headers,
    )
    assert immutable.status_code == 422

    stale = client.patch(
        f"{BASE_PATH}/{library['id']}",
        json={
            "city": "Delhi",
            "expectedUpdatedAt": library["updatedAt"],
        },
        headers=super_admin_headers,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "PLATFORM_LIBRARY_STATE_CHANGED"


def test_status_lifecycle_requires_reason_and_blocks_tenant_authentication(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    owner_email = "assigned.owner@example.com"
    owner_id = _create_user(
        testing_session,
        email=owner_email,
        role_name=RoleName.LIBRARY_OWNER,
    )
    library = _create_library(
        client,
        super_admin_headers,
        ownerId=str(owner_id),
    )
    activated = client.patch(
        f"{BASE_PATH}/{library['id']}/status",
        json={"status": "active", "expectedUpdatedAt": library["updatedAt"]},
        headers=super_admin_headers,
    )
    assert activated.status_code == 200
    active = activated.json()["data"]
    owner_headers = _login(client, owner_email)

    missing_reason = client.patch(
        f"{BASE_PATH}/{library['id']}/status",
        json={"status": "suspended", "expectedUpdatedAt": active["updatedAt"]},
        headers=super_admin_headers,
    )
    assert missing_reason.status_code == 422

    suspended_response = client.patch(
        f"{BASE_PATH}/{library['id']}/status",
        json={
            "status": "suspended",
            "reason": "Policy review",
            "expectedUpdatedAt": active["updatedAt"],
        },
        headers=super_admin_headers,
    )
    assert suspended_response.status_code == 200
    suspended = suspended_response.json()["data"]
    assert suspended["suspensionReason"] == "Policy review"
    assert client.get("/api/v1/auth/me", headers=owner_headers).status_code == 401

    repeated = client.patch(
        f"{BASE_PATH}/{library['id']}/status",
        json={"status": "suspended", "reason": "Again"},
        headers=super_admin_headers,
    )
    assert repeated.status_code == 409

    reactivated = client.patch(
        f"{BASE_PATH}/{library['id']}/status",
        json={"status": "active", "expectedUpdatedAt": suspended["updatedAt"]},
        headers=super_admin_headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["data"]["suspensionReason"] is None
    assert client.get("/api/v1/auth/me", headers=owner_headers).status_code == 200


def test_owner_assignment_preserves_membership_history_and_rejects_conflicts(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    first_id = _create_user(
        testing_session,
        email="first.owner@example.com",
        role_name=RoleName.LIBRARY_OWNER,
    )
    second_id = _create_user(
        testing_session,
        email="second.owner@example.com",
        role_name=RoleName.LIBRARY_OWNER,
    )
    invalid_id = _create_user(
        testing_session,
        email="not.owner@example.com",
        role_name=RoleName.STAFF,
    )
    options = client.get(
        f"{BASE_PATH}/owner-options",
        headers=super_admin_headers,
    )
    assert options.status_code == 200
    option_ids = {item["id"] for item in options.json()["data"]}
    assert option_ids == {str(first_id), str(second_id)}
    assert str(invalid_id) not in option_ids
    first_library = _create_library(
        client,
        super_admin_headers,
        ownerId=str(first_id),
    )
    second_library = _create_library(client, super_admin_headers)

    replaced = client.patch(
        f"{BASE_PATH}/{first_library['id']}/owner",
        json={
            "ownerId": str(second_id),
            "expectedUpdatedAt": first_library["updatedAt"],
        },
        headers=super_admin_headers,
    )
    assert replaced.status_code == 200
    assert replaced.json()["data"]["owner"]["id"] == str(second_id)

    duplicate = client.patch(
        f"{BASE_PATH}/{first_library['id']}/owner",
        json={"ownerId": str(second_id)},
        headers=super_admin_headers,
    )
    assert duplicate.status_code == 409

    cross_library = client.patch(
        f"{BASE_PATH}/{second_library['id']}/owner",
        json={"ownerId": str(second_id)},
        headers=super_admin_headers,
    )
    assert cross_library.status_code == 409
    assert cross_library.json()["error"]["code"] == "PLATFORM_LIBRARY_OWNER_CONFLICT"

    invalid = client.patch(
        f"{BASE_PATH}/{second_library['id']}/owner",
        json={"ownerId": str(invalid_id)},
        headers=super_admin_headers,
    )
    assert invalid.status_code == 422

    with testing_session() as db:
        memberships = list(
            db.scalars(
                select(LibraryMembership).where(
                    LibraryMembership.library_id == uuid.UUID(first_library["id"])
                )
            )
        )
        assert len(memberships) == 2
        first_membership = next(item for item in memberships if item.user_id == first_id)
        second_membership = next(item for item in memberships if item.user_id == second_id)
        assert first_membership.status == MembershipStatus.LEFT
        assert first_membership.left_at is not None
        assert second_membership.status == MembershipStatus.ACTIVE


def test_create_rolls_back_library_and_audit_when_audit_write_fails(
    api,
    super_admin_headers,
    monkeypatch,
) -> None:
    _client, testing_session = api
    payload = _library_payload(name="Rollback Library", code="ROLLBACK")

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(platform_service, "write_audit_log", fail_audit)
    with testing_session() as db:
        actor_id = db.scalar(
            select(User.id).where(User.email == "platform.admin@example.com")
        )
        with pytest.raises(RuntimeError, match="audit unavailable"):
            platform_service.create_library(
                db,
                PlatformLibraryCreate.model_validate(payload),
                actor_id,
            )
        assert db.scalar(select(Library.id).where(Library.code == "ROLLBACK")) is None
        assert db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.action == "platform.library.created"
            )
        ) == 0


def test_failed_status_transition_does_not_write_audit(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    library = _create_library(client, super_admin_headers)
    response = client.patch(
        f"{BASE_PATH}/{library['id']}/status",
        json={"status": "suspended", "reason": "Not allowed from pending"},
        headers=super_admin_headers,
    )
    assert response.status_code == 409
    with testing_session() as db:
        assert db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.library_id == uuid.UUID(library["id"]),
                AuditLog.action == "platform.library.suspended",
            )
        ) == 0


def test_suspension_blocks_invitation_validation_and_acceptance(
    api,
    registered_owner,
    owner_headers,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    created = client.post(
        "/api/v1/students",
        json={
            "firstName": "Suspended",
            "lastName": "Student",
            "email": "suspended.student@example.com",
            "phone": "9876543211",
            "joiningDate": "2026-08-03",
            "feeAmount": 1200,
            "status": "active",
            "sendInvitation": True,
        },
        headers=owner_headers,
    )
    assert created.status_code == 201
    token = parse_qs(
        urlsplit(created.json()["data"]["invitationSetupUrl"]).query
    )["token"][0]
    library_id = registered_owner["user"]["libraryId"]
    detail = client.get(
        f"{BASE_PATH}/{library_id}",
        headers=super_admin_headers,
    ).json()["data"]
    suspended = client.patch(
        f"{BASE_PATH}/{library_id}/status",
        json={
            "status": "suspended",
            "reason": "Platform review",
            "expectedUpdatedAt": detail["updatedAt"],
        },
        headers=super_admin_headers,
    )
    assert suspended.status_code == 200

    validation = client.get(
        "/api/v1/auth/invitations/validate",
        params={"token": token},
    )
    acceptance = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "StudentPass123"},
    )
    assert validation.status_code == 422
    assert acceptance.status_code == 422
