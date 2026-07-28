# Owner Announcement Management

## Scope

Milestone 3 Phase 5 replaces the Library Owner announcement mock with a real,
tenant-scoped API. Owners and active staff can list, search, filter, create,
edit, publish, archive, and soft-delete eligible announcements. The Student
Portal announcement feed and read state remain mock-backed until their later
API phase. Automatic scheduled publication and expiry workers are also outside
this phase.

## Lifecycle

The backend is authoritative for every transition:

```text
Draft -> Scheduled
Draft -> Published
Draft -> Deleted
Scheduled -> Draft
Scheduled -> Published
Scheduled -> Archived
Published -> Archived
Expired -> Archived
Archived -> Deleted
```

- Create accepts only `draft` or `scheduled`.
- Draft and scheduled announcements are editable.
- Publishing is an explicit command and sets `publishedAt` to server UTC time.
- Archiving preserves the record, sets `archivedAt`, and may include an audit
  reason.
- Deletion is soft deletion and accepts only draft or archived records.
- A scheduled announcement must be archived before deletion.
- Published and archived content cannot be edited or republished.

Invalid transitions return `ANNOUNCEMENT_INVALID_STATE_TRANSITION` with the
announcement ID and its current/requested status. Tenant lookups return `404`
for another library's IDs and never reveal cross-library details.

## Date Rules

- API timestamps are ISO 8601; the Vue form converts browser-local date inputs
  to UTC before submission.
- Scheduled announcements require a future `scheduledAt`.
- Drafts cannot carry `scheduledAt`.
- `expiresAt`, when present, must be in the future.
- For scheduled content, expiry must be later than `scheduledAt`.
- Manual publishing of a draft or scheduled announcement is allowed.
- List responses expose an effective `expired` status and `isExpired=true`
  when published content has passed its expiry, without mutating the stored
  lifecycle state. Published/expired filters and summary counts use the same
  effective rule. A later worker phase will persist automatic expiry and
  scheduled publication.

## Consistency And Audit

- Every mutation re-reads the tenant-owned announcement with a database row
  lock.
- Edit requests include `expectedUpdatedAt`. A stale editor receives
  `ANNOUNCEMENT_STATE_CHANGED`, and the frontend refreshes the list while
  retaining the error for the administrator.
- Create, edit, publish, archive, and delete each write an audit row in the
  same transaction as the announcement change.
- Audit records contain actor, library, request ID, request metadata, action,
  entity ID, safe changed-field/status details, and archive reason when given.
- List summary counts cover all non-deleted announcements in the current
  library, independently of active list filters.

## API Mapping

| Owner operation | API |
| --- | --- |
| Search, filter, sort, and page | `GET /api/v1/announcements` |
| Create draft or schedule | `POST /api/v1/announcements` |
| Edit draft or schedule | `PATCH /api/v1/announcements/{announcementId}` |
| Publish immediately | `POST /api/v1/announcements/{announcementId}/publish` |
| Archive and preserve history | `POST /api/v1/announcements/{announcementId}/archive` |
| Soft-delete draft or archived | `DELETE /api/v1/announcements/{announcementId}` |

The owner page calls the Pinia announcement store, which calls
`frontend/src/services/announcementService.js`, which uses the shared Axios
client. It has no owner mock fallback and never submits a library or actor ID.

## Domain Error Codes

| Code | Meaning |
| --- | --- |
| `ANNOUNCEMENT_NOT_FOUND` | Missing, deleted, or outside the current library. |
| `ANNOUNCEMENT_CREATE_STATUS_INVALID` | Create attempted a non-draft/scheduled state. |
| `ANNOUNCEMENT_INVALID_STATE_TRANSITION` | Current state does not permit the command. |
| `ANNOUNCEMENT_STATE_CHANGED` | The record changed after the form opened. |
| `ANNOUNCEMENT_FIELD_REQUIRED` | An editable required field was explicitly null. |
| `ANNOUNCEMENT_DRAFT_SCHEDULE_INVALID` | A draft included a schedule. |
| `ANNOUNCEMENT_SCHEDULE_REQUIRED` | Scheduled state omitted its date. |
| `ANNOUNCEMENT_SCHEDULE_NOT_FUTURE` | Scheduled date is not in the future. |
| `ANNOUNCEMENT_EXPIRY_NOT_FUTURE` | Expiry is not in the future. |
| `ANNOUNCEMENT_EXPIRY_BEFORE_PUBLISH` | Expiry is not after scheduled publication. |

Pydantic field failures use the shared `VALIDATION_ERROR`. Every API error
contains the request ID.

## Verification

From the repository root:

```bash
backend/venv/bin/pytest backend/tests/test_announcement_api.py -q
backend/venv/bin/pytest backend/tests/test_announcement_concurrency_postgres.py -q
backend/venv/bin/python backend/scripts/export_openapi.py --check
backend/venv/bin/pytest backend/tests/test_openapi_contract.py -q
```

The PostgreSQL test requires `TEST_POSTGRES_DATABASE_URL` and verifies that two
concurrent publish commands result in one publication and one rejection.

From `frontend/`:

```bash
npm test
npm run lint
npm run build
```
