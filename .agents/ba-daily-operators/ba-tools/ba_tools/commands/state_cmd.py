"""ba-tools state — update/patch/advance .ba-ops/STATE.md with lockfile guard (TOOL-03).

Every write to STATE.md is guarded by a FileLock(timeout=10) (D-01/D-02).
Stale locks (mtime > 10s) are reclaimed Windows-safely (RESEARCH Pattern 2,
Pitfall 1). A Timeout exception surfaces as BaToolsError(LOCK_TIMEOUT), exit 2.
Unguarded fallback on Timeout is explicitly forbidden (RESEARCH Anti-Patterns).
"""

import json
from pathlib import Path

from filelock import Timeout

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root
from ba_tools.state_store import acquire_state_lock, merge_state


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "state",
        help="Update .ba-ops/STATE.md (guarded by FileLock, timeout=10s)",
    )
    p.add_argument(
        "action",
        choices=["update", "patch", "advance"],
        help="Write action to perform on STATE.md",
    )
    p.add_argument(
        "--data",
        required=True,
        help="JSON string of key/value fields to write into STATE.md frontmatter",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    """Execute the state update/patch/advance command.

    Steps:
      1. Resolve repo root and ensure .ba-ops/ exists.
      2. Parse --data as JSON (BAD_DATA on failure — T-1-08).
      3. Acquire FileLock with stale-lock reclaim (TOOL-03 / D-01).
      4. Inside the lock: read-modify-write STATE.md with merge_state().
      5. On Timeout: raise BaToolsError(LOCK_TIMEOUT) — NEVER an unguarded write.
      6. On success: print ok_json(action=...).
    """
    root: Path = resolve_repo_root(args.repo_root)
    ba_ops: Path = root / ".ba-ops"
    state_path: Path = ba_ops / "STATE.md"
    lock_path: Path = ba_ops / "STATE.md.lock"

    # Ensure .ba-ops/ exists (idempotent)
    ba_ops.mkdir(parents=True, exist_ok=True)

    # Validate --data JSON (T-1-08: structure validation before writing)
    try:
        data: dict = json.loads(args.data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise BaToolsError(
            [
                {
                    "code": "BAD_DATA",
                    "message": f"--data is not valid JSON: {exc}",
                }
            ]
        ) from exc

    if not isinstance(data, dict):
        raise BaToolsError(
            [
                {
                    "code": "BAD_DATA",
                    "message": "--data must be a JSON object (dict), not a scalar or array",
                }
            ]
        )

    # Acquire lock with Windows-safe stale-lock reclaim
    lock = acquire_state_lock(lock_path)

    try:
        with lock:
            # Read-modify-write STATE.md (entirely within the lock)
            existing: str = (
                state_path.read_text(encoding="utf-8")
                if state_path.exists()
                else ""
            )
            new_text: str = merge_state(existing, data, args.action)
            state_path.write_text(new_text, encoding="utf-8")

    except Timeout:
        # LOCK_TIMEOUT — explicitly forbidden from falling back to unguarded write
        raise BaToolsError(
            [
                {
                    "code": "LOCK_TIMEOUT",
                    "message": (
                        "STATE.md.lock held for >10s; another writer may be active. "
                        "No write was performed."
                    ),
                }
            ]
        )

    ok_json(action=args.action)
