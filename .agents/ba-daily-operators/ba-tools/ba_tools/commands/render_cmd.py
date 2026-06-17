"""ba-tools render — deterministic JSON→IEEE-830 renderer (TOOL-XX, plan 02-02).

Subcommands:
    render srs --slug <slug>
        Reads  .ba-ops/srs/<slug>/requirements.json
        Writes .ba-ops/srs/<slug>/SRS.md (lockfile-guarded)

    render registry
        Globs ALL .ba-ops/srs/*/requirements.json (sorted, union of every slug)
        Writes .ba-ops/REQUIREMENTS.md (lockfile-guarded, D-08)

Security:
    T-02-06: slug-derived write path is resolved under root; is_within_root guard
             before any file write → PATH_TRAVERSAL exit 2 on escape.
    T-02-03: --slug user input may contain '..' — resolved and guarded here.

Determinism boundary (D-05):
    NO import of openai, anthropic, or any model client.
    render_srs / render_registry are pure functions; no nondeterminism injected here.
"""

import json
import string
from pathlib import Path

from filelock import FileLock, Timeout

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root
from ba_tools.srs_render import render_registry, render_srs

# Lock timeout — matches STATE.md convention (D-02 / DESIGN §8)
_LOCK_TIMEOUT = 10


def _templates_dir(root: Path) -> Path:
    """Return the ba-core/templates path relative to repo root."""
    return root / ".agents" / "ba-daily-operators" / "ba-tools" / "ba-core" / "templates"


def _read_srs_template(root: Path) -> str:
    """Load the IEEE-830 srs.md template from ba-core/templates."""
    tpl_path = _templates_dir(root) / "srs.md"
    if not tpl_path.exists():
        raise BaToolsError([{
            "code": "TEMPLATE_NOT_FOUND",
            "path": str(tpl_path),
            "message": "srs.md template not found in ba-core/templates",
        }])
    return tpl_path.read_text(encoding="utf-8")


def _guarded_write(file_path: Path, content: str, lock_name: str) -> None:
    """Write content to file_path under a FileLock(timeout=10).

    Ensures the parent directory exists before writing.

    Raises:
        BaToolsError(LOCK_TIMEOUT) if the lock is not acquired within 10 seconds.
    """
    lock_path = file_path.parent / lock_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path), timeout=_LOCK_TIMEOUT)
    try:
        with lock:
            file_path.write_text(content, encoding="utf-8")
    except Timeout:
        raise BaToolsError([{
            "code": "LOCK_TIMEOUT",
            "lock": str(lock_path),
            "message": (
                f"{lock_name} held for >{_LOCK_TIMEOUT}s; another writer may be active. "
                "No write was performed."
            ),
        }])


def register(subparsers) -> None:
    """Register the render subcommand."""
    p = subparsers.add_parser(
        "render",
        help="Render SRS.md (per slug) or REQUIREMENTS.md (union registry) from requirements.json",
    )
    sub = p.add_subparsers(dest="render_target", required=True)

    # render srs --slug <slug>
    srs_p = sub.add_parser(
        "srs",
        help="Render .ba-ops/srs/<slug>/SRS.md from .ba-ops/srs/<slug>/requirements.json",
    )
    srs_p.add_argument(
        "--slug",
        required=True,
        help="Use-case slug (subdirectory name under .ba-ops/srs/)",
    )
    srs_p.set_defaults(func=run)

    # render registry
    reg_p = sub.add_parser(
        "registry",
        help=(
            "Render .ba-ops/REQUIREMENTS.md as the union of ALL slugs' requirements.json (D-08)"
        ),
    )
    reg_p.set_defaults(func=run)

    p.set_defaults(func=run)


def run(args) -> None:
    """Dispatch to _run_srs or _run_registry based on render_target."""
    target = getattr(args, "render_target", None)
    if target == "srs":
        _run_srs(args)
    elif target == "registry":
        _run_registry(args)
    else:
        raise BaToolsError([{
            "code": "UNKNOWN_TARGET",
            "target": target,
            "message": f"Unknown render target: {target!r}. Use 'srs' or 'registry'.",
        }])


def _run_srs(args) -> None:
    """Render one slug's SRS.md from its requirements.json.

    Path: .ba-ops/srs/<slug>/requirements.json → .ba-ops/srs/<slug>/SRS.md
    """
    root = resolve_repo_root(getattr(args, "repo_root", None))
    slug = args.slug

    # Slug safety: resolve the slug-derived path and check it stays within root (T-02-06)
    slug_dir = (root / ".ba-ops" / "srs" / slug).resolve()
    if not is_within_root(slug_dir, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "slug": slug,
            "message": (
                f"--slug '{slug}' resolves outside repo root. "
                "Slugs must not contain path traversal sequences."
            ),
        }])

    reqs_path = slug_dir / "requirements.json"
    if not reqs_path.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "path": str(reqs_path),
            "message": f"requirements.json not found for slug '{slug}': {reqs_path}",
        }])

    # Parse requirements.json
    try:
        reqs_doc = json.loads(reqs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as exc:
        raise BaToolsError([{
            "code": "MALFORMED_JSON",
            "path": str(reqs_path),
            "message": f"Could not parse requirements.json for slug '{slug}': {exc}",
        }]) from exc

    template_text = _read_srs_template(root)

    # Inject slug into template variables (safe_substitute leaves unknowns as-is)
    template_with_slug = string.Template(template_text).safe_substitute({"slug": slug})
    rendered = render_srs(reqs_doc, template_with_slug)

    srs_out = slug_dir / "SRS.md"
    _guarded_write(srs_out, rendered, "SRS.md.lock")

    ok_json(slug=slug, out=str(srs_out))


def _run_registry(args) -> None:
    """Render REQUIREMENTS.md as the union of ALL slugs' requirements.json (D-08).

    Globs .ba-ops/srs/*/requirements.json (sorted for determinism), loads each,
    unions all requirements, writes .ba-ops/REQUIREMENTS.md.
    """
    root = resolve_repo_root(getattr(args, "repo_root", None))
    srs_dir = root / ".ba-ops" / "srs"

    # Collect all slug requirements.json files, sorted for determinism
    reqs_files: list[Path] = sorted(srs_dir.glob("*/requirements.json")) if srs_dir.exists() else []

    reqs_docs: list[dict] = []
    for reqs_path in reqs_files:
        # Safety: each discovered path should be within root (glob is bounded, but verify)
        if not is_within_root(reqs_path, root):
            # Skip silently — a symlink could point outside, ignore it
            continue
        try:
            doc = json.loads(reqs_path.read_text(encoding="utf-8"))
            reqs_docs.append(doc)
        except (json.JSONDecodeError, ValueError):
            # Skip malformed files — registry is best-effort union of valid docs
            continue

    rendered = render_registry(reqs_docs)

    ba_ops = root / ".ba-ops"
    ba_ops.mkdir(parents=True, exist_ok=True)
    reg_out = ba_ops / "REQUIREMENTS.md"
    _guarded_write(reg_out, rendered, "REQUIREMENTS.md.lock")

    ok_json(
        out=str(reg_out),
        slugs=[p.parent.name for p in reqs_files],
    )
