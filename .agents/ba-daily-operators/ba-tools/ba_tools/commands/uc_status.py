"""ba-tools uc-status — return single-UC pipeline state and next_step (TOOL-09).

Design §5: `uc-status` returns a pure read + deterministic computation:
  uc         — the UC ID from STATE.md (or null if not set)
  steps      — dict of step name → status from STATE.md Pipeline Steps table
  next_step  — first step in canonical spine order not yet 'complete'; or 'done'

Canonical spine order (DESIGN §2 + §8):
  srs-analyze → mermaid → mockup → index

This is a pure read command — no agent invocation, no route inference.
Missing STATE.md raises BaToolsError NO_STATE (exit 2).
"""

import re
from pathlib import Path

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root
from ba_tools.state_store import _parse_state

# Canonical pipeline step order (DESIGN §2 — ba-uc conductor sequence)
PIPELINE_STEPS: list[str] = ["srs-analyze", "mermaid", "mockup", "index"]

# Status values that mean "completed" (case-insensitive check)
_COMPLETE_STATUSES: frozenset[str] = frozenset({"complete", "completed", "done"})

# Regex to parse a Markdown table row:  | cell | cell | cell |
_TABLE_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|")


def _parse_pipeline_steps(body: str) -> dict[str, str]:
    """Extract step statuses from the '## Pipeline Steps' table in STATE.md body.

    Returns a dict mapping step name -> status string.
    Missing steps default to 'pending'.
    """
    steps: dict[str, str] = {step: "pending" for step in PIPELINE_STEPS}

    # Find the Pipeline Steps section
    in_section = False
    header_skipped = False

    for line in body.splitlines():
        # Detect section heading
        if re.match(r"^#+\s+Pipeline Steps", line, re.IGNORECASE):
            in_section = True
            header_skipped = False
            continue

        # Stop at next heading
        if in_section and re.match(r"^#+\s+", line):
            break

        if not in_section:
            continue

        # Skip header and separator rows
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # GFM alignment separators may carry colons (|:---|:---:|) — accept
        # colons and whitespace so the separator is correctly skipped and the
        # column-header row is not mistaken for a data row (CR-02).
        if re.match(r"^\|[\s:|-]+\|$", stripped):
            header_skipped = True
            continue
        if not header_skipped:
            # This is the column header row
            header_skipped = True
            continue

        # Parse data row — format: | step | status | ... |
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) >= 2:
            step_name = cells[0].strip()
            status = cells[1].strip()
            if step_name in steps:
                steps[step_name] = status

    return steps


def _compute_next_step(steps: dict[str, str]) -> str:
    """Return the first incomplete step in canonical order, or 'done' if all complete."""
    for step in PIPELINE_STEPS:
        status = steps.get(step, "pending").lower()
        if status not in _COMPLETE_STATUSES:
            return step
    return "done"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "uc-status",
        help="Return pipeline state and next_step for a use-case (TOOL-09)",
    )
    p.add_argument(
        "--uc",
        default=None,
        metavar="UC_ID",
        help="Use-case ID to query (e.g. UC-001); defaults to current UC in STATE.md",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    """Read STATE.md, compute pipeline state + next_step, emit JSON."""
    root = resolve_repo_root(getattr(args, "repo_root", None))
    state_path = root / ".ba-ops" / "STATE.md"

    if not state_path.exists():
        raise BaToolsError([{
            "code": "NO_STATE",
            "message": (
                ".ba-ops/STATE.md not found. "
                "Run `ba-tools init <operator>` first to scaffold the project."
            ),
            "path": str(state_path),
        }])

    text = state_path.read_text(encoding="utf-8")
    fm, body = _parse_state(text)

    # Determine UC identifier: --uc arg > STATE.md uc_id > null
    uc_id = getattr(args, "uc", None) or fm.get("uc_id") or None
    # Normalize empty string to None
    if uc_id == "":
        uc_id = None

    # Parse pipeline step statuses from the Markdown body table
    steps = _parse_pipeline_steps(body)

    # Deterministically compute next_step from the static spine order
    next_step = _compute_next_step(steps)

    ok_json(
        uc=uc_id,
        steps=steps,
        next_step=next_step,
    )
