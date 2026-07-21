"""Fresh and idempotent initialization of canonical workspace state."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedBusinessPath, ResolvedRepoRoot, resolve_business_path
from ba_tools.state.atomic import atomic_create, canonical_file_bytes
from ba_tools.state.locking import WorkspaceLock

REQUIRED_STATE_FILES = (
    ".ba-ops/config.json",
    ".ba-ops/coverage-policy.json",
    ".ba-ops/business-goals.json",
)


@dataclass(frozen=True, slots=True)
class InitResult:
    """Mechanical facts returned by initialization."""

    changed: bool
    created: tuple[str, ...]


def _targets(root: ResolvedRepoRoot) -> tuple[ResolvedBusinessPath, ...]:
    return tuple(resolve_business_path(root, relative) for relative in REQUIRED_STATE_FILES)


def _state_error(
    code: str,
    message: str,
    remediation: tuple[str, ...],
) -> BaToolsError:
    return BaToolsError(
        code=code,
        message=message,
        remediation=remediation,
    )


def _read_exact(target: ResolvedBusinessPath, expected: bytes) -> None:
    try:
        actual = target.path.read_bytes()
    except OSError as error:
        raise _state_error(
            "STATE_READ_FAILED",
            "Existing workspace state could not be read safely.",
            ("Check repository permissions, then retry.",),
        ) from error
    if actual != expected:
        raise _state_error(
            "STATE_INVALID",
            "Existing state is invalid and was preserved.",
            ("Correct the existing workspace file, then retry.",),
        )


def run_init(root: ResolvedRepoRoot) -> InitResult:
    """Create the three packaged defaults or prove an exact no-op rerun."""

    expected_by_path = {
        relative: canonical_file_bytes(relative.rsplit("/", maxsplit=1)[-1])
        for relative in REQUIRED_STATE_FILES
    }

    with WorkspaceLock(root):
        state_directory = resolve_business_path(root, ".ba-ops")
        targets = _targets(root)
        present = tuple(os.path.lexists(target.path) for target in targets)

        if all(present):
            for target in targets:
                if not target.path.is_file():
                    raise _state_error(
                        "STATE_INVALID",
                        "Existing state is invalid and was preserved.",
                        ("Correct the existing workspace file, then retry.",),
                    )
                _read_exact(target, expected_by_path[target.relative])
            return InitResult(changed=False, created=())

        if any(present) or os.path.lexists(state_directory.path):
            raise _state_error(
                "STATE_INCOMPLETE",
                "Required workspace files are missing.",
                ("Run init --repair to create missing files only.",),
            )

        try:
            state_directory.path.mkdir(mode=0o700)
            targets = _targets(root)
            for target in targets:
                atomic_create(target, expected_by_path[target.relative])
            for target in targets:
                _read_exact(target, expected_by_path[target.relative])
        except BaToolsError:
            raise
        except (FileExistsError, OSError) as error:
            raise _state_error(
                "STATE_WRITE_FAILED",
                "Workspace state could not be created safely.",
                ("Check repository permissions and state, then retry.",),
            ) from error

    return InitResult(changed=True, created=REQUIRED_STATE_FILES)
