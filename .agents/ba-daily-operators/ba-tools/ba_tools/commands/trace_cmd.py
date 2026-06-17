"""ba-tools trace — record artifact→REQ-ID provenance (TOOL-07, TRACE-04).

Writes a D-05 trace record to .ba-ops/traces/<kind>-<slug>.json capturing:
  - kind, slug  — artifact type and unique name (validated regex)
  - artifact_path  — path to the artifact file (relative to repo root)
  - source_doc     — path to the source document (relative to repo root)
  - source_hash    — SHA-256 of the live source doc bytes (D-06)
  - req_ids        — list of {id, statement_hash} objects (D-12)

Security notes:
  - T-02-07b: kind/slug validated against ^[a-z0-9][a-z0-9-]*$ before composing the
    output path; output path re-confirmed under root via is_within_root before write.
  - T-02-07:  --artifact and --source-doc resolved under root; PATH_TRAVERSAL exit 2.
  - T-02-08b: TRACE_EXISTS exit 2 unless --force is passed (no silent overwrite).
  - T-02-09:  FileLock(timeout=10) on <kind>-<slug>.json.lock; LOCK_TIMEOUT on contention.
  - T-02-10:  No model-client import. Determinism boundary enforced.

Shared hashing:
  _sha256_file and _statement_hash are imported from ba_tools.hashing (plan 02-01).
  Neither is redefined here — this eliminates the circular-import risk between
  trace_cmd and index_cmd (OpenCode MEDIUM feedback, resolved in Wave-0).
"""

import json
import re
from pathlib import Path

from filelock import Timeout

from ba_tools.errors import BaToolsError
from ba_tools.hashing import _sha256_file, _statement_hash
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root, resolve_under_root
from ba_tools.state_store import acquire_state_lock

# Validation regex for kind and slug: ^[a-z0-9][a-z0-9-]*$
# Rejects any value containing path separators, dots, uppercase, or special chars.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def register(subparsers) -> None:
    """Register the ``trace`` subcommand."""
    p = subparsers.add_parser(
        "trace",
        help="Record artifact→REQ-ID provenance trace (TOOL-07)",
    )
    p.add_argument(
        "action",
        choices=["write"],
        help="Action to perform (currently: write)",
    )
    p.add_argument(
        "--kind",
        required=True,
        help="Artifact kind, e.g. srs, mermaid, mockup, story (^[a-z0-9][a-z0-9-]*$)",
    )
    p.add_argument(
        "--slug",
        required=True,
        help="Unique slug for this artifact trace (^[a-z0-9][a-z0-9-]*$)",
    )
    p.add_argument(
        "--artifact",
        required=True,
        help="Path to the artifact file (must be under repo root)",
    )
    p.add_argument(
        "--source-doc",
        required=True,
        help="Path to the source document (must be under repo root)",
    )
    p.add_argument(
        "--requirements",
        required=True,
        help="Path to the requirements JSON file (used for statement-hash lookup only)",
    )
    p.add_argument(
        "--req-ids",
        default=None,
        help=(
            "Comma-separated REQ-IDs to include in this trace (caller-supplied subset). "
            "Required for non-srs kinds. Omit for srs to default to all requirements."
        ),
    )
    p.add_argument(
        "--req-ids-file",
        default=None,
        help=(
            "Path to a newline-separated file of REQ-IDs (alternative to --req-ids). "
            "Required for non-srs kinds when --req-ids is not provided."
        ),
    )
    p.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite an existing <kind>-<slug>.json (default: fail with TRACE_EXISTS)",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    """Execute the trace write command.

    Steps:
      1. Validate kind + slug against the regex (T-02-07b: slug path-injection guard).
      2. Resolve repo root and all path arguments under root.
      3. Parse --requirements JSON; build {id: statement} lookup.
      4. Determine req-id set: explicit --req-ids / --req-ids-file, or all (kind=srs only).
      5. Build the D-05 record with relative paths + sha256 hashes.
      6. Confirm output path is within root; check TRACE_EXISTS / --force.
      7. Write under FileLock (LOCK_TIMEOUT on contention).
      8. Emit ok_json.
    """
    kind: str = args.kind
    slug: str = args.slug

    # Step 1: validate kind and slug (T-02-07b)
    for label, value in (("kind", kind), ("slug", slug)):
        if not _SLUG_RE.fullmatch(value):
            raise BaToolsError([{
                "code": "INVALID_KIND_SLUG",
                "message": (
                    f"--{label} {value!r} is invalid. "
                    "Must match ^[a-z0-9][a-z0-9-]*$ "
                    "(lowercase letters, digits, hyphens; no dots, slashes, or uppercase)."
                ),
            }])

    # Step 2: resolve paths
    root: Path = resolve_repo_root(args.repo_root)

    artifact_path = resolve_under_root(args.artifact, root)
    if not is_within_root(artifact_path, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "message": f"--artifact {args.artifact!r} resolves outside repo root.",
        }])
    if not artifact_path.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "message": f"--artifact file not found: {artifact_path}",
        }])

    source_doc = resolve_under_root(args.source_doc, root)
    if not is_within_root(source_doc, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "message": f"--source-doc {args.source_doc!r} resolves outside repo root.",
        }])
    if not source_doc.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "message": f"--source-doc file not found: {source_doc}",
        }])

    requirements_path = resolve_under_root(args.requirements, root)
    if not is_within_root(requirements_path, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "message": f"--requirements {args.requirements!r} resolves outside repo root.",
        }])
    if not requirements_path.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "message": f"--requirements file not found: {requirements_path}",
        }])

    # Step 3: parse requirements JSON; build id→statement lookup
    try:
        payload = json.loads(requirements_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as exc:
        raise BaToolsError([{
            "code": "MALFORMED_JSON",
            "message": f"--requirements is not valid JSON: {exc}",
        }]) from exc

    # Accept list or {"requirements": [...]}
    if isinstance(payload, list):
        reqs_list = payload
    elif isinstance(payload, dict) and "requirements" in payload:
        reqs_list = payload["requirements"]
    else:
        raise BaToolsError([{
            "code": "MALFORMED_JSON",
            "message": (
                "--requirements must be a list or an object with a 'requirements' key."
            ),
        }])

    # Build id → statement lookup (used only for statement_hash computation)
    id_to_statement: dict[str, str] = {}
    for req in reqs_list:
        if isinstance(req, dict):
            req_id = req.get("id", "")
            statement = req.get("statement", "")
            if req_id:
                id_to_statement[req_id] = statement

    # Step 4: determine the req-id set
    req_ids_str: str | None = args.req_ids
    req_ids_file: str | None = args.req_ids_file

    if req_ids_str is not None:
        # Caller-supplied comma-separated list
        selected_ids = [rid.strip() for rid in req_ids_str.split(",") if rid.strip()]
    elif req_ids_file is not None:
        # Caller-supplied newline-separated file
        ids_path = resolve_under_root(req_ids_file, root)
        if not is_within_root(ids_path, root):
            raise BaToolsError([{
                "code": "PATH_TRAVERSAL",
                "message": f"--req-ids-file {req_ids_file!r} resolves outside repo root.",
            }])
        if not ids_path.exists():
            raise BaToolsError([{
                "code": "FILE_NOT_FOUND",
                "message": f"--req-ids-file not found: {ids_path}",
            }])
        selected_ids = [
            line.strip()
            for line in ids_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    elif kind == "srs":
        # srs: default to ALL requirements
        selected_ids = list(id_to_statement.keys())
    else:
        # Non-srs kind without explicit req-ids: error
        raise BaToolsError([{
            "code": "MISSING_REQ_IDS",
            "message": (
                f"--kind {kind!r} requires explicit --req-ids or --req-ids-file. "
                "Only kind=srs defaults to all requirements."
            ),
        }])

    # Build req_ids list: {id, statement_hash}
    req_ids_records: list[dict] = []
    for req_id in selected_ids:
        statement = id_to_statement.get(req_id, "")
        req_ids_records.append({
            "id": req_id,
            "statement_hash": _statement_hash(statement),
        })

    # Step 5: build the D-05 record (paths relative to root)
    try:
        rel_artifact = str(artifact_path.relative_to(root))
    except ValueError:
        rel_artifact = str(artifact_path)

    try:
        rel_source = str(source_doc.relative_to(root))
    except ValueError:
        rel_source = str(source_doc)

    source_hash: str = _sha256_file(source_doc)

    record: dict = {
        "kind": kind,
        "slug": slug,
        "artifact_path": rel_artifact,
        "source_doc": rel_source,
        "source_hash": source_hash,
        "req_ids": req_ids_records,
    }

    # Step 6: compute output path + confirm under root
    traces_dir = root / ".ba-ops" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    out_path = traces_dir / f"{kind}-{slug}.json"
    # Re-confirm the composed path is inside root (T-02-07b: belt-and-suspenders)
    if not is_within_root(out_path, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "message": (
                f"Composed output path {out_path} resolves outside repo root. "
                "kind/slug must not contain path separators."
            ),
        }])

    if out_path.exists() and not args.force:
        raise BaToolsError([{
            "code": "TRACE_EXISTS",
            "message": (
                f".ba-ops/traces/{kind}-{slug}.json already exists. "
                "Pass --force to overwrite."
            ),
        }])

    # Step 7: write under lockfile (T-02-09: concurrent-write guard)
    lock_path = out_path.with_suffix(".json.lock")
    lock = acquire_state_lock(lock_path)

    try:
        with lock:
            out_path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    except Timeout:
        raise BaToolsError([{
            "code": "LOCK_TIMEOUT",
            "message": (
                f"{out_path.name}.lock held for >10s; another writer may be active. "
                "No write was performed."
            ),
        }])

    # Step 8: emit ok_json
    ok_json(
        trace=f"{kind}-{slug}",
        kind=kind,
        slug=slug,
        req_ids=[item["id"] for item in req_ids_records],
    )
