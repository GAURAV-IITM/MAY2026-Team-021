# Phase 3, Part 2: Platform Owner Management

## Repository Findings

- Owners are global `User` records with the `library_owner` role and tenant
  access is represented by `LibraryMembership`.
- `Library.primary_owner_user_id` and the existing Super Admin UI model one
  primary owner per library. Tenant resolution also assumes one active owner
  membership per owner.
- Membership statuses are `invited`, `active`, `suspended`, and `left`.
  Membership rows are unique per user and library and are retained for history.
- Users have an `is_active` account flag rather than a separate user-status
  enum. Active sessions are stored in `UserSession` and can be revoked.
- `AccountInvitation` already stores hashed invitation tokens, expiry,
  lifecycle status, inviter, role, and library. Student setup uses the public
  `/auth/invitations/validate` and `/auth/invitations/accept` endpoints.
- No email delivery provider exists. In development, invitation creation
  returns a setup URL using the same controlled contract as student invites.
- Platform routes already use a dedicated Super Admin dependency, structured
  errors, request IDs, audit logs, shared pagination, and OpenAPI drift checks.
- The existing Owners page and its service methods are mock-backed and perform
  search, filtering, and pagination in the browser.

## Frozen Policies

### Ownership And Assignment

A library has at most one primary owner and may temporarily have no owner. An
owner has at most one active owner membership. Assignment to a new library is
an explicit transactional reassignment: the previous membership is marked
`left`, its `left_at` timestamp is recorded, the previous library's primary
owner is cleared, and the target membership is created or reactivated. A target
library that already has another owner rejects owner-side reassignment; the
library-management command remains the explicit workflow for replacing that
library's current owner.

### Invitations

New owner accounts use the existing `AccountInvitation` system. The platform
stores only the token hash and safe invitee metadata. No temporary password is
accepted, generated, stored, or returned. Pending and expired invitations
appear in the owner list so Super Admins can track the account lifecycle.

An email belonging to an eligible active owner account may be assigned directly
without a new invitation. An email belonging to another account type, a
deleted account, a suspended account, an already assigned owner, or an active
pending owner invitation is rejected with a stable conflict code. An expired
owner invitation may be reissued; the expired row is retained.

Only active or pending libraries may receive an owner invitation or assignment.
Suspended or deleted libraries are ineligible. A library may have only one
primary owner or pending owner invitation at a time.

### Profile Edits

Accepted owner accounts may edit only name and phone through platform Owner
Management. Email is immutable because the repository does not yet provide a
verified email-change workflow. Invitations are immutable profile records and
must be reissued when their details need correction. Passwords and roles are
never editable here.

### Suspension And Sessions

Suspending an accepted owner sets `User.is_active` to false, marks only active
owner memberships as `suspended`, and revokes every active session in the same
transaction. It does not suspend libraries, remove primary-owner links, alter
other membership roles, or delete history. Login and refresh are therefore
blocked immediately. Activation restores the account and only owner
memberships suspended by this lifecycle; revoked sessions stay revoked and the
owner must log in again. Pending invitations cannot be activated or suspended.

The current account flag is global. Consequently, suspending an owner also
blocks any secondary role held by that same user. This follows the existing
authentication model and is documented rather than hidden.

### Transactions And Concurrency

- Services own every transaction and audit write.
- Invitation creation locks the target library and conflicting invitation or
  account rows; database partial unique indexes protect concurrent pending
  owner invitations by email and by library.
- Assignment locks the owner and affected libraries, re-reads current state,
  and preserves membership history.
- Status mutation locks the owner, supports `expectedUpdatedAt`, updates owner
  memberships, revokes sessions, writes audit data, and commits once.
- Failed mutations roll back invitation, assignment, session, and audit changes.

## Prompt Differences

- The repository uses `User.is_active`, not an owner status enum. API owner
  status values are derived as `invited`, `active`, or `suspended`.
- Pagination uses `sortOrder`, not `sortDirection`.
- Assignment is singular because the existing library and tenant model has one
  primary owner and one active owner membership.
- Invitation acceptance remains on the existing authentication endpoints;
  Owner Management does not introduce another token or password setup route.
- Email delivery is not implemented. The development setup URL is returned only
  at invitation creation or reissue and is not recoverable later.
