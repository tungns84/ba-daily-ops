"""Tests for path resolution and traversal guard (TOOL-14, T-1-01)."""

import pytest
from pathlib import Path
from ba_tools.repo import resolve_repo_root, is_within_root


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


@pytest.mark.xfail(reason="Wave 1: verify sys.executable used in subprocess calls (TOOL-14)")
def test_no_hardcoded_python_path():
    """No ba-tools command invokes 'python' or 'python3' directly as a subprocess."""
    raise NotImplementedError
