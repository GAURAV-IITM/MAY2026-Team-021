"""API coverage for Super Admin platform owner management."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import func, select

from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.enums import (
    InvitationStatus,
    LibraryStatus,
    MembershipStatus,
    RoleName,
)
from app.models.identity import AccountInvitation, Role, User, UserRole, UserSession
from app.models.library import Library, LibraryMembership
from tests.api_helpers import bearer


PASSWORD = "SecurePass123"
BASE_PATH = "/api/v1/platform/owners"


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
    active: bool = True,
) -> uuid.UUID:
    with testing_session() as db:
        user = User(
            email=email,
            password_hash=hash_password(PASSWORD),
            full_name=email.split("@", 1)[0].replace(".", " ").title(),
            phone="9876543210",
            is_active=active,
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
    email = "owner.platform.admin@example.com"
    _create_user(testing_session, email=email, role_name=RoleName.SUPER_ADMIN)
    return _login(client, email)


def _create_library(client, headers, *, name: str | None = None) -> dict:
    suffix = uuid.uuid4().hex[:8].upper()
    response = client.post(
        "/api/v1/platform/libraries",
        headers=headers,
        json={
            "name": name or f"Owner Test Library {suffix}",
            "code": f"OWN-{suffix}",
            "contactEmail": f"library-{suffix.lower()}@example.com",
            "timezone": "Asia/Kolkata",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _invite(client, headers, library_id: str, **overrides) -> dict:
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "name": "Invited Owner",
        "email": f"owner-{suffix}@example.com",
        "phone": "+91 9876543210",
        "libraryId": library_id,
    }
    payload.update(overrides)
    response = client.post(
        f"{BASE_PATH}/invitations",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _accept(client, setup_url: str) -> dict:
    token = parse_qs(urlsplit(setup_url).query)["token"][0]
    response = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": PASSWORD},
    )
    assert response.status_code == 200, response.json()
    return response.json()


def test_owner_routes_require_super_admin(api, registered_owner, owner_headers) -> None:
    client, testing_session = api
    assert client.get(BASE_PATH).status_code == 401
    assert client.get(BASE_PATH, headers=owner_headers).status_code == 403

    library_id = uuid.UUID(registered_owner["user"]["libraryId"])
    for role_name in (RoleName.STAFF, RoleName.STUDENT):
        email = f"platform-owner-denied-{role_name.value}@example.com"
        _create_user(
            testing_session,
            email=email,
            role_name=role_name,
            library_id=library_id,
        )
        assert client.get(BASE_PATH, headers=_login(client, email)).status_code == 403


def test_invite_list_search_filter_page_and_detail(api, super_admin_headers) -> None:
    client, _testing_session = api
    library = _create_library(client, super_admin_headers, name="Jaipur Reading Hub")
    invited = _invite(
        client,
        super_admin_headers,
        library["id"],
        name="Aditi Platform Owner",
        email="aditi.platform@example.com",
    )
    assert invited["createdInvitation"] is True
    assert invited["invitationSetupUrl"].startswith("http")
    owner = invited["owner"]
    assert owner["status"] == "invited"
    assert owner["invitationStatus"] == "pending"

    listed = client.get(
        BASE_PATH,
        headers=super_admin_headers,
        params={
            "search": "jaipur",
            "status": "invited",
            "libraryId": library["id"],
            "invitationStatus": "pending",
            "page": 1,
            "pageSize": 1,
            "sortBy": "name",
            "sortOrder": "asc",
        },
    )
    assert listed.status_code == 200, listed.json()
    assert listed.json()["meta"]["totalItems"] == 1
    assert listed.json()["data"][0]["email"] == "aditi.platform@example.com"
    assert listed.json()["summary"]["invited"] == 1

    detail = client.get(
        f"{BASE_PATH}/{owner['id']}",
        headers=super_admin_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["assignmentHistory"] == []
    assert "token" not in str(detail.json()).lower()
    assert "password" not in str(detail.json()).lower()


def test_owner_invitation_acceptance_uses_shared_secure_flow(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    library = _create_library(client, super_admin_headers)
    invited = _invite(client, super_admin_headers, library["id"])
    accepted = _accept(client, invited["invitationSetupUrl"])
    assert accepted["role"] == "library_owner"

    with testing_session() as db:
        invitation = db.get(
            AccountInvitation,
            uuid.UUID(invited["owner"]["invitationId"]),
        )
        assert invitation.status == InvitationStatus.ACCEPTED
        assert invitation.accepted_user_id is not None
        assert invitation.token_hash not in invited["invitationSetupUrl"]
        user = db.get(User, invitation.accepted_user_id)
        assert user.password_hash != PASSWORD
        membership = db.scalar(
            select(LibraryMembership).where(
                LibraryMembership.library_id == uuid.UUID(library["id"]),
                LibraryMembership.user_id == user.id,
            )
        )
        assert membership.status == MembershipStatus.ACTIVE


def test_duplicate_invitation_and_ineligible_library_are_rejected(
    api,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    library = _create_library(client, super_admin_headers)
    invited = _invite(
        client,
        super_admin_headers,
        library["id"],
        email="duplicate.owner@example.com",
    )
    duplicate = client.post(
        f"{BASE_PATH}/invitations",
        headers=super_admin_headers,
        json={
            "name": "Duplicate Owner",
            "email": "duplicate.owner@example.com",
            "libraryId": library["id"],
        },
    )
    assert invited["createdInvitation"] is True
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PLATFORM_OWNER_INVITATION_EXISTS"

    suspended_library = _create_library(client, super_admin_headers)
    activated = client.patch(
        f"/api/v1/platform/libraries/{suspended_library['id']}/status",
        headers=super_admin_headers,
        json={"status": "active", "expectedUpdatedAt": suspended_library["updatedAt"]},
    ).json()["data"]
    client.patch(
        f"/api/v1/platform/libraries/{activated['id']}/status",
        headers=super_admin_headers,
        json={
            "status": "suspended",
            "reason": "Review",
            "expectedUpdatedAt": activated["updatedAt"],
        },
    )
    rejected = client.post(
        f"{BASE_PATH}/invitations",
        headers=super_admin_headers,
        json={
            "name": "Blocked Owner",
            "email": "blocked.owner@example.com",
            "libraryId": suspended_library["id"],
        },
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "PLATFORM_OWNER_LIBRARY_INELIGIBLE"


def test_expired_invitation_can_be_reissued_without_deleting_history(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    library = _create_library(client, super_admin_headers)
    original = _invite(
        client,
        super_admin_headers,
        library["id"],
        email="expired.owner@example.com",
    )
    with testing_session() as db:
        invitation = db.get(
            AccountInvitation,
            uuid.UUID(original["owner"]["invitationId"]),
        )
        invitation.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    reissued = _invite(
        client,
        super_admin_headers,
        library["id"],
        email="expired.owner@example.com",
    )
    assert reissued["owner"]["invitationId"] != original["owner"]["invitationId"]
    with testing_session() as db:
        statuses = list(
            db.scalars(
                select(AccountInvitation.status).where(
                    AccountInvitation.email == "expired.owner@example.com"
                )
            )
        )
        assert sorted(status.value for status in statuses) == ["expired", "pending"]


def test_existing_eligible_owner_is_assigned_without_invitation(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    owner_id = _create_user(
        testing_session,
        email="existing.eligible.owner@example.com",
        role_name=RoleName.LIBRARY_OWNER,
    )
    library = _create_library(client, super_admin_headers)
    result = _invite(
        client,
        super_admin_headers,
        library["id"],
        name="Existing Eligible Owner",
        email="existing.eligible.owner@example.com",
    )
    assert result["createdInvitation"] is False
    assert result["invitationSetupUrl"] is None
    assert result["owner"]["id"] == str(owner_id)

    with testing_session() as db:
        assert db.scalar(
            select(func.count(AccountInvitation.id)).where(
                AccountInvitation.email == "existing.eligible.owner@example.com"
            )
        ) == 0


def test_invite_rejects_assigned_owner_and_invalid_input(
    api,
    registered_owner,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    target = _create_library(client, super_admin_headers)
    assigned = client.post(
        f"{BASE_PATH}/invitations",
        headers=super_admin_headers,
        json={
            "name": registered_owner["user"]["name"],
            "email": registered_owner["user"]["email"],
            "libraryId": target["id"],
        },
    )
    assert assigned.status_code == 409
    assert assigned.json()["error"]["code"] == "PLATFORM_OWNER_ASSIGNMENT_CONFLICT"

    invalid_email = client.post(
        f"{BASE_PATH}/invitations",
        headers=super_admin_headers,
        json={"name": "Invalid", "email": "not-an-email", "libraryId": target["id"]},
    )
    invalid_phone = client.post(
        f"{BASE_PATH}/invitations",
        headers=super_admin_headers,
        json={
            "name": "Invalid Phone",
            "email": "invalid-phone@example.com",
            "phone": "phone-number",
            "libraryId": target["id"],
        },
    )
    assert invalid_email.status_code == 422
    assert invalid_phone.status_code == 422
    assert invalid_phone.json()["error"]["code"] == "PLATFORM_OWNER_PHONE_INVALID"


def test_owner_edit_rejects_security_and_assignment_fields(
    api,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    library = _create_library(client, super_admin_headers)
    invited = _invite(client, super_admin_headers, library["id"])
    accepted = _accept(client, invited["invitationSetupUrl"])
    owner = client.get(
        BASE_PATH,
        headers=super_admin_headers,
        params={"search": accepted["email"]},
    ).json()["data"][0]
    rejected = client.patch(
        f"{BASE_PATH}/{owner['id']}",
        headers=super_admin_headers,
        json={
            "email": "changed@example.com",
            "password": "PlaintextPassword123",
            "role": "super_admin",
            "libraryId": library["id"],
        },
    )
    assert rejected.status_code == 422
    detail = client.get(
        f"{BASE_PATH}/{owner['id']}",
        headers=super_admin_headers,
    ).json()["data"]
    assert detail["email"] == accepted["email"]


def test_edit_and_reassign_owner_preserve_membership_history(
    api,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    first = _create_library(client, super_admin_headers, name="First Owner Library")
    second = _create_library(client, super_admin_headers, name="Second Owner Library")
    invited = _invite(client, super_admin_headers, first["id"])
    accepted = _accept(client, invited["invitationSetupUrl"])
    owner_email = accepted["email"]
    listed = client.get(
        BASE_PATH,
        headers=super_admin_headers,
        params={"search": owner_email},
    ).json()["data"]
    owner = listed[0]

    edited = client.patch(
        f"{BASE_PATH}/{owner['id']}",
        headers=super_admin_headers,
        json={
            "name": "Updated Owner Name",
            "phone": "+91 9000000001",
            "expectedUpdatedAt": owner["updatedAt"],
        },
    )
    assert edited.status_code == 200, edited.json()
    updated = edited.json()["data"]
    assert updated["name"] == "Updated Owner Name"

    reassigned = client.patch(
        f"{BASE_PATH}/{owner['id']}/assignment",
        headers=super_admin_headers,
        json={
            "libraryId": second["id"],
            "expectedUpdatedAt": updated["updatedAt"],
        },
    )
    assert reassigned.status_code == 200, reassigned.json()
    assert reassigned.json()["data"]["assignments"][0]["id"] == second["id"]
    detail = client.get(
        f"{BASE_PATH}/{owner['id']}",
        headers=super_admin_headers,
    ).json()["data"]
    history = {item["libraryId"]: item for item in detail["assignmentHistory"]}
    assert history[first["id"]]["membershipStatus"] == "left"
    assert history[first["id"]]["leftAt"] is not None
    assert history[second["id"]]["membershipStatus"] == "active"


def test_owner_suspension_revokes_sessions_and_activation_requires_new_login(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    library = _create_library(client, super_admin_headers)
    invited = _invite(
        client,
        super_admin_headers,
        library["id"],
        email="session.owner@example.com",
    )
    _accept(client, invited["invitationSetupUrl"])
    pending_library = client.get(
        f"/api/v1/platform/libraries/{library['id']}",
        headers=super_admin_headers,
    ).json()["data"]
    client.patch(
        f"/api/v1/platform/libraries/{library['id']}/status",
        headers=super_admin_headers,
        json={
            "status": "active",
            "expectedUpdatedAt": pending_library["updatedAt"],
        },
    )
    owner_headers = _login(client, "session.owner@example.com")
    owner = client.get(
        BASE_PATH,
        headers=super_admin_headers,
        params={"search": "session.owner@example.com"},
    ).json()["data"][0]

    suspended = client.patch(
        f"{BASE_PATH}/{owner['id']}/status",
        headers=super_admin_headers,
        json={
            "status": "suspended",
            "reason": "Administrative review",
            "expectedUpdatedAt": owner["updatedAt"],
        },
    )
    assert suspended.status_code == 200, suspended.json()
    assert client.get("/api/v1/auth/me", headers=owner_headers).status_code == 401
    with testing_session() as db:
        owner_id = uuid.UUID(owner["id"])
        assert db.scalar(
            select(func.count(UserSession.id)).where(
                UserSession.user_id == owner_id,
                UserSession.revoked_at.is_not(None),
            )
        ) >= 1
        membership = db.scalar(
            select(LibraryMembership).where(
                LibraryMembership.user_id == owner_id,
                LibraryMembership.library_id == uuid.UUID(library["id"]),
            )
        )
        assert membership.status == MembershipStatus.SUSPENDED

    suspended_owner = suspended.json()["data"]
    activated = client.patch(
        f"{BASE_PATH}/{owner['id']}/status",
        headers=super_admin_headers,
        json={
            "status": "active",
            "expectedUpdatedAt": suspended_owner["updatedAt"],
        },
    )
    assert activated.status_code == 200
    assert client.get("/api/v1/auth/me", headers=owner_headers).status_code == 401
    assert _login(client, "session.owner@example.com")


def test_failed_owner_mutation_does_not_write_audit(api, super_admin_headers) -> None:
    client, testing_session = api
    library = _create_library(client, super_admin_headers)
    _invite(
        client,
        super_admin_headers,
        library["id"],
        email="audit.owner@example.com",
    )
    with testing_session() as db:
        before = db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.action.like("platform.owner.%")
            )
        )
    failed = client.post(
        f"{BASE_PATH}/invitations",
        headers=super_admin_headers,
        json={
            "name": "Audit Duplicate",
            "email": "audit.owner@example.com",
            "libraryId": library["id"],
        },
    )
    assert failed.status_code == 409
    with testing_session() as db:
        after = db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.action.like("platform.owner.%")
            )
        )
    assert after == before
