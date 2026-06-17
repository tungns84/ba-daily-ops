"""ba-tools index — rebuild INDEX.md from trace records (TOOL-08, TRACE-05).

Reads ONLY .ba-ops/traces/*.json trace records (D-04: uniform-input).
Never parses raw artifacts (requirements.json / SRS.md / .mmd / .html).

INDEX.md is written with:
  - A Matrix table with columns REQ-ID | SRS § | Mermaid | Mockup | Story | Status
    where Status is one of: gap | orphan | stale | ok
  - ## Gaps   — REQ-IDs in SRS trace with no downstream (non-srs) coverage
  - ## Orphans — REQ-IDs cited by non-srs traces but absent from all SRS traces
  - ## Stale  — slugs whose live source_hash ≠ recorded source_hash; also 'missing'
                 when source_doc file absent or resolves outside repo root

Security notes:
  - T-02-07c: each trace record's source_doc is UNTRUSTED. Resolved via
    resolve_under_root + is_within_root before any re-hash. If out-of-root
    or absent → reported 'missing', never hashed.
  - T-02-09: INDEX.md write guarded by INDEX.md.lock (FileLock timeout=10).
  - T-02-10: no model-client import (determinism boundary enforced).

Shared hashing:
  _sha256_file imported from ba_tools.hashing (plan 02-01 Wave-0).
  NOT imported from trace_cmd — prevents circular import (OpenCode MEDIUM).
"""

import json
from pathlib import Path

from filelock import Timeout

from ba_tools.errors import BaToolsError
from ba_tools.hashing import _sha256_file
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root, resolve_under_root
from ba_tools.state_store import acquire_state_lock


def register(subparsers) -> None:
    """Register the ``index`` subcommand."""
    p = subparsers.add_parser(
        "index",
        help="Rebuild INDEX.md traceability matrix from trace records (TOOL-08)",
    )
    p.add_argument(
        "action",
        choices=["update"],
        help="Action to perform (currently: update)",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    """Execute the index update command.

    Steps:
      1. Resolve repo root; locate .ba-ops/traces/.
      2. Load all *.json trace records (skip non-JSON files like requirements.json
         or .lock files — only parse files matching the <kind>-<slug>.json pattern).
      3. Compute valid REQ-ID set = union of req_ids[].id across kind=srs records (D-08).
      4. For each trace record, resolve source_doc under root (T-02-07c) and compare
         live hash vs recorded hash → classify as stale / missing.
      5. For each valid REQ-ID: gap if no non-srs trace covers it; stale if its srs
         trace is stale (stale > gap > ok precedence).
      6. Collect orphans = ids in non-srs traces not in valid set.
      7. Render INDEX.md and write under FileLock (T-02-09).
      8. Emit ok_json.
    """
    root: Path = resolve_repo_root(args.repo_root)
    traces_dir = root / ".ba-ops" / "traces"
    index_path = root / ".ba-ops" / "INDEX.md"
    lock_path = index_path.with_suffix(".md.lock")

    # Step 1: ensure .ba-ops/ exists
    (root / ".ba-ops").mkdir(parents=True, exist_ok=True)

    # Step 2: load trace records (only files named <kind>-<slug>.json)
    records: list[dict] = []
    if traces_dir.is_dir():
        for f in sorted(traces_dir.glob("*.json")):
            # D-04: skip decoy artifacts — only parse files that look like
            # kind-slug.json (contains a hyphen, excludes requirements.json etc.)
            stem = f.stem  # e.g. "srs-demo", "mermaid-draft"
            if "-" not in stem:
                continue
            try:
                raw = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError) as exc:
                raise BaToolsError([{
                    "code": "MALFORMED_JSON",
                    "message": f"Trace record {f.name} is not valid JSON: {exc}",
                }]) from exc
            if isinstance(raw, dict) and "kind" in raw and "slug" in raw:
                records.append(raw)

    # Step 3: compute valid REQ-ID set from srs traces (D-08)
    srs_req_ids: set[str] = set()
    for rec in records:
        if rec.get("kind") == "srs":
            for item in rec.get("req_ids", []):
                rid = item.get("id", "")
                if rid:
                    srs_req_ids.add(rid)

    # Step 4: stale/missing detection per trace slug
    # stale_slugs: slug → reason string ("stale" or "missing")
    stale_slugs: dict[str, str] = {}
    # stale_req_ids: set of REQ-IDs whose owning srs trace is stale/missing
    stale_req_ids: set[str] = set()

    for rec in records:
        kind = rec.get("kind", "")
        slug = rec.get("slug", "")
        trace_key = f"{kind}-{slug}"
        source_doc_raw = rec.get("source_doc", "")
        recorded_hash = rec.get("source_hash", "")

        # Resolve source_doc under root (T-02-07c: source_doc is UNTRUSTED)
        resolved = resolve_under_root(source_doc_raw, root)
        if not is_within_root(resolved, root):
            stale_slugs[trace_key] = "missing"
        elif not resolved.exists():
            stale_slugs[trace_key] = "missing"
        else:
            live_hash = _sha256_file(resolved)
            if live_hash != recorded_hash:
                stale_slugs[trace_key] = "stale"

        # If the owning srs trace is stale/missing, mark its req_ids
        if trace_key in stale_slugs and kind == "srs":
            for item in rec.get("req_ids", []):
                rid = item.get("id", "")
                if rid:
                    stale_req_ids.add(rid)

    # Step 5: classify each valid REQ-ID
    # covered_by: req_id → set of non-srs slug keys that cover it
    covered_by: dict[str, set[str]] = {rid: set() for rid in srs_req_ids}
    for rec in records:
        kind = rec.get("kind", "")
        slug = rec.get("slug", "")
        if kind == "srs":
            continue
        trace_key = f"{kind}-{slug}"
        for item in rec.get("req_ids", []):
            rid = item.get("id", "")
            if rid in covered_by:
                covered_by[rid].add(trace_key)

    # Classify: stale > gap > ok
    req_status: dict[str, str] = {}
    for rid in srs_req_ids:
        if rid in stale_req_ids:
            req_status[rid] = "stale"
        elif not covered_by[rid]:
            req_status[rid] = "gap"
        else:
            req_status[rid] = "ok"

    # Step 6: collect orphans (cited by non-srs but not in srs_req_ids)
    orphan_ids: set[str] = set()
    for rec in records:
        if rec.get("kind") == "srs":
            continue
        for item in rec.get("req_ids", []):
            rid = item.get("id", "")
            if rid and rid not in srs_req_ids:
                orphan_ids.add(rid)

    # Step 7: render INDEX.md
    gap_ids = sorted(rid for rid, status in req_status.items() if status == "gap")
    stale_status_ids = sorted(rid for rid, status in req_status.items() if status == "stale")
    ok_ids = sorted(rid for rid, status in req_status.items() if status == "ok")
    all_req_ids = sorted(srs_req_ids)

    # Build Matrix table rows (sort by REQ-ID)
    matrix_rows: list[str] = []
    for rid in all_req_ids:
        status = req_status.get(rid, "gap")
        matrix_rows.append(f"| {rid} | | | | | {status} |")

    matrix_block = "\n".join(matrix_rows) if matrix_rows else "| (none) | | | | | |"

    # Gaps section
    if gap_ids:
        gaps_body = "\n".join(f"- {rid}" for rid in gap_ids)
    else:
        gaps_body = "(none)"

    # Orphans section
    if orphan_ids:
        orphans_body = "\n".join(f"- {rid}" for rid in sorted(orphan_ids))
    else:
        orphans_body = "(none)"

    # Stale section (includes missing)
    stale_entries: list[str] = []
    for trace_key, reason in sorted(stale_slugs.items()):
        stale_entries.append(f"- {trace_key}: {reason}")
    stale_body = "\n".join(stale_entries) if stale_entries else "(none)"

    index_content = f"""\
---
version: "0.0"
---

# Traceability Index

> REQ-ID → SRS § → Mermaid diagram → Mockup screen → Backlog story.
> Built by `ba-tools index update`. Orphans and gaps flagged automatically.

## Matrix

| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |
|--------|-------|---------|--------|-------|--------|
{matrix_block}

## Gaps

{gaps_body}

## Orphans

{orphans_body}

## Stale

{stale_body}
"""

    # Write under FileLock (T-02-09)
    lock = acquire_state_lock(lock_path)
    try:
        with lock:
            index_path.write_text(index_content, encoding="utf-8")
    except Timeout:
        raise BaToolsError([{
            "code": "LOCK_TIMEOUT",
            "message": (
                "INDEX.md.lock held for >10s; another writer may be active. "
                "No write was performed."
            ),
        }])

    ok_json(
        updated=str(index_path.relative_to(root)),
        req_ids=sorted(srs_req_ids),
        gaps=gap_ids,
        orphans=sorted(orphan_ids),
        stale=list(stale_slugs.keys()),
    )
