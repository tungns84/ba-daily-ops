"""Same-directory, synced, create-only state publication."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from ba_tools.contracts import canonical_json_bytes
from ba_tools.errors import BaToolsError
from ba_tools.paths import (
    ResolvedBusinessPath,
    ResolvedRepoRoot,
    resolve_business_path,
)

FaultHook = Callable[[str], None]
_TEMP_PATTERN = re.compile(
    r"^\.(?P<target>.+)\.ba-tmp-(?P<token>[A-Za-z0-9][A-Za-z0-9._-]*)$"
)


@dataclass(frozen=True, slots=True)
class AbandonedTemp:
    """Repo-relative identity of one quarantined atomic-write temporary."""

    source_relative: str
    target_relative: str
    quarantine_relative: str


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


def _fault(fault: FaultHook | None, step: str) -> None:
    if fault is not None:
        fault(step)


def _revalidate_target(target: ResolvedBusinessPath) -> None:
    current = resolve_business_path(
        target.root,
        target.relative,
        policy=target.policy,
    )
    if current.path != target.path:
        raise BaToolsError(
            code="PATH_REDIRECTED",
            message="The requested path is outside the repository or uses a disallowed form.",
            remediation=("Retry after removing filesystem redirects from the business path.",),
        )


def prepare_temp(
    target: ResolvedBusinessPath,
    payload: bytes,
    *,
    fault: FaultHook | None = None,
) -> Path:
    """Write and sync a secure temporary file beside its canonical target."""

    _revalidate_target(target)
    descriptor, raw_path = tempfile.mkstemp(
        dir=target.path.parent,
        prefix=f".{target.path.name}.ba-tmp-",
    )
    temporary = Path(raw_path)
    with os.fdopen(descriptor, "wb") as handle:
        _fault(fault, "before_write")
        handle.write(payload)
        _fault(fault, "after_write")
        handle.flush()
        _fault(fault, "after_flush")
        os.fsync(handle.fileno())
        _fault(fault, "after_fsync")
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


def _sync_publication_parent(
    target: ResolvedBusinessPath,
    fault: FaultHook | None,
) -> None:
    _fault(fault, "before_parent_sync")
    sync_parent_directory(target.path.parent)
    _fault(fault, "after_parent_sync")


def atomic_create(
    target: ResolvedBusinessPath,
    payload: bytes,
    *,
    fault: FaultHook | None = None,
) -> None:
    """Publish complete bytes without ever replacing an existing target."""

    temporary = prepare_temp(target, payload, fault=fault)
    _fault(fault, "before_link")
    try:
        os.link(temporary, target.path, follow_symlinks=False)
    except FileExistsError:
        temporary.unlink(missing_ok=True)
        raise
    _fault(fault, "after_link")
    _fault(fault, "before_cleanup")
    temporary.unlink()
    _fault(fault, "after_cleanup")
    _sync_publication_parent(target, fault)


def atomic_replace(
    target: ResolvedBusinessPath,
    payload: bytes,
    *,
    fault: FaultHook | None = None,
) -> None:
    """Atomically replace a canonical target with fully synced bytes."""

    temporary = prepare_temp(target, payload, fault=fault)
    _fault(fault, "before_replace")
    os.replace(temporary, target.path)
    _fault(fault, "after_replace")
    _fault(fault, "before_cleanup")
    temporary.unlink(missing_ok=True)
    _fault(fault, "after_cleanup")
    _sync_publication_parent(target, fault)


def _is_redirect(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise BaToolsError(
            code="PATH_INSPECTION_FAILED",
            message="The requested path could not be inspected safely.",
            remediation=("Check repository permissions and retry.",),
        ) from error
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _iter_abandoned_temps(root: ResolvedRepoRoot) -> Iterator[tuple[Path, str, str, str]]:
    quarantine_prefix = ".ba-ops/quarantine"
    for current_text, directories, filenames in os.walk(root.path, followlinks=False):
        current = Path(current_text)
        current_relative = current.relative_to(root.path).as_posix()
        if current_relative == quarantine_prefix or current_relative.startswith(
            f"{quarantine_prefix}/"
        ):
            directories[:] = []
            continue

        safe_directories: list[str] = []
        for name in sorted(directories):
            directory = current / name
            relative = directory.relative_to(root.path).as_posix()
            if relative == quarantine_prefix or _is_redirect(directory):
                continue
            safe_directories.append(name)
        directories[:] = safe_directories

        for name in sorted(filenames):
            match = _TEMP_PATTERN.fullmatch(name)
            if match is None:
                continue
            temporary = current / name
            if _is_redirect(temporary) or not temporary.is_file():
                continue
            target_path = current / match.group("target")
            target_relative = target_path.relative_to(root.path).as_posix()
            resolve_business_path(root, target_relative)
            yield (
                temporary,
                temporary.relative_to(root.path).as_posix(),
                target_relative,
                match.group("token"),
            )


def _unused_quarantine_target(
    root: ResolvedRepoRoot,
    target_relative: str,
    token: str,
) -> ResolvedBusinessPath:
    digest = hashlib.sha256(target_relative.encode("utf-8")).hexdigest()[:16]
    target_name = Path(*target_relative.split("/")).name
    base = f"{digest}-{target_name}.ba-tmp-{token}"
    for index in range(10_000):
        name = base if index == 0 else f"{base}.{index}"
        candidate = resolve_business_path(root, f".ba-ops/quarantine/atomic/{name}")
        if not os.path.lexists(candidate.path):
            return candidate
    raise BaToolsError(
        code="ATOMIC_QUARANTINE_FULL",
        message="Atomic-write evidence could not be quarantined without overwrite.",
        remediation=("Inspect the workspace quarantine, then retry.",),
    )


def quarantine_abandoned_temps(
    root: ResolvedRepoRoot,
    *,
    fault: FaultHook | None = None,
) -> tuple[AbandonedTemp, ...]:
    """Move recognizable temporary files to quarantine without promotion or overwrite."""

    abandoned = tuple(sorted(_iter_abandoned_temps(root), key=lambda item: item[1]))
    if not abandoned:
        return ()

    quarantine = resolve_business_path(root, ".ba-ops/quarantine/atomic")
    quarantine.path.mkdir(mode=0o700, parents=True, exist_ok=True)
    records: list[AbandonedTemp] = []
    for temporary, source_relative, target_relative, token in abandoned:
        destination = _unused_quarantine_target(root, target_relative, token)
        _fault(fault, "before_quarantine_link")
        os.link(temporary, destination.path, follow_symlinks=False)
        _fault(fault, "after_quarantine_link")
        _fault(fault, "before_quarantine_cleanup")
        temporary.unlink()
        _fault(fault, "after_quarantine_cleanup")
        sync_parent_directory(destination.path.parent)
        if temporary.parent != destination.path.parent:
            sync_parent_directory(temporary.parent)
        records.append(
            AbandonedTemp(
                source_relative=source_relative,
                target_relative=target_relative,
                quarantine_relative=destination.relative,
            )
        )
    return tuple(records)
