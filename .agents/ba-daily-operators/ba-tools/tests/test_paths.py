"""Tests for path resolution and traversal guard (TOOL-14, T-1-01, DESIGN §11).

Two categories:
  (a) Runtime path-safety: relative paths resolve under --repo-root; no path escapes root.
  (b) Static source scan: no .py file in ba_tools/ contains a hard-coded machine path
      (drive-letter literals like C:\\ or D:\\) and no bare "python3"/"python " subprocess
      call (must use sys.executable).
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from ba_tools.repo import resolve_repo_root, is_within_root


# ---------------------------------------------------------------------------
# (a) Runtime path-safety: is_within_root and resolve_repo_root
# ---------------------------------------------------------------------------

def test_is_within_root_child_passes(tmp_path):
    """is_within_root returns True for a path inside the root."""
    root = tmp_path.resolve()
    child = root / "subdir" / "file.txt"
    assert is_within_root(child, root) is True


def test_is_within_root_parent_fails(tmp_path):
    """is_within_root returns False for a path outside the root (traversal guard)."""
    root = tmp_path.resolve()
    outside = root.parent
    assert is_within_root(outside, root) is False


def test_is_within_root_equal_passes(tmp_path):
    """is_within_root returns True when candidate equals root."""
    root = tmp_path.resolve()
    assert is_within_root(root, root) is True


def test_is_within_root_dotdot_traversal_fails(tmp_path):
    """is_within_root rejects a path using .. traversal to escape root."""
    root = tmp_path.resolve()
    escape = root / "subdir" / ".." / ".." / "outside"
    assert is_within_root(escape, root) is False


def test_resolve_repo_root_with_arg(tmp_path):
    """resolve_repo_root(str) returns the absolute resolved path of that string."""
    result = resolve_repo_root(str(tmp_path))
    assert result == tmp_path.resolve()
    assert result.is_absolute()


def test_resolve_repo_root_without_arg_returns_absolute():
    """resolve_repo_root(None) returns an absolute path (git root or cwd)."""
    result = resolve_repo_root(None)
    assert result.is_absolute()


# ---------------------------------------------------------------------------
# (b) Runtime: byte-check resolves relative path under --repo-root
# ---------------------------------------------------------------------------

def test_byte_check_resolves_relative_path_under_repo_root(tmp_path):
    """byte-check accepts a relative path and resolves it under --repo-root.

    A file placed at tmp_path/docs/eager.md should be found when the path arg
    is 'docs/eager.md' and --repo-root is tmp_path (TOOL-14 runtime assertion).
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    eager = docs / "eager.md"
    eager.write_text("# Small file\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "ba_tools", "--repo-root", str(tmp_path),
         "byte-check", "docs/eager.md"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"byte-check should resolve relative path under repo-root.\n"
        f"  stdout: {result.stdout!r}\n"
        f"  stderr: {result.stderr!r}"
    )


def test_byte_check_rejects_path_escape(tmp_path):
    """byte-check rejects a path that escapes --repo-root via .. traversal (T-1-01)."""
    # Create a file outside tmp_path
    outside = tmp_path.parent / "outside_file.md"
    outside.write_text("# Outside file\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "ba_tools", "--repo-root", str(tmp_path),
         "byte-check", "../outside_file.md"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, (
        "byte-check should exit 2 for path-escape attempts (T-1-01)"
    )
    import json
    payload = json.loads(result.stderr)
    assert any(f.get("code") == "PATH_ESCAPE" for f in payload.get("failures", [])), (
        f"Expected PATH_ESCAPE failure code, got: {payload}"
    )


# ---------------------------------------------------------------------------
# (c) Static source scan: no drive-letter paths, no bare python3 subprocess
# ---------------------------------------------------------------------------

def _get_package_py_files() -> list[Path]:
    """Return all .py files under ba_tools/ package directory."""
    # Locate the package: it's the parent of this test file's parent / ba_tools/
    tests_dir = Path(__file__).parent
    package_dir = tests_dir.parent / "ba_tools"
    assert package_dir.exists(), f"ba_tools package dir not found: {package_dir}"
    return list(package_dir.rglob("*.py"))


def test_no_hardcoded_drive_letter_paths():
    """No .py file in ba_tools/ contains a Windows drive-letter literal (DESIGN §11, T-1-12).

    Patterns rejected: C:\\ D:\\ E:\\ etc. (upper or lower case)
    These would be hard-coded machine paths — forbidden by DESIGN §11.
    """
    # Pattern: optional space/quote then a drive letter followed by :\
    drive_pattern = re.compile(r"[A-Za-z]:\\\\", re.IGNORECASE)

    violations: list[str] = []
    for py_file in _get_package_py_files():
        content = py_file.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(content.splitlines(), start=1):
            if drive_pattern.search(line):
                violations.append(f"  {py_file.name}:{lineno}: {line.strip()!r}")

    assert not violations, (
        "Hard-coded drive-letter paths found in ba_tools/ source (DESIGN §11):\n"
        + "\n".join(violations)
    )


def test_no_bare_python_subprocess_calls():
    """No .py file in ba_tools/ invokes 'python3' or 'python ' as a bare subprocess string.

    Subprocess self-calls must use sys.executable (DESIGN §11, TOOL-14).
    Patterns rejected: "python3", "python " as the first element of a subprocess list
    or as a shell string argument.
    """
    # Patterns that would represent a bare python call (not sys.executable)
    # We look for: ["python3", ...] or ["python ", ...] or subprocess.run("python3 ...)
    # but NOT for comments or import statements.
    bad_patterns: list[tuple[str, re.Pattern]] = [
        # Literal string "python3" as a subprocess argument
        ('"python3"', re.compile(r'["\']python3["\']')),
        # Literal string "python " (with space — bare python command)
        ('"python "', re.compile(r'["\']python\s["\']')),
        # subprocess.run(["python3", ...) or ["python", ...] as first list element
        ('["python3"', re.compile(r'\[\s*["\']python3["\']')),
        ('["python"', re.compile(r'\[\s*["\']python["\']')),
    ]

    violations: list[str] = []
    for py_file in _get_package_py_files():
        content = py_file.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(content.splitlines(), start=1):
            # Skip comment lines and docstrings heuristically
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for label, pattern in bad_patterns:
                if pattern.search(line):
                    violations.append(
                        f"  {py_file.name}:{lineno} [{label}]: {stripped!r}"
                    )

    assert not violations, (
        "Bare python/python3 subprocess call found in ba_tools/ source.\n"
        "Use sys.executable instead (DESIGN §11, TOOL-14):\n"
        + "\n".join(violations)
    )


def test_no_hardcoded_python_path():
    """No ba-tools command invokes 'python' or 'python3' directly as a subprocess (TOOL-14).

    This test is a live integration of the above static scan, confirming the package
    as-installed has no hard-coded interpreter path.
    """
    # This is satisfied by test_no_bare_python_subprocess_calls above.
    # Kept as an explicit named test (replaces the Wave-0 xfail stub) so the
    # requirement TOOL-14 is traceable to a named test function.
    py_files = _get_package_py_files()
    assert len(py_files) > 0, "Should find at least one .py file in ba_tools/"

    drive_pattern = re.compile(r"[A-Za-z]:\\\\", re.IGNORECASE)
    bare_python = re.compile(r'\[\s*["\']python(?:3)?["\']')

    violations: list[str] = []
    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if drive_pattern.search(line):
                violations.append(f"  {py_file.name}:{lineno} [drive-letter]: {stripped!r}")
            if bare_python.search(line):
                violations.append(f"  {py_file.name}:{lineno} [bare-python]: {stripped!r}")

    assert not violations, (
        "Hard-coded paths or bare python found in ba_tools/ (DESIGN §11, TOOL-14):\n"
        + "\n".join(violations)
    )
