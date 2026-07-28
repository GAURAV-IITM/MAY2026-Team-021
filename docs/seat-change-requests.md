# Owner Seat Change Requests

## Scope

This module lets a Library Owner or authorised staff member list and review
seat-change requests submitted by students. Student submission and cancellation
remain part of the Student Portal mock flow until that API is implemented.

Approving a request records the owner's decision only. It does **not** create,
cancel, reserve, or transfer a seat allocation. Any later allocation change must
use the separate seat-allocation workflow.

## Lifecycle

Requests use the existing statuses:

- `pending`: may be approved or rejected once.
- `approved`: final decision; no allocation is changed.
- `rejected`: final decision and requires a review note of 5-2000 characters.
- `cancelled`: historical student cancellation and cannot be reviewed.

The database already enforces one pending request per student within a library.
Requests are historical records and are not soft-deleted.

Every successful review stores the reviewer, review timestamp, optional note,
and an append-only audit record in the same transaction. Review requests lock
the database row, so only one concurrent reviewer can succeed. A later or
competing review receives `409 SEAT_REQUEST_ALREADY_REVIEWED`.

## API

Both endpoints require JWT authentication, an active library membership, and
the `library_owner` or `staff` role. Tenant filtering comes from the current
membership; clients never submit a library ID.

### List requests

`GET /api/v1/seat-requests`

Supported query parameters:

- `status`: `pending`, `approved`, `rejected`, or `cancelled`
- `search`: student name, enrollment number, reason, or preferred seat number
- `studentId`, `preferredFloorId`, and `preferredShiftId`
- `page`, `pageSize`, `sortBy`, and `sortOrder`

The response includes nested student, current-allocation, preference, and
reviewer summaries, pagination metadata, and tenant-wide status counts.

### Review a request

`PATCH /api/v1/seat-requests/{requestId}/review`

Approval:

```json
{
  "decision": "approved",
  "reviewNote": "Approved for a later allocation review."
}
```

Rejection:

```json
{
  "decision": "rejected",
  "reviewNote": "The requested seat is not currently available."
}
```

The payload intentionally has no seat, floor, shift, or allocation fields.
The full contract, examples, request-ID headers, and structured errors are in
`docs/api/openapi.yaml`.

## Frontend Flow

`SeatRequests.vue` uses `seatRequestStore`, which calls
`seatRequestService` through the shared Axios client. Search, status filters,
pagination, loading, and summary counts are server-backed. Successful reviews
refresh the current list without resetting its filters.

If another administrator reviews the same request first, the modal retains the
entered note, displays the server conflict, disables review actions, and
refreshes the list. No owner request method falls back to mock data.

## Errors

- `401 AUTHENTICATION_REQUIRED`: no valid session.
- `403 PERMISSION_DENIED`: the user is not Library Owner or staff.
- `404 SEAT_REQUEST_NOT_FOUND`: missing or tenant-hidden request.
- `409 SEAT_REQUEST_ALREADY_REVIEWED`: the request has a final status.
- `422 VALIDATION_ERROR`: invalid decision or review note.

## Verification

The module is covered by:

- API list, filtering, pagination, authorization, tenant isolation, validation,
  audit, and allocation non-mutation tests.
- PostgreSQL row-lock tests for approval-versus-rejection and duplicate approval
  races when `TEST_POSTGRES_DATABASE_URL` is configured.
- Frontend service, Pinia stale-response, and review-modal tests.
- OpenAPI export and drift checks.

Run:

```bash
backend/venv/bin/python -m pytest backend/tests -q
backend/venv/bin/python backend/scripts/export_openapi.py --check
cd frontend && npm test && npm run lint && npm run build
```
