"""D-15 canonical defaults and their local schema contract."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ba_tools.errors import BaToolsError

EXPECTED_DEFAULTS = {
    "config.json": b'{"profile":"light","schema_version":1}\n',
    "coverage-policy.json": (
        b'{"per_req":{},"profile":"light",'
        b'"required_artifact_kinds":["srs","flow","mockup"],'
        b'"schema_version":1,"waivers":[]}\n'
    ),
    "business-goals.json": b'{"business_goals":[],"schema_version":1}\n',
}
SCHEMA_BY_DEFAULT = {
    "config.json": "config.schema.json",
    "coverage-policy.json": "coverage-policy.schema.json",
    "business-goals.json": "business-goals.schema.json",
}


def _default_bytes(name: str) -> bytes:
    return (
        resources.files("ba_tools")
        .joinpath("state", "resources", "defaults", name)
        .read_bytes()
    )


def test_exact_default_payload_bytes() -> None:
    """D-15: packaged defaults are exact canonical UTF-8 resources."""

    assert {name: _default_bytes(name) for name in EXPECTED_DEFAULTS} == EXPECTED_DEFAULTS


def test_defaults_validate_against_local_schemas() -> None:
    """D-15: each default validates against exactly its matching local schema."""

    from ba_tools.state.validation import load_schema

    for default_name, schema_name in SCHEMA_BY_DEFAULT.items():
        schema = load_schema(schema_name)
        Draft202012Validator.check_schema(schema)
        payload = json.loads(_default_bytes(default_name))
        assert list(Draft202012Validator(schema).iter_errors(payload)) == []


def test_empty_business_goals_are_valid() -> None:
    """D-15: an empty business-goal registry is valid and intentionally populated."""

    from ba_tools.state.validation import validate_state_file

    diagnostics = validate_state_file(
        ".ba-ops/business-goals.json",
        EXPECTED_DEFAULTS["business-goals.json"],
    )

    assert diagnostics == ()


def test_defaults_contain_no_business_inference() -> None:
    """D-15: initialization ships policy only and invents no business content."""

    decoded = {
        name: json.loads(payload)
        for name, payload in EXPECTED_DEFAULTS.items()
    }

    assert decoded["business-goals.json"]["business_goals"] == []
    assert decoded["coverage-policy.json"]["per_req"] == {}
    assert decoded["coverage-policy.json"]["waivers"] == []
    combined = b"".join(EXPECTED_DEFAULTS.values()).lower()
    assert b"sample" not in combined
    assert b"example" not in combined
    assert b"placeholder" not in combined


def test_schema_loader_rejects_remote_references(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """D-14: packaged schemas cannot introduce remote resolution."""

    from ba_tools.state import validation

    schema_root = tmp_path / "ba_tools" / "state" / "resources" / "schemas"
    schema_root.mkdir(parents=True)
    (schema_root / "config.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": "https://example.invalid/remote.schema.json",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(validation.resources, "files", lambda _package: tmp_path / "ba_tools")

    with pytest.raises(BaToolsError) as captured:
        validation.load_schema("config.schema.json")

    assert captured.value.code == "PACKAGED_SCHEMA_INVALID"
