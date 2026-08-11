"""Whitelisted platform-setting registry and transactional use cases."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.exceptions import BusinessRuleError, ConflictError
from app.models.library import PlatformSetting
from app.repositories import platform_settings as repository
from app.schemas.platform import (
    PlatformSettingDefinition,
    PlatformSettingValueType,
    PlatformSettingsResponse,
    PlatformSettingsUpdate,
    PlatformSettingsValues,
    PlatformTimezone,
)
from app.services.audit import AuditContext, write_audit_log


VERSION_STORAGE_KEY = "__platform_settings_version__"


@dataclass(frozen=True, slots=True)
class SettingSpec:
    api_key: str
    storage_key: str | None
    display_name: str
    value_type: PlatformSettingValueType
    default: str | bool | int
    editable: bool
    description: str
    runtime_effect: str
    minimum: int | None = None
    maximum: int | None = None
    options: tuple[str, ...] = ()


SETTING_REGISTRY: tuple[SettingSpec, ...] = (
    SettingSpec(
        api_key="platformName",
        storage_key=None,
        display_name="Platform name",
        value_type=PlatformSettingValueType.TEXT,
        default=app_settings.app_name,
        editable=False,
        description="Deployment-managed name of the Smart Library platform.",
        runtime_effect="Names the running API and its OpenAPI document at startup.",
    ),
    SettingSpec(
        api_key="allowLibraryRegistrations",
        storage_key="allow_library_registrations",
        display_name="Allow library registrations",
        value_type=PlatformSettingValueType.BOOLEAN,
        default=True,
        editable=True,
        description="Controls whether public library registration is available.",
        runtime_effect="Disabled registrations are rejected before any account or library is created.",
    ),
    SettingSpec(
        api_key="sessionTimeoutMinutes",
        storage_key="session_timeout_minutes",
        display_name="Access-token timeout",
        value_type=PlatformSettingValueType.INTEGER,
        default=max(15, min(1440, app_settings.access_token_expire_minutes)),
        editable=True,
        description="Lifetime of newly issued access tokens in minutes.",
        runtime_effect="Applies to login, registration, and refresh tokens issued after the update.",
        minimum=15,
        maximum=1440,
    ),
    SettingSpec(
        api_key="defaultTimezone",
        storage_key="default_timezone",
        display_name="Default library timezone",
        value_type=PlatformSettingValueType.ENUM,
        default=PlatformTimezone.ASIA_KOLKATA.value,
        editable=True,
        description="Timezone assigned to newly registered libraries.",
        runtime_effect="Applied when public registration creates a new library.",
        options=tuple(item.value for item in PlatformTimezone),
    ),
)

REGISTRY_BY_API_KEY = {item.api_key: item for item in SETTING_REGISTRY}
EDITABLE_SPECS = tuple(item for item in SETTING_REGISTRY if item.editable)
STORAGE_SPECS = {
    item.storage_key: item for item in SETTING_REGISTRY if item.storage_key is not None
}


@dataclass(frozen=True, slots=True)
class RuntimePlatformSettings:
    allow_library_registrations: bool
    session_timeout_minutes: int
    default_timezone: PlatformTimezone


def _validate_stored_value(spec: SettingSpec, value: Any) -> str | bool | int:
    valid = False
    if spec.value_type == PlatformSettingValueType.BOOLEAN:
        valid = type(value) is bool
    elif spec.value_type == PlatformSettingValueType.INTEGER:
        valid = (
            type(value) is int
            and (spec.minimum is None or value >= spec.minimum)
            and (spec.maximum is None or value <= spec.maximum)
        )
    elif spec.value_type in {PlatformSettingValueType.ENUM, PlatformSettingValueType.TEXT}:
        valid = isinstance(value, str) and bool(value.strip())
        if spec.options:
            valid = valid and value in spec.options
    if not valid:
        raise RuntimeError(f"Stored platform setting is invalid: {spec.storage_key}")
    return value


def _resolved_values(rows: dict[str, PlatformSetting]) -> dict[str, str | bool | int]:
    values: dict[str, str | bool | int] = {}
    for spec in SETTING_REGISTRY:
        if spec.storage_key is None:
            values[spec.api_key] = spec.default
            continue
        row = rows.get(spec.storage_key)
        values[spec.api_key] = (
            spec.default
            if row is None
            else _validate_stored_value(spec, row.value)
        )
    return values


def _version(rows: dict[str, PlatformSetting]) -> int:
    row = rows.get(VERSION_STORAGE_KEY)
    if row is None:
        return 0
    if type(row.value) is not int or row.value < 0:
        raise RuntimeError("Stored platform settings version is invalid.")
    return row.value


def _definitions() -> list[PlatformSettingDefinition]:
    return [
        PlatformSettingDefinition(
            key=spec.api_key,
            display_name=spec.display_name,
            type=spec.value_type,
            editable=spec.editable,
            default_value=spec.default,
            description=spec.description,
            runtime_effect=spec.runtime_effect,
            minimum=spec.minimum,
            maximum=spec.maximum,
            options=list(spec.options),
        )
        for spec in SETTING_REGISTRY
    ]


def _response_from_rows(rows: dict[str, PlatformSetting]) -> PlatformSettingsResponse:
    values = _resolved_values(rows)
    updated_rows = [
        row
        for key, row in rows.items()
        if key == VERSION_STORAGE_KEY or key in STORAGE_SPECS
    ]
    updated_at: datetime | None = max(
        (row.updated_at for row in updated_rows),
        default=None,
    )
    return PlatformSettingsResponse(
        settings=PlatformSettingsValues(
            platform_name=str(values["platformName"]),
            allow_library_registrations=bool(values["allowLibraryRegistrations"]),
            session_timeout_minutes=int(values["sessionTimeoutMinutes"]),
            default_timezone=PlatformTimezone(str(values["defaultTimezone"])),
        ),
        definitions=_definitions(),
        version=_version(rows),
        updated_at=updated_at,
    )


def get_settings(db: Session) -> PlatformSettingsResponse:
    rows = repository.get_rows(
        db,
        [*STORAGE_SPECS, VERSION_STORAGE_KEY],
    )
    return _response_from_rows(rows)


def get_runtime_settings(db: Session) -> RuntimePlatformSettings:
    rows = repository.get_rows(db, STORAGE_SPECS)
    values = _resolved_values(rows)
    return RuntimePlatformSettings(
        allow_library_registrations=bool(values["allowLibraryRegistrations"]),
        session_timeout_minutes=int(values["sessionTimeoutMinutes"]),
        default_timezone=PlatformTimezone(str(values["defaultTimezone"])),
    )


def update_settings(
    db: Session,
    payload: PlatformSettingsUpdate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PlatformSettingsResponse:
    requested_fields = payload.model_fields_set - {"version"}
    if not requested_fields:
        raise BusinessRuleError(
            "Provide at least one editable platform setting.",
            code="PLATFORM_SETTING_INVALID_VALUE",
        )

    try:
        rows = repository.get_rows(
            db,
            [*STORAGE_SPECS, VERSION_STORAGE_KEY],
            for_update=True,
        )
        current_version = _version(rows)
        if payload.version != current_version:
            raise ConflictError(
                "Platform settings changed after this form was loaded. Refresh and try again.",
                code="PLATFORM_SETTINGS_UPDATE_CONFLICT",
                details={"currentVersion": current_version},
            )

        current_values = _resolved_values(rows)
        previous: dict[str, str | bool | int] = {}
        updated: dict[str, str | bool | int] = {}
        for field_name in requested_fields:
            api_key = {
                "allow_library_registrations": "allowLibraryRegistrations",
                "session_timeout_minutes": "sessionTimeoutMinutes",
                "default_timezone": "defaultTimezone",
            }[field_name]
            spec = REGISTRY_BY_API_KEY[api_key]
            submitted = getattr(payload, field_name)
            value = submitted.value if isinstance(submitted, StrEnum) else submitted
            if value == current_values[api_key]:
                continue
            assert spec.storage_key is not None
            previous[api_key] = current_values[api_key]
            updated[api_key] = value
            row = rows.get(spec.storage_key)
            if row is None:
                row = repository.add_row(
                    db,
                    PlatformSetting(
                        key=spec.storage_key,
                        value=value,
                        description=spec.description,
                        updated_by_user_id=actor_user_id,
                    ),
                )
                rows[spec.storage_key] = row
            else:
                row.value = value
                row.description = spec.description
                row.updated_by_user_id = actor_user_id

        if not updated:
            raise ConflictError(
                "The submitted values do not change platform settings.",
                code="PLATFORM_SETTINGS_UPDATE_CONFLICT",
                details={"currentVersion": current_version},
            )

        next_version = current_version + 1
        version_row = rows.get(VERSION_STORAGE_KEY)
        if version_row is None:
            version_row = repository.add_row(
                db,
                PlatformSetting(
                    key=VERSION_STORAGE_KEY,
                    value=next_version,
                    description="Internal platform settings concurrency version.",
                    updated_by_user_id=actor_user_id,
                ),
            )
            rows[VERSION_STORAGE_KEY] = version_row
        else:
            version_row.value = next_version
            version_row.updated_by_user_id = actor_user_id

        write_audit_log(
            db,
            library_id=None,
            actor_user_id=actor_user_id,
            action="platform.settings.updated",
            entity_type="platform_settings",
            entity_id="global",
            old_values=previous,
            new_values=updated,
            context={
                "changedKeys": sorted(updated),
                "previousVersion": current_version,
                "newVersion": next_version,
            },
            request_context=audit_context,
        )
        db.commit()
        db.expire_all()
        return get_settings(db)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Platform settings were updated concurrently. Refresh and try again.",
            code="PLATFORM_SETTINGS_UPDATE_CONFLICT",
        ) from exc
    except Exception:
        db.rollback()
        raise
