"""ba-tools discovery — capture and list iteration discoveries (TOOL-12)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "discovery",
        help="Capture and list iteration discoveries",
    )
    sub = p.add_subparsers(dest="discovery_action", required=True)

    add_p = sub.add_parser("add", help="Append a discovery to .ba-ops/discoveries.jsonl")
    add_p.add_argument("--text", required=True, help="Discovery text")
    add_p.add_argument("--uc", default=None, help="Associated UC ID (optional)")
    add_p.set_defaults(func=run)

    list_p = sub.add_parser("list", help="List all discoveries")
    list_p.add_argument("--uc", default=None, help="Filter by UC ID (optional)")
    list_p.set_defaults(func=run)

    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "discovery"}])
