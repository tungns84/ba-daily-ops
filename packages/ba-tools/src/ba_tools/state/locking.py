"""Bounded native workspace locking."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from types import TracebackType

from filelock import FileLock, SoftFileLock, Timeout

from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedRepoRoot

LOCK_TIMEOUT_SECONDS = 5.0


def _lock_path(root: ResolvedRepoRoot) -> Path:
    """Return a stable per-workspace runtime lock without polluting durable state."""

    identity = os.path.normcase(str(root.path)).encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()
    lock_directory = Path(tempfile.gettempdir()) / "ba-tools-locks"
    lock_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if lock_directory.is_symlink():
        raise BaToolsError(
            code="NATIVE_LOCK_UNAVAILABLE",
            message="The workspace lock could not be established safely.",
            remediation=("Retry after checking local temporary-directory permissions.",),
        )
    return lock_directory / f"{digest}.ba-ops.lock"


class WorkspaceLock:
    """Hold one native lock for an entire workspace mutation."""

    def __init__(
        self,
        root: ResolvedRepoRoot,
        timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.lock_path = _lock_path(root)
        self._lock = FileLock(self.lock_path, timeout=timeout_seconds)
        if isinstance(self._lock, SoftFileLock):
            raise BaToolsError(
                code="NATIVE_LOCK_UNAVAILABLE",
                message="A native workspace lock is unavailable.",
                remediation=("Use a supported local filesystem and retry.",),
            )

    def __enter__(self) -> WorkspaceLock:
        try:
            self._lock.acquire(timeout=self.timeout_seconds)
        except Timeout as error:
            raise BaToolsError(
                code="WORKSPACE_LOCK_TIMEOUT",
                message="Another workspace writer did not finish in time.",
                remediation=("Retry after the other ba-tools command completes.",),
            ) from error
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        self._lock.release()


def acquire_workspace_lock(
    root: ResolvedRepoRoot,
    timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
) -> WorkspaceLock:
    """Construct the workspace lock used by state-changing commands."""

    return WorkspaceLock(root, timeout_seconds=timeout_seconds)
