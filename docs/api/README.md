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
