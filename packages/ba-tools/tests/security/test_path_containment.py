"""FOUND-05 adversarial path-containment evidence."""

from __future__ import annotations

import concurrent.futures
import os
import subprocess
import threading
from pathlib import Path

import pytest

from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedRepoRoot, parse_business_path, resolve_business_path


def _assert_path_error(value: object, expected: str | None = None) -> None:
    with pytest.raises(BaToolsError) as captured:
        parse_business_path(value)  # type: ignore[arg-type]
    if expected is not None:
        assert captured.value.code == expected


@pytest.mark.parametrize(
    ("value", "code"),
    [
        pytest.param(None, "PATH_INVALID", id="FOUND-05-null"),
        pytest.param("", "PATH_INVALID", id="FOUND-05-empty"),
        pytest.param(".", "PATH_TRAVERSAL", id="FOUND-05-dot"),
        pytest.param("./state.json", "PATH_TRAVERSAL", id="FOUND-05-dot-prefix"),
        pytest.param("state/./file.json", "PATH_TRAVERSAL", id="FOUND-05-dot-segment"),
        pytest.param("state//file.json", "PATH_TRAVERSAL", id="FOUND-05-empty-segment"),
        pytest.param("/absolute/file.json", "PATH_TRAVERSAL", id="FOUND-05-posix-absolute"),
        pytest.param("C:relative.json", "PATH_TRAVERSAL", id="FOUND-05-drive-relative"),
        pytest.param("C:/absolute.json", "PATH_TRAVERSAL", id="FOUND-05-drive-absolute"),
        pytest.param("//server/share/file.json", "PATH_TRAVERSAL", id="FOUND-05-unc"),
        pytest.param(r"state\file.json", "PATH_INVALID", id="FOUND-05-backslash"),
        pytest.param("state/\x00/file.json", "PATH_INVALID", id="FOUND-05-nul"),
        pytest.param("../outside.json", "PATH_TRAVERSAL", id="FOUND-05-parent"),
        pytest.param("state/../../outside.json", "PATH_TRAVERSAL", id="FOUND-05-nested-parent"),
    ],
)
def test_rejects_empty_and_non_relative_forms(value: object, code: str) -> None:
    """Unsafe grammar is rejected before any candidate filesystem access."""

    _assert_path_error(value, code)


def test_rejected_grammar_never_resolves_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid text cannot become accepted through lossy normalization."""

    root = ResolvedRepoRoot(tmp_path.resolve())

    def forbidden_resolve(self: Path, *args: object, **kwargs: object) -> Path:
        del self, args, kwargs
        raise AssertionError("candidate filesystem resolution occurred")

    monkeypatch.setattr(Path, "resolve", forbidden_resolve)
    with pytest.raises(BaToolsError, match="disallowed form"):
        resolve_business_path(root, "state/../outside.json")


def test_rejects_traversal_and_sibling_prefix(tmp_path: Path) -> None:
    """A sibling sharing the repository name prefix is never treated as contained."""

    repo = tmp_path / "repo"
    sibling = tmp_path / "repo-secret"
    repo.mkdir()
    sibling.mkdir()
    root = ResolvedRepoRoot(repo.resolve())

    with pytest.raises(BaToolsError) as captured:
        resolve_business_path(root, "../repo-secret/evidence.json")

    assert captured.value.code == "PATH_TRAVERSAL"
    assert not (sibling / "evidence.json").exists()


def _create_directory_redirect(link: Path, outside: Path) -> str:
    try:
        link.symlink_to(outside, target_is_directory=True)
        return "symbolic-link"
    except OSError as symlink_error:
        if os.name != "nt":
            pytest.skip(
                "symbolic-link capability unavailable: "
                f"{type(symlink_error).__name__}: {symlink_error}"
            )

    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        reason = (result.stderr or result.stdout).strip()
        pytest.skip(
            "Windows symbolic-link and junction/reparse creation capabilities unavailable: "
            f"{reason}"
        )
    return "junction-reparse"


def test_rejects_symlink_and_reparse_escape(tmp_path: Path) -> None:
    """Real symbolic-link or junction/reparse redirects are rejected."""

    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    redirect = repo / "redirect"
    capability = _create_directory_redirect(redirect, outside)
    root = ResolvedRepoRoot(repo.resolve())

    with pytest.raises(BaToolsError) as captured:
        resolve_business_path(root, "redirect/canonical.json")

    assert capability in {"symbolic-link", "junction-reparse"}
    assert captured.value.code == "PATH_REDIRECTED"
    assert not (outside / "canonical.json").exists()


def test_unicode_contained_path_is_accepted(tmp_path: Path) -> None:
    """Canonical UTF-8 POSIX-relative names retain exact identity."""

    repo = tmp_path / "Dự án có khoảng trắng"
    repo.mkdir()
    root = ResolvedRepoRoot(repo.resolve())

    resolved = resolve_business_path(root, "giao-phẩm/Yêu-cầu-01.json")

    assert resolved.root is root
    assert resolved.relative == "giao-phẩm/Yêu-cầu-01.json"
    assert resolved.path == repo / "giao-phẩm" / "Yêu-cầu-01.json"


def test_concurrent_resolution_never_escapes_root(tmp_path: Path) -> None:
    """Concurrent callers reuse one root capability and reject a real redirect."""

    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    _create_directory_redirect(repo / "redirect", outside)
    root = ResolvedRepoRoot(repo.resolve())
    workers = 8
    barrier = threading.Barrier(workers)

    def resolve_once(index: int) -> tuple[int, str]:
        barrier.wait(timeout=5)
        try:
            resolve_business_path(root, f"redirect/result-{index}.json")
        except BaToolsError as error:
            return index, error.code
        return index, "AUTHORIZED_OUTSIDE"

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        outcomes = tuple(executor.map(resolve_once, range(workers)))

    assert outcomes == tuple((index, "PATH_REDIRECTED") for index in range(workers))
    assert tuple(outside.iterdir()) == ()
