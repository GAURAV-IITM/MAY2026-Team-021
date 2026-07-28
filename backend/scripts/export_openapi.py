"""Export and verify the checked-in OpenAPI YAML contract."""
from __future__ import annotations

import argparse
import sys
import difflib
from pathlib import Path
from typing import Any

import yaml
from openapi_spec_validator import validate


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "api" / "openapi.yaml"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import create_app  # noqa: E402


def build_openapi_schema() -> dict[str, Any]:
    schema = create_app().openapi()
    validate(schema)
    return schema


def load_openapi_yaml(path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"OpenAPI contract not found: {path}")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"OpenAPI contract must contain an object: {path}")
    validate(document)
    return document


def write_openapi_yaml(
    schema: dict[str, Any],
    path: Path = DEFAULT_OUTPUT,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            schema,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        ),
        encoding="utf-8",
    )


def check_openapi_contract(path: Path = DEFAULT_OUTPUT) -> bool:
    schema = build_openapi_schema()
    generated_yaml = yaml.safe_dump(
        schema,
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )
    if not path.exists():
        return False
    current_yaml = path.read_text(encoding="utf-8")
    if current_yaml == generated_yaml:
        return True

    print("OpenAPI contract drift detected! Difference:", file=sys.stderr)
    diff = difflib.unified_diff(
        current_yaml.splitlines(keepends=True),
        generated_yaml.splitlines(keepends=True),
        fromfile="Current docs/api/openapi.yaml",
        tofile="Generated OpenAPI schema",
    )
    sys.stderr.writelines(diff)
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export or verify the Smart Library OpenAPI YAML.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with an error when the checked-in YAML differs from FastAPI.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.resolve()

    if args.check:
        try:
            is_current = check_openapi_contract(output)
        except (FileNotFoundError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        if not is_current:
            print(
                "OpenAPI contract drift detected. Run "
                "`python scripts/export_openapi.py` and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(f"OpenAPI contract is valid and current: {output}")
        return 0

    schema = build_openapi_schema()
    write_openapi_yaml(schema, output)
    print(f"OpenAPI contract exported: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
