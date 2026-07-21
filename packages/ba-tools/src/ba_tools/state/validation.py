"""Local JSON Schema loading and mutation-free workspace classification."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from importlib import resources
from pathlib import PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedRepoRoot, resolve_business_path

SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
STATE_SCHEMA_BY_PATH = {
    ".ba-ops/config.json": "config.schema.json",
    ".ba-ops/coverage-policy.json": "coverage-policy.schema.json",
    ".ba-ops/business-goals.json": "business-goals.schema.json",
}
DEFAULT_REQUIRED_STATE_FILES = tuple(STATE_SCHEMA_BY_PATH)


class WorkspaceStateKind(StrEnum):
    """The four non-mutating classifications used by init transitions."""

    FRESH = "fresh"
    COMPLETE = "complete"
    PARTIAL = "partial"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ValidationDiagnostic:
    """One safe, field-addressed validation finding."""

    path: str
    pointer: str
    validator: str
    message: str

    def as_dict(self) -> dict[str, str]:
        """Return the allowlisted process representation."""

        return {
            "path": self.path,
            "pointer": self.pointer,
            "validator": self.validator,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceState:
    """Complete classification facts for all declared required state files."""

    kind: WorkspaceStateKind
    present: tuple[str, ...]
    missing: tuple[str, ...]
    diagnostics: tuple[ValidationDiagnostic, ...]


def _schema_error() -> BaToolsError:
    return BaToolsError(
        code="PACKAGED_SCHEMA_INVALID",
        message="A packaged workspace schema is invalid.",
        remediation=("Reinstall the exact ba-tools package and retry.",),
    )


def _contains_remote_reference(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"$ref", "$dynamicRef"} and (
                not isinstance(item, str) or not item.startswith("#")
            ):
                return True
            if _contains_remote_reference(item):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_remote_reference(item) for item in value)
    return False


def load_schema(schema_name: str) -> dict[str, Any]:
    """Load and self-check one allowlisted local Draft 2020-12 schema."""

    if schema_name not in STATE_SCHEMA_BY_PATH.values():
        raise _schema_error()
    source = (
        resources.files("ba_tools")
        .joinpath("state")
        .joinpath("resources")
        .joinpath("schemas")
        .joinpath(schema_name)
    )
    try:
        decoded = json.loads(source.read_bytes().decode("utf-8"))
        if (
            not isinstance(decoded, dict)
            or decoded.get("$schema") != SCHEMA_DRAFT
            or _contains_remote_reference(decoded)
        ):
            raise ValueError("schema locality contract failed")
        Draft202012Validator.check_schema(decoded)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, SchemaError, ValueError) as error:
        raise _schema_error() from error
    return decoded


def _json_pointer(parts: object) -> str:
    encoded: list[str] = []
    for part in parts:  # type: ignore[union-attr]
        token = str(part).replace("~", "~0").replace("/", "~1")
        encoded.append(token)
    return "" if not encoded else "/" + "/".join(encoded)


def _diagnostic_sort_key(
    diagnostic: ValidationDiagnostic,
) -> tuple[str, str, str]:
    return diagnostic.pointer, diagnostic.validator, diagnostic.message


def validate_state_file(
    relative_path: str,
    payload: bytes,
) -> tuple[ValidationDiagnostic, ...]:
    """Parse and validate one canonical state payload without filesystem mutation."""

    schema_name = STATE_SCHEMA_BY_PATH.get(relative_path)
    if schema_name is None:
        raise BaToolsError(
            code="STATE_TARGET_UNKNOWN",
            message="A required workspace state target is not recognized.",
            remediation=("Use the declared workspace state targets and retry.",),
        )
    try:
        instance = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return (
            ValidationDiagnostic(
                path=relative_path,
                pointer="",
                validator="parse",
                message="File is not valid UTF-8 JSON.",
            ),
        )

    validator = Draft202012Validator(load_schema(schema_name))
    diagnostics: list[ValidationDiagnostic] = []
    for error in validator.iter_errors(instance):
        pointer = _json_pointer(error.absolute_path)
        message = error.message
        if pointer == "/schema_version" and error.validator == "const":
            message = "Unsupported schema_version; expected 1."
        diagnostics.append(
            ValidationDiagnostic(
                path=relative_path,
                pointer=pointer,
                validator=str(error.validator),
                message=message,
            )
        )
    return tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def _duplicate_key(relative_path: str) -> str:
    portable = PurePosixPath(relative_path).as_posix()
    return os.path.normcase(portable)


def classify_workspace_state(
    root: ResolvedRepoRoot,
    *,
    required_files: tuple[str, ...] = DEFAULT_REQUIRED_STATE_FILES,
) -> WorkspaceState:
    """Classify all declared targets in order without creating or changing files."""

    duplicate_keys = tuple(_duplicate_key(relative) for relative in required_files)
    if len(set(duplicate_keys)) != len(duplicate_keys):
        raise BaToolsError(
            code="DUPLICATE_STATE_TARGET",
            message="Required workspace state targets contain a duplicate path.",
            remediation=("Correct the required target configuration and retry.",),
        )

    targets = tuple(resolve_business_path(root, relative) for relative in required_files)
    state_directory = resolve_business_path(root, ".ba-ops")
    present: list[str] = []
    missing: list[str] = []
    diagnostics: list[ValidationDiagnostic] = []

    for relative, target in zip(required_files, targets, strict=True):
        if not os.path.lexists(target.path):
            missing.append(relative)
            continue
        present.append(relative)
        if not target.path.is_file():
            diagnostics.append(
                ValidationDiagnostic(
                    path=relative,
                    pointer="",
                    validator="file",
                    message="Required state path is not a regular file.",
                )
            )
            continue
        try:
            payload = target.path.read_bytes()
        except OSError as error:
            raise BaToolsError(
                code="STATE_READ_FAILED",
                message="Existing workspace state could not be read safely.",
                remediation=("Check repository permissions, then retry.",),
            ) from error
        diagnostics.extend(validate_state_file(relative, payload))

    if diagnostics:
        kind = WorkspaceStateKind.INVALID
    elif not present and not os.path.lexists(state_directory.path):
        kind = WorkspaceStateKind.FRESH
    elif not missing:
        kind = WorkspaceStateKind.COMPLETE
    else:
        kind = WorkspaceStateKind.PARTIAL

    return WorkspaceState(
        kind=kind,
        present=tuple(present),
        missing=tuple(missing),
        diagnostics=tuple(diagnostics),
    )
