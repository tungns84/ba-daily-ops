"""ba-tools verify — verbatim citation-exists gate, REQ-ID coverage, hash-match (TOOL-06).

Folds lint findings (from lint.py heuristics) and runs the hardened grounding gate:
for each 'stated' requirement, confirm the source_trace.span is a real >=12-char
verbatim substring scoped to the cited section (RESEARCH Pattern 3).

Exit contract (D-08):
  - exit 0  → ok:true, findings contain only WARN-class items (or none)
  - exit 2  → at least one FAIL-class finding (folded lint FAIL + citation FAIL)
"""

import json
from pathlib import Path

from ba_tools.citation import citation_exists
from ba_tools.commands.lint_reqs import _parse_md_table
from ba_tools.errors import BaToolsError
from ba_tools.lint import (
    check_ambiguity,
    check_atomicity,
    check_grounding,
    check_verifiability,
)
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root, resolve_under_root


def register(subparsers) -> None:
    """Register the verify subcommand."""
    p = subparsers.add_parser(
        "verify",
        help="Run the verification gate (citation-exists, lint fold, hash-match) (TOOL-06)",
    )
    p.add_argument("--reqs", required=True, help="Requirements file path (Markdown table or JSON)")
    p.add_argument(
        "--reqs-format",
        choices=["auto", "md", "json"],
        default="auto",
        help="Requirements format: auto (detect from extension), md, or json (default: auto)",
    )
    p.add_argument(
        "--source",
        default=None,
        help="Default source document to cite from (can be overridden per-row by Source column)",
    )
    p.add_argument(
        "--cite-scope",
        choices=["section", "document"],
        default="section",
        help="Citation search scope (default: section). --cite-scope document overrides per-row.",
    )
    p.set_defaults(func=run)


def _validate_reqs_schema(payload) -> None:
    """Validate the parsed JSON requirements payload structure.

    Raises BaToolsError with SCHEMA_INVALID when the top-level shape is wrong.
    Raises BaToolsError with INVALID_REQUIREMENT for per-requirement violations.

    Valid shape:
      - A list of requirement objects, OR
      - An object with a "requirements" key whose value is a list.

    Per-requirement rules:
      - Must have "id" (non-empty string)
      - Must have "statement" (non-empty string)
      - "status" must be in {"stated", "derived"} if present
      - A "stated" requirement must have source_trace.span (non-empty)
    """
    # Normalize: accept list or {"requirements": [...]}
    if isinstance(payload, list):
        reqs_list = payload
    elif isinstance(payload, dict):
        if "requirements" not in payload:
            raise BaToolsError([{
                "code": "SCHEMA_INVALID",
                "message": (
                    "requirements.json must be a list or an object with a "
                    "'requirements' key."
                ),
            }])
        if not isinstance(payload["requirements"], list):
            raise BaToolsError([{
                "code": "SCHEMA_INVALID",
                "message": (
                    "'requirements' must be a list, not "
                    f"{type(payload['requirements']).__name__}."
                ),
            }])
        reqs_list = payload["requirements"]
    else:
        raise BaToolsError([{
            "code": "SCHEMA_INVALID",
            "message": (
                f"requirements.json payload must be a list or object, not "
                f"{type(payload).__name__}."
            ),
        }])

    for idx, req in enumerate(reqs_list):
        if not isinstance(req, dict):
            raise BaToolsError([{
                "code": "INVALID_REQUIREMENT",
                "index": idx,
                "message": f"Requirement at index {idx} must be an object.",
            }])

        req_id = req.get("id", "")
        if not req_id or not str(req_id).strip():
            raise BaToolsError([{
                "code": "INVALID_REQUIREMENT",
                "index": idx,
                "message": f"Requirement at index {idx} is missing 'id' field.",
            }])

        statement = req.get("statement", "")
        if not statement or not str(statement).strip():
            raise BaToolsError([{
                "code": "INVALID_REQUIREMENT",
                "req_id": req_id,
                "message": f"Requirement '{req_id}' is missing 'statement' field.",
            }])

        status = str(req.get("status", "stated")).strip().lower()
        if status not in {"stated", "derived"}:
            raise BaToolsError([{
                "code": "INVALID_REQUIREMENT",
                "req_id": req_id,
                "message": (
                    f"Requirement '{req_id}' has invalid status '{status}'. "
                    "Must be 'stated' or 'derived'."
                ),
            }])

        if status == "stated":
            source_trace = req.get("source_trace", {})
            if isinstance(source_trace, dict):
                span = source_trace.get("span", "")
            else:
                span = str(source_trace) if source_trace else ""
            if not span or not str(span).strip():
                raise BaToolsError([{
                    "code": "INVALID_REQUIREMENT",
                    "req_id": req_id,
                    "message": (
                        f"Stated requirement '{req_id}' is missing source_trace.span. "
                        "Add a >=12-char verbatim span from the cited section."
                    ),
                }])


def _parse_reqs(reqs_text: str, reqs_path: Path, reqs_format: str) -> list[dict]:
    """Dispatch to the appropriate parser based on reqs_format.

    Args:
        reqs_text: raw text content of the requirements file.
        reqs_path: Path to the requirements file (used for format auto-detection).
        reqs_format: "auto", "md", or "json".

    Returns:
        A list of row dicts normalized for the verify pipeline.
        JSON rows carry: id, statement, status, span, section, source (cited doc path string),
        AND the original source_trace dict under "source_trace" so check_grounding
        (dict-aware after plan 02-01) reads it correctly.

    Raises:
        BaToolsError with MALFORMED_JSON if json.loads fails.
        BaToolsError with SCHEMA_INVALID / INVALID_REQUIREMENT from _validate_reqs_schema.
    """
    # Resolve "auto" to concrete format
    effective_format = reqs_format
    if reqs_format == "auto":
        if reqs_path.suffix.lower() == ".json":
            effective_format = "json"
        else:
            effective_format = "md"

    if effective_format == "md":
        return _parse_md_table(reqs_text)

    # JSON path
    try:
        payload = json.loads(reqs_text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise BaToolsError([{
            "code": "MALFORMED_JSON",
            "message": f"Could not parse requirements.json: {exc}",
        }]) from exc

    # Schema validation before building rows
    _validate_reqs_schema(payload)

    # Normalize to list
    if isinstance(payload, list):
        reqs_list = payload
    else:
        reqs_list = payload["requirements"]

    rows: list[dict] = []
    for req in reqs_list:
        req_id = str(req.get("id", "")).strip()
        statement = str(req.get("statement", "")).strip()
        status = str(req.get("status", "stated")).strip().lower()

        source_trace = req.get("source_trace", {})
        if isinstance(source_trace, dict):
            doc = str(source_trace.get("doc", "") or "").strip()
            span = str(source_trace.get("span", "") or "").strip()
            raw_section = source_trace.get("section")
            # section:null → None (document scope per D-03)
            section = str(raw_section).strip() if raw_section is not None else None
        else:
            doc = str(source_trace).strip() if source_trace else ""
            span = ""
            section = None

        row = {
            "id": req_id,
            "statement": statement,
            "status": status,
            # Flattened fields for citation pipeline
            "source": doc,          # cited doc path string (from source_trace.doc)
            "span": span,
            "section": section,
            # Preserve original source_trace dict for check_grounding (dict-aware, plan 02-01)
            "source_trace": source_trace,
        }
        rows.append(row)

    return rows


def run(args) -> None:
    """Run the verify gate.

    Reads the requirements file, folds lint heuristics, then for each 'stated'
    requirement checks citation_exists for the row's span in the cited section.

    Exit codes:
        0 — ok:true with only WARN-class findings (or no findings)
        2 — at least one FAIL-class finding (BaToolsError with failures list)

    Source: D-07, D-08, RESEARCH Pattern 3, ROADMAP criteria 1 & 4.
    """
    root = resolve_repo_root(getattr(args, "repo_root", None))

    # Resolve and validate requirements path (T-1-01).
    # Relative paths resolve under --repo-root, not the CWD (WR-01).
    reqs_path = resolve_under_root(args.reqs, root)
    if not is_within_root(reqs_path, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "path": str(args.reqs),
            "message": "Requirements file path resolves outside repo root.",
        }])
    if not reqs_path.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "path": str(args.reqs),
            "message": f"Requirements file not found: {args.reqs}",
        }])

    # Default source document (optional — rows/JSON source_trace.doc can override)
    default_source: Path | None = None
    if getattr(args, "source", None):
        source_path = resolve_under_root(args.source, root)
        if not is_within_root(source_path, root):
            raise BaToolsError([{
                "code": "PATH_TRAVERSAL",
                "path": str(args.source),
                "message": "Source document path resolves outside repo root.",
            }])
        if not source_path.exists():
            raise BaToolsError([{
                "code": "FILE_NOT_FOUND",
                "path": str(args.source),
                "message": f"Source document not found: {args.source}",
            }])
        default_source = source_path

    reqs_text = reqs_path.read_text(encoding="utf-8")
    reqs_format = getattr(args, "reqs_format", "auto")
    rows = _parse_reqs(reqs_text, reqs_path, reqs_format)

    findings: list[dict] = []
    checked = 0

    for row in rows:
        req_id = row.get("id", "").strip()
        statement = row.get("statement", "").strip()

        if not req_id or not statement:
            continue  # skip empty/header rows

        checked += 1

        # --- Fold lint heuristics (TOOL-04) ---
        ambiguity = check_ambiguity(req_id, statement)
        if ambiguity:
            findings.append(ambiguity)

        verifiability = check_verifiability(req_id, statement)
        if verifiability:
            findings.append(verifiability)

        atomicity = check_atomicity(req_id, statement)
        if atomicity:
            findings.append(atomicity)

        grounding = check_grounding(req_id, row)
        if grounding:
            findings.append(grounding)

        # --- Citation-exists gate (TOOL-06) ---
        # Only check stated requirements with a span
        status = row.get("status", "stated").strip().lower()
        if status not in {"stated", ""}:
            continue  # skip derived/inferred for citation check

        span = row.get("span", "").strip()
        if not span:
            # No span column — skip citation check for this row
            continue

        # Resolve source doc: for JSON rows, source_trace.doc takes priority.
        # For Markdown rows, row["source"] is the Source column value.
        # In both cases the "source" key on the row carries the cited doc path.
        # CLI --source is the fallback ONLY when the row supplies no doc.
        row_source = row.get("source", "").strip()
        source_doc: Path | None = None

        if row_source:
            # Resolve the row-supplied source under --repo-root (WR-01).
            candidate = resolve_under_root(row_source, root)
            if not is_within_root(candidate, root):
                findings.append({
                    "severity": "fail",
                    "code": "PATH_TRAVERSAL",
                    "req_id": req_id,
                    "path": row_source,
                    "message": f"Source document path resolves outside repo root: {row_source}",
                })
                continue
            if candidate.exists():
                source_doc = candidate
            else:
                findings.append({
                    "severity": "fail",
                    "code": "SOURCE_NOT_FOUND",
                    "req_id": req_id,
                    "message": f"Source document not found: {row_source}",
                })
                continue

        if source_doc is None:
            source_doc = default_source

        if source_doc is None:
            # No source available — cannot verify
            findings.append({
                "severity": "fail",
                "code": "SOURCE_NOT_PROVIDED",
                "req_id": req_id,
                "message": "No source document available for citation check.",
            })
            continue

        # Section from row's section field (may be None for document-scope, D-03)
        section = row.get("section")
        # Normalize empty string to None (both trigger document-scope in citation_exists)
        if section is not None and not str(section).strip():
            section = None

        cite_scope = getattr(args, "cite_scope", "section")

        found = citation_exists(source_doc, span, section, cite_scope=cite_scope)
        if not found:
            findings.append({
                "severity": "fail",
                "code": "CITATION_NOT_FOUND",
                "req_id": req_id,
                "message": (
                    f"Span not found in source"
                    + (f" section '{section}'" if section else "")
                    + f": '{span[:50]}{'...' if len(span) > 50 else ''}'"
                ),
            })

    # Gate: any FAIL-class finding → exit 2 (D-08)
    fail_findings = [f for f in findings if f.get("severity") == "fail"]
    if fail_findings:
        raise BaToolsError(fail_findings)

    # All clear or WARN-only → exit 0
    ok_json(findings=findings, checked=checked)
