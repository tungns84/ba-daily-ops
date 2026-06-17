"""
Repository root resolution and path-traversal guard (TOOL-14, T-1-01).

All ba-tools commands receive an optional --repo-root argument. These helpers:
1. Resolve that argument to an absolute Path (or fall back to git toplevel / cwd).
2. Validate that a candidate path is inside the resolved root (traversal guard).

No hard-coded machine paths. Python interpreter via sys.executable (DESIGN §11).
"""

import subprocess
from pathlib import Path


def resolve_repo_root(arg: str | None) -> Path:
    """Return an absolute Path to use as the repository root.

    Resolution order (first that works wins):
      1. ``arg`` — the value of ``--repo-root`` from the CLI, if provided.
      2. ``git rev-parse --show-toplevel`` — the git project root, if the
         current working directory is inside a git repository.
      3. ``Path.cwd()`` — the current working directory as a last resort.

    Args:
        arg: raw string value of the ``--repo-root`` CLI argument, or None.

    Returns:
        An absolute, resolved ``pathlib.Path``.
    """
    if arg is not None:
        return Path(arg).resolve()

    # Shell out to git directly for the project toplevel.
    try:
        git_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
        )
        if git_result.returncode == 0:
            toplevel = git_result.stdout.strip()
            if toplevel:
                return Path(toplevel).resolve()
    except (FileNotFoundError, OSError):
        pass

    return Path.cwd().resolve()


def resolve_under_root(raw: str, root: Path) -> Path:
    """Resolve a CLI-supplied path *raw* relative to *root* (not the CWD).

    Mirrors the convention already used by byte_check, extract_uc, scan_cmd,
    and template_cmd: an absolute path is honored as-is; a relative path is
    joined onto *root* before resolution. This keeps every path-taking command
    consistent with the documented "paths resolve relative to --repo-root"
    contract and removes the latent dependency on the ambient CWD (WR-01).

    Args:
        raw: the raw path string from the CLI argument.
        root: the resolved repository root.

    Returns:
        An absolute, resolved ``Path``.
    """
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def is_within_root(candidate: Path, root: Path) -> bool:
    """Return True if ``candidate`` is inside (or equal to) ``root``.

    Resolves both paths and tests containment via
    ``candidate.resolve().relative_to(root.resolve())`` inside a
    ``try/except ValueError`` (a ``ValueError`` means *candidate* is not under
    *root*). ``..`` traversal is normalised away by ``resolve()`` before the
    comparison (T-1-01).

    Symlink caveat: on POSIX, ``resolve()`` canonicalises symlinks so a link
    pointing outside *root* is correctly rejected. On Windows, ``resolve()`` of
    a path whose final component does not exist does not always canonicalise
    junctions/symlinks, so containment of a non-existent target via a junction
    is NOT guaranteed here. Callers that require hard symlink containment must
    add an explicit check/test.

    Args:
        candidate: path to test.
        root: the repository root or allowed directory.

    Returns:
        True if ``candidate.resolve()`` is ``root.resolve()`` or a descendant.
        False otherwise (path-traversal detected).
    """
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
