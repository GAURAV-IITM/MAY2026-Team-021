# Milestone 3 and 4 Implementation Plan

Project: Smart Library App  
Team: MAY2026-Team-021  
Plan created: 24 July 2026  
Milestone 3 due: 2 August 2026  
Milestone 4 due: 12 August 2026

## 1. Purpose

This document is the shared execution plan for replacing the frontend mock
services with a tested FastAPI and PostgreSQL backend. It defines what the team
will build, who owns each area, how work is reviewed, and what evidence must be
kept for the course submissions.

Every team member should read this document before starting Milestone 3 work.
Any scope, API, database, or ownership change must be recorded here, in the
linked GitHub issue, or in an Architecture Decision Record (ADR).

## 2. Course Requirements Covered

The two provided course documents use slightly different milestone labels:

- The Project Guide describes Milestones 3 and 4 as API Sprint 1 and Sprint 2.
- The May 2026 project document also asks the August 2 report to carry forward
  design, scheduling, frontend, class diagram, and database evidence.

To avoid submission risk, Milestone 3 will contain both:

1. Consolidated design and frontend evidence from the earlier milestone.
2. Sprint 1 API contracts, backend code, pytest tests, integration evidence,
   and primary-user feedback.

Both milestones must include:

- Swagger-compatible API YAML.
- Implemented backend code matching the API contract and user stories.
- Positive and negative API test cases.
- Input, expected output, actual output, and pass/fail result for each
  showcased test.
- Pytest source code and readable test-result evidence.
- Frontend integration evidence.
- User feedback and the resulting action plan.
- Traceable GitHub issues, pull requests, reviews, and bug records.

## 3. Current Project Baseline

### Completed

- Vue 3 frontend for library owners, students, and super admins.
- Pinia stores and mock services for all major features.
- Responsive pages, routing, role guards, and shared UI components.
- PostgreSQL database design with 24 SQLAlchemy tables.
- Alembic configuration and initial migration.
- Models for identity, libraries, students, seats, shifts, allocations,
  payments, receipts, announcements, settings, and audit logs.
- Backend package structure for API, schemas, repositories, services, and
  tasks.
- PostgreSQL connectivity through Psycopg 3.

### Still Required

- Real authentication, authorization, and tenant dependencies.
- Pydantic request and response schemas.
- Repository queries and transactional service implementations.
- FastAPI endpoint implementations.
- Standard error responses and pagination.
- API-level pytest coverage.
- Checked-in OpenAPI YAML and user-story mapping.
- Axios authentication, API base URL, proxy, and error interceptors.
- Replacement of mock service operations with HTTP requests.
- End-to-end integration and user feedback.

## 4. Delivery Principles

1. API contract first: update and review `docs/api/openapi.yaml` before coding
   an endpoint.
2. Vertical slices: complete contract, backend, tests, frontend integration,
   and documentation for a workflow before starting another.
3. Backend authority: authorization, tenancy, validation, conflicts, and
   business rules are enforced by FastAPI even when frontend validation exists.
4. No direct mock imports from pages: frontend pages continue using
   Page -> Store -> Service -> API.
5. One source of business truth: analytics and availability are derived from
   database records instead of duplicated counters.
6. Historical data is preserved: use status transitions and soft deletion
   where the database design requires it.
7. Review before merge: every user story uses a feature branch, linked issue,
   pull request, assigned reviewer, and resolved review comments.
8. Evidence while working: test output, screenshots, feedback, and decisions
   are collected during the sprint, not reconstructed on submission day.

## 5. Proposed Team Ownership

These assignments are proposed from the current module boundaries. Confirm them
in the Milestone 3 kickoff meeting and record any change in the meeting minutes.

| Team member | Primary ownership | Secondary responsibility | Reviewer |
|---|---|---|---|
| Shubham Nagar | Backend foundation, authentication, tenancy, integration coordination | Dashboard aggregation and release checks | Gaurav |
| Gaurav Ghodge | Student management and student portal APIs | Student account invitation and seat-request flows | Mandeep |
| Hitarth Mehta | Floors, seats, shifts, availability, and allocations | Allocation conflict and transfer testing | Shubham |
| Piyush Jha | Monthly fees, payments, receipts, reminders, and reports | API test matrix coordination | Hitarth |
| Mandeep | Announcements, library settings, and super-admin APIs | Error-response consistency and documentation checks | Piyush |

Reviewers must not approve their own work. Shubham coordinates integration but
does not silently rewrite another member's feature; changes should go through
the feature owner or a documented handover.

## 6. Target Backend Architecture

```text
HTTP request
    |
FastAPI route + authentication/tenant dependencies
    |
Pydantic request validation
    |
Application service and transaction boundary
    |
Tenant-scoped repository
    |
SQLAlchemy models
    |
PostgreSQL
```

Responsibilities:

- `api/v1/endpoints`: HTTP parameters, status codes, and response mapping.
- `schemas`: validated API input/output contracts and camelCase aliases.
- `services`: business rules, transaction boundaries, and audit calls.
- `repositories`: tenant-scoped SQLAlchemy queries only.
- `models`: persistence definitions and database constraints.
- `tasks`: scheduled fee generation, announcements, and reminders.
- `core`: configuration, security, error handling, and shared dependencies.

Endpoints must not query mock data or contain large SQL/business-rule blocks.

## 7. API Conventions to Freeze on 25 July

### URLs and JSON

- Base path: `/api/v1`.
- Resource names: lowercase plural nouns with hyphens where needed.
- Python and database fields: `snake_case`.
- API JSON fields: `camelCase` to match the Vue frontend.
- Dates: `YYYY-MM-DD`.
- Date-times: ISO 8601 with timezone.
- IDs: UUID strings.

### Success response

```json
{
  "message": "Student created successfully.",
  "data": {},
  "meta": {}
}
```

`meta` is optional and contains pagination or filter information.

### Error response

```json
{
  "error": {
    "code": "SEAT_ALLOCATION_CONFLICT",
    "message": "Seat A-01 is occupied during the requested period.",
    "details": {}
  },
  "requestId": "request-correlation-id"
}
```

### Status codes

| Situation | Status |
|---|---:|
| Successful read/update | 200 |
| Successful create | 201 |
| Successful operation with no body | 204 |
| Invalid input/business validation | 422 |
| Missing or invalid login | 401 |
| Authenticated but not permitted | 403 |
| Resource not found in current tenant | 404 |
| Duplicate or allocation conflict | 409 |

### Authentication

- Short-lived JWT access token.
- Rotating refresh session stored in `user_sessions`.
- Passwords hashed with a supported password-hashing library.
- `get_current_user`, `get_current_library`, and role dependencies are required
  for protected routes.
- Student self-service endpoints derive the student from the authenticated
  user. They never accept another student's ID from the browser.
- Library IDs sent by clients are not trusted as authorization.

### Pagination

List endpoints use:

```text
page=1&pageSize=20&search=&sortBy=createdAt&sortOrder=desc
```

The response metadata includes `page`, `pageSize`, `totalItems`, and
`totalPages`.

## 8. API Workstreams

The exact request and response schemas will be written in
`docs/api/openapi.yaml`. This table freezes the intended route groups.

| Workstream | Main routes | Sprint | Owner |
|---|---|---|---|
| Authentication | `POST /auth/register-library`, `/login`, `/refresh`, `/logout`, `/forgot-password`, `/reset-password`; `GET /auth/me`; `PATCH /auth/me`, `/auth/password` | M3 | Shubham |
| Students | `GET/POST /students`; `GET/PATCH/DELETE /students/{id}`; `PATCH /students/{id}/status` | M3 | Gaurav |
| Floors and seats | `GET/POST /floors`; `GET/POST /seats`; `GET/PATCH/DELETE /seats/{id}`; bulk status/delete routes | M3 | Hitarth |
| Shifts | `GET/POST /shifts`; `PATCH/DELETE /shifts/{id}`; status route | M3 | Hitarth |
| Availability and allocations | `GET /seats/availability`; `GET/POST /seat-allocations`; close/cancel/history routes | M3 | Hitarth |
| Monthly fees and payments | fee-record list/generation; payment recording and status routes | M3 | Piyush |
| Announcements and settings | announcement CRUD/publish/archive; `GET/PATCH /settings/library` | M3 | Mandeep |
| Student portal | `/student/me/dashboard`, `/seat`, `/fees`, `/receipts`, `/announcements`, `/profile` | M4 | Gaurav |
| Seat requests | student create/cancel and owner list/approve/reject routes | M4 | Gaurav + Hitarth |
| Receipts and reminders | receipt detail/download data; WhatsApp/SMS/email reminder recording | M4 | Piyush |
| Owner dashboard and reports | dashboard summary, revenue, occupancy, student, pending-fee, and export routes | M4 | Piyush + Shubham |
| Super admin | platform dashboard, libraries, owners, analytics, and settings | M4 | Mandeep |
| Audit history | authorized audit-list endpoints and audit writes for mutations | M4 | Shubham + feature owners |

No real payment gateway is required. Payment APIs record manual cash, UPI,
bank-transfer, or card entries.

## 9. Critical Business Rules

These rules require explicit tests and cannot be left only in Vue code.

### Tenant and roles

- Every library query is scoped by the authenticated membership.
- Owners cannot access another library's data.
- Students can access only their own portal records.
- Super-admin-only actions reject owner and student accounts.

### Students

- Only active students can receive new allocations.
- Enrollment number and email uniqueness are enforced per library.
- Creating a portal login uses an expiring setup invitation; plain-text
  passwords are never stored or logged.
- Student deletion is historical/soft deletion where applicable.

### Seats, shifts, and allocations

- Seat number is unique within a library.
- Maintenance, blocked, inactive, or deleted seats cannot be allocated.
- Inactive/deleted shifts cannot be used for new allocations.
- Shift comparison supports overnight windows such as `22:00-02:00`.
- Adjacent shifts such as `06:00-12:00` and `12:00-18:00` do not overlap.
- Date ranges are inclusive; the end date cannot precede the start date.
- The same seat cannot have active allocations whose dates and shift times
  both overlap.
- The same student cannot hold overlapping seat allocations.
- Transfers close the old allocation and create a linked new record in one
  transaction.
- Seat-map `Available`, `Allotted`, `Reserved`, and blocked-by-another-shift
  values are calculated for the selected shift and dates.
- Conflict checks must be transaction-safe to avoid two simultaneous bookings.

### Payments

- Monthly generation is idempotent for library + student + billing month.
- Only eligible active students receive new monthly fee records.
- Partial payment is supported through multiple payment transactions.
- Completed transaction totals determine fee status.
- Receipt number is unique per library and receipt snapshots are historical.
- Reminder attempts record channel, recipient, sender, status, and timestamp.

### Announcements and reports

- Announcement lifecycle supports draft, scheduled, published, expired, and
  archived states.
- Students see only published, non-expired announcements for their audience.
- Read status is student-specific.
- Reports use tenant-scoped source records and date filters.

## 10. Milestone 3: Sprint 1

### Sprint goal

Deliver working, tested vertical slices for authentication and the main owner
operations, integrate them with the frontend, and collect primary-user
feedback.

### Scope

1. Freeze API conventions and create the first OpenAPI YAML.
2. Implement shared authentication, tenancy, error, and pagination support.
3. Implement student CRUD and account-invitation foundation.
4. Implement floor, seat, shift, availability, and allocation workflows.
5. Implement monthly fee generation and payment recording.
6. Implement announcement CRUD and library settings.
7. Integrate the corresponding owner frontend services.
8. Add pytest cases and prepare the required test matrix.
9. Demonstrate the integrated owner workflow to at least one primary user.
10. Record feedback and convert accepted feedback into Milestone 4 issues.
11. Update the class/component diagrams and ERD where implementation decisions
    changed the Milestone 2 design.

### Day-by-day schedule

| Date | Team outcome |
|---|---|
| Fri 24 Jul | Kickoff, confirm ownership, create issues, identify user stories, and agree API conventions |
| Sat 25 Jul | Review first `openapi.yaml`; implement common schemas, errors, auth dependencies, and test fixtures |
| Sun 26 Jul | Authentication and tenant foundation; domain owners begin repository/service work |
| Mon 27 Jul | Student, seat, shift, payment, announcement, and settings endpoints under implementation |
| Tue 28 Jul | Complete first endpoint pass and positive/negative pytest cases |
| Wed 29 Jul | Frontend service integration for completed vertical slices |
| Thu 30 Jul | Shared integration session; fix response-contract and tenant issues |
| Fri 31 Jul | Regression tests, migration-from-clean-DB check, and code review closure |
| Sat 1 Aug | Primary-user demo, feedback log, screenshots, test matrix, and report assembly |
| Sun 2 Aug | Final validation, tag `milestone-3`, and submit |

### Milestone 3 exit criteria

- All M3 routes are documented in valid Swagger YAML.
- YAML descriptions map endpoints to user stories.
- Backend code matches route names, schemas, statuses, and errors in YAML.
- Critical M3 workflows have positive and negative pytest coverage.
- Owner frontend uses real APIs for the delivered workflows.
- At least one cross-tenant test exists for each tenant-owned route group.
- At least one expected-vs-actual defect is documented with its fix.
- User feedback is recorded and converted into an M4 action plan.
- All M3 PRs are reviewed and merged; no unresolved requested changes remain.

### Milestone 3 submission package

```text
Milestone-3/
  Milestone-3-Report.pdf
  API/
    openapi.yaml
    test-case-matrix.pdf
    pytest-results/
  Code/
    backend/
    frontend/
  Evidence/
    frontend-screenshots/
    swagger-screenshots/
    user-feedback/
    scrum-minutes/
    gantt-and-kanban/
```

The PDF should include the class diagram, revised ERD, component description,
schedule, meeting minutes, Gantt/Kanban screenshots, frontend screenshots, API
summary, test evidence, and user feedback.

## 11. Milestone 4: Sprint 2

### Sprint goal

Apply validated user feedback, complete the remaining role-specific APIs,
finish frontend integration, and deliver a stable regression-tested system.

### Scope

1. Triage M3 feedback into accepted, deferred, and rejected decisions.
2. Implement student portal and seat-change request workflows.
3. Complete receipts, reminders, payment history, and reports.
4. Implement owner dashboard aggregation.
5. Implement super-admin library, owner, analytics, and settings APIs.
6. Add audit logging to administrative mutations.
7. Replace remaining production-path mock calls with API requests.
8. Complete integration and role/tenant regression tests.
9. Update OpenAPI YAML, user-story mapping, and report evidence.
10. Run a second primary-user review and close accepted feedback.

### Day-by-day schedule

| Date | Team outcome |
|---|---|
| Mon 3 Aug | M3 retrospective, feedback triage, M4 issue assignment, and contract update |
| Tue 4 Aug | Student portal, seat requests, receipts/reminders, reports, and platform APIs begin |
| Wed 5 Aug | Complete repositories/services and initial route tests |
| Thu 6 Aug | Frontend integration for student and remaining owner workflows |
| Fri 7 Aug | Super-admin integration and audit logging |
| Sat 8 Aug | Shared integration session across all three roles |
| Sun 9 Aug | Full API regression, permission matrix, and tenant-isolation testing |
| Mon 10 Aug | Bug fixing, user feedback demonstration, and accessibility/responsive smoke check |
| Tue 11 Aug | Freeze code; update YAML, test matrix, screenshots, report, and README files |
| Wed 12 Aug | Final clean setup test, tag `milestone-4`, and submit |

### Milestone 4 exit criteria

- Accepted M3 feedback is implemented or explicitly deferred with reason.
- All core frontend modules use backend APIs in normal application mode.
- OpenAPI YAML includes all implemented routes, errors, and user-story mapping.
- Authentication, permissions, tenancy, allocation conflicts, monthly payment
  generation, and student data isolation have automated tests.
- Clean database migration and clean frontend/backend startup are documented.
- Owner, student, and super-admin smoke flows pass.
- Test matrix contains actual results from the final revision.
- All M4 PRs are reviewed and merged.

### Milestone 4 submission package

```text
Milestone-4/
  Milestone-4-Report.pdf
  API/
    openapi.yaml
    test-case-matrix.pdf
    pytest-results/
  Code/
    backend/
    frontend/
  Evidence/
    feedback-before-after/
    integrated-workflow-screenshots/
    swagger-screenshots/
    scrum-minutes/
    issue-and-pr-traceability/
```

## 12. Frontend Integration Plan

1. Add `VITE_API_BASE_URL` with a development default of `/api/v1`.
2. Add a Vite development proxy to the FastAPI server.
3. Configure Axios timeouts, credentials, auth headers, and request IDs.
4. Add a single response interceptor that:
   - refreshes an expired session once;
   - redirects 401 responses to login;
   - redirects forbidden role access to 403;
   - passes structured field errors to forms;
   - shows a safe generic message for unexpected 500 responses.
5. Keep existing Pinia store method names where practical.
6. Replace mock behavior inside one feature service at a time.
7. Add a temporary explicit mock/API environment flag only if parallel work
   requires it. API mode must be the submission default.
8. Remove fake JWT generation and do not log tokens or passwords.

## 13. Testing Strategy

### Test levels

| Level | Purpose | Tool |
|---|---|---|
| Model/utility unit | Constraints and pure business functions | pytest |
| Service unit | Validation, overlap, status, and amount rules | pytest |
| API integration | Request, auth, DB transaction, response, error | pytest + ASGI test client |
| Migration | Upgrade from empty DB and schema drift | Alembic |
| Frontend integration | Store/service behavior against API | Vitest if added, otherwise documented integration checks |
| Role smoke | Owner, student, super-admin critical journeys | Playwright if feasible plus manual UAT evidence |

### Required API test categories

- Valid create/read/update/status workflow.
- Missing required field.
- Invalid enum/date/amount/time.
- Unauthenticated request.
- Wrong-role request.
- Cross-library resource ID.
- Resource not found in current tenant.
- Duplicate/conflicting request.
- Soft-deleted or inactive resource.
- Pagination, search, and filter behavior.
- Database rollback after service failure.

### Minimum quality target

- Every implemented route has at least one success and one failure test.
- Every critical business rule has a dedicated automated test.
- Target at least 80% coverage for backend services and endpoints.
- Tests must be deterministic and must not depend on production data.
- Use a separate test database/schema and reset state between tests.

The report test matrix uses
`docs/milestones/templates/API_TEST_CASE_MATRIX.md`.

## 14. GitHub and Review Workflow

### Issue rules

Each implementation issue must include:

- User story and acceptance criteria.
- API paths.
- database tables involved.
- Owner and reviewer.
- Test cases required.
- Frontend screens/stores/services affected.
- Documentation/evidence required.
- Dependencies and blockers.

Suggested labels:

```text
milestone-3
milestone-4
backend
frontend-integration
api-contract
testing
documentation
bug
blocked
feedback
```

### Branch names

```text
m3/auth-foundation
m3/student-api
m3/seat-allocation-api
m3/payment-api
m3/announcement-settings-api
m4/student-portal-api
m4/reports-api
m4/superadmin-api
fix/<short-description>
```

### Pull request requirements

- Link the issue using `Closes #<issue>`.
- Summarize API and database changes.
- List tests run and their results.
- Include screenshots when frontend behavior changes.
- Update OpenAPI YAML in the same PR as an API contract change.
- Add an Alembic migration for schema changes.
- Assign the planned reviewer.
- Resolve all review threads before merge.
- Do not combine unrelated modules in one PR.
- Do not push directly to `main`.

## 15. Team Communication and Records

### Cadence

- Daily async update: completed, next, blocker, PR link.
- 20-minute stand-up on agreed team days.
- API contract review: 25 July and 3 August.
- Integration sessions: 30 July and 8 August.
- User review: 1 August and 10 August.
- Retrospective: 3 August and after M4 submission.

### Meeting records

Use `docs/milestones/templates/SCRUM_MEETING_MINUTES.md`. Record:

- attendees;
- completed work;
- blockers;
- decisions;
- action owner and due date;
- changed scope or API contract.

Significant architecture decisions use `docs/adr/`.

## 16. User Feedback Process

Use a library owner as the primary user for the required feedback session.
Include one student-view task if possible.

### Suggested M3 demo tasks

1. Log in as a library owner.
2. Create or edit a student.
3. Create a shift and inspect overlap validation.
4. Find a seat for a selected shift and date.
5. Allocate the seat and verify conflict handling.
6. Generate a monthly fee record and record a payment.
7. Publish an announcement.

### Feedback handling

Each item is classified as:

- Accepted for M4.
- Deferred after M4.
- Rejected with reason.
- Defect requiring immediate correction.

Use `docs/milestones/templates/USER_FEEDBACK_LOG.md`. Accepted M4 feedback must
have a GitHub issue and owner.

## 17. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Too many endpoints for two short sprints | Incomplete integration | Deliver vertical slices, freeze M3 scope, and defer non-core polish |
| Contract drift between YAML, FastAPI, and Vue | Integration failures | Contract-first review and YAML update in every API PR |
| Cross-library data leakage | Critical security defect | Central tenant dependency, tenant-scoped repositories, and negative tests |
| Allocation race or overlap bug | Double booking | Transactional service, row locking strategy, and overnight/date tests |
| Team members block each other in shared files | Merge delays | Domain files, small PRs, early contract freeze, and integration sessions |
| Report evidence prepared too late | Lost marks | Evidence owner and daily capture in milestone folders |
| Tests pass only on SQLite | PostgreSQL failures | Run migrations and key integration tests against PostgreSQL |
| Frontend mocks hide API failures | False confidence | API mode as default and visible loading/error states |
| Unreviewed last-day changes | Regression | Code freeze one day before each submission |

## 18. Definition of Done for Every User Story

A user story is done only when:

- Acceptance criteria are met.
- OpenAPI YAML is updated and valid.
- Request/response schemas are implemented.
- Repository queries are tenant-scoped.
- Service rules and transaction behavior are implemented.
- Endpoint uses correct status and structured errors.
- Positive, negative, permission, and tenant tests pass.
- Audit logging is added where required.
- Frontend service/store/page is integrated when in sprint scope.
- Loading, empty, validation, and error states work.
- Documentation and evidence are updated.
- A teammate has reviewed and approved the PR.
- CI/local lint, build, pytest, migration, and schema checks pass.

## 19. Ready-to-Create GitHub Backlog

Create these issues during kickoff, then split an item further when its pull
request would touch unrelated workflows.

| Issue | Milestone | Owner | Depends on |
|---|---|---|---|
| Freeze API conventions and first OpenAPI contract | M3 | Shubham + all reviewers | None |
| Add common schemas, error handlers, pagination, and test fixtures | M3 | Shubham | API conventions |
| Implement authentication, refresh sessions, roles, and tenant dependencies | M3 | Shubham | Common foundation |
| Implement student CRUD and account invitation | M3 | Gaurav | Auth and tenant dependencies |
| Implement floor, seat, and bulk seat management | M3 | Hitarth | Common foundation |
| Implement shifts and overnight overlap validation | M3 | Hitarth | Common foundation |
| Implement seat availability and allocation lifecycle | M3 | Hitarth | Seats, shifts, and students |
| Implement monthly fee generation and payment recording | M3 | Piyush | Students and common foundation |
| Implement announcement CRUD and library settings | M3 | Mandeep | Auth and tenant dependencies |
| Integrate M3 owner frontend services with FastAPI | M3 | Each feature owner | Corresponding backend API |
| Execute M3 API matrix and primary-user feedback | M3 | Piyush + Shubham | Integrated M3 workflows |
| Consolidate diagrams, Gantt/Kanban evidence, UI screenshots, minutes, and frontend README/archive | M3 | Report coordinator | M3 implementation evidence |
| Implement student portal self-service APIs | M4 | Gaurav | Auth, students, payments, allocations |
| Implement seat change request review and resulting allocation | M4 | Gaurav + Hitarth | Portal and allocations |
| Implement receipts, reminders, payment history, and reports | M4 | Piyush | M3 payment APIs |
| Implement owner dashboard aggregation | M4 | Shubham + Piyush | All owner source modules |
| Implement platform library, owner, analytics, and settings APIs | M4 | Mandeep | Auth and library foundation |
| Add administrative audit logging and audit queries | M4 | Shubham + feature owners | Domain mutation APIs |
| Remove remaining production mock calls and run three-role regression | M4 | All | All M4 APIs |
| Apply user feedback and prepare M4 evidence | M4 | Assigned feedback owners | M3 feedback log |

## 20. Release Checklists

### Milestone 3

- [ ] Course design carry-forward evidence included.
- [ ] Updated component/class diagrams and ERD included.
- [ ] Frontend source archive includes installation and run instructions.
- [ ] M3 issues assigned and closed or explicitly deferred.
- [ ] OpenAPI YAML validates.
- [ ] M3 backend and integration tests pass.
- [ ] Frontend lint and build pass.
- [ ] Alembic upgrade works from an empty database.
- [ ] Primary-user feedback recorded.
- [ ] Test matrix contains expected and actual results.
- [ ] Four to five readable pytest result screenshots captured.
- [ ] All PR reviews resolved.
- [ ] Tag `milestone-3` created from the submitted revision.

### Milestone 4

- [ ] Accepted M3 feedback is traceable to issues and PRs.
- [ ] Updated OpenAPI YAML validates.
- [ ] All role and tenant regression tests pass.
- [ ] Owner, student, and super-admin smoke flows pass.
- [ ] No production-path page reads mocks directly.
- [ ] Frontend lint and build pass.
- [ ] Backend pytest and Alembic checks pass.
- [ ] Final test matrix and screenshots match the submitted revision.
- [ ] All PR reviews resolved.
- [ ] Tag `milestone-4` created from the submitted revision.

## 21. Kickoff Decisions Required

Record these decisions on 24-25 July:

1. Confirm the proposed feature owners and reviewers.
2. Confirm the exact list of user stories submitted in Sprint 1.
3. Confirm access-token storage and refresh-cookie behavior.
4. Confirm JSON camelCase and response envelope.
5. Confirm the shared development and test database strategy.
6. Confirm the primary user and feedback-session time.
7. Confirm who owns the PDF report, YAML validation, test matrix, and final
   submission upload.

Once confirmed, convert each workstream into GitHub issues and link those issue
numbers from this document or the sprint board.
