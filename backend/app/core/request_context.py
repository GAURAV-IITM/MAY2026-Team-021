"""Request correlation helpers."""
from __future__ import annotations

import re
import uuid

from fastapi import Request


REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def resolve_request_id(request: Request) -> str:
    supplied_request_id = request.headers.get(REQUEST_ID_HEADER, "").strip()
    if REQUEST_ID_PATTERN.fullmatch(supplied_request_id):
        return supplied_request_id
    return str(uuid.uuid4())
