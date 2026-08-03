# TA Progress Review Guide

**Meeting date:** 3 August 2026  
**Project:** Community Services Platform  
**System:** Library Management System for Study Libraries  
**Product:** Smart Library App  
**Current iteration:** Milestone 3 API Sprint 1 / Project Sprint 7

## One-line status

The frontend foundation from Milestone 2 is now backed by 74 documented FastAPI
operations covering authentication, tenant-scoped library management, seat allocation,
payments, announcements, seat requests, reports, and settings. The current local test
run has 133 passing tests.

## Recommended 8-minute agenda

| Time | Topic | What to show |
|---|---|---|
| 0:00-0:45 | Context | Milestone 1 need -> Milestone 2 design -> Milestone 3 APIs |
| 0:45-1:30 | Architecture | Vue page -> Pinia -> Axios -> FastAPI -> service -> repository -> database |
| 1:30-4:45 | API demo | Swagger groups, registration/authentication, one seat rule, one payment flow |
| 4:45-6:15 | Testing | Targeted pytest run, failed-then-fixed case, OpenAPI drift check |
| 6:15-7:15 | Current limitations | Remaining Super Admin integration, production database evidence, UAT |
| 7:15-8:00 | Next sprint | Priorities, ownership, exit criteria, and TA questions |

## Opening script

> Good afternoon. Our application manages study libraries for three roles: Library
> Owner/Admin, Student, and Super Admin. Milestone 1 identified manual seat conflicts,
> fragmented student records, fee tracking, and missed communication as the main user
> problems. Milestone 2 established the Vue and layered service architecture. In the
> current API sprint, we implemented the real FastAPI contracts behind the main owner
> and student workflows. We will briefly show the API contract, a few important business
> rules, our test evidence, and our plan for the next sprint.

## Current progress

| API group | Operations | Current capability |
|---|---:|---|
| Authentication | 13 | Registration, login, browser sessions, rotation, logout, profile, password, invitations |
| Students | 9 | CRUD, status, invitation, tenant isolation, seat-aware registration/editing |
| Floors and seats | 12 | Physical layout CRUD, status, maintenance/blocked state, bulk actions |
| Shifts | 6 | CRUD, activation, overnight timings, multi-shift overlap validation |
| Seat allocations | 5 | Availability, create, list/history, close, student view |
| Seat requests | 5 | Student submit/cancel and owner list/review |
| Payments and receipts | 9 | Monthly records, partial payments, receipts, downloads, reminders, student view |
| Announcements | 8 | Owner lifecycle and student feed/read state |
| Reports | 3 | Filter metadata, owner reports, dashboard metrics |
| Settings and system | 4 | Library settings, API discovery, health |
| **Total** | **74** | All operations documented in OpenAPI 3.1 |

## Architecture explanation

```text
Vue page/component
  -> Pinia store
  -> Axios service
  -> FastAPI route + role/tenant dependency
  -> Pydantic request/response schema
  -> application service + transaction boundary
  -> tenant-scoped SQLAlchemy repository
  -> database models and audit/history records
```

Key points to say:

- The authenticated membership determines `libraryId`; tenant-owned routes do not trust
  a library ID supplied by the client.
- Pages still follow the page -> store -> service pattern, so mock services can be
  replaced module by module without rewriting the UI.
- OpenAPI YAML is generated from FastAPI and checked for semantic drift in tests and CI.
- Expected errors use one code/message/details envelope and include an `X-Request-ID`.
- Historical allocations, payments, receipts, and audit records are retained rather
  than overwritten.

## Before the meeting

Run these checks at least 15 minutes before joining:

```bash
cd backend
source venv/bin/activate
python scripts/export_openapi.py --check
pytest -q
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm run lint
npm run dev
```

Open these tabs in advance:

1. Backend Swagger UI: `http://127.0.0.1:8000/docs`
2. Frontend URL printed by Vite
3. `docs/api/openapi.yaml`
4. `submission/milestone-3/MAY2026-Team-021-Milestone-3-Report.pdf`
5. A terminal already positioned inside `backend/`

Use a disposable local database for the demonstration. Avoid pulling branches,
installing dependencies, or changing migrations immediately before the call.

## Live demo sequence

### 1. API contract and health

1. Open Swagger UI and briefly show the 12 API groups.
2. Execute `GET /health` and show the `200` response.
3. Open one operation and point out its description, request schema, success response,
   structured errors, and user-story mapping in `openapi.yaml`.

Say:

> The Swagger document contains the same 74 operations exposed by FastAPI. A drift test
> fails if code and the checked-in YAML differ.

### 2. Registration and validation

Use `POST /api/v1/auth/register-library` with a fresh email:

```json
{
  "libraryName": "TA Demo Study Library",
  "ownerName": "Demo Owner",
  "email": "ta.demo.20260803@example.com",
  "password": "SecurePass123",
  "phone": "9876543210",
  "address": "1 Reading Lane",
  "seatCount": 12
}
```

Explain that one transaction creates the library, owner, membership, settings, first
floor, default shifts, requested seats, and authenticated session.

Optional negative case: set `seatCount` to `0` and show `422 VALIDATION_ERROR` with a
request ID.

### 3. One important seat rule

Show the relevant Swagger operations or the Seat Map UI:

- `POST /api/v1/shifts/validate-selection`
- `POST /api/v1/seat-allocations`

Explain:

> Physical seat state and calculated availability are different. Maintenance and
> blocked are physical states. Allotted, reserved, and blocked by another shift are
> calculated for the selected shift and date range. For example, 22:00-02:00 overlaps
> 01:00-06:00, and selecting both is rejected. The same seat can still be used by
> different students in non-overlapping shifts or date ranges.

If time permits, show the allocation conflict response with HTTP `409` and code
`SEAT_ALLOCATION_CONFLICT`.

### 4. One payment flow

Show the Payment Management UI or these operations:

- `POST /api/v1/payments/monthly-generation`
- `POST /api/v1/payments/{fee_record_id}/transactions`
- `GET /api/v1/payments/receipts/{receipt_id}/download`

Explain:

> Monthly fee records are separate from payment transactions. This supports partial
> payments, server-calculated balances, multiple transactions, permanent receipts, and
> safe monthly regeneration.

### 5. Testing evidence

Run a small, readable selection instead of the whole suite during the meeting:

```bash
pytest -vv \
  tests/test_auth_api.py::test_registration_bootstraps_library_and_me \
  tests/test_core_library_api.py::test_floor_seat_shift_and_settings_workflows \
  tests/test_seat_allocation_api.py::test_conflicts_atomicity_status_precedence_and_consecutive_dates \
  tests/test_payment_api.py::test_partial_and_full_payments_recalculate_server_totals
```

Then show the saved full result:

```text
133 passed in the current local suite
```

Seven additional database-specific concurrency/performance checks are conditional and
are not executed by the ordinary local SQLite run. Do not claim that all 140 tests ran.

Show the OpenAPI check:

```bash
python scripts/export_openapi.py --check
pytest -q tests/test_openapi_contract.py
```

## Failed test to discuss

Use the expired backing-session case because it demonstrates useful testing rather than
a cosmetic issue:

- **Endpoint:** `GET /api/v1/auth/me`
- **Expected:** `401` when the database session has expired.
- **Initial actual:** `200` because JWT signature/expiry was checked but the backing
  session expiry was not checked on every protected request.
- **Fix:** Validate active server-side session state for protected requests and strengthen
  refresh/logout revocation.
- **Retest:** `401`, with a permanent regression test.

Say:

> This test showed why JWT verification alone was insufficient. We now validate both the
> signed token and its revocable server-side session.

## Next sprint plan

1. Replace remaining Super Admin mocks with tenant- and role-tested APIs.
2. Run concurrency and report-performance tests using a disposable production-like
   database and record query plans and timing evidence.
3. Expand audit coverage for student, floor, shift, and settings mutations.
4. Complete scheduled/background behavior required by final scope for fees, reminders,
   and announcement lifecycle.
5. Run owner and student end-to-end UAT, accessibility regression, and security review.
6. Prepare deployment configuration, final migration rehearsal, Milestone 4 evidence,
   and demonstration.

Exit criteria:

- No silent fallback to mock data in modules declared integrated.
- Role and tenant tests pass for every new endpoint.
- OpenAPI, backend code, frontend services, and tests remain synchronized.
- UAT feedback and resolved actions are documented.

## Honest current limitations

- Super Admin frontend areas still include mock-backed workflows.
- Local SQLite tests do not prove production database lock behavior or query performance.
- Final external owner/student demonstration feedback still needs to be captured for the
  milestone report; earlier Milestone 1 interviews occurred before implementation.
- Deployment secrets, secure cookie behavior, CORS origins, migration execution, and
  production monitoring still require environment-specific verification.

## Likely TA questions

### How do you prevent one library from reading another library's data?

The access token identifies the user, and the active membership dependency derives the
current library. Repositories always filter library-owned records by that library. A
cross-library resource is returned as `404` so its existence is not disclosed.

### Why keep a server-side session if access tokens are JWTs?

The session enables logout, refresh-token rotation, reuse detection, and immediate
revocation. A validly signed token is rejected when its backing session is revoked or
expired.

### Why are overlapping shift definitions allowed?

Owners can create useful custom shifts such as Office Hours alongside Morning and
Afternoon. Definitions may overlap, but assigning one student to multiple overlapping
shifts is rejected. Seat availability also treats an allocation in an overlapping shift
as blocked for that time window.

### How do you prevent double booking?

The service checks seat, shift-time, student, and inclusive date-range overlaps inside a
transaction. Conflicts return `409`; failed multi-shift operations roll back atomically.

### Why are payments split into fee records and transactions?

A fee record is the monthly amount due. Transactions are append-only payments against
that amount. This supports instalments, accurate balances, immutable receipts, and
historical reporting.

### Is the Swagger YAML manually maintained?

No. It is generated from FastAPI, validated as OpenAPI 3.1, and compared semantically
with the checked-in YAML. CI fails on contract drift.

### What remains mocked?

The core owner/student vertical slices listed above use real APIs. Remaining Super Admin
workflows are the main mock-backed area planned for the next sprint.

## Questions to ask the TA

1. Does post-demonstration feedback need to come from the original external interviewees,
   or is a new representative owner/student acceptable?
2. For final concurrency evidence, is a documented disposable database run sufficient,
   or is CI execution expected?
3. Is the custom `x-user-stories` OpenAPI extension acceptable for user-story mapping?
4. Should Milestone 3 API Sprint 1 be labelled Project Sprint 7 for continuity with the
   six sprints shown in Milestone 2?
5. Does the final submission require deployment evidence, or only executable local setup
   and tests?

## Suggested team handoff

Adjust this to actual ownership before the meeting:

| Person | Suggested section |
|---|---|
| Shubham | Opening, milestone continuity, integrated demo |
| Gaurav | Architecture, authentication, tenant isolation |
| Piyush | Payments, receipts, reminders |
| Mandeep | Student portal and seat-change request APIs |
| Hitarth | Test evidence, failed-test learning, next sprint |

Each person should be ready to answer one implementation question about their section.

## Fallback if the live demo fails

1. Spend no more than two minutes diagnosing live.
2. Show `openapi.yaml` and the Swagger operation schemas.
3. Show the API test cases and pytest snapshots in the Milestone 3 PDF.
4. Show `submission/milestone-3/pytest-results.txt` and run one targeted test.
5. Explain the likely local environment issue and continue with architecture and plan.

## Closing script

> To summarize, we have moved the main owner and student workflows from frontend mocks
> to 74 documented, tenant-scoped API operations. Today's backend run has 133 passing
> tests, including validation, security, history, conflict, payment, and contract cases.
> Our next sprint will complete the remaining platform scope, production-like database
> evidence, UAT, deployment hardening, and Milestone 4 preparation. We would appreciate
> feedback on our test evidence and next-sprint priorities.
