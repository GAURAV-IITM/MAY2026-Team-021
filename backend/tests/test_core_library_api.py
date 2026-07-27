"""Phase 2 API coverage for tenant-owned library data."""
from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

from tests.api_helpers import bearer, register


def student_payload(**overrides):
    payload = {
        "firstName": "Aarav",
        "lastName": "Sharma",
        "email": "aarav@example.com",
        "phone": "9876543211",
        "joiningDate": "2026-07-25",
        "feeAmount": 1200,
        "status": "active",
        "sendInvitation": True,
    }
    payload.update(overrides)
    return payload


def test_student_crud_invitation_and_password_setup(api, owner_headers) -> None:
    client, _ = api
    created = client.post(
        "/api/v1/students",
        json=student_payload(),
        headers=owner_headers,
    )
    assert created.status_code == 201
    student = created.json()["data"]
    assert student["enrollmentNumber"].startswith("STU-")
    assert student["portalAccessStatus"] == "not_activated"
    setup_url = student["invitationSetupUrl"]
    token = parse_qs(urlsplit(setup_url).query)["token"][0]

    validation = client.get(
        "/api/v1/auth/invitations/validate",
        params={"token": token},
    )
    assert validation.status_code == 200
    assert validation.json()["email"] == "aarav@example.com"

    accepted = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "StudentPass123"},
    )
    assert accepted.status_code == 200
    assert client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "StudentPass123"},
    ).status_code == 422

    login = client.post(
        "/api/v1/auth/session/login",
        json={
            "email": "aarav@example.com",
            "password": "StudentPass123",
        },
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "student"

    updated = client.patch(
        f"/api/v1/students/{student['id']}",
        json={"email": "aarav.updated@example.com"},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert client.post(
        "/api/v1/auth/session/login",
        json={
            "email": "aarav.updated@example.com",
            "password": "StudentPass123",
        },
    ).status_code == 200
    assert client.post(
        "/api/v1/auth/session/login",
        json={
            "email": "aarav@example.com",
            "password": "StudentPass123",
        },
    ).status_code == 401

    changed = client.patch(
        f"/api/v1/students/{student['id']}/status",
        json={"status": "inactive"},
        headers=owner_headers,
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["status"] == "inactive"
    assert client.post(
        "/api/v1/auth/session/login",
        json={
            "email": "aarav.updated@example.com",
            "password": "StudentPass123",
        },
    ).status_code == 401


def test_student_records_are_isolated_by_library(api, owner_headers) -> None:
    client, _ = api
    created = client.post(
        "/api/v1/students",
        json=student_payload(sendInvitation=False),
        headers=owner_headers,
    )
    student_id = created.json()["data"]["id"]

    second_registration = register(
        client,
        libraryName="Second Library",
        email="second.owner@example.com",
        phone="9876543299",
    )
    second_headers = bearer(second_registration.json()["accessToken"])
    hidden = client.get(
        f"/api/v1/students/{student_id}",
        headers=second_headers,
    )
    assert hidden.status_code == 404


def test_floor_seat_shift_and_settings_workflows(api, owner_headers) -> None:
    client, _ = api
    floors = client.get("/api/v1/floors", headers=owner_headers)
    assert floors.status_code == 200
    default_floor = floors.json()["data"][0]
    assert default_floor["seatCount"] == 10

    second_floor = client.post(
        "/api/v1/floors",
        json={
            "name": "Floor 2",
            "code": "F2",
            "levelNumber": 2,
            "sortOrder": 2,
        },
        headers=owner_headers,
    )
    assert second_floor.status_code == 201
    floor_id = second_floor.json()["data"]["id"]

    seat = client.post(
        "/api/v1/seats",
        json={
            "seatNumber": "B-01",
            "floorId": floor_id,
            "seatType": "accessible",
            "status": "available",
            "notes": "Near entrance",
        },
        headers=owner_headers,
    )
    assert seat.status_code == 201
    seat_id = seat.json()["data"]["id"]

    changed = client.patch(
        "/api/v1/seats/bulk/status",
        json={
            "seatIds": [seat_id],
            "status": "maintenance",
            "reason": "Electrical repair",
        },
        headers=owner_headers,
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["seats"][0]["physicalStatus"] == "maintenance"

    overnight = client.post(
        "/api/v1/shifts",
        json={
            "name": "Overnight",
            "startTime": "22:00",
            "endTime": "02:00",
        },
        headers=owner_headers,
    )
    early = client.post(
        "/api/v1/shifts",
        json={
            "name": "Early",
            "startTime": "01:00",
            "endTime": "06:00",
        },
        headers=owner_headers,
    )
    assert overnight.status_code == 201
    assert overnight.json()["data"]["crossesMidnight"] is True
    overlap = client.post(
        "/api/v1/shifts/validate-selection",
        json={
            "shiftIds": [
                overnight.json()["data"]["id"],
                early.json()["data"]["id"],
            ]
        },
        headers=owner_headers,
    )
    assert overlap.status_code == 200
    assert overlap.json()["data"]["valid"] is False

    settings = client.get("/api/v1/settings/library", headers=owner_headers)
    payload = settings.json()["data"]
    payload.update(
        {
            "libraryName": "Central Library Updated",
            "contactPhone": "9876543210",
            "address": "1 Reading Lane",
            "city": "Delhi",
            "state": "Delhi",
            "postalCode": "110001",
            "openingTime": "06:00",
            "closingTime": "23:00",
            "defaultMonthlyFee": 1500,
        }
    )
    updated_settings = client.patch(
        "/api/v1/settings/library",
        json=payload,
        headers=owner_headers,
    )
    assert updated_settings.status_code == 200
    assert updated_settings.json()["data"]["defaultMonthlyFee"] == 1500

    assert client.delete(
        f"/api/v1/floors/{floor_id}",
        headers=owner_headers,
    ).status_code == 409
    assert client.delete(
        f"/api/v1/seats/{seat_id}",
        headers=owner_headers,
    ).status_code == 200
    assert client.delete(
        f"/api/v1/floors/{floor_id}",
        headers=owner_headers,
    ).status_code == 200
