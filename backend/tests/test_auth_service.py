from __future__ import annotations

import unittest
import uuid
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - imports all SQLAlchemy model metadata
from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token
from app.db.base import Base
from app.schemas.auth import RegisterLibraryRequest
from app.services import auth


class AuthenticationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_registration_login_and_refresh_rotation(self) -> None:
        registered = auth.register_library(
            self.db,
            RegisterLibraryRequest(
                library_name="Central Study Library",
                owner_name="Library Owner",
                email="owner@example.com",
                password="SecurePass123",
                seat_count=10,
            ),
            ip_address="127.0.0.1",
            user_agent="test",
        )
        claims = decode_access_token(registered.access_token)
        self.assertIsNotNone(claims)
        self.assertEqual("admin", registered.user.role)

        logged_in = auth.login(
            self.db, "owner@example.com", "SecurePass123", ip_address=None, user_agent=None
        )
        refreshed = auth.refresh(
            self.db, logged_in.refresh_token, ip_address=None, user_agent=None
        )
        self.assertNotEqual(logged_in.refresh_token, refreshed.refresh_token)

        with self.assertRaises(Exception) as context:
            auth.refresh(self.db, logged_in.refresh_token, ip_address=None, user_agent=None)
        self.assertEqual(401, context.exception.status_code)

    def test_incorrect_password_is_rejected(self) -> None:
        auth.register_library(
            self.db,
            RegisterLibraryRequest(
                library_name="Central Study Library",
                owner_name="Library Owner",
                email="owner@example.com",
                password="SecurePass123",
            ),
            ip_address=None,
            user_agent=None,
        )
        with self.assertRaises(Exception) as context:
            auth.login(self.db, "owner@example.com", "WrongPassword123", ip_address=None, user_agent=None)
        self.assertEqual(401, context.exception.status_code)

    def test_decode_access_token_verify_expiry(self) -> None:
        expired_settings = Settings(access_token_expire_minutes=-10)
        with patch("app.core.security.settings", expired_settings):
            token = create_access_token(subject="user-123", session_id="session-456", roles=["admin"])
            self.assertIsNone(decode_access_token(token))
            payload = decode_access_token(token, verify_expiry=False)
            self.assertIsNotNone(payload)
            self.assertEqual(payload["sub"], "user-123")
            self.assertEqual(payload["sid"], "session-456")

    def test_jwt_algorithms(self) -> None:
        for alg in ["HS256", "HS384", "HS512"]:
            alg_settings = Settings(jwt_algorithm=alg)
            with patch("app.core.security.settings", alg_settings):
                token = create_access_token(subject="user-123", session_id="session-456", roles=["admin"])
                payload = decode_access_token(token)
                self.assertIsNotNone(payload)
                self.assertEqual(payload["sub"], "user-123")
                other_settings = Settings(jwt_algorithm="HS256" if alg != "HS256" else "HS512")
                with patch("app.core.security.settings", other_settings):
                    self.assertIsNone(decode_access_token(token))

        invalid_settings = Settings(jwt_algorithm="INVALID")
        with patch("app.core.security.settings", invalid_settings):
            with self.assertRaises(ValueError):
                create_access_token(subject="user-123", session_id="session-456", roles=["admin"])

    def test_logout_with_expired_token_revokes_session(self) -> None:
        registered = auth.register_library(
            self.db,
            RegisterLibraryRequest(
                library_name="Central Study Library",
                owner_name="Library Owner",
                email="owner@example.com",
                password="SecurePass123",
            ),
            ip_address=None,
            user_agent=None,
        )
        access_token = registered.access_token
        claims = decode_access_token(access_token)
        self.assertIsNotNone(claims)
        session_id = uuid.UUID(claims["sid"])

        from app.models.identity import UserSession
        session = self.db.get(UserSession, session_id)
        self.assertIsNotNone(session)
        self.assertIsNone(session.revoked_at)

        expired_settings = Settings(access_token_expire_minutes=-10)
        with patch("app.core.security.settings", expired_settings):
            expired_token = create_access_token(subject=claims["sub"], session_id=claims["sid"], roles=claims["roles"])

        self.assertIsNone(decode_access_token(expired_token))

        from unittest.mock import MagicMock
        from fastapi import Response

        mock_request = MagicMock()
        mock_request.headers = {"authorization": f"Bearer {expired_token}"}
        mock_response = MagicMock(spec=Response)

        from app.api.v1.endpoints.auth import logout
        logout(request=mock_request, response=mock_response, db=self.db)

        self.db.expire(session)
        self.assertIsNotNone(session.revoked_at)
