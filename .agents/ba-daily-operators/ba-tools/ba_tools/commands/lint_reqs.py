"""ba-tools lint-requirements — flag ambiguity, atomicity, grounding, verifiability (TOOL-04, TOOL-05).

Reads a requirements Markdown table and runs deterministic heuristics.
Outputs a flat JSON envelope with a `findings` list.

Lint is the REPORTER; verify is the GATE. This command exits 0 unless
--fail-on-warn is given (not exposed in v1 — lint stays advisory, D-08).
The findings list carries severity in {fail, warn} and code identifiers
so the verify command can fold and gate on FAIL-class findings.
"""

import re
from pathlib import Path

from ba_tools.errors import BaToolsError
from ba_tools.lint import (
    check_ambiguity,
    check_atomicity,
    check_grounding,
    check_verifiability,
    detect_reqid_issues,
)
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root


# ---------------------------------------------------------------------------
# Markdown table parser
# ---------------------------------------------------------------------------


def _parse_md_table(text: str) -> list[dict]:
    """Extract rows from a Markdown pipe table, returning a list of dicts.

    Handles the common pattern:
        | ID | Statement | Status | Source |
        |----|-----------|--------|--------|
        | TOOL-01 | ... | stated | SRS §1 |

    Header names are lowercased and stripped. Leading/trailing ``|`` are
    stripped from each cell. Separator rows (``---``) are skipped.

    Returns a list of row dicts (keys = lowercase header names).
    """
    rows: list[dict] = []
    headers: list[str] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Split on '|', strip each cell
        cells = [c.strip() for c in stripped.split("|")]
        # Remove the empty strings from the leading/trailing '|'
        cells = [c for c in cells if True]  # keep all (head/tail may be empty)
        # Strip leading/trailing empty cells caused by '|...|' format
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if not cells:
            continue

        # Detect separator row. GFM alignment separators may carry colons
        # (:---, ---:, :---:) — accept an optional leading/trailing colon so
        # the separator is never mistaken for the header row (CR-02).
        if all(re.match(r'^:?-+:?$', c) for c in cells):
            continue

        if headers is None:
            headers = [c.lower() for c in cells]
            continue

        # Data row
        if len(cells) < len(headers):
            # Pad with empty strings for missing columns
            cells = cells + [""] * (len(headers) - len(cells))
        row = {headers[i]: cells[i] for i in range(len(headers))}
        rows.append(row)

    return rows


def _extract_reqs_dict(text: str) -> dict[str, str]:
    """Extract {req_id: statement} from a parsed requirements table."""
    rows = _parse_md_table(text)
    result: dict[str, str] = {}
    for row in rows:
        req_id = row.get("id", "").strip()
        statement = row.get("statement", "").strip()
        if req_id and statement:
            result[req_id] = statement
    return result


# ---------------------------------------------------------------------------
# Command registration
# ---------------------------------------------------------------------------


def register(subparsers) -> None:
    """Register the lint-requirements subcommand."""
    p = subparsers.add_parser(
        "lint-requirements",
        help="Lint a requirements document for quality issues (TOOL-04, TOOL-05)",
    )
    p.add_argument(
        "file",
        help="Path to requirements file (Markdown with pipe table)",
    )
    p.add_argument(
        "--baseline",
        default=None,
        metavar="FILE",
        help="Baseline requirements file for REQ-ID stability check (TOOL-05)",
    )
    p.set_defaults(func=run)


# ---------------------------------------------------------------------------
# Command implementation
# ---------------------------------------------------------------------------


def run(args) -> None:
    """Run the lint-requirements heuristics and output findings as JSON.

    Exit codes:
        0 — always (lint is reporter not gate; verify owns gating per D-08)
        2 — only if the requirements file cannot be found/read (BaToolsError)

    Output: ok_json(findings=[...], checked=<count>)
    Each finding: {"severity": "fail"|"warn", "code": "...", "req_id": "...", "message": "..."}
    """
    root = resolve_repo_root(getattr(args, "repo_root", None))

    # Resolve and validate the requirements file path (T-1-01)
    reqs_path = Path(args.file).resolve()
    if not is_within_root(reqs_path, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "path": str(args.file),
            "message": "Requirements file path resolves outside repo root.",
        }])
    if not reqs_path.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "path": str(args.file),
            "message": f"Requirements file not found: {args.file}",
        }])

    reqs_text = reqs_path.read_text(encoding="utf-8")
    rows = _parse_md_table(reqs_text)

    findings: list[dict] = []
    checked = 0

    for row in rows:
        req_id = row.get("id", "").strip()
        statement = row.get("statement", "").strip()

        if not req_id or not statement:
            continue  # skip header-like or empty rows

        checked += 1

        # Heuristic checks
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

    # REQ-ID stability check (TOOL-05) — only when --baseline provided
    if getattr(args, "baseline", None):
        baseline_path = Path(args.baseline).resolve()
        if not is_within_root(baseline_path, root):
            raise BaToolsError([{
                "code": "PATH_TRAVERSAL",
                "path": str(args.baseline),
                "message": "Baseline file path resolves outside repo root.",
            }])
        if not baseline_path.exists():
            raise BaToolsError([{
                "code": "FILE_NOT_FOUND",
                "path": str(args.baseline),
                "message": f"Baseline file not found: {args.baseline}",
            }])

        baseline_text = baseline_path.read_text(encoding="utf-8")
        old_reqs = _extract_reqs_dict(baseline_text)
        new_reqs = _extract_reqs_dict(reqs_text)
        stability_findings = detect_reqid_issues(old_reqs, new_reqs)
        findings.extend(stability_findings)

    ok_json(findings=findings, checked=checked)
