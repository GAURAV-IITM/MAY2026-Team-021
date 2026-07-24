from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import anyio.to_thread
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers all SQLAlchemy metadata
from app.core.security import decode_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.enums import LibraryStatus, MembershipStatus
from app.models.identity import UserSession
from app.models.library import Library, LibraryMembership, LibrarySettings
from app.models.seat import Floor, Seat, Shift


@dataclass(frozen=True)
class ASGIResponse:
    status_code: int
    body: bytes
    headers: dict[str, str]

    def json(self) -> Any:
        return json.loads(self.body)


class ASGITestClient:
    """Small synchronous client for exercising the application through ASGI."""

    def __init__(self, application) -> None:
        self.application = application

    def get(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> ASGIResponse:
        return self.request("GET", path, headers=headers)

    def post(
        self,
        path: str,
        *,
        json_body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> ASGIResponse:
        if "json" in kwargs:
            json_body = kwargs["json"]
        return self.request("POST", path, json_body=json_body, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ASGIResponse:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._request(
                    method,
                    path,
                    json_body=json_body,
                    headers=headers,
                )
            )
        finally:
            loop.run_until_complete(asyncio.sleep(0))
            loop.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, object] | None,
        headers: dict[str, str] | None,
    ) -> ASGIResponse:
        body = (
            json.dumps(json_body).encode("utf-8")
            if json_body is not None
            else b""
        )
        request_headers = {
            "host": "testserver",
            "content-length": str(len(body)),
            **(headers or {}),
        }
        if json_body is not None:
            request_headers["content-type"] = "application/json"

        response_messages: list[dict[str, Any]] = []
        response_complete = asyncio.Event()
        request_sent = False

        async def receive() -> dict[str, Any]:
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False,
                }
            await response_complete.wait()
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            response_messages.append(message)
            if (
                message["type"] == "http.response.body"
                and not message.get("more_body", False)
            ):
                response_complete.set()

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "root_path": "",
            "headers": [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in request_headers.items()
            ],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "state": {},
        }
        await self.application(scope, receive, send)

        start = next(
            message
            for message in response_messages
            if message["type"] == "http.response.start"
        )
        response_body = b"".join(
            message.get("body", b"")
            for message in response_messages
            if message["type"] == "http.response.body"
        )
        response_headers = {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in start.get("headers", [])
        }
        return ASGIResponse(
            status_code=start["status"],
            body=response_body,
            headers=response_headers,
        )


@pytest.fixture
def api(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[ASGITestClient, sessionmaker[Session]], None, None]:
    async def run_sync_inline(function, *args, **_kwargs):
        return function(*args)

    # The test environment cannot shut down asyncio worker threads reliably.
    # Running sync callables inline keeps these in-process ASGI tests deterministic.
    monkeypatch.setattr(anyio.to_thread, "run_sync", run_sync_inline)

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as db:
            yield db

    application.dependency_overrides[get_db] = override_get_db
    yield ASGITestClient(application), testing_session

    application.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def registration_payload(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "library_name": "Central Study Library",
        "owner_name": "Library Owner",
        "email": "owner@example.com",
        "password": "SecurePass123",
        "phone": "9876543210",
        "address": "1 Reading Lane",
        "seat_count": 10,
    }
    payload.update(overrides)
    return payload


def register(client: ASGITestClient, **overrides) -> ASGIResponse:
    return client.post(
        "/api/v1/auth/register-library",
        json=registration_payload(**overrides),
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_registration_bootstraps_library_and_me(api) -> None:
    client, testing_session = api

    response = register(client, seat_count=25)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "admin"
    assert body["user"]["library_id"]
    assert body["access_token"]
    assert body["refresh_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers=bearer(body["access_token"]),
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

    invalid = register(client, seat_count=0)
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
        json={"refresh_token": registered["refresh_token"]},
    )
    assert refreshed.status_code == 200
    rotated = refreshed.json()
    assert rotated["refresh_token"] != registered["refresh_token"]

    reused = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered["refresh_token"]},
    )
    assert reused.status_code == 401

    old_access = client.get(
        "/api/v1/auth/me",
        headers=bearer(registered["access_token"]),
    )
    assert old_access.status_code == 401

    active_access = client.get(
        "/api/v1/auth/me",
        headers=bearer(rotated["access_token"]),
    )
    assert active_access.status_code == 200

    logged_out = client.post(
        "/api/v1/auth/logout",
        headers=bearer(rotated["access_token"]),
    )
    assert logged_out.status_code == 200

    after_logout = client.get(
        "/api/v1/auth/me",
        headers=bearer(rotated["access_token"]),
    )
    assert after_logout.status_code == 401


def test_expired_backing_session_is_rejected(api) -> None:
    client, testing_session = api
    registered = register(client).json()
    claims = decode_access_token(registered["access_token"])
    assert claims is not None

    with testing_session() as db:
        session = db.get(UserSession, uuid.UUID(claims["sid"]))
        assert session is not None
        session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers=bearer(registered["access_token"]),
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
        headers=bearer(registered["access_token"]),
    )
    assert suspended_me.status_code == 401

    suspended_login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "SecurePass123"},
    )
    assert suspended_login.status_code == 401

    suspended_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered["refresh_token"]},
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
        headers=bearer(registered["access_token"]),
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
