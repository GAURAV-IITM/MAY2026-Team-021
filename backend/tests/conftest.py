"""Shared pytest fixtures for API and database integration tests."""
from __future__ import annotations

from collections.abc import Generator
from typing import Any

import anyio.to_thread
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers all SQLAlchemy metadata
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from tests.api_helpers import ASGITestClient, bearer, register


@pytest.fixture
def db_engine() -> Generator[Engine, None, None]:
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
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def testing_session(
    db_engine: Engine,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest.fixture
def api(
    monkeypatch: pytest.MonkeyPatch,
    testing_session: sessionmaker[Session],
) -> Generator[tuple[ASGITestClient, sessionmaker[Session]], None, None]:
    async def run_sync_inline(function, *args, **_kwargs):
        return function(*args)

    # Inline execution keeps the in-process ASGI client deterministic in CI.
    monkeypatch.setattr(anyio.to_thread, "run_sync", run_sync_inline)
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as db:
            yield db

    application.dependency_overrides[get_db] = override_get_db
    yield ASGITestClient(application), testing_session
    application.dependency_overrides.clear()


@pytest.fixture
def registered_owner(api) -> dict[str, Any]:
    client, _testing_session = api
    response = register(client)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def owner_headers(registered_owner: dict[str, Any]) -> dict[str, str]:
    return bearer(registered_owner["accessToken"])
