"""ba-tools byte-check — fail if any eager-loaded doc >= 32768 B (GATE-04, CDX-04).

Enforces the Codex silent-truncation limit (DESIGN §7, CLAUDE.md CONFIRMED):
  - project_doc_max_bytes = 32768 B (CONFIRMED)
  - Files >= limit fail with EXCEEDS_LIMIT (strict less-than: size < limit)
  - Files not found fail with FILE_NOT_FOUND
  - Paths escaping repo root fail with PATH_ESCAPE (T-1-01)
  - --limit overrides the default for workflow tier checks (CDX-04)

Path resolution: every raw path arg is resolved as (repo_root / raw).resolve()
and checked via is_within_root — no hard-coded machine paths (DESIGN §11).
"""

from pathlib import Path

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root

CODEX_LIMIT = 32768  # bytes — DESIGN §7 hard limit (Codex truncates AT this value)


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "byte-check",
        help="Fail if any listed file is >= byte limit (default: 32768 B, GATE-04)",
    )
    p.add_argument("paths", nargs="+", help="Files to check (relative to --repo-root)")
    p.add_argument(
        "--limit",
        type=int,
        default=CODEX_LIMIT,
        help=f"Byte limit — file must be strictly LESS than this value (default: {CODEX_LIMIT})",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    repo_root: Path = resolve_repo_root(args.repo_root)
    limit: int = args.limit
    results: list[dict] = []
    failures: list[dict] = []

    for raw in args.paths:
        resolved = (repo_root / raw).resolve()

        # T-1-01: reject path-traversal attempts
        if not is_within_root(resolved, repo_root):
            failures.append({
                "code": "PATH_ESCAPE",
                "message": f"Path escapes repository root: {raw!r}",
                "path": raw,
                "repo_root": str(repo_root),
            })
            continue

        # Missing file check
        if not resolved.exists():
            failures.append({
                "code": "FILE_NOT_FOUND",
                "message": f"File not found: {raw!r}",
                "path": raw,
                "resolved": str(resolved),
            })
            continue

        # Size check: file must be strictly LESS than limit (>= limit fails)
        size = resolved.stat().st_size
        passed = size < limit
        result_entry = {
            "path": raw,
            "resolved": str(resolved),
            "size_bytes": size,
            "limit_bytes": limit,
            "passed": passed,
        }
        results.append(result_entry)

        if not passed:
            failures.append({
                "code": "EXCEEDS_LIMIT",
                "message": (
                    f"File {raw!r} is {size} bytes, which is >= limit of {limit} bytes"
                ),
                "path": raw,
                "size_bytes": size,
                "limit_bytes": limit,
            })

    if failures:
        raise BaToolsError(failures)

    ok_json(checks=results)
