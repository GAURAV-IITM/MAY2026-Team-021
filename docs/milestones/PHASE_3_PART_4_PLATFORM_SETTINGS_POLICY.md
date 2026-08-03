# Phase 3, Part 4: Platform Settings Policy

## Repository Findings

- `PlatformSetting` already stores one JSON value per unique key with a
  description, updater user ID, and created/updated timestamps. No second
  settings table or migration is required.
- No platform setting rows are seeded by the current migrations. Missing rows
  must therefore resolve to registry defaults.
- The existing Super Admin page is mock-backed and includes settings that have
  no backend behavior. Platform settings and tenant `LibrarySettings` are
  separate models and routes.
- Public library registration currently creates an active library, owner,
  resources, and token session. JWT access-token lifetime currently comes from
  environment configuration.
- Platform routes already share the repository-defined Super Admin dependency,
  structured errors, request IDs, and append-only audit writer.

## Approved Registry

| API key | Storage key | Display name | Type | Default | Validation | Editable | Runtime effect | Classification | Frontend control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `platformName` | None | Platform name | Text | `APP_NAME` configuration | Non-empty, maximum 120 characters | No | Names the running API and OpenAPI document at application startup | Non-sensitive | Read-only text |
| `allowLibraryRegistrations` | `allow_library_registrations` | Allow library registrations | Boolean | `true` | Strict JSON boolean | Yes | Public library-registration endpoints reject new registrations when disabled | Non-sensitive | Toggle with confirmation when disabling |
| `sessionTimeoutMinutes` | `session_timeout_minutes` | Access-token timeout | Integer | Current `ACCESS_TOKEN_EXPIRE_MINUTES` | Strict integer from 15 through 1440 | Yes | Controls newly issued access-token expiry and `expiresIn`; existing tokens keep their original expiry | Non-sensitive | Number input |
| `defaultTimezone` | `default_timezone` | Default library timezone | Enum | `Asia/Kolkata` | `Asia/Kolkata`, `UTC`, or `Asia/Dubai` | Yes | Applied to libraries created by public registration after the change | Non-sensitive | Select menu |

Only these API keys are returned. Rows with unknown keys, including any secret
or infrastructure-like values, are ignored by reads and cannot be addressed by
writes through this API.

## Excluded Or Deferred Controls

| Existing mock control | Decision | Reason |
| --- | --- | --- |
| Support email and phone | Excluded | No public support-contact service or configuration contract consumes them |
| Require registration approval | Deferred | The current registration endpoint creates an active authenticated owner; changing this requires a separate pending-registration workflow and response contract |
| Maintenance mode | Excluded | No approved route allowlist, middleware, session behavior, or maintenance error contract exists |
| Registration and owner notification toggles | Excluded | No platform notification delivery system consumes them |
| Weekly summary | Excluded | No scheduled platform summary job exists |

Database URLs, JWT secrets, SMTP credentials, API tokens, storage credentials,
environment variables, arbitrary JSON, and tenant settings are permanently
outside this API.

## Storage And Concurrency

- Missing editable rows return registry defaults and are persisted only when a
  Super Admin updates them.
- `__platform_settings_version__` is an internal row in the existing table. It
  is never returned as a setting or accepted as an API key.
- GET returns the current integer version. PATCH requires that version, locks
  the version and affected setting rows, validates all values, applies all
  changes, increments the version, writes one safe audit event, and commits
  once.
- A stale version returns `PLATFORM_SETTINGS_UPDATE_CONFLICT`. Concurrent first
  writes are protected by the unique key constraint and translated to the same
  conflict. The repository never commits.
- Validation is completed before persistence, so a mixed valid/invalid request
  writes no setting and no audit record.

## Audit Policy

Successful changes write `platform.settings.updated` with the actor, changed
keys, safe previous/new values, version transition, request ID, and timestamp.
Unknown, invalid, stale, no-op, and rolled-back updates create no success audit.
