"""Canonical JSON contracts shared by every ba-tools command."""

from __future__ import annotations

import json
from typing import IO, Any

from ba_tools.errors import BaToolsError

SCHEMA_VERSION = 1


def canonical_json_bytes(payload: object) -> bytes:
    """Serialize one deterministic UTF-8 JSON document with one trailing LF."""

    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def success_envelope(command: str, data: dict[str, object]) -> dict[str, object]:
    """Build the stable success envelope."""

    return {
        "schema_version": SCHEMA_VERSION,
        "ok": True,
        "command": command,
        "data": data,
        "warnings": [],
    }


def error_envelope(command: str, error: BaToolsError) -> dict[str, object]:
    """Build the stable error envelope from allowlisted fields."""

    return {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "command": command,
        "error": {
            "code": error.code,
            "message": error.message,
            "details": list(error.details),
            "remediation": list(error.remediation),
        },
    }


def emit_json(stream: IO[Any], payload: dict[str, object]) -> None:
    """Write exactly one canonical document to a text or binary-backed stream."""

    encoded = canonical_json_bytes(payload)
    binary_stream = getattr(stream, "buffer", None)
    if binary_stream is not None:
        binary_stream.write(encoded)
        binary_stream.flush()
        return

    try:
        stream.write(encoded)
    except TypeError:
        stream.write(encoded.decode("utf-8"))
    stream.flush()
