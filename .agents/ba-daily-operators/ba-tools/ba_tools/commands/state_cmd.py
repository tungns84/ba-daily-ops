"""ba-tools state — update/patch/advance .ba-ops/STATE.md with lockfile guard (TOOL-03)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "state",
        help="Update .ba-ops/STATE.md (guarded by filelock)",
    )
    p.add_argument(
        "action",
        choices=["update", "patch", "advance"],
        help="Write action to perform",
    )
    p.add_argument("--data", required=True, help="JSON string of fields to write")
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "state"}])
