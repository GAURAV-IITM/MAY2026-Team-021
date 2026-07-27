# Phase 3: Seat Availability And Allocation

Status: Implemented  
Target: 28-31 July 2026

## Goal

Provide one tenant-scoped source of truth for seat availability and the full
allocation lifecycle. Library owners and staff can inspect a shift/date window,
create one or more non-overlapping shift allocations atomically, view history,
and complete or cancel active records.

## Architecture

```text
Vue page -> Pinia seat store -> seatService -> FastAPI allocation router
-> allocation service -> tenant-scoped repositories -> SQLAlchemy models
```

The backend is authoritative. The frontend only groups records by floor,
formats labels, and performs advisory form validation. It never falls back to
allocation mock data after an API error.

## Availability Statuses

Physical seat state is evaluated before allocation state:

1. `maintenance`: the physical seat is under maintenance.
2. `physically_blocked`: an administrator blocked the physical seat.
3. `allotted`: an active allocation uses the exact selected shift and is not
   exclusively in the future.
4. `reserved`: exact-shift blockers all start after today.
5. `blocked`: an allocation for another shift overlaps the selected shift's
   time and the selected date range.
6. `available`: no physical or allocation blocker exists.

Occupancy is not stored as a physical seat status.

## Overlap Rules

Allocation date ranges are inclusive:

```text
newStart <= existingEnd AND newEnd >= existingStart
```

Therefore 1-10 August conflicts with 10-20 August, while a new allocation
starting 11 August is consecutive and allowed.

Shift ranges use half-open time intervals. A shift ending when another starts
does not overlap. Overnight shifts are split at midnight:

```text
22:00-02:00 -> [22:00, 24:00) + [00:00, 02:00)
```

Thus `22:00-02:00` overlaps `01:00-06:00`, while it does not overlap
`06:00-12:00`. Different shift IDs still conflict when their times overlap.

## Validation And Atomicity

The tenant is always resolved from the authenticated active membership. The
request never supplies `libraryId`.

Creation verifies:

- active, non-deleted student in the current library;
- active seat and floor in the current library;
- physically available seat;
- active, non-deleted shifts in the current library;
- unique, mutually non-overlapping selected shifts;
- valid dates after the student's joining date;
- no active seat conflict;
- no active student conflict on another seat.

One selected shift creates one allocation row. Multiple selected shifts share a
transfer group ID and are flushed and committed together. Any validation,
conflict, audit, or database failure rolls back the entire operation.

## Locking

Creation uses this deterministic lock order:

1. physical seat row;
2. student row;
3. selected shift rows ordered by UUID;
4. matching seat allocation rows;
5. matching student allocation rows.

Conflict checks run after locks are acquired. PostgreSQL serializes concurrent
requests targeting the same seat or student, so one transaction succeeds and
the later transaction sees the committed conflict. SQLite is used for the fast
suite but is not considered evidence for row-lock behavior.

## Lifecycle And History

Allowed transitions:

```text
Active -> Completed
Active -> Cancelled
Completed -> no transition
Cancelled -> no transition
```

Closing records the outcome, effective end date where applicable, reason,
actor, and timestamp. Records are never deleted. Shift name/times and seat/floor
names are snapshotted so history remains meaningful after edits.

Successful create, complete, and cancel operations append an audit record in
the same transaction. Failed operations do not create success audit records.

## API And Frontend Mapping

| API | Frontend |
| --- | --- |
| `GET /api/v1/seat-allocations/availability` | Seat Map filters, cards, blocker details, summary |
| `GET /api/v1/seat-allocations` | Allocation History list, search, filters, pagination |
| `POST /api/v1/seat-allocations` | Seat Allocation dialog |
| `PATCH /api/v1/seat-allocations/{id}/status` | Complete/cancel dialog |

The Seat Map defaults to today and the first enabled shift. A monotonically
increasing request token prevents a stale availability response from replacing
a newer response. Conflict errors keep the allocation form open and show the
server message and request ID.

## Stable Error Codes

- `ALLOCATION_SHIFT_REQUIRED`
- `ALLOCATION_SHIFT_INVALID`
- `ALLOCATION_SHIFTS_OVERLAP`
- `ALLOCATION_DATE_RANGE_INVALID`
- `ALLOCATION_END_DATE_IN_PAST`
- `ALLOCATION_BEFORE_JOINING_DATE`
- `STUDENT_NOT_FOUND`
- `STUDENT_NOT_ACTIVE`
- `SEAT_NOT_FOUND`
- `SEAT_INACTIVE`
- `SEAT_NOT_OPERATIONALLY_AVAILABLE`
- `SEAT_ALLOCATION_CONFLICT`
- `STUDENT_ALLOCATION_CONFLICT`
- `SEAT_ALLOCATION_NOT_FOUND`
- `ALLOCATION_ALREADY_CLOSED`
- `ALLOCATION_EFFECTIVE_END_INVALID`

All errors use the shared structured response and include a request ID.

## Verification

Backend:

```bash
cd backend
venv/bin/python scripts/export_openapi.py
venv/bin/python scripts/export_openapi.py --check
venv/bin/pytest
```

PostgreSQL row-lock evidence:

```bash
cd backend
TEST_POSTGRES_DATABASE_URL='postgresql://user:pass@localhost/test_db' \
  venv/bin/pytest -q tests/test_seat_allocation_postgres.py
```

The PostgreSQL user must be allowed to create and drop a temporary schema.

Frontend:

```bash
cd frontend
npm test
npm run lint
npm run build
```

Production mock scan:

```bash
rg -n "mock|Mock|FEATURE_NOT_AVAILABLE|Phase 3" \
  frontend/src/pages/admin/SeatAvailability.vue \
  frontend/src/components/seat frontend/src/stores/seatStore.js \
  frontend/src/services/seatService.js
```

## Out Of Scope

Seat-transfer APIs, automatic seat-request approval transfers, student
self-service allocation APIs, scheduled completion jobs, and an audit-log
frontend are deferred.
