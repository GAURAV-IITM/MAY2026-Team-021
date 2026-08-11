"""Aggregate and access coverage for the Super Admin dashboard."""
from __future__ import annotations

import uuid
import time as clock
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import event, select

from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.enums import (
    AllocationStatus,
    InvitationStatus,
    LibraryStatus,
    MembershipStatus,
    RoleName,
    StudentStatus,
)
from app.models.identity import AccountInvitation, Role, User, UserRole
from app.models.library import Library, LibraryMembership
from app.models.seat import Floor, Seat, SeatAllocation, Shift
from app.models.student import Student
from app.services.platform import get_dashboard
from tests.api_helpers import bearer


PASSWORD = "SecurePass123"
BASE_PATH = "/api/v1/platform/dashboard"


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
    is_active: bool = True,
    deleted_at: datetime | None = None,
    library_id: uuid.UUID | None = None,
) -> uuid.UUID:
    with testing_session() as db:
        user = User(
            email=email,
            password_hash=hash_password(PASSWORD),
            full_name=email.split("@")[0].replace(".", " ").title(),
            phone="9876543210",
            is_active=is_active,
            deleted_at=deleted_at,
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
    email = "dashboard.admin@example.com"
    _create_user(
        testing_session,
        email=email,
        role_name=RoleName.SUPER_ADMIN,
    )
    return _login(client, email)


def _month_start(offset: int = 0) -> date:
    today = date.today()
    index = today.year * 12 + today.month - 1 + offset
    return date(index // 12, index % 12 + 1, 1)


def _seed_aggregate_fixture(testing_session) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    with testing_session() as db:
        owner_role = _role(db, RoleName.LIBRARY_OWNER)
        active_owner = User(
            email="active.dashboard.owner@example.com",
            password_hash=hash_password(PASSWORD),
            full_name="Active Dashboard Owner",
            is_active=True,
        )
        active_owner.role_links.append(
            UserRole(role=owner_role, assigned_at=now - timedelta(days=65))
        )
        suspended_owner = User(
            email="suspended.dashboard.owner@example.com",
            password_hash=hash_password(PASSWORD),
            full_name="Suspended Dashboard Owner",
            is_active=False,
        )
        suspended_owner.role_links.append(
            UserRole(role=owner_role, assigned_at=now - timedelta(days=5))
        )
        deleted_owner = User(
            email="deleted.dashboard.owner@example.com",
            password_hash=hash_password(PASSWORD),
            full_name="Deleted Dashboard Owner",
            is_active=True,
            deleted_at=now,
        )
        deleted_owner.role_links.append(UserRole(role=owner_role))
        db.add_all([active_owner, suspended_owner, deleted_owner])

        libraries = [
            Library(
                code="DASH-A",
                name="Dashboard Alpha",
                contact_email="dash-a@example.com",
                status=LibraryStatus.ACTIVE,
                city="Pune",
                state="Maharashtra",
                created_at=now - timedelta(days=70),
            ),
            Library(
                code="DASH-B",
                name="Dashboard Beta",
                contact_email="dash-b@example.com",
                status=LibraryStatus.ACTIVE,
                city="Jaipur",
                state="Rajasthan",
                created_at=now - timedelta(days=10),
            ),
            Library(
                code="DASH-P",
                name="Dashboard Pending",
                contact_email="dash-p@example.com",
                status=LibraryStatus.PENDING,
                created_at=now - timedelta(days=4),
            ),
            Library(
                code="DASH-S",
                name="Dashboard Suspended",
                contact_email="dash-s@example.com",
                status=LibraryStatus.SUSPENDED,
                created_at=now - timedelta(days=3),
            ),
            Library(
                code="DASH-X",
                name="Dashboard Deleted",
                contact_email="dash-x@example.com",
                status=LibraryStatus.ACTIVE,
                deleted_at=now,
            ),
        ]
        db.add_all(libraries)
        db.flush()

        db.add_all(
            [
                LibraryMembership(
                    library_id=libraries[0].id,
                    user_id=active_owner.id,
                    role=RoleName.LIBRARY_OWNER,
                    status=MembershipStatus.ACTIVE,
                    joined_at=now - timedelta(days=60),
                ),
                LibraryMembership(
                    library_id=libraries[1].id,
                    user_id=active_owner.id,
                    role=RoleName.LIBRARY_OWNER,
                    status=MembershipStatus.LEFT,
                    joined_at=now - timedelta(days=50),
                    left_at=now - timedelta(days=20),
                ),
            ]
        )

        db.add(
            AccountInvitation(
                library_id=libraries[2].id,
                email="pending.dashboard.owner@example.com",
                invitee_name="Pending Dashboard Owner",
                role=RoleName.LIBRARY_OWNER,
                token_hash="dashboard-pending-invitation-hash",
                status=InvitationStatus.PENDING,
                expires_at=now + timedelta(days=2),
            )
        )

        students = [
            Student(
                library_id=libraries[0].id,
                enrollment_number="DASH-001",
                first_name="Asha",
                last_name="One",
                email="asha.one@example.com",
                phone="9876500001",
                joined_on=_month_start(-2),
                monthly_fee=500,
                status=StudentStatus.ACTIVE,
            ),
            Student(
                library_id=libraries[0].id,
                enrollment_number="DASH-002",
                first_name="Bala",
                last_name="Two",
                email="bala.two@example.com",
                phone="9876500002",
                joined_on=_month_start(0),
                monthly_fee=500,
                status=StudentStatus.LEFT,
            ),
            Student(
                library_id=libraries[3].id,
                enrollment_number="DASH-003",
                first_name="Chitra",
                last_name="Three",
                email="chitra.three@example.com",
                phone="9876500003",
                joined_on=_month_start(0),
                monthly_fee=500,
                status=StudentStatus.INACTIVE,
            ),
            Student(
                library_id=libraries[0].id,
                enrollment_number="DASH-004",
                first_name="Deleted",
                last_name="Student",
                email="deleted.student@example.com",
                phone="9876500004",
                joined_on=_month_start(0),
                monthly_fee=500,
                status=StudentStatus.ACTIVE,
                deleted_at=now,
            ),
        ]
        db.add_all(students)

        floor = Floor(
            library_id=libraries[0].id,
            name="Ground Floor",
            code="GF",
        )
        shift = Shift(
            library_id=libraries[0].id,
            name="Morning",
            start_time=datetime.strptime("06:00", "%H:%M").time(),
            end_time=datetime.strptime("12:00", "%H:%M").time(),
        )
        db.add_all([floor, shift])
        db.flush()
        seats = [
            Seat(
                library_id=libraries[0].id,
                floor_id=floor.id,
                seat_number="D-01",
            ),
            Seat(
                library_id=libraries[0].id,
                floor_id=floor.id,
                seat_number="D-02",
            ),
        ]
        db.add_all(seats)
        db.flush()
        db.add(
            SeatAllocation(
                library_id=libraries[0].id,
                student_id=students[0].id,
                seat_id=seats[0].id,
                shift_id=shift.id,
                start_date=date.today() - timedelta(days=1),
                end_date=date.today() + timedelta(days=1),
                status=AllocationStatus.ACTIVE,
                shift_name="Morning",
                shift_start_time=shift.start_time,
                shift_end_time=shift.end_time,
            )
        )

        for index in range(8):
            db.add(
                AuditLog(
                    library_id=libraries[index % 4].id,
                    actor_user_id=active_owner.id,
                    action=(
                        "platform.library.suspended"
                        if index % 2
                        else "platform.owner.assigned"
                    ),
                    entity_type="library" if index % 2 else "owner",
                    entity_id=str(libraries[index % 4].id),
                    old_values={"token": "must-not-leak"},
                    new_values={"password": "must-not-leak"},
                    request_id=f"dashboard-request-{index}",
                    created_at=now - timedelta(minutes=index),
                )
            )
        db.add(
            AuditLog(
                library_id=libraries[0].id,
                actor_user_id=active_owner.id,
                action="seat.updated",
                entity_type="seat",
                entity_id=str(seats[0].id),
            )
        )
        db.commit()
        return {"libraries": libraries, "activeOwnerId": active_owner.id}


def test_dashboard_requires_super_admin(api, registered_owner, owner_headers) -> None:
    client, testing_session = api
    assert client.get(BASE_PATH).status_code == 401
    assert client.get(BASE_PATH, headers=owner_headers).status_code == 403

    library_id = uuid.UUID(registered_owner["user"]["libraryId"])
    for role_name in (RoleName.STAFF, RoleName.STUDENT):
        email = f"dashboard.{role_name.value}@example.com"
        _create_user(
            testing_session,
            email=email,
            role_name=role_name,
            library_id=library_id,
        )
        assert client.get(BASE_PATH, headers=_login(client, email)).status_code == 403


def test_empty_dashboard_returns_zero_metrics_and_continuous_trend(
    api,
    super_admin_headers,
) -> None:
    client, _testing_session = api
    response = client.get(BASE_PATH, headers=super_admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(value == 0 for value in data["totals"].values())
    assert [item["status"] for item in data["libraryStatus"]] == [
        "pending",
        "active",
        "suspended",
    ]
    assert all(item["count"] == 0 for item in data["libraryStatus"])
    assert len(data["trend"]) == 7
    assert data["topLibraries"] == []
    assert data["recentActivity"] == []


def test_dashboard_aggregates_distinct_source_records_and_safe_activity(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    _seed_aggregate_fixture(testing_session)
    response = client.get(
        BASE_PATH,
        params={
            "startMonth": _month_start(-2).strftime("%Y-%m"),
            "endMonth": _month_start(0).strftime("%Y-%m"),
        },
        headers=super_admin_headers,
    )
    assert response.status_code == 200, response.json()
    data = response.json()["data"]
    assert data["totals"] == {
        "totalLibraries": 4,
        "activeLibraries": 2,
        "pendingLibraries": 1,
        "suspendedLibraries": 1,
        "totalOwners": 2,
        "activeOwners": 1,
        "suspendedOwners": 1,
        "invitedOwners": 1,
        "totalStudents": 3,
        "totalSeats": 2,
        "averageOccupancy": 50,
    }
    assert len(data["trend"]) == 3
    assert [point["month"] for point in data["trend"]] == [
        _month_start(offset).strftime("%Y-%m") for offset in (-2, -1, 0)
    ]
    assert data["trend"][1]["students"] == 1
    assert data["trend"][2]["students"] == 3
    assert data["topLibraries"][0]["name"] == "Dashboard Alpha"
    assert data["topLibraries"][0]["occupancyRate"] == 50
    assert len(data["recentActivity"]) == 6
    assert all(item["action"].startswith("platform.") for item in data["recentActivity"])
    serialized_activity = str(data["recentActivity"])
    assert "must-not-leak" not in serialized_activity
    assert "oldValues" not in serialized_activity
    assert "requestId" not in serialized_activity


def test_dashboard_totals_reconcile_with_platform_lists(
    api,
    super_admin_headers,
) -> None:
    client, testing_session = api
    _seed_aggregate_fixture(testing_session)
    dashboard = client.get(BASE_PATH, headers=super_admin_headers).json()["data"]

    all_libraries = client.get(
        "/api/v1/platform/libraries",
        params={"page": 1, "pageSize": 100},
        headers=super_admin_headers,
    ).json()
    assert dashboard["totals"]["totalLibraries"] == all_libraries["meta"]["totalItems"]
    for status in ("active", "pending", "suspended"):
        listing = client.get(
            "/api/v1/platform/libraries",
            params={"status": status, "page": 1, "pageSize": 100},
            headers=super_admin_headers,
        ).json()
        assert dashboard["totals"][f"{status}Libraries"] == listing["meta"]["totalItems"]

    owners = client.get(
        "/api/v1/platform/owners",
        params={"page": 1, "pageSize": 100},
        headers=super_admin_headers,
    ).json()
    distinct_people = owners["summary"]["active"] + owners["summary"]["suspended"]
    assert dashboard["totals"]["totalOwners"] == distinct_people


@pytest.mark.parametrize(
    ("params", "code"),
    [
        ({"startMonth": "2026-01"}, "PLATFORM_DASHBOARD_MONTH_RANGE_REQUIRED"),
        (
            {"startMonth": "2026-03", "endMonth": "2026-02"},
            "PLATFORM_DASHBOARD_MONTH_RANGE_INVALID",
        ),
        (
            {"startMonth": "2020-01", "endMonth": "2026-01"},
            "PLATFORM_DASHBOARD_RANGE_TOO_LARGE",
        ),
        (
            {
                "startMonth": _month_start(0).strftime("%Y-%m"),
                "endMonth": _month_start(1).strftime("%Y-%m"),
            },
            "PLATFORM_DASHBOARD_FUTURE_RANGE",
        ),
    ],
)
def test_dashboard_rejects_invalid_date_ranges(
    api,
    super_admin_headers,
    params,
    code,
) -> None:
    client, _testing_session = api
    response = client.get(BASE_PATH, params=params, headers=super_admin_headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == code


def test_dashboard_uses_bounded_queries_and_response_size(
    api,
    super_admin_headers,
) -> None:
    _client, testing_session = api
    _seed_aggregate_fixture(testing_session)
    engine = testing_session.kw["bind"]
    query_count = 0

    def count_query(*_args) -> None:
        nonlocal query_count
        query_count += 1

    event.listen(engine, "before_cursor_execute", count_query)
    started = clock.perf_counter()
    try:
        with testing_session() as db:
            dashboard = get_dashboard(db)
    finally:
        event.remove(engine, "before_cursor_execute", count_query)
    elapsed = clock.perf_counter() - started
    response_bytes = len(dashboard.model_dump_json(by_alias=True))
    print(
        {
            "queries": query_count,
            "seconds": round(elapsed, 4),
            "responseBytes": response_bytes,
        }
    )

    assert query_count <= 12
    assert elapsed < 1
    assert response_bytes < 100_000
