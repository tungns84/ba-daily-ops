"""Same-directory, synced, create-only state publication."""

from __future__ import annotations

import json
import os
import tempfile
from importlib import resources
from pathlib import Path

from ba_tools.contracts import canonical_json_bytes
from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedBusinessPath


def canonical_file_bytes(resource_name: str) -> bytes:
    """Load an exact packaged default after proving its canonical byte form."""

    source = (
        resources.files("ba_tools")
        .joinpath("state")
        .joinpath("resources")
        .joinpath("defaults")
        .joinpath(resource_name)
    )
    payload = source.read_bytes()
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BaToolsError(
            code="PACKAGED_DEFAULT_INVALID",
            message="A packaged workspace default is invalid.",
            remediation=("Reinstall the exact ba-tools package and retry.",),
        ) from error
    if payload != canonical_json_bytes(decoded):
        raise BaToolsError(
            code="PACKAGED_DEFAULT_INVALID",
            message="A packaged workspace default is not canonical.",
            remediation=("Reinstall the exact ba-tools package and retry.",),
        )
    return payload


def prepare_temp(target: ResolvedBusinessPath, payload: bytes) -> Path:
    """Write and sync a secure temporary file beside its canonical target."""

    descriptor, raw_path = tempfile.mkstemp(
        dir=target.path.parent,
        prefix=f".{target.path.name}.ba-tmp-",
    )
    temporary = Path(raw_path)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def sync_parent_directory(directory: Path) -> None:
    """Sync directory metadata on platforms that expose directory descriptors."""

    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_create(target: ResolvedBusinessPath, payload: bytes) -> None:
    """Publish complete bytes without ever replacing an existing target."""

    temporary = prepare_temp(target, payload)
    try:
        os.link(temporary, target.path, follow_symlinks=False)
        temporary.unlink()
        sync_parent_directory(target.path.parent)
    finally:
        temporary.unlink(missing_ok=True)
