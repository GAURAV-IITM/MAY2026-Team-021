from __future__ import annotations

import unittest
from http.cookies import SimpleCookie
from types import SimpleNamespace

from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - registers all SQLAlchemy metadata
from app.api.v1.endpoints.auth import (
    REFRESH_COOKIE_NAME,
    login_session,
    refresh_session,
)
from app.db.base import Base
from app.schemas.auth import LoginRequest, RegisterLibraryRequest
from app.services import auth


def request_stub(*, cookies: dict[str, str] | None = None):
    return SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={"user-agent": "test"},
        cookies=cookies or {},
    )


def response_cookies(response: Response) -> SimpleCookie:
    cookies = SimpleCookie()
    for key, value in response.raw_headers:
        if key.lower() == b"set-cookie":
            cookies.load(value.decode("latin-1"))
    return cookies


class BrowserAuthenticationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.registered = auth.register_library(
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

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_browser_login_uses_http_only_persistent_cookie(self) -> None:
        response = Response()
        result = login_session(
            payload=LoginRequest(
                email="owner@example.com",
                password="SecurePass123",
                remember_me=True,
            ),
            request=request_stub(),
            response=response,
            db=self.db,
        )

        self.assertTrue(result.access_token)
        self.assertFalse(hasattr(result, "refresh_token"))

        cookies = response_cookies(response)
        refresh_cookie = cookies[REFRESH_COOKIE_NAME]
        self.assertTrue(refresh_cookie.value)
        self.assertTrue(refresh_cookie["httponly"])
        self.assertTrue(refresh_cookie["max-age"])
        self.assertEqual("/api/v1/auth", refresh_cookie["path"])

    def test_browser_refresh_rotates_cookie_without_exposing_token(self) -> None:
        login_response = Response()
        login_session(
            payload=LoginRequest(
                email="owner@example.com",
                password="SecurePass123",
                remember_me=False,
            ),
            request=request_stub(),
            response=login_response,
            db=self.db,
        )
        login_cookies = response_cookies(login_response)
        old_refresh_token = login_cookies[REFRESH_COOKIE_NAME].value

        refresh_response = Response()
        result = refresh_session(
            request=request_stub(
                cookies={
                    REFRESH_COOKIE_NAME: old_refresh_token,
                    "smart_library_remember_session": "0",
                }
            ),
            response=refresh_response,
            db=self.db,
        )

        new_refresh_token = response_cookies(refresh_response)[
            REFRESH_COOKIE_NAME
        ].value
        self.assertTrue(result.access_token)
        self.assertNotEqual(old_refresh_token, new_refresh_token)
        self.assertFalse(hasattr(result, "refresh_token"))

        with self.assertRaises(Exception) as reused:
            auth.refresh(
                self.db,
                old_refresh_token,
                ip_address=None,
                user_agent=None,
            )
        self.assertEqual(401, reused.exception.status_code)

    def test_profile_and_password_changes_are_persisted(self) -> None:
        user = self.db.get(
            app.models.User,
            self.registered.user.id,
        )
        updated = auth.update_profile(
            self.db,
            user,
            name="Updated Owner",
            email="updated@example.com",
            phone="9876543210",
        )
        self.assertEqual("Updated Owner", updated.name)
        self.assertEqual("updated@example.com", updated.email)

        auth.change_password(
            self.db,
            user,
            current_password="SecurePass123",
            new_password="NewSecurePass456",
        )
        logged_in = auth.login(
            self.db,
            "updated@example.com",
            "NewSecurePass456",
            ip_address=None,
            user_agent=None,
        )
        self.assertEqual(user.id, logged_in.user.id)

        with self.assertRaises(Exception) as old_password:
            auth.login(
                self.db,
                "updated@example.com",
                "SecurePass123",
                ip_address=None,
                user_agent=None,
            )
        self.assertEqual(401, old_password.exception.status_code)


if __name__ == "__main__":
    unittest.main()
