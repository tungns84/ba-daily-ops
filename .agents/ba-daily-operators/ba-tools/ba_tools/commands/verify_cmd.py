"""ba-tools verify — verbatim citation-exists gate, REQ-ID coverage, hash-match (TOOL-06).

Folds lint findings (from lint.py heuristics) and runs the hardened grounding gate:
for each 'stated' requirement, confirm the source_trace.span is a real >=12-char
verbatim substring scoped to the cited section (RESEARCH Pattern 3).

Exit contract (D-08):
  - exit 0  → ok:true, findings contain only WARN-class items (or none)
  - exit 2  → at least one FAIL-class finding (folded lint FAIL + citation FAIL)
"""

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
    p.add_argument("--reqs", required=True, help="Requirements file path (Markdown table)")
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

    # Default source document (optional — rows can specify their own)
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
    rows = _parse_md_table(reqs_text)

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

        # Resolve source doc: row's Source column > default_source
        row_source = row.get("source", "").strip()
        source_doc: Path | None = None

        if row_source:
            # Resolve the row-supplied source under --repo-root, not the CWD (WR-01).
            candidate = resolve_under_root(row_source, root)
            if is_within_root(candidate, root) and candidate.exists():
                source_doc = candidate
            else:
                # Row specifies a source but it can't be resolved
                findings.append({
                    "severity": "fail",
                    "code": "SOURCE_NOT_FOUND",
                    "req_id": req_id,
                    "message": f"Source document not found or outside root: {row_source}",
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

        # Section from row's Section column
        section = row.get("section", "").strip() or None
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
