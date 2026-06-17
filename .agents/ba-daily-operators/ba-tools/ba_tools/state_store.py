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

    Returns:
        The serialized STATE.md string (YAML frontmatter + body).

    Raises:
        ValueError: if *action* is not a recognised value.
    """
    fm, body = _parse_state(existing_text)

    # Filter data to allowlisted keys only (T-1-08 security contract)
    safe_data = {k: v for k, v in data.items() if k in ALLOWED_KEYS}

    if action == "update":
        # Replace entire frontmatter with safe_data
        fm = safe_data

    elif action == "patch":
        # Shallow-merge: existing keys not in safe_data are kept
        fm.update(safe_data)

    elif action == "advance":
        # Increment step counter, then apply extra keys
        try:
            current = int(fm.get("step", 0))
        except (TypeError, ValueError):
            current = 0
        # Allow data to override step explicitly; otherwise auto-increment
        if "step" in safe_data:
            fm["step"] = safe_data.pop("step")
        else:
            fm["step"] = str(current + 1)
        fm.update(safe_data)

    else:
        raise ValueError(f"Unknown action: {action!r}")

    return _serialize_state(fm, body)
