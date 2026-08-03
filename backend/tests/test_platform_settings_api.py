"""Security, validation, persistence, and runtime tests for platform settings."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.core.security import decode_access_token, hash_password
from app.models.audit import AuditLog
from app.models.enums import MembershipStatus, RoleName
from app.models.identity import Role, User, UserRole
from app.models.library import Library, LibraryMembership, PlatformSetting
from app.schemas.platform import PlatformSettingsUpdate
from app.services import platform_settings as platform_settings_service
from tests.api_helpers import bearer, registration_payload


PASSWORD = "SecurePass123"
BASE_PATH = "/api/v1/platform/settings"


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
    email = "settings.admin@example.com"
    _create_user(testing_session, email=email, role_name=RoleName.SUPER_ADMIN)
    return _login(client, email)


def _update(client, headers, version: int = 0, **settings):
    return client.patch(
        BASE_PATH,
        json={"version": version, **settings},
        headers=headers,
    )


def test_registry_contains_only_approved_keys_and_defaults(api, super_admin_headers) -> None:
    client, _testing_session = api
    response = client.get(BASE_PATH, headers=super_admin_headers)
    assert response.status_code == 200
    assert response.headers["x-request-id"]
    data = response.json()["data"]
    assert data["settings"] == {
        "platformName": "Smart Library API",
        "allowLibraryRegistrations": True,
        "sessionTimeoutMinutes": 30,
        "defaultTimezone": "Asia/Kolkata",
    }
    assert data["version"] == 0
    assert data["updatedAt"] is None
    assert {item["key"] for item in data["definitions"]} == {
        "platformName",
        "allowLibraryRegistrations",
        "sessionTimeoutMinutes",
        "defaultTimezone",
    }
    assert next(
        item for item in data["definitions"] if item["key"] == "platformName"
    )["editable"] is False


def test_platform_settings_routes_require_super_admin(
    api,
    registered_owner,
    owner_headers,
) -> None:
    client, testing_session = api
    assert client.get(BASE_PATH).status_code == 401
    assert client.get(BASE_PATH, headers=owner_headers).status_code == 403
    assert _update(client, owner_headers, allowLibraryRegistrations=False).status_code == 403

    library_id = uuid.UUID(registered_owner["user"]["libraryId"])
    for role_name in (RoleName.STAFF, RoleName.STUDENT):
        email = f"settings.{role_name.value}@example.com"
        _create_user(
            testing_session,
            email=email,
            role_name=role_name,
            library_id=library_id,
        )
        assert client.get(BASE_PATH, headers=_login(client, email)).status_code == 403


def test_update_persists_all_values_and_writes_one_safe_audit(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    response = _update(
        client,
        super_admin_headers,
        allowLibraryRegistrations=False,
        sessionTimeoutMinutes=90,
        defaultTimezone="UTC",
    )
    assert response.status_code == 200, response.json()
    assert response.headers["x-request-id"]
    data = response.json()["data"]
    assert data["version"] == 1
    assert data["settings"]["allowLibraryRegistrations"] is False
    assert data["settings"]["sessionTimeoutMinutes"] == 90
    assert data["settings"]["defaultTimezone"] == "UTC"
    assert data["updatedAt"] is not None

    with testing_session() as db:
        rows = {
            row.key: row.value
            for row in db.scalars(select(PlatformSetting))
        }
        assert rows == {
            "allow_library_registrations": False,
            "session_timeout_minutes": 90,
            "default_timezone": "UTC",
            "__platform_settings_version__": 1,
        }
        audits = list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.action == "platform.settings.updated"
                )
            )
        )
        assert len(audits) == 1
        assert set(audits[0].new_values or {}) == {
            "allowLibraryRegistrations",
            "sessionTimeoutMinutes",
            "defaultTimezone",
        }
        assert "secret" not in str(audits[0].new_values).lower()


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"version": 0, "databaseUrl": "postgres://secret"}, "PLATFORM_SETTING_UNKNOWN"),
        ({"version": 0, "platformName": "Changed"}, "PLATFORM_SETTING_READ_ONLY"),
        (
            {"version": 0, "allowLibraryRegistrations": "false"},
            "PLATFORM_SETTING_INVALID_VALUE",
        ),
        (
            {"version": 0, "sessionTimeoutMinutes": 14},
            "PLATFORM_SETTING_INVALID_VALUE",
        ),
        (
            {"version": 0, "sessionTimeoutMinutes": 1441},
            "PLATFORM_SETTING_INVALID_VALUE",
        ),
        (
            {"version": 0, "defaultTimezone": "Europe/London"},
            "PLATFORM_SETTING_INVALID_VALUE",
        ),
    ],
)
def test_update_rejects_unknown_read_only_and_invalid_values(
    api,
    super_admin_headers,
    payload,
    code,
) -> None:
    client, testing_session = api
    response = client.patch(BASE_PATH, json=payload, headers=super_admin_headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == code
    with testing_session() as db:
        assert db.scalar(select(func.count(PlatformSetting.id))) == 0
        assert db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.action == "platform.settings.updated"
            )
        ) == 0


def test_mixed_invalid_update_is_atomic_and_stale_version_conflicts(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    invalid = _update(
        client,
        super_admin_headers,
        allowLibraryRegistrations=False,
        sessionTimeoutMinutes=0,
    )
    assert invalid.status_code == 422
    with testing_session() as db:
        assert db.scalar(select(func.count(PlatformSetting.id))) == 0

    first = _update(client, super_admin_headers, sessionTimeoutMinutes=120)
    assert first.status_code == 200
    stale = _update(
        client,
        super_admin_headers,
        version=0,
        allowLibraryRegistrations=False,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "PLATFORM_SETTINGS_UPDATE_CONFLICT"
    current = client.get(BASE_PATH, headers=super_admin_headers).json()["data"]
    assert current["version"] == 1
    assert current["settings"]["allowLibraryRegistrations"] is True
    assert current["settings"]["sessionTimeoutMinutes"] == 120


def test_safe_read_ignores_unknown_secret_rows(api, super_admin_headers) -> None:
    client, testing_session = api
    with testing_session() as db:
        db.add(
            PlatformSetting(
                key="jwt_secret_key",
                value="never-return-this-secret",
                description="Unsafe row outside the registry",
            )
        )
        db.commit()
    body = client.get(BASE_PATH, headers=super_admin_headers).json()
    assert "never-return-this-secret" not in str(body)
    assert "jwt_secret_key" not in str(body)


def test_runtime_settings_control_registration_timezone_and_new_token_lifetime(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    disabled = _update(
        client,
        super_admin_headers,
        allowLibraryRegistrations=False,
    )
    assert disabled.status_code == 200
    rejected = client.post(
        "/api/v1/auth/register-library",
        json=registration_payload(email="blocked-registration@example.com"),
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "LIBRARY_REGISTRATION_DISABLED"

    enabled = _update(
        client,
        super_admin_headers,
        version=1,
        allowLibraryRegistrations=True,
        sessionTimeoutMinutes=120,
        defaultTimezone="Asia/Dubai",
    )
    assert enabled.status_code == 200
    registered = client.post(
        "/api/v1/auth/register-library",
        json=registration_payload(email="runtime-registration@example.com"),
    )
    assert registered.status_code == 201, registered.json()
    assert registered.json()["expiresIn"] == 120 * 60
    claims = decode_access_token(registered.json()["accessToken"])
    assert claims is not None
    assert claims["exp"] - claims["iat"] == 120 * 60
    with testing_session() as db:
        library = db.scalar(
            select(Library).where(
                Library.contact_email == "runtime-registration@example.com"
            )
        )
        assert library is not None
        assert library.timezone == "Asia/Dubai"


def test_service_rolls_back_settings_and_audit_when_audit_write_fails(
    api,
    super_admin_headers,
    monkeypatch,
) -> None:
    _client, testing_session = api

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(platform_settings_service, "write_audit_log", fail_audit)
    with testing_session() as db:
        actor_id = db.scalar(
            select(User.id).where(User.email == "settings.admin@example.com")
        )
        assert actor_id is not None
        with pytest.raises(RuntimeError, match="audit unavailable"):
            platform_settings_service.update_settings(
                db,
                PlatformSettingsUpdate(
                    version=0,
                    sessionTimeoutMinutes=60,
                ),
                actor_id,
            )
    with testing_session() as db:
        assert db.scalar(select(func.count(PlatformSetting.id))) == 0
        assert db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.action == "platform.settings.updated"
            )
        ) == 0
