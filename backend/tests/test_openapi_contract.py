from __future__ import annotations

from openapi_spec_validator import validate

from scripts.export_openapi import (
    DEFAULT_OUTPUT,
    build_openapi_schema,
    load_openapi_yaml,
)


def test_checked_in_openapi_yaml_is_valid_and_current() -> None:
    checked_in_contract = load_openapi_yaml(DEFAULT_OUTPUT)
    generated_contract = build_openapi_schema()

    validate(checked_in_contract)
    assert checked_in_contract == generated_contract


def test_authentication_operations_have_stable_ids_and_user_stories() -> None:
    contract = load_openapi_yaml(DEFAULT_OUTPUT)
    auth_operations = [
        operation
        for path, path_item in contract["paths"].items()
        if path.startswith("/api/v1/auth/")
        for operation in path_item.values()
        if isinstance(operation, dict)
    ]

    operation_ids = [operation.get("operationId") for operation in auth_operations]
    assert len(operation_ids) == len(set(operation_ids))
    assert all(operation_ids)
    assert all(operation.get("x-user-stories") for operation in auth_operations)


def test_all_operations_are_submission_documented() -> None:
    contract = load_openapi_yaml(DEFAULT_OUTPUT)
    methods = {"get", "post", "put", "patch", "delete"}

    for path, path_item in contract["paths"].items():
        for method, operation in path_item.items():
            if method not in methods:
                continue

            label = f"{method.upper()} {path}"
            assert operation.get("operationId"), label
            assert operation.get("summary"), label
            assert operation.get("description"), label
            assert operation.get("x-user-stories"), label
            assert any(
                str(status_code).startswith(("4", "5"))
                for status_code in operation.get("responses", {})
            ), label
