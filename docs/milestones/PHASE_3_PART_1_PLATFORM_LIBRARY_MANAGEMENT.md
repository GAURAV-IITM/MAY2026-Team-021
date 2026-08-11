# Phase 3, Part 1: Platform Library Management

## Repository Findings

- `Library.status` supports `pending`, `active`, and `suspended`.
- `Library.primary_owner_user_id` and the Super Admin UI model one primary owner.
- `LibraryMembership` preserves the user's library role and lifecycle through
  `invited`, `active`, `suspended`, and `left` statuses. Its unique constraint
  prevents duplicate memberships for the same user and library.
- Public registration creates an active library, owner account and membership,
  settings, a floor, default shifts, seats, and an authentication session.
- Tenant authentication already requires an active library and active
  membership. Super Admin authentication intentionally does not require a
  tenant membership.
- Audit logs, request IDs, structured errors, pagination, role dependencies,
  and OpenAPI drift checks already exist and are reused by this feature.
- The existing Super Admin Library page is entirely mock-backed and performs
  filtering and pagination in the browser.

## Frozen Policies

### Platform Library Creation

Super Admin creation creates a `Library` in `pending` status and its default
`LibrarySettings`. It does not reuse public registration because no owner
password, login session, floor, shift, or seat creation is part of platform
administration. An eligible existing owner may be assigned in the same
transaction. Library code is required, normalized to uppercase, globally
unique, and immutable after creation.

### Ownership

A library has at most one active primary owner and may temporarily have none.
An owner has at most one active owner membership so tenant resolution remains
unambiguous. Assignment requires an active, non-deleted user with the global
`library_owner` role. Reassignment marks the previous active membership as
`left` and records `left_at`; it never deletes membership history. A historical
membership for the same user and library is reactivated instead of duplicated.

### Suspension

Suspension preserves all library, membership, student, seat, allocation,
payment, announcement, and audit records. It stores the actor, timestamp, and
required reason. Existing authentication and active-membership checks block
owners, staff, and students from login, refresh, and tenant APIs while the
library is suspended. Invitation validation and acceptance are also blocked.
Reactivation clears current suspension metadata and restores access for users
whose account and membership are otherwise active. Scheduled jobs are not yet
implemented; future jobs must select active libraries explicitly.

### Validation And Concurrency

- Library names are trimmed, non-empty, length-limited, and unique among
  non-deleted libraries using case-insensitive comparison.
- Email, phone, and IANA timezone values are validated.
- Allowed transitions are `pending -> active`, `active -> suspended`, and
  `suspended -> active`. Repeated or stale transitions return a conflict.
- Generic edits cannot change code, status, ownership, approval fields,
  suspension metadata, soft-delete fields, or audit values.
- Mutation services own transactions. Status, edit, and owner assignment lock
  the target library and support `expectedUpdatedAt` stale-write detection.
- The database code uniqueness constraint protects concurrent duplicate codes;
  services translate integrity conflicts to stable platform error codes.

## Prompt Differences

- The repository uses `contactEmail`, `contactPhone`, and `addressLine`, not
  generic `email`, `phone`, and `address` model attributes.
- Pagination uses `sortOrder`, not `sortDirection`.
- The repository has no library capacity field. Seat totals are derived from
  physical seat records, so the mock-only `seatCount` form field is removed.
- The repository has no inactive library status; `pending`, `active`, and
  `suspended` remain the authoritative values.
- Owner invitation creation and generic role assignment remain outside this
  phase. This feature assigns only eligible existing owner accounts.
