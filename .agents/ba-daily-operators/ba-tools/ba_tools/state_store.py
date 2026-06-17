"""
State store: FileLock guard + STATE.md merge helpers (TOOL-03, D-01/D-02).

Design decisions:
- D-01: Use filelock.FileLock(timeout=10), NOT raw os.open(O_EXCL).
- D-02: filelock is the single runtime dependency.
- STALE_SECONDS: a stale lock older than this is forcibly removed on Windows
  via os.remove(), where PermissionError is the sentinel for a live lock.
- merge_state: rewrites ONLY owned frontmatter keys (allowlist); unknown keys
  are silently ignored per T-1-08 security contract.

STATE.md format: YAML frontmatter (--- ... ---) + optional Markdown body.
The command rewrites only the keys it owns (ALLOWED_KEYS).
"""

import os
import re
import time
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout  # noqa: F401 — re-exported for state_cmd

from ba_tools.errors import BaToolsError

# Lock timeout and stale-lock threshold — both 10 seconds per D-02 / DESIGN §8
STALE_SECONDS: int = 10

# Keys that state commands are allowed to write into STATE.md frontmatter.
# Unknown keys supplied via --data are silently dropped (T-1-08).
ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "step",
        "current_step",
        "status",
        "operator",
        "uc_id",
        "uc_name",
        "phase",
        "started_at",
        "updated_at",
        "completed_at",
        "last_action",
        "next_step",
        "position",
        "iteration",
        "note",
    }
)


def acquire_state_lock(lock_path: Path) -> FileLock:
    """Return a FileLock for *lock_path* with Windows-safe stale-lock reclaim.

    If the lock file already exists and its mtime is older than STALE_SECONDS,
    this function attempts ``os.remove(lock_path)`` to clear a crash-leftover.
    On Windows, ``os.remove`` raises ``PermissionError`` when a live process
    still holds the file open — that PermissionError IS the "lock is live"
    sentinel, so it is silently swallowed and FileLock will handle the wait /
    Timeout normally (RESEARCH Pitfall 1).

    Args:
        lock_path: path to the ``.lock`` file (e.g. ``.ba-ops/STATE.md.lock``).

    Returns:
        A ``filelock.FileLock`` instance with ``timeout=STALE_SECONDS``.
        The caller must use it as a context manager.
    """
    # Stale-lock reclaim: attempt forced removal only if the file is old enough.
    if lock_path.exists():
        try:
            age = time.time() - lock_path.stat().st_mtime
        except OSError:
            age = 0.0
        if age > STALE_SECONDS:
            try:
                os.remove(lock_path)  # PermissionError = live lock — swallow it
            except PermissionError:
                pass  # Live lock: let FileLock(timeout=STALE_SECONDS) handle it

    return FileLock(str(lock_path), timeout=STALE_SECONDS)


# ---------------------------------------------------------------------------
# STATE.md read / merge helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\r?\n(.*?)\r?\n---\r?\n(.*)", re.DOTALL
)


def _parse_state(text: str) -> tuple[dict[str, Any], str]:
    """Parse STATE.md text into (frontmatter_dict, body_text).

    The frontmatter is a simplified YAML: ``key: value`` pairs only.
    Multi-line values and nested structures are NOT supported (the state
    file is machine-written and uses only scalar values).

    Returns ``({}, "")`` when the file is empty or has no frontmatter block.
    """
    if not text.strip():
        return {}, ""

    m = _FRONTMATTER_RE.match(text)
    if not m:
        # No frontmatter block — treat entire content as body
        return {}, text

    fm_text = m.group(1)
    body = m.group(2)

    fm: dict[str, Any] = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()

    return fm, body


# Canonical pipeline step names that may appear in the body "Pipeline Steps"
# table. Kept in sync with uc_status.PIPELINE_STEPS (the single reader of this
# table). A copy is held here to avoid a circular import (uc_status imports
# from state_store).
PIPELINE_STEPS: tuple[str, ...] = ("srs-analyze", "mermaid", "mockup", "index")

# Separator-row detector for the body table (GFM alignment separators allowed).
_BODY_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")
_PIPELINE_HEADING_RE = re.compile(r"^#+\s+Pipeline Steps", re.IGNORECASE)
_NEXT_HEADING_RE = re.compile(r"^#+\s+")


def update_pipeline_step(body: str, step_name: str, status: str) -> str:
    """Return *body* with the Pipeline Steps row for *step_name* set to *status*.

    Pure, deterministic string surgery — no judgement. Rewrites only the
    Status cell (column 2) of the matching data row in the '## Pipeline Steps'
    table; all other cells (e.g. 'Completed At') and all other lines are left
    byte-for-byte unchanged. If the section or the named row is not found, the
    body is returned unmodified (the caller validates *step_name* first).

    This makes the body table the single source of truth that ``uc-status``
    reads: ``state`` writes it under the STATE.md lock; ``uc-status`` reads it.
    """
    lines = body.splitlines(keepends=True)
    in_section = False
    header_skipped = False
    out: list[str] = []

    for line in lines:
        stripped = line.strip()
        if _PIPELINE_HEADING_RE.match(stripped):
            in_section = True
            header_skipped = False
            out.append(line)
            continue
        if in_section and _NEXT_HEADING_RE.match(stripped):
            in_section = False
        if not in_section or not stripped.startswith("|"):
            out.append(line)
            continue
        if _BODY_SEPARATOR_RE.match(stripped):
            header_skipped = True
            out.append(line)
            continue
        if not header_skipped:
            # Column-header row.
            header_skipped = True
            out.append(line)
            continue
        # Data row: | step | status | ... |
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and cells[0] == step_name:
            if len(cells) >= 2:
                cells[1] = status
            else:
                cells.append(status)
            # Preserve the line's trailing newline (if any) exactly.
            newline = line[len(line.rstrip("\r\n")):]
            out.append("| " + " | ".join(cells) + " |" + newline)
        else:
            out.append(line)

    return "".join(out)


def _serialize_state(fm: dict[str, Any], body: str) -> str:
    """Serialize frontmatter dict + body back to STATE.md text."""
    if not fm and not body.strip():
        return ""

    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body.rstrip())
        lines.append("")

    return "\n".join(lines)


def merge_state(existing_text: str, data: dict[str, Any], action: str) -> str:
    """Apply *action* to *existing_text* using *data* and return the new text.

    Args:
        existing_text: current contents of STATE.md (may be empty for new file).
        data: dict of keys/values from ``--data`` JSON; only ALLOWED_KEYS are
              written; unknown keys are silently ignored (T-1-08).
        action: one of ``"update"``, ``"patch"``, or ``"advance"``.

            - ``update``: replace ALL frontmatter fields with the allowlisted
              subset of *data* (prior frontmatter is discarded).
            - ``patch``: shallow-merge *data* into existing frontmatter
              (existing keys not in *data* are preserved).
            - ``advance``: increment the ``step`` field by 1 (or set to 1 if
              absent), then apply any extra allowlisted keys from *data*.

    Reserved keys (CR-03), processed for every action:
        ``pipeline_step`` + ``pipeline_status`` update the body "Pipeline
        Steps" table row (the single source of truth read by ``uc-status``).
        ``pipeline_step`` must be a canonical step name; ``pipeline_status``
        must be a non-empty string. These keys are consumed here and are never
        written into frontmatter. Use the ``patch`` action to mark a step
        without discarding existing frontmatter.

    Returns:
        The serialized STATE.md string (YAML frontmatter + body).

    Raises:
        ValueError: if *action* is not a recognised value.
    """
    fm, body = _parse_state(existing_text)

    # Reserved body-table directive (CR-03): pipeline_step + pipeline_status
    # update the body "Pipeline Steps" table that uc-status reads, making it the
    # single source of truth for pipeline position. These are NOT frontmatter
    # keys and are never written into frontmatter.
    pipeline_step = data.get("pipeline_step")
    pipeline_status = data.get("pipeline_status")
    if pipeline_step is not None:
        if pipeline_step not in PIPELINE_STEPS:
            raise BaToolsError([{
                "code": "UNKNOWN_PIPELINE_STEP",
                "message": (
                    f"pipeline_step {pipeline_step!r} is not a canonical step "
                    f"(expected one of {list(PIPELINE_STEPS)})."
                ),
            }])
        if not isinstance(pipeline_status, str) or not pipeline_status.strip():
            raise BaToolsError([{
                "code": "MISSING_PIPELINE_STATUS",
                "message": "pipeline_step requires a non-empty pipeline_status string.",
            }])
        body = update_pipeline_step(body, pipeline_step, pipeline_status.strip())

    # Filter data to allowlisted keys only (T-1-08 security contract).
    # The reserved pipeline_* directive keys are consumed above, never written.
    safe_data = {k: v for k, v in data.items() if k in ALLOWED_KEYS}

    if action == "update":
        # Replace entire frontmatter with safe_data
        fm = safe_data

    elif action == "patch":
        # Shallow-merge: existing keys not in safe_data are kept
        fm.update(safe_data)

    elif action == "advance":
        # Allow data to override step explicitly; otherwise auto-increment.
        if "step" in safe_data:
            fm["step"] = safe_data.pop("step")
        else:
            # Fail loudly instead of silently resetting to 1 (CR-04): a silent
            # reset of a non-numeric step would lose durable pipeline position
            # with no signal to the caller.
            try:
                current = int(fm.get("step", 0))
            except (TypeError, ValueError) as exc:
                raise BaToolsError([{
                    "code": "STEP_NOT_NUMERIC",
                    "message": (
                        f"Cannot advance: step is non-numeric ({fm.get('step')!r}). "
                        "Pass an explicit step in --data to set it."
                    ),
                }]) from exc
            fm["step"] = str(current + 1)
        fm.update(safe_data)

    else:
        raise ValueError(f"Unknown action: {action!r}")

    return _serialize_state(fm, body)
