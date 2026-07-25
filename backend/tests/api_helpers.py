"""Reusable helpers for backend API integration tests."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlsplit


@dataclass(frozen=True)
class ASGIResponse:
    status_code: int
    body: bytes
    headers: dict[str, str]

    def json(self) -> Any:
        return json.loads(self.body)


class ASGITestClient:
    """Small synchronous client for deterministic in-process ASGI tests."""

    def __init__(self, application) -> None:
        self.application = application

    def get(
        self,
        path: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ASGIResponse:
        return self.request("GET", path, params=params, headers=headers)

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

    def patch(
        self,
        path: str,
        *,
        json_body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> ASGIResponse:
        if "json" in kwargs:
            json_body = kwargs["json"]
        return self.request("PATCH", path, json_body=json_body, headers=headers)

    def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> ASGIResponse:
        return self.request("DELETE", path, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json_body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ASGIResponse:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._request(
                    method,
                    path,
                    params=params,
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
        params: dict[str, object] | None,
        json_body: dict[str, object] | None,
        headers: dict[str, str] | None,
    ) -> ASGIResponse:
        parsed_path = urlsplit(path)
        query_string = parsed_path.query
        if params:
            encoded_params = urlencode(params, doseq=True)
            query_string = "&".join(
                value for value in (query_string, encoded_params) if value
            )

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
            "path": parsed_path.path,
            "raw_path": parsed_path.path.encode("ascii"),
            "query_string": query_string.encode("ascii"),
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


def registration_payload(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "libraryName": "Central Study Library",
        "ownerName": "Library Owner",
        "email": "owner@example.com",
        "password": "SecurePass123",
        "phone": "9876543210",
        "address": "1 Reading Lane",
        "seatCount": 10,
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
