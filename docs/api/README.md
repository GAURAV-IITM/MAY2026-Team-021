# API Documentation

[`openapi.yaml`](openapi.yaml) is the reviewed OpenAPI 3.1 contract for
Milestones 3 and 4. FastAPI serves the same schema through `/openapi.json` and
the interactive Swagger UI through `/docs`.

## Frozen Conventions

- Base path: `/api/v1`.
- JSON fields: `camelCase`.
- Python and database fields: `snake_case`.
- Identifiers: UUID strings.
- Dates: `YYYY-MM-DD`.
- Date-times: ISO 8601 with timezone.
- Pagination: `page`, `pageSize`, `search`, `sortBy`, and `sortOrder`.
- Every response includes an `X-Request-ID` header.
- Expected errors use one structured response:

```json
{
  "error": {
    "code": "RESOURCE_CONFLICT",
    "message": "The request conflicts with existing data.",
    "details": {}
  },
  "requestId": "frontend-request-123"
}
```

Resource endpoints should use `SuccessResponse` or `PaginatedResponse`.
Authentication token responses remain direct because the frontend session
adapter already consumes that contract.

Library-owned routes derive their tenant from the authenticated active
membership. They must not trust a client-supplied library ID for authorization.

## Contract Workflow

The YAML is generated deterministically from FastAPI route metadata and
Pydantic schemas. Do not hand-edit it.

For every endpoint:

1. Define the route contract, Pydantic schemas, stable `operationId`, expected
   error responses, role requirements, and `x-user-stories`.
2. Export the contract and review its Swagger representation before completing
   the repository and service behavior.
3. Implement the endpoint and its positive, negative, role, and tenant tests.
4. Run the drift check and commit the generated YAML with the implementation.

From `backend/`:

```bash
python scripts/export_openapi.py
python scripts/export_openapi.py --check
pytest tests/test_openapi_contract.py
```

The export and check both run formal OpenAPI validation. Backend CI repeats the
drift check and full pytest suite on every relevant pull request.

## Feature Author Template

Use the shared dependencies instead of reading `libraryId` from request data:

```python
from typing import Annotated

from fastapi import Depends

from app.api.deps import CurrentTenant, Pagination, require_library_staff
from app.models.identity import User
from app.schemas.common import PaginatedResponse, error_responses


@router.get(
    "",
    response_model=PaginatedResponse[StudentResponse],
    operation_id="listStudents",
    responses=error_responses(401, 403),
    openapi_extra={"x-user-stories": ["STUDENT-LIST"]},
)
def list_students(
    tenant: CurrentTenant,
    pagination: Pagination,
    _actor: Annotated[User, Depends(require_library_staff)],
):
    ...
```

Repository queries must receive `tenant.library_id`. Expected service failures
should raise a typed exception from `app.core.exceptions`; the API handlers
will produce the shared error envelope automatically.

## Operation Checklist

Every operation must include:

- a stable `operationId`;
- summary and description;
- user-story reference using an `x-user-stories` extension;
- authentication and role expectations;
- parameters or request body;
- success response;
- validation, authentication, permission, not-found, and conflict responses
  where applicable;
- example input and output.

The contract test fails when the checked-in YAML differs from the current
FastAPI schema.

## Phase 2 Route Groups

The checked-in contract now includes the following real vertical slices:

- `/students`: list, create, detail, update, status, delete, and invitation;
- `/auth/invitations`: public validation and password setup;
- `/floors`: list, create, update, and delete;
- `/seats`: list, create, detail, update, delete, status, and bulk actions;
- `/shifts`: list, create, update, status, delete, and selection validation;
- `/settings/library`: read and update library settings.

Every protected operation derives its library from `CurrentTenant`. Client
payloads do not contain an authorization-level `libraryId`.

## Phase 3 Payment Routes

The contract includes the real owner/staff payment vertical slice:

- `GET /payments` lists tenant-scoped fee records with server-calculated
  totals, balances, statuses, transactions, summary totals, and pagination.
- `POST /payments/monthly-generation` idempotently generates one monthly fee
  record per eligible active student.
- `POST /payments/{feeRecordId}/transactions` records an append-only full or
  partial payment after locking and recalculating the current balance.

See [`../payments.md`](../payments.md) for eligibility, calculation,
concurrency, frontend mapping, and test details.

## Sprint 2 / Milestone 4 Additions

The current contract contains 90 operations. Sprint 2 extends the Milestone 3
contract with the remaining role-specific workflows while preserving the same
authentication, tenant, response, and error conventions:

- Student self-service for profile, allocations, fees, receipts, announcements,
  and seat-change requests.
- Owner receipts, payment reminders, operational dashboards, and reports.
- Super Admin platform dashboard, platform settings, library management, and
  owner invitations, assignment, lifecycle, and profile management.
- Shared invitation validation/acceptance for student and platform-owner
  account activation.

Every Sprint 2 operation has a stable `operationId`, a summary and full
description, one or more `x-user-stories`, documented success and error
responses, and the request-ID response header. The contract audit in
`backend/tests/test_openapi_contract.py` verifies these rules and checks that
the checked-in YAML is byte-for-byte current with FastAPI's generated schema.

The feedback-to-implementation record and final test matrix are maintained in
[`../milestones/MILESTONE_4_SPRINT_2_DELIVERABLES.md`](../milestones/MILESTONE_4_SPRINT_2_DELIVERABLES.md)
and [`../milestones/MILESTONE_4_API_TEST_CASE_MATRIX.md`](../milestones/MILESTONE_4_API_TEST_CASE_MATRIX.md).
