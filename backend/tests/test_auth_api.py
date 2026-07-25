from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.security import decode_access_token
from app.models.enums import LibraryStatus, MembershipStatus
from app.models.identity import UserSession
from app.models.library import Library, LibraryMembership, LibrarySettings
from app.models.seat import Floor, Seat, Shift
from tests.api_helpers import bearer, register


def test_registration_bootstraps_library_and_me(api) -> None:
    client, testing_session = api

    response = register(client, seatCount=25)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "admin"
    assert body["user"]["libraryId"]
    assert body["accessToken"]
    assert body["refreshToken"]

    me = client.get(
        "/api/v1/auth/me",
        headers=bearer(body["accessToken"]),
    )
    assert me.status_code == 200
    assert me.json()["email"] == "owner@example.com"

    with testing_session() as db:
        assert db.scalar(select(func.count()).select_from(LibrarySettings)) == 1
        assert db.scalar(select(func.count()).select_from(Floor)) == 1
        assert db.scalar(select(func.count()).select_from(Shift)) == 3
        assert db.scalar(select(func.count()).select_from(Seat)) == 25


def test_registration_validation_and_duplicate_conflict(api) -> None:
    client, _testing_session = api

    invalid = register(client, seatCount=0)
    assert invalid.status_code == 422

    first = register(client)
    assert first.status_code == 201

    duplicate = register(client)
    assert duplicate.status_code == 409


def test_refresh_rotation_revokes_old_session_and_logout_revokes_new_one(api) -> None:
    client, _testing_session = api
    registered = register(client).json()

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": registered["refreshToken"]},
    )
    assert refreshed.status_code == 200
    rotated = refreshed.json()
    assert rotated["refreshToken"] != registered["refreshToken"]

    reused = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": registered["refreshToken"]},
    )
    assert reused.status_code == 401

    old_access = client.get(
        "/api/v1/auth/me",
        headers=bearer(registered["accessToken"]),
    )
    assert old_access.status_code == 401

    active_access = client.get(
        "/api/v1/auth/me",
        headers=bearer(rotated["accessToken"]),
    )
    assert active_access.status_code == 200

    logged_out = client.post(
        "/api/v1/auth/logout",
        headers=bearer(rotated["accessToken"]),
    )
    assert logged_out.status_code == 200

    after_logout = client.get(
        "/api/v1/auth/me",
        headers=bearer(rotated["accessToken"]),
    )
    assert after_logout.status_code == 401


def test_expired_backing_session_is_rejected(api) -> None:
    client, testing_session = api
    registered = register(client).json()
    claims = decode_access_token(registered["accessToken"])
    assert claims is not None

    with testing_session() as db:
        session = db.get(UserSession, uuid.UUID(claims["sid"]))
        assert session is not None
        session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers=bearer(registered["accessToken"]),
    )
    assert response.status_code == 401


def test_suspended_library_or_membership_blocks_login_and_me(api) -> None:
    client, testing_session = api
    registered = register(client).json()

    with testing_session() as db:
        library = db.scalar(select(Library))
        assert library is not None
        library.status = LibraryStatus.SUSPENDED
        db.commit()

    suspended_me = client.get(
        "/api/v1/auth/me",
        headers=bearer(registered["accessToken"]),
    )
    assert suspended_me.status_code == 401

    suspended_login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "SecurePass123"},
    )
    assert suspended_login.status_code == 401

    suspended_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": registered["refreshToken"]},
    )
    assert suspended_refresh.status_code == 401

    with testing_session() as db:
        library = db.scalar(select(Library))
        membership = db.scalar(select(LibraryMembership))
        assert library is not None
        assert membership is not None
        library.status = LibraryStatus.ACTIVE
        membership.status = MembershipStatus.SUSPENDED
        db.commit()

    membership_login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "SecurePass123"},
    )
    assert membership_login.status_code == 401

    membership_me = client.get(
        "/api/v1/auth/me",
        headers=bearer(registered["accessToken"]),
    )
    assert membership_me.status_code == 401


def test_missing_and_malformed_access_tokens_are_rejected(api) -> None:
    client, _testing_session = api

    missing = client.get("/api/v1/auth/me")
    malformed = client.get(
        "/api/v1/auth/me",
        headers=bearer("not-a-valid-jwt"),
    )

    assert missing.status_code == 401
    assert malformed.status_code == 401
