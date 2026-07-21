"""D-18 atomic publication, durability-fault, and quarantine evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from ba_tools.paths import ResolvedBusinessPath, resolve_business_path, resolve_repo_root
from ba_tools.state import atomic


@dataclass(frozen=True)
class FileSnapshot:
    exists: bool
    payload: bytes | None
    digest: str | None
    mtime_ns: int | None


def _snapshot(path: Path) -> FileSnapshot:
    if not path.exists():
        return FileSnapshot(False, None, None, None)
    payload = path.read_bytes()
    return FileSnapshot(
        True,
        payload,
        hashlib.sha256(payload).hexdigest(),
        path.stat().st_mtime_ns,
    )


def _target(tmp_path: Path, relative: str = ".ba-ops/config.json") -> ResolvedBusinessPath:
    root = resolve_repo_root(tmp_path)
    target = resolve_business_path(root, relative)
    target.path.parent.mkdir(parents=True, exist_ok=True)
    return target


def _temps(target: ResolvedBusinessPath) -> tuple[Path, ...]:
    return tuple(sorted(target.path.parent.glob(f".{target.path.name}.ba-tmp-*")))


def _raise_at(expected: str):
    def fault(step: str) -> None:
        if step == expected:
            raise OSError(f"injected fault at {step}")

    return fault


def test_atomic_create_never_replaces(tmp_path: Path) -> None:
    """D-18 create-only publication preserves existing canonical bytes and mtime."""

    target = _target(tmp_path)
    target.path.write_bytes(b"previous-complete")
    before = _snapshot(target.path)

    with pytest.raises(FileExistsError):
        atomic.atomic_create(target, b"new-complete")

    assert _snapshot(target.path) == before
    assert _temps(target) == ()


def test_atomic_replace_is_complete(tmp_path: Path) -> None:
    """D-18 replacement publishes all new bytes and leaks no temporary file."""

    target = _target(tmp_path)
    target.path.write_bytes(b"previous-complete")
    payload = ("Tiếng Việt — " * 4096).encode()

    atomic.atomic_replace(target, payload)

    assert target.path.read_bytes() == payload
    assert hashlib.sha256(target.path.read_bytes()).digest() == hashlib.sha256(payload).digest()
    assert _temps(target) == ()


@pytest.mark.parametrize(
    "step",
    [
        "before_write",
        "after_write",
        "after_flush",
        "after_fsync",
        "before_replace",
        "after_replace",
        "before_cleanup",
        "after_cleanup",
        "before_parent_sync",
        "after_parent_sync",
    ],
    ids=lambda step: f"D-18-replace-{step}",
)
def test_fault_preserves_previous_canonical(tmp_path: Path, step: str) -> None:
    """Every replace fault leaves a previous-or-new complete canonical file."""

    target = _target(tmp_path)
    previous = b"previous-complete"
    replacement = b"replacement-complete"
    target.path.write_bytes(previous)
    before = _snapshot(target.path)

    with pytest.raises(OSError, match="injected fault"):
        atomic.atomic_replace(target, replacement, fault=_raise_at(step))

    after = _snapshot(target.path)
    assert after.exists
    assert after.payload in {previous, replacement}
    assert after.digest in {
        hashlib.sha256(previous).hexdigest(),
        hashlib.sha256(replacement).hexdigest(),
    }
    if after.payload == previous:
        assert after == before
    for temporary in _temps(target):
        assert temporary.read_bytes() in {b"", replacement}


@pytest.mark.parametrize(
    "step",
    [
        "before_write",
        "after_write",
        "after_flush",
        "after_fsync",
        "before_link",
        "after_link",
        "before_cleanup",
        "after_cleanup",
        "before_parent_sync",
        "after_parent_sync",
    ],
    ids=lambda step: f"D-18-create-{step}",
)
def test_create_fault_never_exposes_partial_canonical(tmp_path: Path, step: str) -> None:
    """Create faults leave canonical absent or fully complete and retain recognizable evidence."""

    target = _target(tmp_path)
    payload = b"complete-create-payload"

    with pytest.raises(OSError, match="injected fault"):
        atomic.atomic_create(target, payload, fault=_raise_at(step))

    if target.path.exists():
        assert target.path.read_bytes() == payload
    for temporary in _temps(target):
        assert temporary.read_bytes() in {b"", payload}


def test_repeated_publication_yields_canonical_bytes_without_temp_leak(tmp_path: Path) -> None:
    """D-18 successful repeated replacement is idempotently complete."""

    target = _target(tmp_path)
    payload = b"same-complete-canonical"

    atomic.atomic_replace(target, payload)
    first = _snapshot(target.path)
    atomic.atomic_replace(target, payload)

    assert _snapshot(target.path).payload == first.payload
    assert _snapshot(target.path).digest == first.digest
    assert _temps(target) == ()


def test_abandoned_temp_is_quarantined_not_promoted(tmp_path: Path) -> None:
    """D-18 abandoned evidence moves to quarantine and never becomes canonical input."""

    target = _target(tmp_path)
    abandoned = target.path.parent / f".{target.path.name}.ba-tmp-crashed-writer"
    abandoned.write_bytes(b"partial-or-untrusted-evidence")

    records = atomic.quarantine_abandoned_temps(target.root)

    assert len(records) == 1
    record = records[0]
    assert record.target_relative == target.relative
    assert record.source_relative == abandoned.relative_to(tmp_path).as_posix()
    assert record.quarantine_relative.startswith(".ba-ops/quarantine/atomic/")
    quarantined = tmp_path / Path(*record.quarantine_relative.split("/"))
    assert quarantined.read_bytes() == b"partial-or-untrusted-evidence"
    assert not abandoned.exists()
    assert not target.path.exists()


def test_quarantine_preserves_bytes_and_identity_without_overwrite(tmp_path: Path) -> None:
    """D-18/D-19 quarantine collisions retain both byte-distinct evidence files."""

    target = _target(tmp_path, "nested/state.json")
    abandoned = target.path.parent / f".{target.path.name}.ba-tmp-repeat"
    first_payload = b"first-evidence"
    second_payload = b"second-evidence"
    abandoned.write_bytes(first_payload)
    first = atomic.quarantine_abandoned_temps(target.root)[0]
    abandoned.write_bytes(second_payload)
    second = atomic.quarantine_abandoned_temps(target.root)[0]

    first_path = tmp_path / Path(*first.quarantine_relative.split("/"))
    second_path = tmp_path / Path(*second.quarantine_relative.split("/"))
    assert first.target_relative == second.target_relative == target.relative
    assert first_path != second_path
    assert first_path.read_bytes() == first_payload
    assert second_path.read_bytes() == second_payload
    assert not target.path.exists()


@pytest.mark.parametrize(
    "step",
    ["before_quarantine_link", "after_quarantine_link", "before_quarantine_cleanup"],
    ids=lambda step: f"D-18-quarantine-{step}",
)
def test_quarantine_fault_retains_recovery_evidence(tmp_path: Path, step: str) -> None:
    """A quarantine fault cannot promote or destroy the only evidence copy."""

    target = _target(tmp_path)
    abandoned = target.path.parent / f".{target.path.name}.ba-tmp-fault"
    payload = b"recoverable-evidence"
    abandoned.write_bytes(payload)

    with pytest.raises(OSError, match="injected fault"):
        atomic.quarantine_abandoned_temps(target.root, fault=_raise_at(step))

    evidence = tuple(
        path
        for path in tmp_path.rglob("*")
        if path.is_file() and path.read_bytes() == payload
    )
    assert evidence
    assert all(path != target.path for path in evidence)
    assert not target.path.exists()
