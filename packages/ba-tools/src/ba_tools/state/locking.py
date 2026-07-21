"""Bounded native workspace locking."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import stat
import tempfile
import uuid
from collections.abc import Callable
from ctypes import wintypes
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from types import TracebackType

from filelock import FileLock, SoftFileLock, Timeout

from ba_tools.contracts import canonical_json_bytes
from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedRepoRoot

LOCK_TIMEOUT_SECONDS = 5.0
OWNER_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class LockOwner:
    """Exact process evidence associated with a held native workspace lock."""

    schema_version: int
    pid: int
    hostname: str
    owner_id: str

    @classmethod
    def from_bytes(cls, payload: bytes) -> LockOwner:
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("owner metadata is not UTF-8 JSON") from error
        if not isinstance(decoded, dict) or set(decoded) != {
            "schema_version",
            "pid",
            "hostname",
            "owner_id",
        }:
            raise ValueError("owner metadata fields are invalid")
        if (
            decoded["schema_version"] != OWNER_SCHEMA_VERSION
            or not isinstance(decoded["pid"], int)
            or isinstance(decoded["pid"], bool)
            or decoded["pid"] <= 0
            or not isinstance(decoded["hostname"], str)
            or not decoded["hostname"]
            or not isinstance(decoded["owner_id"], str)
            or not decoded["owner_id"]
        ):
            raise ValueError("owner metadata values are invalid")
        return cls(**decoded)

    def to_bytes(self) -> bytes:
        return canonical_json_bytes(asdict(self))


class ProcessLiveness(StrEnum):
    """Conservative process-liveness result used by stale-owner recovery."""

    LIVE = "live"
    DEAD = "dead"
    ACCESS_DENIED = "access-denied"
    UNKNOWN = "unknown"


def _windows_kernel32() -> ctypes.WinDLL:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetComputerNameW.argtypes = [
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.GetComputerNameW.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def _local_hostname() -> str:
    if os.name == "nt":
        size = wintypes.DWORD(256)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not _windows_kernel32().GetComputerNameW(
            buffer,
            ctypes.byref(size),
        ):
            raise _lock_error(
                "NATIVE_LOCK_UNAVAILABLE",
                "The local host identity could not be established.",
            )
        return buffer.value
    try:
        return os.uname().nodename
    except (AttributeError, OSError) as error:
        raise _lock_error(
            "NATIVE_LOCK_UNAVAILABLE",
            "The local host identity could not be established.",
        ) from error


def probe_process_liveness(pid: int) -> ProcessLiveness:
    """Determine liveness without treating access denial or unknown states as death."""

    if pid <= 0:
        return ProcessLiveness.UNKNOWN
    if os.name == "nt":
        process_query_limited_information = 0x1000
        error_access_denied = 5
        error_invalid_parameter = 87
        still_active = 259
        kernel32 = _windows_kernel32()
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            error = ctypes.get_last_error()
            if error == error_invalid_parameter:
                return ProcessLiveness.DEAD
            if error == error_access_denied:
                return ProcessLiveness.ACCESS_DENIED
            return ProcessLiveness.UNKNOWN
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return ProcessLiveness.UNKNOWN
            return (
                ProcessLiveness.LIVE
                if exit_code.value == still_active
                else ProcessLiveness.DEAD
            )
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return ProcessLiveness.DEAD
    except PermissionError:
        return ProcessLiveness.ACCESS_DENIED
    except OSError:
        return ProcessLiveness.UNKNOWN
    return ProcessLiveness.LIVE


def _lock_error(code: str, message: str) -> BaToolsError:
    return BaToolsError(
        code=code,
        message=message,
        remediation=("Check local lock evidence and retry only when ownership is known.",),
    )


def _is_redirect(path: Path) -> bool:
    metadata = path.lstat()
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _assert_safe_runtime_path(path: Path) -> None:
    try:
        if os.path.lexists(path) and _is_redirect(path):
            raise _lock_error(
                "NATIVE_LOCK_UNAVAILABLE",
                "The workspace lock path is redirected.",
            )
    except OSError as error:
        raise _lock_error(
            "NATIVE_LOCK_UNAVAILABLE",
            "The workspace lock path could not be inspected safely.",
        ) from error


def _lock_path(root: ResolvedRepoRoot) -> Path:
    """Return a stable per-workspace runtime lock without polluting durable state."""

    identity = os.path.normcase(str(root.path)).encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()
    lock_directory = Path(tempfile.gettempdir()) / "ba-tools-locks"
    lock_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    _assert_safe_runtime_path(lock_directory)
    lock_path = lock_directory / f"{digest}.ba-ops.lock"
    _assert_safe_runtime_path(lock_path)
    lock_path.touch(mode=0o600, exist_ok=True)
    return lock_path


def recover_stale_owner_metadata(
    owner_path: Path,
    native_lock: FileLock,
    *,
    hostname: str | None = None,
    liveness_probe: Callable[[int], ProcessLiveness] | None = None,
) -> LockOwner | None:
    """Remove owner evidence only under native ownership and dead same-host proof."""

    if not native_lock.is_locked:
        raise RuntimeError("stale-owner recovery requires native lock ownership")
    if not os.path.lexists(owner_path):
        return None
    _assert_safe_runtime_path(owner_path)
    try:
        payload = owner_path.read_bytes()
        owner = LockOwner.from_bytes(payload)
    except (OSError, ValueError) as error:
        raise _lock_error(
            "WORKSPACE_LOCK_OWNER_AMBIGUOUS",
            "Existing workspace lock ownership could not be proven stale.",
        ) from error

    current_hostname = _local_hostname() if hostname is None else hostname
    if owner.hostname != current_hostname:
        raise _lock_error(
            "WORKSPACE_LOCK_OWNER_AMBIGUOUS",
            "Existing workspace lock ownership belongs to another host.",
        )
    probe = probe_process_liveness if liveness_probe is None else liveness_probe
    if probe(owner.pid) is not ProcessLiveness.DEAD:
        raise _lock_error(
            "WORKSPACE_LOCK_OWNER_AMBIGUOUS",
            "Existing workspace lock ownership is live or cannot be proven stale.",
        )
    try:
        owner_path.unlink()
    except OSError as error:
        raise _lock_error(
            "WORKSPACE_LOCK_OWNER_AMBIGUOUS",
            "Stale workspace lock ownership could not be recovered safely.",
        ) from error
    return owner


def _write_owner_metadata(owner_path: Path, owner: LockOwner) -> None:
    descriptor, raw_path = tempfile.mkstemp(
        dir=owner_path.parent,
        prefix=f".{owner_path.name}.ba-tmp-",
    )
    temporary = Path(raw_path)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(owner.to_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, owner_path)
    finally:
        temporary.unlink(missing_ok=True)


class WorkspaceLock:
    """Hold one native lock for an entire workspace mutation."""

    def __init__(
        self,
        root: ResolvedRepoRoot,
        timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.lock_path = _lock_path(root)
        self.owner_path = self.lock_path.with_name(f"{self.lock_path.name}.owner.json")
        _assert_safe_runtime_path(self.owner_path)
        self._lock = FileLock(self.lock_path, timeout=timeout_seconds)
        self.owner: LockOwner | None = None
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
        try:
            recover_stale_owner_metadata(self.owner_path, self._lock)
            self.owner = LockOwner(
                schema_version=OWNER_SCHEMA_VERSION,
                pid=os.getpid(),
                hostname=_local_hostname(),
                owner_id=uuid.uuid4().hex,
            )
            _write_owner_metadata(self.owner_path, self.owner)
        except BaseException:
            self._lock.release()
            self.lock_path.touch(mode=0o600, exist_ok=True)
            raise
        return self

    def _remove_current_owner(self) -> None:
        if self.owner is None or not os.path.lexists(self.owner_path):
            return
        _assert_safe_runtime_path(self.owner_path)
        try:
            observed = LockOwner.from_bytes(self.owner_path.read_bytes())
        except (OSError, ValueError) as error:
            raise _lock_error(
                "WORKSPACE_LOCK_OWNER_AMBIGUOUS",
                "Current workspace lock ownership evidence changed unexpectedly.",
            ) from error
        if observed.owner_id != self.owner.owner_id:
            raise _lock_error(
                "WORKSPACE_LOCK_OWNER_AMBIGUOUS",
                "Current workspace lock ownership evidence changed unexpectedly.",
            )
        self.owner_path.unlink()
        self.owner = None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        cleanup_error: BaseException | None = None
        try:
            self._remove_current_owner()
        except BaseException as error:
            cleanup_error = error
        finally:
            self._lock.release()
            self.lock_path.touch(mode=0o600, exist_ok=True)
        if cleanup_error is not None:
            raise cleanup_error


def acquire_workspace_lock(
    root: ResolvedRepoRoot,
    timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
) -> WorkspaceLock:
    """Construct the workspace lock used by state-changing commands."""

    return WorkspaceLock(root, timeout_seconds=timeout_seconds)
