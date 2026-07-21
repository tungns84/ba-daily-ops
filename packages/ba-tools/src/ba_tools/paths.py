"""Repository-root and contained business-path capabilities."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath

from ba_tools.errors import BaToolsError

PATH_MESSAGE = "The requested path is outside the repository or uses a disallowed form."
PATH_REMEDIATION = (
    "Use a repository-relative POSIX path without .., a drive, UNC prefix, or backslashes.",
)


class PathPolicy(StrEnum):
    """Filesystem access policy carried by a resolved business path."""

    STRICT = "strict"


@dataclass(frozen=True, slots=True)
class ResolvedRepoRoot:
    """A repository root resolved exactly once."""

    path: Path


@dataclass(frozen=True, slots=True)
class ResolvedBusinessPath:
    """A canonical relative identity paired with its contained absolute target."""

    root: ResolvedRepoRoot
    relative: str
    path: Path
    policy: PathPolicy = PathPolicy.STRICT


def _path_error(code: str = "PATH_INVALID") -> BaToolsError:
    return BaToolsError(
        code=code,
        message=PATH_MESSAGE,
        remediation=PATH_REMEDIATION,
    )


def resolve_repo_root(value: str | os.PathLike[str]) -> ResolvedRepoRoot:
    """Resolve an explicit existing directory into a root capability."""

    text = os.fspath(value)
    if not text or "\x00" in text:
        raise _path_error()

    try:
        resolved = Path(text).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise _path_error("REPO_ROOT_INVALID") from error
    if not resolved.is_dir():
        raise _path_error("REPO_ROOT_INVALID")
    return ResolvedRepoRoot(resolved)


def parse_business_path(value: str) -> PurePosixPath:
    """Reject non-canonical or potentially escaping path text before filesystem access."""

    if not value or "\x00" in value or "\\" in value:
        raise _path_error()

    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise _path_error("PATH_TRAVERSAL")

    portable = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if portable.is_absolute() or windows.is_absolute() or windows.drive or windows.root:
        raise _path_error("PATH_TRAVERSAL")
    if portable.as_posix() != value:
        raise _path_error()
    return portable


def reject_symlink_or_reparse_components(root: ResolvedRepoRoot, path: PurePosixPath) -> None:
    """Fail closed if an existing target component redirects filesystem access."""

    current = root.path
    for part in path.parts:
        current = current / part
        if not os.path.lexists(current):
            continue
        try:
            metadata = current.lstat()
        except OSError as error:
            raise _path_error("PATH_INSPECTION_FAILED") from error
        attributes = getattr(metadata, "st_file_attributes", 0)
        if stat.S_ISLNK(metadata.st_mode) or (
            attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise _path_error("PATH_REDIRECTED")


def assert_resolved_containment(root: ResolvedRepoRoot, candidate: Path) -> None:
    """Prove a resolved candidate is a descendant of the resolved repository root."""

    try:
        candidate.relative_to(root.path)
    except ValueError as error:
        raise _path_error("PATH_TRAVERSAL") from error


def resolve_business_path(
    root: ResolvedRepoRoot,
    value: str | PurePosixPath,
    *,
    policy: PathPolicy = PathPolicy.STRICT,
) -> ResolvedBusinessPath:
    """Resolve a canonical business path beneath a trusted root."""

    portable = parse_business_path(value if isinstance(value, str) else value.as_posix())
    reject_symlink_or_reparse_components(root, portable)

    try:
        candidate = (root.path / Path(*portable.parts)).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise _path_error("PATH_TRAVERSAL") from error
    assert_resolved_containment(root, candidate)
    reject_symlink_or_reparse_components(root, portable)

    return ResolvedBusinessPath(
        root=root,
        relative=portable.as_posix(),
        path=candidate,
        policy=policy,
    )
