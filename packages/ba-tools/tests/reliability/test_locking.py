"""D-16/D-17/D-19 native workspace-lock reliability evidence."""

from __future__ import annotations

import json
import multiprocessing
import os
import queue
import socket
import time
from pathlib import Path
from typing import Any

import pytest
from filelock import SoftFileLock

from ba_tools.errors import BaToolsError
from ba_tools.paths import resolve_repo_root
from ba_tools.state import locking


def _hold_workspace(
    root_text: str,
    ready: Any,
    release: Any,
    *,
    crash: bool = False,
) -> None:
    root = resolve_repo_root(root_text)
    with locking.WorkspaceLock(root):
        ready.set()
        if crash:
            os._exit(0)
        if not release.wait(timeout=15):
            raise RuntimeError("bounded holder release event was not signaled")


def _wait_for_workspace(root_text: str, ready: Any, acquired: Any) -> None:
    root = resolve_repo_root(root_text)
    ready.set()
    started = time.monotonic()
    with locking.WorkspaceLock(root):
        acquired.put(time.monotonic() - started)


def _spawn_context() -> multiprocessing.context.BaseContext:
    return multiprocessing.get_context("spawn")


def _owner_bytes(pid: int, hostname: str, owner_id: str = "prior-owner") -> bytes:
    return (
        json.dumps(
            {
                "hostname": hostname,
                "owner_id": owner_id,
                "pid": pid,
                "schema_version": 1,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _lock_for(tmp_path: Path, timeout: float = 0.2) -> locking.WorkspaceLock:
    return locking.WorkspaceLock(resolve_repo_root(tmp_path), timeout_seconds=timeout)


def test_native_workspace_lock_has_owner_metadata_only_while_held(tmp_path: Path) -> None:
    """D-19 uses one native lock and an exact owner sidecar lifecycle."""

    workspace_lock = _lock_for(tmp_path)
    assert not isinstance(workspace_lock._lock, SoftFileLock)  # noqa: SLF001
    assert workspace_lock.lock_path.name.endswith(".ba-ops.lock")
    assert workspace_lock.owner_path.name.endswith(".ba-ops.lock.owner.json")
    assert not workspace_lock.owner_path.exists()

    with workspace_lock:
        owner = json.loads(workspace_lock.owner_path.read_text(encoding="utf-8"))
        assert owner == {
            "hostname": socket.gethostname(),
            "owner_id": workspace_lock.owner.owner_id,
            "pid": os.getpid(),
            "schema_version": 1,
        }

    assert workspace_lock.lock_path.exists()
    assert not workspace_lock.owner_path.exists()


def test_lock_timeout_is_bounded(tmp_path: Path) -> None:
    """D-16 production timeout is near five seconds and preserves owner evidence."""

    context = _spawn_context()
    ready = context.Event()
    release = context.Event()
    holder = context.Process(target=_hold_workspace, args=(str(tmp_path), ready, release))
    holder.start()
    assert ready.wait(timeout=10), "holder did not acquire the native lock"
    contender = locking.WorkspaceLock(resolve_repo_root(tmp_path))
    before = contender.owner_path.read_bytes()
    started = time.monotonic()
    try:
        with pytest.raises(BaToolsError) as captured:
            with contender:
                raise AssertionError("contender acquired a held workspace lock")
        elapsed = time.monotonic() - started
        assert captured.value.code == "WORKSPACE_LOCK_TIMEOUT"
        assert 4.5 <= elapsed <= 7.5
        assert contender.owner_path.read_bytes() == before
    finally:
        release.set()
        holder.join(timeout=10)
        if holder.is_alive():
            holder.kill()
            holder.join(timeout=5)
    assert holder.exitcode == 0


def test_concurrent_writers_are_serialized(tmp_path: Path) -> None:
    """D-19 a waiter cannot enter until the current native owner releases."""

    context = _spawn_context()
    ready = context.Event()
    release = context.Event()
    waiter_ready = context.Event()
    acquired = context.Queue()
    holder = context.Process(target=_hold_workspace, args=(str(tmp_path), ready, release))
    holder.start()
    assert ready.wait(timeout=10)
    waiter = context.Process(
        target=_wait_for_workspace,
        args=(str(tmp_path), waiter_ready, acquired),
    )
    waiter.start()
    try:
        assert waiter_ready.wait(timeout=10)
        with pytest.raises(queue.Empty):
            acquired.get(timeout=0.25)
        release.set()
        waited = acquired.get(timeout=10)
        assert waited >= 0.20
    finally:
        release.set()
        holder.join(timeout=10)
        waiter.join(timeout=10)
        for process in (holder, waiter):
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
    assert holder.exitcode == waiter.exitcode == 0


def test_crashed_holder_releases_native_lock(tmp_path: Path) -> None:
    """D-17 a process crash leaves evidence but releases kernel ownership."""

    context = _spawn_context()
    ready = context.Event()
    unused_release = context.Event()
    holder = context.Process(
        target=_hold_workspace,
        args=(str(tmp_path), ready, unused_release),
        kwargs={"crash": True},
    )
    holder.start()
    assert ready.wait(timeout=10)
    holder.join(timeout=10)
    assert not holder.is_alive()
    assert holder.exitcode == 0

    successor = _lock_for(tmp_path)
    stale = successor.owner_path.read_bytes()
    assert json.loads(stale)["pid"] == holder.pid
    with successor:
        current = json.loads(successor.owner_path.read_bytes())
        assert current["pid"] == os.getpid()
        assert current["owner_id"] != json.loads(stale)["owner_id"]
    assert not successor.owner_path.exists()


def test_only_dead_same_host_owner_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-17 provably dead same-host evidence changes only after native acquisition."""

    workspace_lock = _lock_for(tmp_path)
    workspace_lock.owner_path.parent.mkdir(parents=True, exist_ok=True)
    stale = _owner_bytes(424242, socket.gethostname())
    workspace_lock.owner_path.write_bytes(stale)
    monkeypatch.setattr(
        locking,
        "probe_process_liveness",
        lambda _pid: locking.ProcessLiveness.DEAD,
    )
    assert workspace_lock.owner_path.read_bytes() == stale

    with workspace_lock:
        assert workspace_lock.owner_path.read_bytes() != stale
        assert json.loads(workspace_lock.owner_path.read_bytes())["pid"] == os.getpid()

    assert not workspace_lock.owner_path.exists()


@pytest.mark.parametrize(
    ("owner_bytes", "liveness"),
    [
        pytest.param(
            _owner_bytes(os.getpid(), socket.gethostname()),
            "LIVE",
            id="D-17-live-owner",
        ),
        pytest.param(
            _owner_bytes(424242, "foreign.example.invalid"),
            "DEAD",
            id="D-17-foreign-owner",
        ),
        pytest.param(
            _owner_bytes(424242, socket.gethostname()),
            "UNKNOWN",
            id="D-17-unknown-owner",
        ),
        pytest.param(
            _owner_bytes(424242, socket.gethostname()),
            "ACCESS_DENIED",
            id="D-17-access-denied-owner",
        ),
        pytest.param(b"{malformed-json", "DEAD", id="D-17-malformed-owner"),
    ],
)
def test_ambiguous_owner_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    owner_bytes: bytes,
    liveness: str,
) -> None:
    """Live, foreign, unknown, denied, and malformed owner evidence is immutable."""

    workspace_lock = _lock_for(tmp_path)
    workspace_lock.owner_path.parent.mkdir(parents=True, exist_ok=True)
    workspace_lock.owner_path.write_bytes(owner_bytes)
    monkeypatch.setattr(
        locking,
        "probe_process_liveness",
        lambda _pid: getattr(locking.ProcessLiveness, liveness),
    )

    with pytest.raises(BaToolsError) as captured:
        with workspace_lock:
            raise AssertionError("ambiguous owner evidence was accepted")

    assert captured.value.code == "WORKSPACE_LOCK_OWNER_AMBIGUOUS"
    assert workspace_lock.owner_path.read_bytes() == owner_bytes


def test_unreadable_owner_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-17 unreadable owner evidence remains byte-identical."""

    workspace_lock = _lock_for(tmp_path)
    workspace_lock.owner_path.parent.mkdir(parents=True, exist_ok=True)
    prior = _owner_bytes(424242, socket.gethostname())
    workspace_lock.owner_path.write_bytes(prior)
    original_read_bytes = Path.read_bytes

    def denied(path: Path) -> bytes:
        if path == workspace_lock.owner_path:
            raise PermissionError("injected owner metadata denial")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", denied)
    with pytest.raises(BaToolsError) as captured:
        with workspace_lock:
            raise AssertionError("unreadable owner evidence was accepted")
    assert captured.value.code == "WORKSPACE_LOCK_OWNER_AMBIGUOUS"

    monkeypatch.undo()
    assert workspace_lock.owner_path.read_bytes() == prior


def test_interruption_releases_owner_metadata_and_native_lock(tmp_path: Path) -> None:
    """D-16 interruption cleans current ownership and permits the next writer."""

    first = _lock_for(tmp_path)
    with pytest.raises(KeyboardInterrupt):
        with first:
            assert first.owner_path.exists()
            raise KeyboardInterrupt

    assert not first.owner_path.exists()
    with _lock_for(tmp_path):
        pass
