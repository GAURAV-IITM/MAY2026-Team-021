"""Password and JWT primitives used by the authentication service."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    """Hash a password using scrypt with a unique random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt$16384$8$1${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, n, r, p, salt, expected = password_hash.split("$")
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=_b64decode(salt), n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(actual, _b64decode(expected))
    except (ValueError, TypeError):
        return False


_ALGORITHMS = {
    "HS256": hashlib.sha256,
    "HS384": hashlib.sha384,
    "HS512": hashlib.sha512,
}


def create_access_token(*, subject: str, session_id: str, roles: list[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "sid": session_id, "roles": roles, "iat": int(now.timestamp()),
               "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()), "typ": "access"}
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    hash_fn = _ALGORITHMS.get(settings.jwt_algorithm)
    if hash_fn is None:
        raise ValueError(f"Unsupported algorithm: {settings.jwt_algorithm}")
    encoded_header = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(settings.jwt_secret_key.encode(), f"{encoded_header}.{encoded_payload}".encode(), hash_fn).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64encode(signature)}"


def decode_access_token(token: str, verify_expiry: bool = True) -> dict[str, Any] | None:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        header = json.loads(_b64decode(encoded_header))
        alg = header.get("alg")
        if alg not in _ALGORITHMS or alg != settings.jwt_algorithm:
            return None
        hash_fn = _ALGORITHMS[alg]
        expected_signature = hmac.new(settings.jwt_secret_key.encode(), f"{encoded_header}.{encoded_payload}".encode(), hash_fn).digest()
        if not hmac.compare_digest(expected_signature, _b64decode(encoded_signature)):
            return None
        payload = json.loads(_b64decode(encoded_payload))
        if payload.get("typ") != "access":
            return None
        if verify_expiry and int(payload["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
