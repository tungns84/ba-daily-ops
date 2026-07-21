"""Schema-backed initialization and explicit repair of canonical workspace state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedBusinessPath, ResolvedRepoRoot, resolve_business_path
from ba_tools.state.atomic import (
    AbandonedTemp,
    atomic_create,
    canonical_file_bytes,
    quarantine_abandoned_temps,
)
from ba_tools.state.locking import WorkspaceLock
from ba_tools.state.validation import (
    WorkspaceState,
    WorkspaceStateKind,
    classify_workspace_state,
)

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
    quarantined: tuple[AbandonedTemp, ...]


class StateTransition(StrEnum):
    """Allowed state mutations selected only after complete classification."""

    INITIALIZE = "initialize"
    NOOP = "noop"
    REPAIR = "repair"


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


def _invalid_state_error(state: WorkspaceState) -> BaToolsError:
    return BaToolsError(
        code="STATE_SCHEMA_INVALID",
        message="Existing state is invalid and was preserved.",
        details=tuple(diagnostic.as_dict() for diagnostic in state.diagnostics),
        remediation=("Correct the reported fields, then retry.",),
    )


def classify_then_transition(
    state: WorkspaceState,
    *,
    repair: bool,
) -> StateTransition:
    """Select one explicit transition without touching the filesystem."""

    if state.kind is WorkspaceStateKind.INVALID:
        raise _invalid_state_error(state)
    if state.kind is WorkspaceStateKind.COMPLETE:
        return StateTransition.NOOP
    if state.kind is WorkspaceStateKind.FRESH:
        return StateTransition.INITIALIZE
    if repair:
        return StateTransition.REPAIR
    raise _state_error(
        "STATE_INCOMPLETE",
        "Required workspace files are missing.",
        ("Run init --repair to create missing files only.",),
    )


def run_init(root: ResolvedRepoRoot, *, repair: bool = False) -> InitResult:
    """Classify under one lock, then initialize, repair, or prove a no-op."""

    created: tuple[str, ...] = ()

    with WorkspaceLock(root):
        quarantined = quarantine_abandoned_temps(root)
        state_directory = resolve_business_path(root, ".ba-ops")
        targets = _targets(root)
        state = classify_workspace_state(root, required_files=REQUIRED_STATE_FILES)
        transition = classify_then_transition(state, repair=repair)

        if transition is not StateTransition.NOOP:
            expected_by_path = {
                relative: canonical_file_bytes(relative.rsplit("/", maxsplit=1)[-1])
                for relative in REQUIRED_STATE_FILES
            }
            created = (
                REQUIRED_STATE_FILES
                if transition is StateTransition.INITIALIZE
                else state.missing
            )
            try:
                if transition is StateTransition.INITIALIZE:
                    state_directory.path.mkdir(mode=0o700)
                    targets = _targets(root)
                target_by_relative = {target.relative: target for target in targets}
                for relative in created:
                    atomic_create(target_by_relative[relative], expected_by_path[relative])
            except BaToolsError:
                raise
            except (FileExistsError, OSError) as error:
                raise _state_error(
                    "STATE_WRITE_FAILED",
                    "Workspace state could not be created safely.",
                    ("Check repository permissions and state, then retry.",),
                ) from error

        final_state = classify_workspace_state(root, required_files=REQUIRED_STATE_FILES)
        if final_state.kind is not WorkspaceStateKind.COMPLETE:
            if final_state.kind is WorkspaceStateKind.INVALID:
                raise _invalid_state_error(final_state)
            raise _state_error(
                "STATE_READ_FAILED",
                "Workspace state could not be verified after publication.",
                ("Check repository permissions and state, then retry.",),
            )

        expected_by_path = {
            relative: canonical_file_bytes(relative.rsplit("/", maxsplit=1)[-1])
            for relative in created
        }
        target_by_relative = {target.relative: target for target in _targets(root)}
        for relative in created:
            _read_exact(target_by_relative[relative], expected_by_path[relative])

    return InitResult(
        changed=bool(created or quarantined),
        created=created,
        quarantined=quarantined,
    )
